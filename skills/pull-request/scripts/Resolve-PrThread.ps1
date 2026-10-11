<#
.SYNOPSIS
Replies to a pull request review thread, then resolves it; never resolves without the reply.

.DESCRIPTION
Posts -Body as a reply on the thread (addPullRequestReviewThreadReply), then resolves it
(resolveReviewThread). Throws, leaving the thread open, if the reply fails. On success prints
exactly one line: `resolved <thread id> <reply url>`. Requires an authenticated gh CLI.

.EXAMPLE
./Resolve-PrThread.ps1 -ThreadId PRRT_kwDO... -Body 'Fixed in 4be91c2: ...'
#>
[CmdletBinding()]
param(
    # The thread's node id, PRRT_...
    [Parameter(Mandatory)][string]$ThreadId,
    [Parameter(Mandatory)][string]$Body
)
$ErrorActionPreference = 'Stop'

$reply = 'mutation($id: ID!, $body: String!) { addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $id, body: $body}) { comment { url } } }'
$raw = gh api graphql -f "query=$reply" -f "id=$ThreadId" -f "body=$Body"
if ($LASTEXITCODE -ne 0) { throw "Reply to $ThreadId failed; the thread was left open: $raw" }
$url = ($raw | ConvertFrom-Json).data.addPullRequestReviewThreadReply.comment.url

$resolve = 'mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }'
$raw = gh api graphql -f "query=$resolve" -f "id=$ThreadId"
if ($LASTEXITCODE -ne 0) { throw "Replied on $ThreadId ($url) but resolving it failed: $raw" }

"resolved $ThreadId $url"
