# Offline checks for Get-PrFeedback.ps1 against a mocked gh; no GitHub access or test framework.
$ErrorActionPreference = 'Stop'
$collector = Join-Path $PSScriptRoot '../scripts/Get-PrFeedback.ps1'
$global:ghScenario = 'populated'
$global:ghCalls = [System.Collections.Generic.List[string]]::new()
$suppressedBody = @'
## Review
<details>
<summary>Comments suppressed due to low confidence (1)</summary>
src/export.py:41 - `until` is exclusive here but inclusive in the CLI help.
</details>
'@

function New-ThreadPage([object[]]$Nodes, [bool]$More) {
    @{ data = @{ repository = @{ pullRequest = @{ reviewThreads = @{
        pageInfo = @{ hasNextPage = $More; endCursor = 'c1' }; nodes = $Nodes } } } } }
}
function New-Thread([string]$Id, [bool]$Resolved, [bool]$Outdated) {
    @{ id = $Id; isResolved = $Resolved; isOutdated = $Outdated; path = 'src/a.py'; line = 3
       comments = @{ nodes = @(@{ fullDatabaseId = '4197153031'; author = @{ login = 'copilot-pull-request-reviewer' }; body = 'Check this.'; url = 'u' }) } }
}

# Stands in for gh; any call it does not recognise throws, so the network is never reached.
function gh {
    $call = $args -join ' '
    $global:ghCalls.Add($call)
    $global:LASTEXITCODE = 0
    if ($call -ceq 'repo view --json nameWithOwner -q .nameWithOwner') {
        if ($global:ghScenario -eq 'no-repo') { $global:LASTEXITCODE = 1; return 'no git remotes' }
        return 'example/repo'
    }
    if ($call -ceq 'pr view --json number -q .number') { return '123' }
    if ($call -match '^api graphql ') {
        switch ($global:ghScenario) {
            'threads-fail' { $global:LASTEXITCODE = 1; return 'HTTP 502' }
            'body-only' { return ConvertTo-Json -Depth 12 -InputObject @(New-ThreadPage @() $false) }
        }
        $pages = @(
            (New-ThreadPage @((New-Thread 'PRRT_open' $false $true), (New-Thread 'PRRT_done' $true $false)) $true),
            (New-ThreadPage @(, (New-Thread 'PRRT_page2' $false $false)) $false))
        return ConvertTo-Json -Depth 12 -InputObject $pages
    }
    if ($call -match '^api repos/example/repo/pulls/123/reviews ') {
        if ($global:ghScenario -eq 'reviews-fail') { $global:LASTEXITCODE = 1; return 'HTTP 502' }
        $copilot = @{ id = 100; user = @{ login = 'copilot-pull-request-reviewer[bot]' }; state = 'COMMENTED'
                      commit_id = 'abc123'; html_url = 'https://example.test/r100'; body = $suppressedBody }
        $human = @{ id = 101; user = @{ login = 'human' }; state = 'COMMENTED'; commit_id = 'def456'
                    html_url = 'https://example.test/r101'; body = 'Looks fine.' }
        return ConvertTo-Json -Depth 6 -InputObject @(@(, $copilot), @(, $human))
    }
    throw "Unexpected gh call (network refused): $call"
}

function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Expect-Failure([string]$Scenario, [string]$Pattern, [hashtable]$Arguments = @{ Pr = 123; Repo = 'example/repo' }) {
    $global:ghScenario = $Scenario
    try { & $collector @Arguments | Out-Null } catch {
        if ($_.Exception.Message -notmatch $Pattern) { throw }
        return
    }
    throw "Scenario $Scenario must throw, not report no feedback."
}

$result = & $collector -Pr 123 -Repo example/repo | ConvertFrom-Json
Assert ($result.threads.threadId -join ',' -eq 'PRRT_open,PRRT_page2') 'Must keep unresolved threads from every page and drop resolved ones.'
Assert ($result.repo -ceq 'example/repo' -and $result.pr -eq 123) 'Must name the repository and pull request.'
$thread = $result.threads[0]
Assert ($thread.isOutdated -eq $true -and $thread.path -ceq 'src/a.py' -and $thread.line -eq 3) 'Must carry isOutdated, path and line.'
$comment = $thread.comments[0]
Assert ($comment.id -ceq '4197153031') 'Must carry the comment fullDatabaseId, as a string, for REST replies.'
Assert ($comment.author -ceq 'copilot-pull-request-reviewer' -and $comment.body -ceq 'Check this.' -and $comment.url -ceq 'u') 'Must carry each comment.'
Assert ($result.reviews.Count -eq 2) 'Must keep reviews from every page.'
Assert ($result.reviews[0].body -ceq $suppressedBody) 'Must keep the suppressed section verbatim.'
Assert ($result.reviews[0].id -eq 100 -and $result.reviews[0].author -ceq 'copilot-pull-request-reviewer[bot]' -and $result.reviews[0].state -ceq 'COMMENTED') 'Must keep review id, author and state.'
Assert ($result.reviews[0].commitId -eq 'abc123' -and $result.reviews[0].url -eq 'https://example.test/r100') 'Must keep review provenance.'
$threadCall = $global:ghCalls | Where-Object { $_ -match '^api graphql ' }
Assert ($threadCall -match '\$endCursor: String' -and $threadCall -match 'after: \$endCursor' -and $threadCall -match 'pageInfo \{ hasNextPage endCursor \}') 'The thread query must be pageable.'
foreach ($field in 'isResolved', 'isOutdated', 'path', 'line', 'fullDatabaseId', 'author { login }', 'body', 'url') {
    Assert ($threadCall -match "[{\s]$([regex]::Escape($field))[\s}]") "The thread query must request $field."
}
Assert ($threadCall -match 'owner=example(\s|$)' -and $threadCall -match 'name=repo(\s|$)' -and $threadCall -match 'pr=123(\s|$)') 'The thread query must name the repository and pull request.'
Assert (@($global:ghCalls | Where-Object { $_ -match '^api graphql --paginate --slurp ' }).Count -eq 1) 'Threads must be fetched with --paginate --slurp.'
Assert (@($global:ghCalls | Where-Object { $_ -match '/reviews --paginate --slurp$' }).Count -eq 1) 'Reviews must be fetched with --paginate --slurp.'

$global:ghScenario = 'body-only'
$result = & $collector -Pr 123 -Repo example/repo | ConvertFrom-Json
Assert ($result.threads -is [array] -and $result.threads.Count -eq 0) 'No threads must serialize as an empty array.'
Assert ($result.reviews.Count -eq 2) 'Body-only feedback must stay visible with zero threads.'

Expect-Failure 'threads-fail' 'Could not collect review threads'
Expect-Failure 'reviews-fail' 'Could not collect review bodies'
Expect-Failure 'no-repo' 'Could not resolve the repository' @{}

$global:ghScenario = 'populated'
$global:ghCalls.Clear()
$result = & $collector | ConvertFrom-Json
Assert ($result.repo -ceq 'example/repo' -and $result.pr -eq 123 -and $result.threads.Count -eq 2) 'Must default to the current repository and branch pull request.'
Write-Output 'PASS Get-PrFeedback: paginated threads and reviews, suppressed bodies, body-only feedback, defaults, three failure paths.'
