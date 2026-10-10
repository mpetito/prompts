# Shared helpers for PR review-thread scripts. Requires gh CLI (authenticated).

function Resolve-PrContext {
    [CmdletBinding()]
    param(
        [string]$Repo,
        [int]$Pr
    )
    if (-not $Repo) {
        $Repo = gh repo view --json nameWithOwner -q .nameWithOwner
        if ($LASTEXITCODE -ne 0 -or -not $Repo) {
            throw "Could not resolve repository. Pass -Repo owner/name or run inside a repo with a GitHub remote."
        }
    }
    if (-not $Pr) {
        $prNum = gh pr view --json number -q .number 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $prNum) {
            throw "Could not resolve PR from the current branch. Pass -Pr <number>."
        }
        $Pr = [int]$prNum
    }
    $owner, $name = $Repo -split '/', 2
    [pscustomobject]@{ Owner = $owner; Name = $name; Repo = $Repo; Pr = $Pr }
}

function Invoke-GhGraphQL {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Query,
        [hashtable]$StringFields = @{},
        [hashtable]$IntFields = @{}
    )
    $ghArgs = @('api', 'graphql', '-f', "query=$Query")
    foreach ($k in $StringFields.Keys) { $ghArgs += @('-f', "$k=$($StringFields[$k])") }
    foreach ($k in $IntFields.Keys) { $ghArgs += @('-F', "$k=$($IntFields[$k])") }
    $raw = gh @ghArgs
    if ($LASTEXITCODE -ne 0) {
        throw "gh api graphql failed (exit $LASTEXITCODE): $raw"
    }
    $raw | ConvertFrom-Json
}

function Get-PrReviewThreads {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][pscustomobject]$Context,
        [switch]$Unresolved
    )
    $query = @'
query($owner: String!, $name: String!, $pr: Int!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $cursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          isResolved
          isOutdated
          path
          line
          startLine
          comments(first: 50) {
            nodes { id author { login } body createdAt url }
          }
        }
      }
    }
  }
}
'@
    $threads = @()
    $cursor = $null
    do {
        $strFields = @{ owner = $Context.Owner; name = $Context.Name }
        if ($cursor) { $strFields.cursor = $cursor }
        $resp = Invoke-GhGraphQL -Query $query -StringFields $strFields -IntFields @{ pr = $Context.Pr }
        $page = $resp.data.repository.pullRequest.reviewThreads
        $threads += $page.nodes
        $cursor = $page.pageInfo.endCursor
    } while ($page.pageInfo.hasNextPage)

    if ($Unresolved) { $threads = @($threads | Where-Object { -not $_.isResolved }) }

    @($threads | ForEach-Object {
        [pscustomobject]@{
            threadId   = $_.id
            isResolved = $_.isResolved
            isOutdated = $_.isOutdated
            path       = $_.path
            line       = $_.line
            startLine  = $_.startLine
            author     = $_.comments.nodes[0].author.login
            comments   = @($_.comments.nodes | ForEach-Object {
                [pscustomobject]@{
                    author    = $_.author.login
                    body      = $_.body
                    createdAt = $_.createdAt
                    url       = $_.url
                }
            })
        }
    })
}

Export-ModuleMember -Function Resolve-PrContext, Invoke-GhGraphQL, Get-PrReviewThreads
