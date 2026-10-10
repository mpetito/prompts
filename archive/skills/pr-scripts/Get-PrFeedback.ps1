<#
.SYNOPSIS
Aggregates PR feedback in one call: unresolved review threads, complete review bodies,
failing CI checks (with log excerpts), and open code-scanning alerts. JSON output shaped for
the pr-feedback skill's collection step.

.EXAMPLE
./Get-PrFeedback.ps1 -Pr 123
#>
[CmdletBinding()]
param(
    [int]$Pr,
    [string]$Repo,
    [int]$LogTailLines = 50
)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSScriptRoot 'PrCommon.psm1') -Force

$ctx = Resolve-PrContext -Repo $Repo -Pr $Pr

$threads = Get-PrReviewThreads -Context $ctx -Unresolved

# Suppressed findings can live inside a review body rather than in review threads.
$reviewsRaw = gh api "repos/$($ctx.Repo)/pulls/$($ctx.Pr)/reviews" --paginate --slurp
if ($LASTEXITCODE -ne 0) { throw "Could not collect review bodies for $($ctx.Repo)#$($ctx.Pr)." }
$reviews = @(foreach ($page in ($reviewsRaw | ConvertFrom-Json)) {
    foreach ($review in $page) {
        [pscustomobject]@{
            id          = $review.id
            author      = $review.user.login
            state       = $review.state
            submittedAt = $review.submitted_at
            commitId    = $review.commit_id
            url         = $review.html_url
            body        = $review.body
        }
    }
})

$checkFailures = & (Join-Path $PSScriptRoot 'Get-PrCheckFailures.ps1') `
    -Pr $ctx.Pr -Repo $ctx.Repo -LogTailLines $LogTailLines | ConvertFrom-Json

# Code-scanning alerts on the PR head; tolerate repos without code scanning enabled
$alerts = @()
$alertsRaw = gh api --method GET "repos/$($ctx.Repo)/code-scanning/alerts" --paginate `
    -f ref="refs/pull/$($ctx.Pr)/head" -f state=open `
    --jq '[.[] | {number, rule: .rule.id, severity: .rule.severity, description: .rule.description, path: .most_recent_instance.location.path, line: .most_recent_instance.location.start_line, url: .html_url}]' 2>$null
if ($LASTEXITCODE -eq 0 -and $alertsRaw) { $alerts = @($alertsRaw | ConvertFrom-Json) }

[pscustomobject]@{
    repo               = $ctx.Repo
    pr                 = $ctx.Pr
    unresolvedThreads  = @($threads)
    reviews            = @($reviews)
    failingChecks      = @($checkFailures)
    codeScanningAlerts = @($alerts)
    summary            = [pscustomobject]@{
        unresolvedThreads  = @($threads).Count
        reviews            = @($reviews).Count
        failingChecks      = @($checkFailures).Count
        codeScanningAlerts = @($alerts).Count
    }
} | ConvertTo-Json -Depth 7
