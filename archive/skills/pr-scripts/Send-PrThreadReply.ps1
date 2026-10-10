<#
.SYNOPSIS
Replies to a PR review thread by thread ID (PRRT_...). No comment-ID lookup needed.

.EXAMPLE
./Send-PrThreadReply.ps1 -ThreadId PRRT_kwDO... -Body "Fixed in commit abc1234."
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$ThreadId,
    [Parameter(Mandatory)][string]$Body
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$mutation = @'
mutation($threadId: ID!, $body: String!) {
  addPullRequestReviewThreadReply(input: { pullRequestReviewThreadId: $threadId, body: $body }) {
    comment { id url }
  }
}
'@
$resp = Invoke-GhGraphQL -Query $mutation -StringFields @{ threadId = $ThreadId; body = $Body }
$resp.data.addPullRequestReviewThreadReply.comment | ConvertTo-Json
