# Offline checks for Resolve-PrThread.ps1 against a mocked gh; no GitHub access or test framework.
$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '../scripts/Resolve-PrThread.ps1'
$global:ghFail = ''
$global:ghCalls = [System.Collections.Generic.List[string]]::new()

# Stands in for gh; any call it does not recognise throws, so the network is never reached.
function gh {
    $call = $args -join ' '
    $global:ghCalls.Add($call)
    $global:LASTEXITCODE = 0
    if ($call -match '^api graphql -f query=mutation.*addPullRequestReviewThreadReply') {
        if ($global:ghFail -eq 'reply') { $global:LASTEXITCODE = 1; return 'HTTP 502' }
        return '{"data":{"addPullRequestReviewThreadReply":{"comment":{"url":"https://example.test/c1"}}}}'
    }
    if ($call -match '^api graphql -f query=mutation.*resolveReviewThread') {
        if ($global:ghFail -eq 'resolve') { $global:LASTEXITCODE = 1; return 'HTTP 502' }
        return '{"data":{"resolveReviewThread":{"thread":{"isResolved":true}}}}'
    }
    throw "Unexpected gh call (network refused): $call"
}

function Assert([bool]$Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Invoke-Case([string]$Fail) {
    $global:ghFail = $Fail
    $global:ghCalls.Clear()
    try { & $script -ThreadId PRRT_x -Body 'Fixed in 4be91c2.'; return } catch { return $_.Exception.Message }
}

$out = @(& $script -ThreadId PRRT_x -Body 'Fixed in 4be91c2.')
Assert ($out.Count -eq 1 -and $out[0] -ceq 'resolved PRRT_x https://example.test/c1') 'Must print exactly one fixed-format line.'
Assert ($global:ghCalls.Count -eq 2) 'Must make exactly two calls.'
Assert ($global:ghCalls[0] -match 'addPullRequestReviewThreadReply' -and $global:ghCalls[0] -match 'id=PRRT_x' -and $global:ghCalls[0] -match 'body=Fixed in 4be91c2\.') 'Must reply first, on the thread, with the body.'
Assert ($global:ghCalls[1] -match 'resolveReviewThread' -and $global:ghCalls[1] -match 'id=PRRT_x') 'Must resolve second.'
Assert ($global:ghCalls[0] -match 'addPullRequestReviewThreadReply\(input: \{pullRequestReviewThreadId: \$id, body: \$body\}\)') 'The reply must pass the thread id and body as its input.'
Assert ($global:ghCalls[1] -match 'resolveReviewThread\(input: \{threadId: \$id\}\)') 'The resolve must pass the thread id as its input.'

$message = Invoke-Case 'reply'
Assert ($message -match 'left open') 'A failed reply must throw.'
Assert ($global:ghCalls.Count -eq 1) 'A failed reply must never be followed by a resolve.'

$message = Invoke-Case 'resolve'
Assert ($message -match 'resolving it failed' -and $message -match 'example.test/c1') 'A failed resolve must throw and name the posted reply.'
Write-Output 'PASS Resolve-PrThread: reply then resolve, one output line, no resolve after a failed reply.'
# The last case leaves the mocked gh's LASTEXITCODE at 1, which a pwsh -command host would exit with.
exit 0
