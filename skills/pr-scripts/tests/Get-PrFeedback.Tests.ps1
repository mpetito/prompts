# Offline regression checks; no GitHub access or external test framework required.
$ErrorActionPreference = 'Stop'
$collector = Join-Path $PSScriptRoot '../Get-PrFeedback.ps1'
$global:prFeedbackTestScenario = 'populated'
$global:prFeedbackTestCalls = [System.Collections.Generic.List[string]]::new()
$global:prFeedbackTestBody = @'
## Review
<details>
<summary>Suppressed comments (1)</summary>
src/example.ts:12 — Check the existing guard before adding another.
</details>
'@

function gh {
    $call = $args -join ' '
    $global:prFeedbackTestCalls.Add($call)
    $global:LASTEXITCODE = 0
    if ($args[0] -eq 'api' -and $args[1] -eq 'graphql') {
        return '{"data":{"repository":{"pullRequest":{"reviewThreads":{"nodes":[],"pageInfo":{"hasNextPage":false,"endCursor":null}}}}}}'
    }
    if ($call -match '/pulls/123/reviews') {
        if ($global:prFeedbackTestScenario -eq 'failure') {
            $global:LASTEXITCODE = 1
            return 'API unavailable'
        }
        if ($global:prFeedbackTestScenario -eq 'empty') { return '[[]]' }
        $reviews = @(
            @{
                id = 100; user = @{ login = 'copilot-pull-request-reviewer[bot]' }; state = 'COMMENTED'
                submitted_at = '2026-09-11T12:00:00Z'; commit_id = 'abc123'
                html_url = 'https://github.com/example/repo/pull/123#pullrequestreview-100'
                body = $global:prFeedbackTestBody
            },
            @{
                id = 101; user = @{ login = 'human' }; state = 'DISMISSED'
                submitted_at = '2026-09-11T12:01:00Z'; commit_id = 'older'
                html_url = 'https://github.com/example/repo/pull/123#pullrequestreview-101'
                body = 'Earlier context'
            }
        )
        if ($global:prFeedbackTestScenario -eq 'single') {
            return ConvertTo-Json -InputObject @(,@($reviews[0])) -Depth 6
        }
        return ConvertTo-Json -InputObject @(@($reviews[0]), @($reviews[1])) -Depth 6
    }
    if ($call -match '^pr checks ') { return '[]' }
    if ($call -match '/code-scanning/alerts') { return '[]' }
    throw "Unexpected gh invocation: $call"
}

function Assert-True([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

$result = & $collector -Pr 123 -Repo example/repo | ConvertFrom-Json
Assert-True ($result.reviews.Count -eq 2) 'Must retain all reviews, including dismissed context.'
Assert-True ($result.reviews[0].body -ceq $global:prFeedbackTestBody) 'Must preserve the full suppressed section verbatim.'
Assert-True ($result.reviews[0].id -eq 100 -and $result.reviews[0].commitId -eq 'abc123') 'Must retain review provenance.'
Assert-True ($result.reviews[0].url -match 'pullrequestreview-100$') 'Must retain the review link.'
Assert-True ($result.summary.reviews -eq 2 -and $result.unresolvedThreads.Count -eq 0) 'Body-only feedback must remain visible with zero threads.'
Assert-True ($result.failingChecks.Count -eq 0 -and $result.codeScanningAlerts.Count -eq 0) 'Must preserve existing feedback fields.'
Assert-True ([bool]($global:prFeedbackTestCalls | Where-Object { $_ -match '/reviews --paginate --slurp' })) 'Must fetch all review pages as one JSON value.'
Assert-True ([bool]($global:prFeedbackTestCalls | Where-Object { $_ -match '^api --method GET .*/code-scanning/alerts' })) 'Scanning filters must use GET, not implicit POST.'

$global:prFeedbackTestScenario = 'single'
$result = & $collector -Pr 123 -Repo example/repo | ConvertFrom-Json
Assert-True ($result.reviews -is [array] -and $result.reviews.Count -eq 1) 'One review must serialize as a flat array.'
Assert-True ($result.reviews[0].author -eq 'copilot-pull-request-reviewer[bot]') 'Must map the API author field.'

$global:prFeedbackTestScenario = 'empty'
$result = & $collector -Pr 123 -Repo example/repo | ConvertFrom-Json
Assert-True ($result.reviews -is [array] -and $result.reviews.Count -eq 0) 'No reviews must serialize as an empty array.'
Assert-True ($result.summary.reviews -eq 0) 'Empty review count must be zero.'

$global:prFeedbackTestScenario = 'failure'
$failed = $false
try { & $collector -Pr 123 -Repo example/repo | Out-Null }
catch {
    if ($_.Exception.Message -notmatch 'Could not collect review bodies') { throw }
    $failed = $true
}
Assert-True $failed 'Review retrieval failure must not masquerade as no feedback.'
Write-Output 'PASS: full review bodies, provenance, pagination flags, empty results, and retrieval failure.'
