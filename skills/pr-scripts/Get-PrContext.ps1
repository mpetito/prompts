<#
.SYNOPSIS
Fetches complete PR review context in one call: metadata, changed files, existing
reviews, review threads, and CI status. JSON output shaped for the pr-review skill.

.EXAMPLE
./Get-PrContext.ps1 -Pr 123
./Get-PrContext.ps1 -Pr 123 -Repo owner/name
#>
[CmdletBinding()]
param(
    [int]$Pr,
    [string]$Repo
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$ctx = Resolve-PrContext -Repo $Repo -Pr $Pr

$meta = gh pr view $ctx.Pr -R $ctx.Repo --json `
    number,title,body,author,state,isDraft,baseRefName,headRefName,additions,deletions,changedFiles,mergeable,url | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw "gh pr view failed for $($ctx.Repo)#$($ctx.Pr)." }

$files = gh api "repos/$($ctx.Repo)/pulls/$($ctx.Pr)/files" --paginate `
    --jq '[.[] | {path: .filename, status, additions, deletions}]' | ConvertFrom-Json

$reviews = gh api "repos/$($ctx.Repo)/pulls/$($ctx.Pr)/reviews" --paginate `
    --jq '[.[] | {author: .user.login, state, submittedAt: .submitted_at, body}]' | ConvertFrom-Json

$threads = Get-PrReviewThreads -Context $ctx

$checksRaw = gh pr checks $ctx.Pr -R $ctx.Repo --json name,state,bucket 2>&1
try { $checks = $checksRaw | ConvertFrom-Json } catch { $checks = @() }

[pscustomobject]@{
    repo    = $ctx.Repo
    pr      = $meta
    files   = @($files)
    reviews = @($reviews)
    threads = @($threads)
    checks  = [pscustomobject]@{
        passing = @($checks | Where-Object bucket -eq 'pass').Count
        failing = @($checks | Where-Object bucket -eq 'fail').Count
        pending = @($checks | Where-Object bucket -eq 'pending').Count
        items   = @($checks)
    }
} | ConvertTo-Json -Depth 7
