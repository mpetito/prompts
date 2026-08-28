<#
.SYNOPSIS
    Produce a copy of a .docx with all tracked changes accepted (or rejected).

.DESCRIPTION
    While revisions are tracked, deleted text is still physically in the document — so a
    term search keeps finding deleted terms long after they have been struck through. This
    script materializes the document as it will read once the recipient accepts the
    markup, so the other tools can be pointed at the *final* state.

    The source document is never modified. Use the output for verification only; the
    tracked copy stays the deliverable.

.PARAMETER Path
    Source .docx.

.PARAMETER OutFile
    Destination. Defaults to "<name>.accepted.docx" beside the source.

.PARAMETER Reject
    Reject all revisions instead of accepting them — useful to confirm the original text
    is recoverable and that no untracked change slipped in.

.EXAMPLE
    # Confirm an editing pass actually removed what it was supposed to
    $final = .\New-DocxAccepted.ps1 '..\work\rev1.docx'
    .\Find-DocxTerms.ps1 $final.Output -HitsOnly | Format-Table -AutoSize
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory, Position = 0)][string]$Path,
    [string]$OutFile,
    [switch]$Reject
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'WordCom.psm1') -Force

if (-not $OutFile) {
    $src = Get-Item -LiteralPath $Path
    $suffix = if ($Reject) { 'rejected' } else { 'accepted' }
    $OutFile = Join-Path $src.DirectoryName "$($src.BaseName).$suffix$($src.Extension)"
}
$working = New-WorkingCopy -Path $Path -Destination $OutFile

$word = $null
try {
    $word = New-WordApp
    $doc  = Open-WordDocument -Word $word -Path $working -Writable

    $before = $doc.Revisions.Count
    $doc.TrackRevisions = $false
    if ($Reject) { $doc.Revisions.RejectAll() } else { $doc.Revisions.AcceptAll() }
    $doc.Repaginate()
    $doc.Save()

    [pscustomobject]@{
        Source    = (Resolve-Path -LiteralPath $Path).ProviderPath
        Output    = $working
        Action    = if ($Reject) { 'rejected' } else { 'accepted' }
        Revisions = $before
        Pages     = $doc.ComputeStatistics(2)
        Words     = $doc.ComputeStatistics(0)
    }

    $doc.Close([bool]$false)
}
finally { Remove-WordApp -Word $word }
