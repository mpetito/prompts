<#
.SYNOPSIS
    List the tracked changes in a .docx so an editing pass can be reviewed without opening Word.

.DESCRIPTION
    After Invoke-DocxEdits runs, this is the receipt: every insertion and deletion, with
    author, page, and the surrounding sentence. Use it to confirm that the edits landed
    where intended before handing the document to a reviewer.

.PARAMETER Path
    The .docx to inspect. Opened read-only.

.PARAMETER Context
    Characters of surrounding text to show with each revision. 0 disables the excerpt.

.PARAMETER Author
    Only show revisions by this author.

.EXAMPLE
    .\Get-DocxRevisions.ps1 '.\plan.tracked.docx' | Format-Table -AutoSize

.EXAMPLE
    .\Get-DocxRevisions.ps1 '.\plan.tracked.docx' | Export-Csv revisions.csv -NoTypeInformation
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [int]$Context = 60,
    [string]$Author
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

# wdRevisionType values worth naming; anything else is reported by number.
$typeName = @{
    1 = 'Insert'; 2 = 'Delete'; 3 = 'Property'; 4 = 'ParagraphNumber'
    5 = 'DisplayField'; 6 = 'Reconcile'; 7 = 'Conflict'; 8 = 'Style'
    9 = 'Replace'; 10 = 'ParagraphProperty'; 11 = 'TableProperty'
    12 = 'SectionProperty'; 13 = 'StyleDefinition'; 14 = 'MovedFrom'; 15 = 'MovedTo'
}

$word = $null
try {
    $word = New-WordApp
    $doc  = Open-WordDocument -Word $word -Path $Path
    $wdPageNumber = Get-WdConst wdActiveEndPageNumber
    $docEnd = $doc.Content.End

    $i = 0
    foreach ($rev in $doc.Revisions) {
        $i++
        if ($Author -and $rev.Author -ne $Author) { continue }

        $text = ''
        try { $text = ($rev.Range.Text -replace "[`r`a`t`n]", ' ').Trim() } catch { }

        $excerpt = ''
        if ($Context -gt 0) {
            try {
                $s = [Math]::Max(0, $rev.Range.Start - $Context)
                $e = [Math]::Min($docEnd, $rev.Range.End + $Context)
                $excerpt = ($doc.Range($s, $e).Text -replace "[`r`a`t`n]", ' ').Trim()
            } catch { }
        }

        $page = ''
        try { $page = $rev.Range.Information($wdPageNumber) } catch { }

        [pscustomobject]@{
            Index   = $i
            Type    = if ($typeName.ContainsKey($rev.Type)) { $typeName[$rev.Type] } else { "Type$($rev.Type)" }
            Author  = $rev.Author
            Date    = $rev.Date
            Page    = $page
            Text    = $text
            Excerpt = $excerpt
        }
    }

    if ($i -eq 0) { Write-Host 'No tracked revisions in this document.' }
    $doc.Close([bool]$false)
}
finally { Remove-WordApp -Word $word }
