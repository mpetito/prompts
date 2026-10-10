<#
.SYNOPSIS
Lists pull request review threads with file/line context and full comment bodies as JSON.

.EXAMPLE
./Get-PrThreads.ps1 -Pr 123
./Get-PrThreads.ps1 -Pr 123 -Repo owner/name -Unresolved
#>
[CmdletBinding()]
param(
    [int]$Pr,
    [string]$Repo,
    [switch]$Unresolved
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$ctx = Resolve-PrContext -Repo $Repo -Pr $Pr
$threads = Get-PrReviewThreads -Context $ctx -Unresolved:$Unresolved
ConvertTo-Json @($threads) -Depth 6
