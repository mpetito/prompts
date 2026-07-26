---
name: pr-resolve
description: |
  Reply to and resolve pull request review threads after changes are pushed.
  Use when responding to PR review comments, resolving review threads, closing out addressed feedback, or verifying thread resolution status after commits are available.
# Claude Code only; other hosts ignore these keys.
model: sonnet
effort: medium
---

# PR Resolve

Use this skill after changes have been committed and pushed, or when the user asks to reply to and resolve PR review threads.

## Prerequisites

- The PR owner, repository, and number are known from user input, PR URL, branch context, or VS Code PR context.
- Changes that claim to fix review feedback are committed and pushed.
- The user has confirmed which items were addressed when there is any ambiguity.

## Tooling

Script invocation, the fallback path when the scripts are unavailable, and the reply templates
are in [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md). Read it before the first call.

The four scripts this skill uses: `Get-PrThreads.ps1`, `Send-PrThreadReply.ps1`,
`Resolve-PrThread.ps1`, `Test-PrThreadsResolved.ps1`.

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

See [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) — resolve when fixed, answered,
or outdated; reply-only for design discussion, deferrals, and disagreements.

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

Short and long forms for fixed / explained / deferred / declined / outdated / clarification
replies are in [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md).

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

See [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) for `Could not resolve to a node`,
`gh: Not Found`, `Cannot resolve thread`, and the script-unavailable fallback.
