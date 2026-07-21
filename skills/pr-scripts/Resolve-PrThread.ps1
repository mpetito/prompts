<#
.SYNOPSIS
Resolves a PR review thread; optionally posts a reply first (reply-then-resolve in one call).

.EXAMPLE
./Resolve-PrThread.ps1 -ThreadId PRRT_kwDO... -Body "Fixed in commit abc1234."
./Resolve-PrThread.ps1 -ThreadId PRRT_kwDO...   # resolve only
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ThreadId,
    [string]$Body
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

if ($Body) {
    & (Join-Path $PSScriptRoot 'Send-PrThreadReply.ps1') -ThreadId $ThreadId -Body $Body | Out-Null
}

$mutation = @'
mutation($threadId: ID!) {
  resolveReviewThread(input: { threadId: $threadId }) {
    thread { id isResolved }
  }
}
'@
$resp = Invoke-GhGraphQL -Query $mutation -StringFields @{ threadId = $ThreadId }
$resp.data.resolveReviewThread.thread | ConvertTo-Json
