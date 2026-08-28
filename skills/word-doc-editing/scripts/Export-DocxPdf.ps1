<#
.SYNOPSIS
    Render a .docx to PDF so the result can be inspected visually.

.DESCRIPTION
    Editing XML you cannot see is how formatting damage goes unnoticed. Export before and
    after an editing pass and compare the PDFs — that is the only check that covers
    pagination, table layout, numbering, and header/footer behavior all at once.

.PARAMETER Path
    The .docx to render. Opened read-only.

.PARAMETER OutFile
    Destination PDF. Defaults to the source name with a .pdf extension.

.PARAMETER ShowMarkup
    Render tracked changes and comments as visible markup (what a reviewer sees).
    Off by default, which renders the document as if all revisions were accepted.

.EXAMPLE
    .\Export-DocxPdf.ps1 '.\plan.docx'

.EXAMPLE
    .\Export-DocxPdf.ps1 '.\plan.tracked.docx' -ShowMarkup -OutFile review.pdf
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [string]$OutFile,
    [switch]$ShowMarkup
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

if (-not $OutFile) {
    $src = Get-Item -LiteralPath $Path
    $OutFile = Join-Path $src.DirectoryName "$($src.BaseName).pdf"
}
# ExportAsFixedFormat needs an absolute path and will not create directories. Resolve a
# relative path against the PowerShell location, not the process working directory —
# [IO.Path]::GetFullPath alone uses the latter, which Set-Location does not move.
if (-not [IO.Path]::IsPathRooted($OutFile)) {
    $OutFile = Join-Path (Get-Location).ProviderPath $OutFile
}
$OutFile = [IO.Path]::GetFullPath($OutFile)
$dir = Split-Path -Parent $OutFile
if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }

$word = $null
try {
    $word = New-WordApp
    $doc  = Open-WordDocument -Word $word -Path $Path

    # wdExportDocumentContent = 0 (final), wdExportDocumentWithMarkup = 7
    $item = if ($ShowMarkup) { 7 } else { 0 }
    $doc.ExportAsFixedFormat(
        $OutFile,
        (Get-WdConst wdExportFormatPDF),
        $false,                                  # OpenAfterExport
        (Get-WdConst wdExportOptimizeForPrint),
        (Get-WdConst wdExportAllDocument),
        0, 0,                                    # From, To
        $item,
        $true,                                   # IncludeDocProps
        $true,                                   # KeepIRM
        (Get-WdConst wdExportCreateHeadingBookmarks)
    )

    [pscustomobject]@{
        Source = (Resolve-Path -LiteralPath $Path).ProviderPath
        Pdf    = $OutFile
        Pages  = $doc.ComputeStatistics(2)
        Markup = [bool]$ShowMarkup
        Size   = (Get-Item -LiteralPath $OutFile).Length
    }

    $doc.Close([bool]$false)
}
finally { Remove-WordApp -Word $word }
