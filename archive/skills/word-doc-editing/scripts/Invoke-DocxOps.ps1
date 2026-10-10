<#
.SYNOPSIS
    Apply structural operations to a .docx through Word, with tracked changes on.

.DESCRIPTION
    Invoke-DocxEdits.ps1 rewrites text inside a paragraph. This script does the things that
    change document structure: delete a run of paragraphs, delete a table, insert new styled
    paragraphs, insert a table, restyle a paragraph. Word performs every operation, so
    tracked changes are genuine revisions and formatting is inherited from the surrounding
    document rather than invented.

    Paragraphs are addressed by anchor text rather than by index, because index numbers
    shift as soon as anything is inserted or deleted. Anchors must be unique; an ambiguous
    anchor is reported and skipped rather than guessed at.

.PARAMETER Path
    Source .docx. Never modified — the script always works on a copy.

.PARAMETER Ops
    Path to the JSON operations manifest, or an array of operation objects.

    Every operation takes an "id" (label for the report) and a "note" (rationale, carried
    into the change log). Supported "op" values:

      replace      find, replace [, scope]        Text rewrite inside one paragraph.
      restyle      anchor, style                  Change a paragraph's style.
      deleteParas  anchor [, through] [, count]   Delete from anchor through a second anchor
                                                  (inclusive), or `count` paragraphs.
      deleteTable  anchor                         Delete the table containing the anchor text.
      insertAfter  anchor, blocks[]               Insert paragraphs after the anchor paragraph.
      insertBefore anchor, blocks[]               Insert paragraphs before the anchor paragraph.
      insertTable  anchor, rows[][] [, style]     Insert a table after the anchor paragraph.

    A "block" is { "text": "...", "style": "Body Text" }. Style names must already exist in
    the document; the script verifies each one up front and refuses unknown styles.

.PARAMETER OutFile
    Destination .docx. Defaults to "<name>.revised.docx" beside the source.

.PARAMETER Author
    Name stamped on the tracked revisions.

.PARAMETER ChangeLog
    Write a CSV change log here — one row per operation with status, page, and rationale.

.PARAMETER NoTrack
    Apply operations as clean changes with revision tracking off.

.EXAMPLE
    .\Invoke-DocxOps.ps1 '.\plan.docx' .\edits\01-restructure.json -ChangeLog .\log\01.csv

.EXAMPLE
    .\Invoke-DocxOps.ps1 '.\plan.docx' .\edits\01-restructure.json -WhatIf | Format-Table -AutoSize
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [Parameter(Mandatory, Position = 1)][object]$Ops,
    [string]$OutFile,
    [string]$Author,
    [string]$ChangeLog,
    [switch]$NoTrack
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

if ($Ops -is [string]) {
    $manifest = Get-Content -LiteralPath $Ops -Raw -Encoding utf8 | ConvertFrom-Json
} else { $manifest = $Ops }
if ($manifest -isnot [array]) { $manifest = @($manifest) }

function Get-Prop { param($Obj, $Name, $Default)
    if ($Obj -and $Obj.PSObject.Properties[$Name]) { $Obj.$Name } else { $Default }
}

<#
    Fill a paragraph without destroying it.

    Paragraph.Range includes the trailing paragraph mark, so the obvious
    `$para.Range.Text = 'x'` deletes that mark and merges the paragraph into the one
    after it. Chain a few of those together and each inserted block silently swallows
    the next. Write to the range that stops one character short of the mark instead.
#>
function Set-ParagraphText {
    param(
        [Parameter(Mandatory)]$Document,
        [Parameter(Mandatory)]$Paragraph,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text
    )
    $r = $Paragraph.Range
    $Document.Range($r.Start, [Math]::Max($r.Start, $r.End - 1)).Text = $Text
}

if (-not $OutFile) {
    $src = Get-Item -LiteralPath $Path
    $OutFile = Join-Path $src.DirectoryName "$($src.BaseName).revised$($src.Extension)"
}
$working = New-WorkingCopy -Path $Path -Destination $OutFile

$word = $null
$report = [System.Collections.Generic.List[object]]::new()

