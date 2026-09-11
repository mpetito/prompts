# PR Thread Tooling Reference

Shared agent-facing material for the `pr-feedback`, `pr-resolve`, and `pr-review` skills.
Script inventory and parameters are in [`README.md`](README.md); this file covers how to use
them in a workflow, what to say in replies, and what to do when they fail.

Keeping this in one place is deliberate — the same tooling block and reply templates previously
lived in two skills and drifted.

## Invocation

All scripts wrap `gh api` / `gh api graphql` and require only an authenticated `gh` CLI. They
auto-resolve `owner/repo` and the PR number from the current branch when `-Repo` / `-Pr` are
omitted. Resolve the path relative to the calling skill's own folder (`../pr-scripts/`), never
relative to a repository root — the skills tree is often symlinked into a user-level location.

```powershell
# Feedback: unresolved threads + full review bodies + failing CI + code-scanning alerts
../pr-scripts/Get-PrFeedback.ps1 -Pr 123 [-Repo owner/name]

# One-shot review context: metadata, description, changed files, reviews, threads, CI status
../pr-scripts/Get-PrContext.ps1 -Pr 123 [-Repo owner/name]

# List all review threads (thread IDs, resolution state, file/line, full comments)
../pr-scripts/Get-PrThreads.ps1 -Pr 123 [-Repo owner/name] [-Unresolved]

# Failing CI checks with trimmed failure-log excerpts
../pr-scripts/Get-PrCheckFailures.ps1 -Pr 123 [-LogTailLines 50]

# Reply to a thread (by thread ID — no comment-ID lookup needed)
../pr-scripts/Send-PrThreadReply.ps1 -ThreadId PRRT_... -Body "Fixed in commit abc1234."

# Reply and resolve in one call (omit -Body to resolve only)
../pr-scripts/Resolve-PrThread.ps1 -ThreadId PRRT_... -Body "Fixed in commit abc1234."

# Verify: exit 0 when all threads resolved, otherwise prints remaining threads
../pr-scripts/Test-PrThreadsResolved.ps1 -Pr 123

# Submit a full review (summary + inline comments from a JSON file) atomically
../pr-scripts/Submit-PrReview.ps1 -Pr 123 -Event COMMENT -Body "..." -CommentsFile review-comments.json
```

Thread IDs start with `PRRT_`. Replies target threads directly.

`Get-PrFeedback.ps1` returns `reviews` with full unmodified bodies and review provenance.
Inspect collapsed `<details>` and suppressed/low-confidence sections in those bodies; these
findings may have no thread ID. An empty `unresolvedThreads` array does not establish that
all feedback was inspected. Collection fails if review bodies cannot be fetched.

For the raw review-body fallback, resolve the repository and PR first, then run:

```powershell
$repo = gh repo view --json nameWithOwner -q .nameWithOwner
$pr = gh pr view --json number -q .number
gh api "repos/$repo/pulls/$pr/reviews" --paginate --slurp
```

The [GitHub reviews API](https://docs.github.com/en/rest/pulls/reviews#list-reviews-for-a-pull-request)
provides review bodies, IDs, commit IDs, and URLs. Preserve the bodies instead of relying on
a heading-specific parser. If a suppressed section is only available in the UI, inspect it
there or disclose the gap. Use the evidence and complexity triage in
[pr-feedback](../pr-feedback/SKILL.md) for both visible and suppressed claims.

**Fallback**: if the scripts are unavailable (e.g. a non-Windows agent), use GitHub MCP PR tools
if configured (`pull_request_read`, `reply_to_pull_request_comment` or its consolidated
successor, `resolve_pull_request_review_thread`), or issue the same GraphQL via `gh api graphql`
directly.

---

## Resolution Decision Matrix

| Thread type                      | Action                                             |
| -------------------------------- | -------------------------------------------------- |
| Code fixed                       | ✅ Reply then resolve                              |
| Question answered                | ✅ Reply then resolve when no reviewer action needed |
| Design explained                 | 💬 Reply only; the reviewer closes it              |
| Deferred to issue                | 💬 Reply only                                      |
| Disagreement                     | 💬 Reply only; discuss further                     |
| Outdated code removed/refactored | ✅ Reply then resolve                              |

Never resolve without replying first, and never resolve another reviewer's thread on their behalf
when the point is still open.

---

## Reply Templates

Short forms:

| Situation | Template                                                            |
| --------- | ------------------------------------------------------------------- |
| Fixed     | `Fixed in commit {sha} — {brief description}.`                      |
| Explained | `This is intentional because {reason}. {justification}.`             |
| Deferred  | `Created issue #{num} to track this. Out of scope for this PR.`      |
| Declined  | `Respectfully declining because {reason}. Happy to discuss.`         |
| Outdated  | `This code was removed/refactored in {commit}.`                      |

Longer forms, when more context genuinely helps:

```text
Fixed in commit {sha}.

{Brief description of the change made to address the feedback.}
```

```text
This is intentional because {reason}.

{Details about why the current approach was chosen.}
{Optional: reference to design doc or prior discussion.}
```

```text
Good point. This is out of scope for this PR, but I've created #{issue_number} to track it.

We can address this in a follow-up.
```

```text
I respectfully disagree with this suggestion because {reason}.

{Explanation of tradeoffs considered.}
{Offer to discuss further if needed.}
```

```text
Great suggestion! Implemented in commit {sha}.

{Brief note on how it improved the code.}
```

```text
Could you clarify what you mean by "{quote from feedback}"?

I want to make sure I address your concern correctly. Are you suggesting {interpretation A}
or {interpretation B}?
```

---

## Common Issues

| Problem                       | Fix                                                                                                                              |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `Could not resolve to a node` | Verify the thread ID starts with `PRRT_`, refresh with `Get-PrThreads.ps1`, and check whether it was deleted or already resolved. |
| `gh: Not Found`               | Check `-Repo`/`-Pr` values; auto-resolution requires the current branch to have an open PR.                                      |
| `Cannot resolve thread`       | Check permissions; some repos require reviewers to resolve their own threads.                                                    |
| Script unavailable            | Use the GitHub MCP fallback or raw `gh api graphql` (see **Invocation**).                                                        |
