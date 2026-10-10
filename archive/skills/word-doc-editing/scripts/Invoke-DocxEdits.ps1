<#
.SYNOPSIS
    Apply a batch of text edits to a .docx through Word, with tracked changes on.

.DESCRIPTION
    Reads an edit manifest (JSON), opens a working copy in Word, turns on revision
    tracking, and rewrites the targeted text. Word does the writing, so run-level
    formatting (bold, styles, numbering, table structure) survives edits that cross run
    boundaries — the failure mode that makes raw OOXML text surgery risky.

    Two design decisions worth knowing:

    1. Paragraph-scoped addressing, not document-wide Find. Word's Find.Execute
       mis-scopes a Range that begins inside a table cell: it will happily return a hit
       that starts *before* the range start, which makes the usual "find, advance, repeat"
       loop spin forever — and form-style documents are often one large table, so
       targets are routinely inside cells. So the script indexes paragraphs once, locates
       matches with exact .NET string search, and edits each paragraph's own Range.

    2. Narrowed replacement. Before writing, the shared prefix and suffix of the find and
       replace strings are trimmed so only the genuinely changed characters are touched.
       Rewriting "see §14.5" -> "see Contract Terms" replaces four characters, not the
       whole phrase, which leaves formatting on the untouched flanks alone.

    Every edit is reported as OK / NOT FOUND / AMBIGUOUS / SKIPPED so nothing changes
    silently. An edit matching more than once is skipped unless the manifest says
    otherwise, because a wrong global replace in a delivered document is expensive.

.PARAMETER Path
    Source .docx. Never modified — the script always works on a copy.

.PARAMETER Edits
    Path to the JSON manifest, or an array of edit objects. Schema per edit:

        id        - short label used in the report (optional)
        find      - literal text to locate (required)
        replace   - replacement text; "" deletes the found text (required)
        scope     - "unique" (default) : apply only if exactly one match exists
                    "first"            : apply to the first match
                    "all"              : apply to every match
        note      - free text carried into the report (optional)
        matchCase - $false for case-insensitive search (default $true)

    Note on highlighting: replacement text inherits the formatting of the text it
    replaces, so an edit inside a reviewer-highlighted passage comes out highlighted too.
    That is usually what you want during review — the flag stays visible next to the fix.
    Removing the highlights is a deliberate final pass to run after the revisions are
    accepted, not something to fold into an edit, because under revision tracking Word
    records a highlight change as a property revision that does not take effect until
    acceptance.

.PARAMETER OutFile
    Destination .docx. Defaults to "<name>.tracked.docx" beside the source.

.PARAMETER Author
    Name stamped on the tracked revisions. Defaults to the Word user name.

.PARAMETER NoTrack
    Apply edits as clean changes with revision tracking off.

.EXAMPLE
    .\Invoke-DocxEdits.ps1 '.\plan.docx' .\edits\xrefs.json

.EXAMPLE
    .\Invoke-DocxEdits.ps1 '.\plan.docx' .\edits\xrefs.json -WhatIf | Format-Table -AutoSize
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [Parameter(Mandatory, Position = 1)][object]$Edits,
    [string]$OutFile,
    [string]$Author,
    [switch]$NoTrack
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

# ---------------------------------------------------------------- manifest ----
if ($Edits -is [string]) {
    $manifest = Get-Content -LiteralPath $Edits -Raw -Encoding utf8 | ConvertFrom-Json
} else { $manifest = $Edits }
if ($manifest -isnot [array]) { $manifest = @($manifest) }

function Get-Prop { param($Obj, $Name, $Default)
    if ($Obj.PSObject.Properties[$Name]) { $Obj.$Name } else { $Default }
}

<#
    Trim the shared prefix/suffix of two strings so only the changed span is rewritten.
    Returns @{ Offset; Length; Text } describing the edit relative to the found text.
#>
function Get-NarrowedEdit {
    param([string]$Old, [string]$New)
    $i = 0
    while ($i -lt $Old.Length -and $i -lt $New.Length -and $Old[$i] -ceq $New[$i]) { $i++ }
    $j = 0
    while ($j -lt ($Old.Length - $i) -and $j -lt ($New.Length - $i) -and
           $Old[$Old.Length - 1 - $j] -ceq $New[$New.Length - 1 - $j]) { $j++ }
    [pscustomobject]@{
        Offset = $i
        Length = $Old.Length - $i - $j
        Text   = $New.Substring($i, $New.Length - $i - $j)
    }
}

