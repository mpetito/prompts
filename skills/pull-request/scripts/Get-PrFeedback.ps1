<#
.SYNOPSIS
Collects a pull request's feedback in one call: every unresolved review thread and every review
body, verbatim, so findings in a body's collapsed "suppressed" section stay visible.

.DESCRIPTION
Threads come from GraphQL and reviews from REST, both through `gh api --paginate --slurp`, so no
page is dropped. Each thread carries its id (PRRT_..., for resolveReviewThread), isOutdated, path,
line and up to 100 comments, each with its REST fullDatabaseId as a string (for
.../comments/<id>/replies). Throws when either fetch fails, a missing pull request included: a
failed fetch is never reported as "no feedback". Requires an authenticated gh CLI.

.EXAMPLE
./Get-PrFeedback.ps1 -Pr 123 -Repo owner/name
#>
[CmdletBinding()]
param(
    # Defaults to the pull request of the current branch.
    [int]$Pr,
    # owner/name; defaults to the current repository.
    [string]$Repo
)
$ErrorActionPreference = 'Stop'

if (-not $Repo) {
    $Repo = gh repo view --json nameWithOwner -q .nameWithOwner
    if ($LASTEXITCODE -ne 0 -or -not $Repo) { throw 'Could not resolve the repository; pass -Repo owner/name.' }
}
if (-not $Pr) {
    $Pr = gh pr view --json number -q .number
    if ($LASTEXITCODE -ne 0 -or -not $Pr) { throw 'Could not resolve the pull request; pass -Pr <number>.' }
}
$owner, $name = $Repo -split '/', 2

$query = @'
query($owner: String!, $name: String!, $pr: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line
          comments(first: 100) { nodes { fullDatabaseId author { login } body url } }
        }
      }
    }
  }
}
'@
$raw = gh api graphql --paginate --slurp -f "query=$query" -f "owner=$owner" -f "name=$name" -F "pr=$Pr"
if ($LASTEXITCODE -ne 0) { throw "Could not collect review threads for ${Repo}#${Pr}: $raw" }
$threads = foreach ($page in ($raw | ConvertFrom-Json)) {
    foreach ($t in $page.data.repository.pullRequest.reviewThreads.nodes) {
        if ($t.isResolved) { continue }
        [pscustomobject]@{
            threadId   = $t.id
            isOutdated = $t.isOutdated
            path       = $t.path
            line       = $t.line
            comments   = @($t.comments.nodes | ForEach-Object {
                [pscustomobject]@{ id = $_.fullDatabaseId; author = $_.author.login; body = $_.body; url = $_.url }
            })
        }
    }
}

$raw = gh api "repos/$Repo/pulls/$Pr/reviews" --paginate --slurp
if ($LASTEXITCODE -ne 0) { throw "Could not collect review bodies for ${Repo}#${Pr}: $raw" }
$reviews = foreach ($page in ($raw | ConvertFrom-Json)) {
    foreach ($r in $page) {
        [pscustomobject]@{
            id = $r.id; author = $r.user.login; state = $r.state; commitId = $r.commit_id
            url = $r.html_url; body = $r.body
        }
    }
}

[pscustomobject]@{
    repo    = $Repo
    pr      = $Pr
    threads = @($threads)
    reviews = @($reviews)
} | ConvertTo-Json -Depth 6
