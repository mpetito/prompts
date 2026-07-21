<#
.SYNOPSIS
Submits a complete PR review (summary body + inline comments) atomically via one REST call.

.DESCRIPTION
Inline comments are supplied as a JSON file: an array of objects with
path, line, body, and optional side (default RIGHT), start_line, start_side.

.EXAMPLE
./Submit-PrReview.ps1 -Pr 123 -Event COMMENT -Body "Overall looks good; two concerns inline." -CommentsFile review-comments.json

.EXAMPLE
./Submit-PrReview.ps1 -Pr 123 -Event APPROVE -Body "LGTM"
#>
[CmdletBinding()]
param(
    [int]$Pr,
    [string]$Repo,
    [Parameter(Mandatory)][ValidateSet('COMMENT', 'APPROVE', 'REQUEST_CHANGES')][string]$Event,
    [Parameter(Mandatory)][string]$Body,
    [string]$CommentsFile
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$ctx = Resolve-PrContext -Repo $Repo -Pr $Pr

$payload = [ordered]@{ event = $Event; body = $Body }
if ($CommentsFile) {
    $comments = Get-Content -Raw $CommentsFile | ConvertFrom-Json
    foreach ($c in $comments) {
        if (-not $c.path -or -not $c.line -or -not $c.body) {
            throw "Each comment needs path, line, and body. Offending entry: $($c | ConvertTo-Json -Compress)"
        }
        if (-not $c.PSObject.Properties['side']) {
            $c | Add-Member -NotePropertyName side -NotePropertyValue 'RIGHT'
        }
    }
    $payload.comments = @($comments)
}

$json = $payload | ConvertTo-Json -Depth 5
$resp = $json | gh api "repos/$($ctx.Repo)/pulls/$($ctx.Pr)/reviews" --method POST --input -
if ($LASTEXITCODE -ne 0) {
    throw "Review submission failed (exit $LASTEXITCODE): $resp"
}
($resp | ConvertFrom-Json) | Select-Object id, state, html_url | ConvertTo-Json