# ------------------------------------------------------------ working copy ----
if (-not $OutFile) {
    $src = Get-Item -LiteralPath $Path
    $OutFile = Join-Path $src.DirectoryName "$($src.BaseName).tracked$($src.Extension)"
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

    # Index every paragraph once. Paragraph indices stay valid for the whole run as long
    # as no replacement introduces a paragraph mark, which is enforced below.
    $paras = [System.Collections.Generic.List[object]]::new()
    $n = 0
    foreach ($p in $doc.Paragraphs) {
        $n++
        $paras.Add([pscustomobject]@{ Index = $n; Text = $p.Range.Text })
    }
    Write-Verbose "Indexed $n paragraphs."

    foreach ($e in $manifest) {
        $id      = [string](Get-Prop $e 'id' '')
        $note    = [string](Get-Prop $e 'note' '')
        $scope   = [string](Get-Prop $e 'scope' 'unique')
        $mcase   = [bool](Get-Prop $e 'matchCase' $true)
        $find    = [string]$e.find
        $replace = [string]$e.replace
        $cmp = if ($mcase) { [StringComparison]::Ordinal } else { [StringComparison]::OrdinalIgnoreCase }

        if ($replace -match "[`r`n`v]") {
            $report.Add([pscustomobject]@{ Id=$id; Status='SKIPPED'; Matches=0; Pages=''
                Detail='replacement contains a paragraph/line break; split into separate edits'
                Find=$find; Note=$note })
            continue
        }

        # Locate every occurrence: paragraph index + offset within that paragraph.
        $sites = [System.Collections.Generic.List[object]]::new()
        foreach ($p in $paras) {
            $at = 0
            while ($at -le ($p.Text.Length - $find.Length) -and
                   ($at = $p.Text.IndexOf($find, $at, $cmp)) -ge 0) {
                $sites.Add([pscustomobject]@{ Para = $p.Index; Offset = $at })
                $at += [Math]::Max(1, $find.Length)
            }
        }

        if ($sites.Count -eq 0) {
            $report.Add([pscustomobject]@{ Id=$id; Status='NOT FOUND'; Matches=0; Pages=''
                Detail='text does not appear in any single paragraph (it may span paragraphs)'
                Find=$find; Note=$note })
            continue
        }
        if ($sites.Count -gt 1 -and $scope -eq 'unique') {
            $report.Add([pscustomobject]@{ Id=$id; Status='AMBIGUOUS'; Matches=$sites.Count; Pages=''
                Detail="$($sites.Count) matches but scope=unique; not applied. Lengthen 'find' or set scope."
                Find=$find; Note=$note })
            continue
        }

        $targets = switch ($scope) {
            'first' { @($sites[0]) }
            'all'   { @($sites) }
            default { @($sites[0]) }
        }

        # Apply back-to-front so earlier offsets stay valid as text shifts.
        $targets = @($targets | Sort-Object Para, Offset -Descending)
        $narrow  = Get-NarrowedEdit -Old $find -New $replace
        $applied = 0; $pages = @(); $problem = $null

        foreach ($t in $targets) {
            $pRange = $doc.Paragraphs.Item($t.Para).Range
            $absStart = $pRange.Start + $t.Offset + $narrow.Offset
            $absEnd   = $absStart + $narrow.Length

            # Verify before writing: paragraph text offsets and Range offsets diverge when
            # a paragraph contains field codes, so confirm we are pointing at the right text.
            $expected = $find.Substring($narrow.Offset, $narrow.Length)
            $actual   = if ($narrow.Length -gt 0) { $doc.Range($absStart, $absEnd).Text } else { '' }
            if ($narrow.Length -gt 0 -and $actual -cne $expected) {
                $problem = "range check failed (expected '$expected', found '$actual') - paragraph $($t.Para) probably contains a field"
                continue
            }

            if (-not $PSCmdlet.ShouldProcess("paragraph $($t.Para)", "replace '$expected' with '$($narrow.Text)'")) {
                $applied++; continue
            }

            $target = $doc.Range($absStart, $absEnd)
            $pages += $target.Information($wdPageNumber)
            # Assigning .Text with tracking on produces a genuine delete+insert revision pair.
            $target.Text = $narrow.Text
            $applied++
        }

        # Paragraph text cache is now stale for the paragraphs we touched.
        foreach ($t in $targets) {
            $paras[$t.Para - 1].Text = $doc.Paragraphs.Item($t.Para).Range.Text
        }

        $status = if ($applied -eq 0) { 'SKIPPED' }
                  elseif ($problem)   { 'PARTIAL' }
                  elseif ($WhatIfPreference) { 'WHATIF' }
                  else { 'OK' }
        $report.Add([pscustomobject]@{
            Id      = $id
            Status  = $status
            Matches = $sites.Count
            Pages   = ($pages | Sort-Object -Unique) -join ','
            Detail  = if ($problem) { $problem } else { "scope=$scope; changed '$($find.Substring($narrow.Offset,$narrow.Length))' -> '$($narrow.Text)'" }
            Find    = $find
            Note    = $note
        })
    }

    $revisionsAfter = $doc.Revisions.Count
    if (-not $WhatIfPreference) { $doc.Save() }
    $doc.Close([bool]$false)

    $report

    Write-Host ''
    Write-Host ("Document  : {0}" -f $working)
    Write-Host ("Revisions : {0} new ({1} -> {2})" -f ($revisionsAfter - $revisionsBefore), $revisionsBefore, $revisionsAfter)
    Write-Host ("Outcomes  : {0}" -f (($report | Group-Object Status | ForEach-Object { "$($_.Name)=$($_.Count)" }) -join '  '))
}
finally { Remove-WordApp -Word $word }
