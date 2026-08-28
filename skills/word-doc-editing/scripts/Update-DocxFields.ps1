<#
.SYNOPSIS
    Refresh every field in a .docx (TOC, PAGEREF, REF) and report the resulting page count.

.DESCRIPTION
    Table-of-contents entries and page references go stale the moment content moves. Word
    only recalculates them on demand, so run this after an editing pass and before sending
    a draft out for review.

    Updates fields in the main story plus headers and footers, then reports pages/words so
    a page-budget target can be checked in the same step.

    Field updates are structural, not editorial: this script turns revision tracking OFF
    for the update so a TOC refresh does not produce hundreds of meaningless tracked
    changes, then restores the document's original setting before saving.

.PARAMETER Path
    The .docx to update. Modified in place unless -OutFile is given.

.PARAMETER OutFile
    Write to a new file instead of updating in place.

.PARAMETER SkipToc
    Update ordinary fields but leave the table of contents alone.

.EXAMPLE
    .\Update-DocxFields.ps1 '.\plan.tracked.docx'
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [string]$OutFile,
    [switch]$SkipToc
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

$target = if ($OutFile) { New-WorkingCopy -Path $Path -Destination $OutFile } else { (Resolve-Path -LiteralPath $Path).ProviderPath }

$word = $null
try {
    $word = New-WordApp
    $doc  = Open-WordDocument -Word $word -Path $target -Writable

    $trackWas = $doc.TrackRevisions
    $doc.TrackRevisions = $false

    if ($PSCmdlet.ShouldProcess($target, 'Update fields')) {
        $doc.Fields.Update() | Out-Null

        foreach ($section in $doc.Sections) {
            foreach ($hf in @($section.Headers, $section.Footers)) {
                foreach ($item in $hf) {
                    if ($item.Exists) { $item.Range.Fields.Update() | Out-Null }
                }
            }
        }

        if (-not $SkipToc) {
            foreach ($toc in $doc.TablesOfContents) { $toc.Update() }
            foreach ($tof in $doc.TablesOfFigures) { $tof.Update() }
        }

        # Repaginate so ComputeStatistics reports post-update numbers.
        $doc.Repaginate()

        $doc.TrackRevisions = $trackWas
        $doc.Save()
    }

    [pscustomobject]@{
        File        = $target
        Pages       = $doc.ComputeStatistics(2)   # wdStatisticPages
        Words       = $doc.ComputeStatistics(0)   # wdStatisticWords
        Fields      = $doc.Fields.Count
        TOCs        = $doc.TablesOfContents.Count
        Revisions   = $doc.Revisions.Count
        TrackingOn  = $doc.TrackRevisions
    }

    $doc.Close([bool]$false)
}
finally { Remove-WordApp -Word $word }
