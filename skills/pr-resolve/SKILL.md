---
name: pr-resolve
description: |
  Reply to and resolve pull request review threads after changes are pushed.
  Use when responding to PR review comments, resolving review threads, closing out addressed feedback, or verifying thread resolution status after commits are available.
---

# PR Resolve

Use this skill after changes have been committed and pushed, or when the user asks to reply to and resolve PR review threads.

## Prerequisites

- The PR owner, repository, and number are known from user input, PR URL, branch context, or VS Code PR context.
- Changes that claim to fix review feedback are committed and pushed.
- The user has confirmed which items were addressed when there is any ambiguity.

## Tooling

Use the PowerShell scripts in `../pr-scripts/` (sibling folder within the skills tree; resolve the path relative to this skill's folder). They wrap `gh api graphql` and require only an authenticated `gh` CLI. All scripts auto-resolve `owner/repo` and PR number from the current branch when omitted.

```powershell
# List all review threads (thread IDs, resolution state, file/line, full comments)
../pr-scripts/Get-PrThreads.ps1 -Pr 123 [-Repo owner/name] [-Unresolved]

# Reply to a thread (by thread ID — no comment-ID lookup needed)
../pr-scripts/Send-PrThreadReply.ps1 -ThreadId PRRT_... -Body "Fixed in commit 186e28a."

# Reply and resolve in one call (omit -Body to resolve only)
../pr-scripts/Resolve-PrThread.ps1 -ThreadId PRRT_... -Body "Fixed in commit 186e28a."

# Verify: exit 0 when all threads resolved, otherwise prints remaining threads
../pr-scripts/Test-PrThreadsResolved.ps1 -Pr 123
```

Thread IDs start with `PRRT_`. Replies target threads directly.

Fallback: if the scripts are unavailable (e.g., non-Windows agent), use GitHub MCP PR tools if configured (`pull_request_read`, `reply_to_pull_request_comment` or its consolidated successor, `resolve_pull_request_review_thread`), or issue the same GraphQL via `gh api graphql` directly.

## Process

1. Identify owner, repo, and PR number from explicit input, PR URL, VS Code PR context, current branch, or `gh pr view`.
2. Fetch all review threads with `Get-PrThreads.ps1`.
3. Skip already-resolved threads unless the user asks to audit them.
4. For each unresolved thread, verify the feedback was addressed by checking the diff, commit history, and relevant test results.
5. Craft a concise reply with a commit reference when available.
6. For threads being resolved, use `Resolve-PrThread.ps1 -ThreadId ... -Body "..."` (reply + resolve in one call); for reply-only threads, use `Send-PrThreadReply.ps1`.
7. Resolve only threads that meet the resolution rules below.
8. Optionally add a PR summary comment or update the PR description when the user requested a broader summary.
9. Verify final state with `Test-PrThreadsResolved.ps1`.

## Resolution Decision Matrix

| Thread Type | Action |
| --- | --- |
| Code fixed | ✅ Reply then resolve |
| Question answered | ✅ Reply then resolve when no reviewer action is needed |
| Design explained | 💬 Reply only; reviewer closes |
| Deferred to issue | 💬 Reply only |
| Disagreement | 💬 Reply only; discuss further |
| Outdated code removed/refactored | ✅ Reply then resolve |

## Resolution Procedure

```text
FOR each unresolved thread:
    1. Verify the feedback was addressed by checking code, commits, and tests.
    2. Craft an appropriate reply with a commit SHA when possible.
    3. IF the thread is fixed, answered, or outdated:
           Resolve-PrThread.ps1 -ThreadId {id} -Body {reply}   # reply + resolve
    4. IF it is a design discussion, deferred work, or disagreement:
           Send-PrThreadReply.ps1 -ThreadId {id} -Body {reply}  # leave open for the reviewer
```

## Batch Resolution Example

```powershell
# 1. Get unresolved threads
../pr-scripts/Get-PrThreads.ps1 -Pr 42 -Unresolved

# 2. Reply and resolve a fixed thread in one call
../pr-scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDOP3aAEM5knHc7 `
  -Body "Fixed in commit 186e28a. Replaced setTimeout with requestAnimationFrame."

# 3. Reply to a design question without resolving
../pr-scripts/Send-PrThreadReply.ps1 -ThreadId PRRT_kwDOP3aAEM5knHco `
  -Body "The current approach optimizes by checking sort_order before updating. A batch API would require interface changes beyond this PR's scope."

# 4. Verify all resolutions
../pr-scripts/Test-PrThreadsResolved.ps1 -Pr 42
```

## Reply Templates

| Type | Template |
| --- | --- |
| Fixed | `Fixed in commit {sha} — {brief description}.` |
| Explained | `This is intentional because {reason}.` |
| Deferred | `Created issue #{num} to track this. Out of scope for this PR.` |
| Outdated | `This code was removed/refactored in {commit}.` |
| Declined | `I respectfully disagree with this suggestion because {reason}. {tradeoff}.` |

### Longer Replies

```text
Fixed in commit {sha}.

{Brief description of the change made to address the feedback.}
```

```text
Good point. This is out of scope for this PR, but I've created #{issue_number} to track it.

We can address this in a follow-up.
```

```text
Could you clarify what you mean by "{quote from feedback}"?

I want to make sure I address your concern correctly. Are you suggesting {interpretation A} or {interpretation B}?
```

## Output Format

```markdown
## Thread Resolution Summary

| Thread | File | Response | Status |
| ------ | ---- | -------- | ------ |
| [Description] | `path/file.ts` | Fixed in {commit} | ✅ Resolved |
| [Description] | `path/file.ts` | Explained rationale | 💬 Replied |

### PR Updates

- [ ] Summary comment added
- [ ] PR description updated (if applicable)

### Verification

- [ ] Resolution status checked
```

If further changes were pushed, suggest `/commit` to update the PR.

## Guidelines

- Reply before resolving; explain what changed.
- Resolve only when fixed, answered, or obsolete.
- Leave design discussions, deferred work, and disagreements open for the reviewer.
- Keep replies concise, professional, and traceable to commit SHAs.
- Batch related replies to avoid notification spam.
- Run `Test-PrThreadsResolved.ps1` after batch updates.

## Common Issues

| Problem | Fix |
| --- | --- |
| `Could not resolve to a node` | Verify the thread ID starts with `PRRT_`, refresh with `Get-PrThreads.ps1`, and check whether it was deleted or already resolved. |
| `gh: Not Found` | Check `-Repo`/`-Pr` values; auto-resolution requires the current branch to have an open PR. |
| `Cannot resolve thread` | Check permissions; some repos require reviewers to resolve their own threads. |

## User Input

```text
$ARGUMENTS
```
