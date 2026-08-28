<#
.SYNOPSIS
    Search a .docx for a checklist of terms and report every hit with its page number.

.DESCRIPTION
    Built for final-sweep verification: run a list of strings that must not survive
    into a delivered document (removed constructs, stale section references, superseded
    figures) and get back a page-located inventory of every place one still appears.

    Like Invoke-DocxEdits.ps1, this indexes paragraphs once and searches their text with
    exact .NET string matching rather than looping Word's Find. Word's Find.Execute
    mis-scopes a Range that starts inside a table cell — it returns hits before the range
    start, so a find-advance-repeat loop never terminates. Form-style documents are
    often one large table, so hits are routinely inside cells.

.PARAMETER Path
    The .docx to search. Opened read-only.

.PARAMETER Terms
    Terms to search for. Accepts an array, or a path to a text file with one term per line
    (blank lines and lines starting with # are ignored).

.PARAMETER Context
    Characters of surrounding text to show with each hit. 0 disables the excerpt.

.PARAMETER HitsOnly
    Suppress rows for terms with zero matches.

.PARAMETER MatchCase
    Case-sensitive search. Off by default.

.EXAMPLE
    .\Find-DocxTerms.ps1 '.\plan.docx' -Terms 'Legacy System','§14','TBD' -HitsOnly

.EXAMPLE
    .\Find-DocxTerms.ps1 '.\plan.docx' -Terms .\stale-terms.txt | Format-Table -AutoSize

.EXAMPLE
    # Summarise: one row per term with the pages it appears on
    .\Find-DocxTerms.ps1 '..\plan.docx' -HitsOnly -Context 0 | Group-Object Term |
        ForEach-Object { [pscustomobject]@{ Term=$_.Name; Hits=$_.Count
            Pages=(($_.Group.Page | Sort-Object -Unique) -join ',') } }
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [Parameter(Mandatory, Position = 1)][object]$Terms,
    [int]$Context = 70,
    [switch]$HitsOnly,
    [switch]$MatchCase
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

if ($Terms -is [string] -and (Test-Path -LiteralPath $Terms)) {
    $termList = Get-Content -LiteralPath $Terms |
        Where-Object { $_.Trim() -and -not $_.TrimStart().StartsWith('#') }
}
else { $termList = @($Terms) }

$cmp = if ($MatchCase) { [StringComparison]::Ordinal } else { [StringComparison]::OrdinalIgnoreCase }

$word = $null
try {
    $word = New-WordApp
    $doc  = Open-WordDocument -Word $word -Path $Path
    $wdPageNumber = Get-WdConst wdActiveEndPageNumber

    # One pass over the document: paragraph text plus the page it starts on.
    $paras = [System.Collections.Generic.List[object]]::new()
    $n = 0
    foreach ($p in $doc.Paragraphs) {
        $n++
        $rng = $p.Range
        $paras.Add([pscustomobject]@{
            Index = $n
            Page  = $rng.Information($wdPageNumber)
            Text  = ($rng.Text -replace "[`r`a]", '')
        })
    }
    Write-Verbose "Indexed $n paragraphs."

    foreach ($term in $termList) {
        $hits = 0
        foreach ($p in $paras) {
            $at = 0
            while ($at -le ($p.Text.Length - $term.Length) -and
                   ($at = $p.Text.IndexOf($term, $at, $cmp)) -ge 0) {
                $hits++

                $excerpt = ''
                if ($Context -gt 0) {
                    $s = [Math]::Max(0, $at - $Context)
                    $len = [Math]::Min($p.Text.Length - $s, $term.Length + 2 * $Context)
                    $excerpt = ($p.Text.Substring($s, $len) -replace "`t", ' ').Trim()
                }

                [pscustomobject]@{
                    Term      = $term
                    Hit       = $hits
                    Page      = $p.Page
                    Paragraph = $p.Index
                    Excerpt   = $excerpt
                }

                $at += [Math]::Max(1, $term.Length)
            }
        }
        if ($hits -eq 0 -and -not $HitsOnly) {
            [pscustomobject]@{ Term = $term; Hit = 0; Page = ''; Paragraph = ''; Excerpt = '(no matches)' }
        }
    }

    $doc.Close([bool]$false)
}
finally { Remove-WordApp -Word $word }
