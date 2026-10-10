<#
.SYNOPSIS
Verifies PR review thread resolution. Prints remaining unresolved threads (compact JSON);
exits 0 when all threads are resolved, 1 otherwise.

.EXAMPLE
./Test-PrThreadsResolved.ps1 -Pr 123
#>
[CmdletBinding()]
param(
    [int]$Pr,
    [string]$Repo
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$ctx = Resolve-PrContext -Repo $Repo -Pr $Pr
$unresolved = @(Get-PrReviewThreads -Context $ctx -Unresolved)

if ($unresolved.Count -eq 0) {
    Write-Output "All review threads resolved on $($ctx.Repo)#$($ctx.Pr)."
    exit 0
}

Write-Output "$($unresolved.Count) unresolved thread(s) on $($ctx.Repo)#$($ctx.Pr):"
$unresolved | Select-Object threadId, path, line, author, isOutdated | ConvertTo-Json -Depth 3
exit 1
