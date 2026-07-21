# PR Scripts

Shared PowerShell wrappers over `gh api` / `gh api graphql` used by the `pr-feedback`,
`pr-resolve`, and `pr-review` skills. Not a skill itself (no SKILL.md).

Requires an authenticated `gh` CLI. All scripts auto-resolve `owner/repo` and the PR number
from the current branch when `-Repo` / `-Pr` are omitted.

| Script | Purpose |
| --- | --- |
| `Get-PrFeedback.ps1` | One-shot feedback aggregation: unresolved threads + failing checks (with log excerpts) + open code-scanning alerts. |
| `Get-PrContext.ps1` | One-shot review context: PR metadata, changed files, reviews, threads, CI status. |
| `Get-PrThreads.ps1` | List review threads (file, line, comments, resolution state) as JSON. `-Unresolved` to filter. |
| `Get-PrCheckFailures.ps1` | Failing CI checks with trimmed failure-log excerpts (`-LogTailLines`, default 50). |
| `Send-PrThreadReply.ps1` | Reply to a thread by thread ID (`PRRT_...`). |
| `Resolve-PrThread.ps1` | Resolve a thread; optional `-Body` replies first (reply-then-resolve). |
| `Test-PrThreadsResolved.ps1` | Verify resolution; exit 0 when clean, prints remaining threads otherwise. |
| `Submit-PrReview.ps1` | Submit a full review (summary + inline comments from a JSON file) in one atomic REST call. |

IDs: thread IDs start with `PRRT_`. Replies target threads directly — no comment IDs needed.
