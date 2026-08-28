<#
.SYNOPSIS
    Dump every paragraph of a .docx with its Word-rendered list number, style, page, and text.

.DESCRIPTION
    The OOXML tells you a paragraph is numbered; only Word tells you what number it
    actually renders as. This script asks Word directly (ListFormat.ListString) so the
    section numbers reported here are exactly what a reader sees on the page.

    Emits one record per paragraph. Use -Format Table for a quick read, Csv/Json to feed
    another tool, or Text for a greppable dump.

.PARAMETER Path
    The .docx to inspect. Opened read-only; never modified.

.PARAMETER HeadingsOnly
    Only paragraphs whose outline level is a real heading (1-9).

.PARAMETER Format
    Text (default), Table, Csv, or Json.

.PARAMETER MaxText
    Truncate paragraph text to this many characters. 0 = no truncation.

.EXAMPLE
    .\Get-DocxOutline.ps1 '.\plan.docx' -HeadingsOnly -Format Table

.EXAMPLE
    .\Get-DocxOutline.ps1 '.\plan.docx' -Format Json |
        Set-Content outline.json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [switch]$HeadingsOnly,
    [ValidateSet('Text', 'Table', 'Csv', 'Json')][string]$Format = 'Text',
    [int]$MaxText = 160
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

$word = $null
try {
    $word = New-WordApp
    $doc  = Open-WordDocument -Word $word -Path $Path
    $wdActiveEndPageNumber = Get-WdConst wdActiveEndPageNumber

    $rows = [System.Collections.Generic.List[object]]::new()
    $i = 0
    foreach ($p in $doc.Paragraphs) {
        $i++
        $rng  = $p.Range
        $text = ($rng.Text -replace "[`r`a`t]", ' ').Trim()
        $level = $p.OutlineLevel        # 1-9 = heading level, 10 = body text
        if ($HeadingsOnly -and $level -ge 10) { continue }
        if (-not $text -and $level -ge 10)    { continue }

        # ListString is the number Word actually paints in the margin ("2.", "9.1", "a)").
        $listNum = ''
        try { $listNum = $p.Range.ListFormat.ListString } catch { }

        # InTable tells us the paragraph lives inside a table, which changes how
        # Find/Replace ranges have to be scoped.
        $inTable = $false
        try { $inTable = [bool]$rng.Tables.Count } catch { }

        $shown = if ($MaxText -gt 0 -and $text.Length -gt $MaxText) {
            $text.Substring(0, $MaxText) + '...'
        } else { $text }

        $rows.Add([pscustomobject]@{
            Index   = $i
            Page    = $rng.Information($wdActiveEndPageNumber)
            Level   = if ($level -ge 10) { '' } else { $level }
            Number  = $listNum
            Style   = $p.Style.NameLocal
            InTable = $inTable
            Start   = $rng.Start
            End     = $rng.End
            Text    = $shown
        })
    }

    switch ($Format) {
        'Table' { $rows | Format-Table Index, Page, Level, Number, Style, Text -AutoSize -Wrap }
        'Csv'   { $rows | ConvertTo-Csv -NoTypeInformation }
        'Json'  { $rows | ConvertTo-Json -Depth 3 }
        default {
            foreach ($r in $rows) {
                $tbl = if ($r.InTable) { 'T' } else { ' ' }
                '{0,4} p{1,-3} {2}{3,-2} {4,-10} {5,-22} | {6}' -f `
                    $r.Index, $r.Page, $tbl, $r.Level, $r.Number, $r.Style, $r.Text
            }
        }
    }

    Write-Verbose "Pages: $($doc.ComputeStatistics(2)) Words: $($doc.ComputeStatistics(0))"
    $doc.Close([bool]$false)
}
finally { Remove-WordApp -Word $word }