try {
    $word = New-WordApp
    if ($Author) { $word.UserName = $Author }

    $doc = Open-WordDocument -Word $word -Path $working -Writable
    $doc.TrackRevisions = (-not $NoTrack)
    $revisionsBefore = $doc.Revisions.Count
    $wdPageNumber = Get-WdConst wdActiveEndPageNumber

    # --- style validation up front -------------------------------------------------
    $available = @{}
    foreach ($s in $doc.Styles) { $available[$s.NameLocal] = $true }
    $wanted = [System.Collections.Generic.HashSet[string]]::new()
    foreach ($o in $manifest) {
        $st = Get-Prop $o 'style' $null
        if ($st) { [void]$wanted.Add($st) }
        foreach ($b in @(Get-Prop $o 'blocks' @())) {
            $bs = Get-Prop $b 'style' $null
            if ($bs) { [void]$wanted.Add($bs) }
        }
    }
    $unknown = @($wanted | Where-Object { -not $available.ContainsKey($_) })
    if ($unknown) {
        throw "Unknown style(s): $($unknown -join ', '). Available styles include: " +
              (($available.Keys | Sort-Object | Select-Object -First 40) -join ', ')
    }

    # --- paragraph index, rebuilt whenever structure changes -----------------------
    $paras = $null
    function Sync-Index {
        $script:paras = [System.Collections.Generic.List[object]]::new()
        $i = 0
        foreach ($p in $doc.Paragraphs) {
            $i++
            $script:paras.Add([pscustomobject]@{ Index = $i; Text = ($p.Range.Text -replace "[`r`a]", '') })
        }
    }
    Sync-Index
    Write-Verbose "Indexed $($paras.Count) paragraphs."

    # Locate the single paragraph containing $needle. Returns index, or 0 / -n for failure.
    function Find-Anchor {
        param([string]$Needle)
        $hits = @($script:paras | Where-Object { $_.Text.Contains($Needle) })
        if ($hits.Count -eq 0) { return 0 }
        if ($hits.Count -gt 1) { return -$hits.Count }
        return $hits[0].Index
    }

    foreach ($o in $manifest) {
        $id     = [string](Get-Prop $o 'id' '')
        $note   = [string](Get-Prop $o 'note' '')
        $op     = [string](Get-Prop $o 'op' 'replace')
        $anchor = [string](Get-Prop $o 'anchor' '')

        $status = 'OK'; $detail = ''; $page = ''
        $structural = $false

        try {
            # Resolve the anchor for every op that needs one.
            $ai = 0
            if ($op -ne 'replace') {
                # anchorIndex addresses a paragraph that has no unique text of its own —
                # a stray empty heading, for instance. Verify the index with
                # Get-DocxOutline against the same file immediately before using it.
                $byIndex = [int](Get-Prop $o 'anchorIndex' 0)
                if ($byIndex -gt 0) {
                    if ($byIndex -gt $script:paras.Count) {
                        $status = 'NOT FOUND'; $detail = "anchorIndex $byIndex is past the last paragraph ($($script:paras.Count))"
                    } else {
                        $ai = $byIndex
                        $anchor = $script:paras[$byIndex - 1].Text
                    }
                }
                elseif (-not $anchor) { throw "op '$op' requires an anchor or anchorIndex" }
                else { $ai = Find-Anchor $anchor }
                if ($ai -eq 0)  { $status = 'NOT FOUND'; $detail = "anchor not present: '$anchor'" }
                elseif ($ai -lt 0) { $status = 'AMBIGUOUS'; $detail = "anchor matches $([Math]::Abs($ai)) paragraphs; lengthen it" }
            }

            if ($status -eq 'OK') {
                switch ($op) {

                    'replace' {
                        $find = [string]$o.find; $rep = [string]$o.replace
                        $scope = [string](Get-Prop $o 'scope' 'unique')
                        $sites = @()
                        foreach ($p in $script:paras) {
                            $at = 0
                            while ($at -le ($p.Text.Length - $find.Length) -and
                                   ($at = $p.Text.IndexOf($find, $at, [StringComparison]::Ordinal)) -ge 0) {
                                $sites += [pscustomobject]@{ Para = $p.Index; Offset = $at }
                                $at += [Math]::Max(1, $find.Length)
                            }
                        }
                        if ($sites.Count -eq 0) { $status = 'NOT FOUND'; $detail = "text absent: '$find'"; break }
                        if ($sites.Count -gt 1 -and $scope -eq 'unique') {
                            $status = 'AMBIGUOUS'; $detail = "$($sites.Count) matches; lengthen 'find' or set scope"; break
                        }
                        $targets = if ($scope -eq 'all') { @($sites) } else { @($sites[0]) }
                        $targets = @($targets | Sort-Object Para, Offset -Descending)

                        # Narrow to the changed span so untouched flanks keep their formatting.
                        $i0 = 0
                        while ($i0 -lt $find.Length -and $i0 -lt $rep.Length -and $find[$i0] -ceq $rep[$i0]) { $i0++ }
                        $j0 = 0
                        while ($j0 -lt ($find.Length - $i0) -and $j0 -lt ($rep.Length - $i0) -and
                               $find[$find.Length-1-$j0] -ceq $rep[$rep.Length-1-$j0]) { $j0++ }
                        $cutLen = $find.Length - $i0 - $j0
                        $newTxt = $rep.Substring($i0, $rep.Length - $i0 - $j0)

                        foreach ($t in $targets) {
                            $pr = $doc.Paragraphs.Item($t.Para).Range
                            $s = $pr.Start + $t.Offset + $i0
                            $e = $s + $cutLen
                            $expected = $find.Substring($i0, $cutLen)
                            $actual = if ($cutLen -gt 0) { $doc.Range($s, $e).Text } else { '' }
                            if ($cutLen -gt 0 -and $actual -cne $expected) {
                                $status = 'SKIPPED'
                                $detail = "range check failed (expected '$expected', found '$actual'); paragraph likely contains a field"
                                break
                            }
                            if ($PSCmdlet.ShouldProcess("paragraph $($t.Para)", "replace '$expected' -> '$newTxt'")) {
                                $tr = $doc.Range($s, $e)
                                $page = $tr.Information($wdPageNumber)
                                $tr.Text = $newTxt
                            }
                            $script:paras[$t.Para - 1].Text = ($doc.Paragraphs.Item($t.Para).Range.Text -replace "[`r`a]", '')
                        }
                        if ($status -eq 'OK') { $detail = "'$($find.Substring($i0,$cutLen))' -> '$newTxt'" }
                    }

                    'restyle' {
                        $style = [string]$o.style
                        $p = $doc.Paragraphs.Item($ai)
                        $page = $p.Range.Information($wdPageNumber)
                        $was = $p.Style.NameLocal
                        if ($PSCmdlet.ShouldProcess("paragraph $ai", "restyle '$was' -> '$style'")) {
                            $p.Style = $style
                        }
                        $detail = "'$was' -> '$style'"
                    }

                    'deleteParas' {
                        $through = [string](Get-Prop $o 'through' '')
                        $count   = [int](Get-Prop $o 'count' 1)
                        $last = $ai + $count - 1
                        if ($through) {
                            $ti = Find-Anchor $through
                            if ($ti -eq 0)     { $status='NOT FOUND'; $detail="'through' anchor not present: '$through'"; break }
                            if ($ti -lt 0)     { $status='AMBIGUOUS'; $detail="'through' anchor matches $([Math]::Abs($ti)) paragraphs"; break }
                            if ($ti -lt $ai)   { $status='SKIPPED';  $detail="'through' anchor ($ti) precedes start ($ai)"; break }
                            $last = $ti
                        }
                        $startPos = $doc.Paragraphs.Item($ai).Range.Start
                        $endPos   = $doc.Paragraphs.Item($last).Range.End
                        $rng = $doc.Range($startPos, $endPos)
                        $page = $rng.Information($wdPageNumber)
                        $words = ($rng.Text -split '\s+' | Where-Object { $_ }).Count

                        # Deletion is the one operation that cannot be reviewed after the fact if
                        # it lands wrong, so verify against the live document rather than trusting
                        # the paragraph index. The resolved range must begin with the anchor and,
                        # where a 'through' anchor was given, end with it.
                        $liveStart = ($doc.Paragraphs.Item($ai).Range.Text -replace "[`r`a]", '')
                        $liveEnd   = ($doc.Paragraphs.Item($last).Range.Text -replace "[`r`a]", '')
                        if (-not $liveStart.Contains($anchor)) {
                            $status = 'SKIPPED'
                            $detail = "refused: paragraph $ai does not contain the anchor (found '" +
                                      $liveStart.Substring(0, [Math]::Min(60, $liveStart.Length)) + "')"
                            break
                        }
                        if ($through -and -not $liveEnd.Contains($through)) {
                            $status = 'SKIPPED'
                            $detail = "refused: paragraph $last does not contain the 'through' anchor (found '" +
                                      $liveEnd.Substring(0, [Math]::Min(60, $liveEnd.Length)) + "')"
                            break
                        }
                        $maxParas = [int](Get-Prop $o 'maxParas' 60)
                        if ((($last - $ai) + 1) -gt $maxParas) {
                            $status = 'SKIPPED'
                            $detail = "refused: range spans $((($last-$ai)+1)) paragraphs, above the $maxParas limit; tighten the anchors or raise maxParas"
                            break
                        }

                        # Word will not delete the final paragraph mark of a table cell, and this
                        # document is one large form table, so most blocks end at a cell boundary.
                        # Shrink off that last mark and leave an empty paragraph behind.
                        $keptMark = $false
                        if ($rng.Tables.Count -gt 0) {
                            $cellEnd = $rng.Cells.Item($rng.Cells.Count).Range.End
                            if ($endPos -ge $cellEnd) {
                                $rng = $doc.Range($startPos, $endPos - 1)
                                $keptMark = $true
                            }
                        }

                        if ($PSCmdlet.ShouldProcess("paragraphs $ai-$last", 'delete')) {
                            $rng.Delete() | Out-Null
                            $structural = $true
                        }
                        $detail = "deleted paragraphs $ai-$last ($(($last-$ai)+1) paras, ~$words words)"
                        if ($keptMark) { $detail += '; kept the cell-final paragraph mark (Word requires it)' }
                    }

                    'deleteTable' {
                        $p = $doc.Paragraphs.Item($ai)
                        if ($p.Range.Tables.Count -lt 1) { $status='SKIPPED'; $detail='anchor is not inside a table'; break }
                        $tbl = $p.Range.Tables.Item(1)
                        $page = $tbl.Range.Information($wdPageNumber)
                        $dims = "$($tbl.Rows.Count)x$($tbl.Columns.Count)"
                        if ($PSCmdlet.ShouldProcess("table at paragraph $ai", 'delete')) {
                            $tbl.Delete()
                            $structural = $true
                        }
                        $detail = "deleted $dims table"
                    }

                    { $_ -in 'insertAfter', 'insertBefore' } {
                        $blocks = @(Get-Prop $o 'blocks' @())
                        if (-not $blocks) { $status='SKIPPED'; $detail='no blocks supplied'; break }
                        $p = $doc.Paragraphs.Item($ai)
                        $page = $p.Range.Information($wdPageNumber)

                        if ($PSCmdlet.ShouldProcess("paragraph $ai", "$op $($blocks.Count) block(s)")) {
                            # Build downward so blocks land in manifest order. For insertBefore
                            # the first block reuses the empty paragraph opened above the anchor.
                            $cursor = $null
                            if ($op -eq 'insertBefore') {
                                $doc.Paragraphs.Item($ai).Range.InsertParagraphBefore()
                                $cursor = $doc.Paragraphs.Item($ai)
                            } else {
                                $cursor = $p
                            }

                            $reuseCursor = ($op -eq 'insertBefore')
                            foreach ($b in $blocks) {
                                if ($reuseCursor) {
                                    $new = $cursor; $reuseCursor = $false
                                } else {
                                    try {
                                        $cursor.Range.InsertParagraphAfter()
                                    } catch {
                                        # The anchor is the last paragraph of a table cell, where
                                        # InsertParagraphAfter would land on the row mark. Step out
                                        # to the paragraph following the whole table instead.
                                        if ($cursor.Range.Tables.Count -lt 1) { throw }
                                        $encl = $cursor.Range.Tables.Item(1)
                                        $after = $doc.Range($encl.Range.End, $encl.Range.End).Paragraphs.Item(1)
                                        $after.Range.InsertParagraphBefore()
                                        $cursor = $doc.Range($encl.Range.End, $encl.Range.End).Paragraphs.Item(1)
                                        $detail += ' [anchor was a row end; inserted after the table]'
                                        $new = $cursor
                                        Set-ParagraphText $doc $new ([string]$b.text)
                                        $bs2 = Get-Prop $b 'style' $null
                                        if ($bs2) { $new.Style = $bs2 }
                                        if ([bool](Get-Prop $b 'noList' $false)) { $new.Range.ListFormat.RemoveNumbers() }
                                        $cursor = $new
                                        continue
                                    }
                                    $new = $cursor.Next()
                                }
                                Set-ParagraphText $doc $new ([string]$b.text)
                                $bs = Get-Prop $b 'style' $null
                                if ($bs) { $new.Style = $bs }
                                # A new paragraph inherits list membership from its neighbour;
                                # blocks that must not be numbered have to say so explicitly.
                                if ([bool](Get-Prop $b 'noList' $false)) { $new.Range.ListFormat.RemoveNumbers() }
                                $cursor = $new
                            }
                            $structural = $true
                        }
                        $detail = "$op $($blocks.Count) paragraph(s)"
                    }

                    'insertTable' {
                        $rows = @(Get-Prop $o 'rows' @())
                        if (-not $rows) { $status='SKIPPED'; $detail='no rows supplied'; break }
                        $nRows = $rows.Count; $nCols = @($rows[0]).Count
                        $p = $doc.Paragraphs.Item($ai)
                        $page = $p.Range.Information($wdPageNumber)
                        if ($PSCmdlet.ShouldProcess("paragraph $ai", "insert ${nRows}x${nCols} table")) {
                            $p.Range.InsertParagraphAfter()
                            $seat = $p.Next()
                            $tbl = $doc.Tables.Add($seat.Range, $nRows, $nCols)
                            $ts = Get-Prop $o 'style' $null
                            if ($ts) { $tbl.Style = $ts }
                            for ($r = 0; $r -lt $nRows; $r++) {
                                $cells = @($rows[$r])
                                for ($c = 0; $c -lt $nCols -and $c -lt $cells.Count; $c++) {
                                    $tbl.Cell($r + 1, $c + 1).Range.Text = [string]$cells[$c]
                                }
                            }
                            if ([bool](Get-Prop $o 'headerRow' $true)) {
                                $tbl.Rows.Item(1).HeadingFormat = $true
                                $tbl.Rows.Item(1).Range.Bold = $true
                            }
                            # "Table Normal" carries no borders; the document's own tables get
                            # theirs from direct formatting, so match that rather than leaving
                            # an inserted table floating without rules.
                            if ([bool](Get-Prop $o 'borders' $true)) {
                                foreach ($edge in 1, 2, 3, 4, 5, 6) {   # l, r, t, b, horiz, vert
                                    $b = $tbl.Borders.Item($edge)
                                    $b.LineStyle = 1                    # wdLineStyleSingle
                                    $b.LineWidth = 8                    # wdLineWidth100pt
                                }
                            }
                            $structural = $true
                        }
                        $detail = "inserted ${nRows}x${nCols} table"
                    }

                    default { $status = 'SKIPPED'; $detail = "unknown op '$op'" }
                }
            }
        }
        catch {
            $status = 'ERROR'; $detail = $_.Exception.Message
        }

        if ($structural) { Sync-Index }

        $report.Add([pscustomobject]@{
            Id     = $id
            Op     = $op
            Status = if ($WhatIfPreference -and $status -eq 'OK') { 'WHATIF' } else { $status }
            Page   = $page
            Detail = $detail
            Note   = $note
        })
    }

    $revisionsAfter = $doc.Revisions.Count
    if (-not $WhatIfPreference) { $doc.Save() }
    $pages = $doc.ComputeStatistics(2)
    $doc.Close([bool]$false)

    if ($ChangeLog -and -not $WhatIfPreference) {
        $dir = Split-Path -Parent $ChangeLog
        if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
        $report | Export-Csv -LiteralPath $ChangeLog -NoTypeInformation -Encoding utf8
        Write-Host "Change log : $ChangeLog"
    }

    $report

    Write-Host ''
    Write-Host ("Document   : {0}" -f $working)
    Write-Host ("Pages      : {0}" -f $pages)
    Write-Host ("Revisions  : {0} new ({1} -> {2})" -f ($revisionsAfter - $revisionsBefore), $revisionsBefore, $revisionsAfter)
    Write-Host ("Outcomes   : {0}" -f (($report | Group-Object Status | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join '  '))
}
finally { Remove-WordApp -Word $word }
