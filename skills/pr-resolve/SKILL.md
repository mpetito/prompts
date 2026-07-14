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

## Core MCP Tools

### Thread Discovery

```javascript
// Get all review threads for a PR
get_pull_request_threads({
  owner: "org-name",
  repo: "repo-name",
  pull_number: 123,
});
```

Returns thread IDs, status, file paths, line numbers, comment IDs, and comment content.

### Replying to Comments

```javascript
// Reply to a specific comment in a thread
reply_to_pull_request_comment({
  owner: "org-name",
  repo: "repo-name",
  pull_number: 123,
  comment_id: "PRRC_kwDOP3aAEM5knHc7",
  body: "Fixed in commit 186e28a. Replaced setTimeout with requestAnimationFrame.",
});
```

Use the comment ID from the thread, not the thread ID. Reply to the latest comment in a thread to maintain conversation flow.

### Resolving Threads

```javascript
// Resolve a thread after addressing feedback
resolve_pull_request_review_thread({
  thread_id: "PRRT_kwDOP3aAEM5knHc7",
});
```

Thread IDs typically start with `PRRT_`; comment IDs typically start with `PRRC_`.

### Checking Resolution Status

```javascript
// Verify thread resolution status
check_pull_request_review_resolution({
  owner: "org-name",
  repo: "repo-name",
  pull_number: 123,
});
```

Use after batch resolutions to confirm all intended threads were resolved.

## Process

1. Identify owner, repo, and PR number from explicit input, PR URL, VS Code PR context, current branch, or `gh pr view`.
2. Fetch all review threads with `get_pull_request_threads`.
3. Skip already-resolved threads unless the user asks to audit them.
4. For each unresolved thread, verify the feedback was addressed by checking the diff, commit history, and relevant test results.
5. Craft a concise reply with a commit reference when available.
6. Post the reply with `reply_to_pull_request_comment`.
7. Resolve only threads that meet the resolution rules below.
8. Optionally add a PR summary comment or update the PR description when the user requested a broader summary.
9. Verify final state with `check_pull_request_review_resolution`.

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
    3. Post the reply via reply_to_pull_request_comment.
    4. IF the thread is fixed, answered, or outdated:
           resolve via resolve_pull_request_review_thread.
    5. IF it is a design discussion, deferred work, or disagreement:
           leave open for the reviewer.
```

## Batch Resolution Example

```javascript
// 1. Get threads
const threads = await get_pull_request_threads({
  owner: "myorg",
  repo: "myrepo",
  pull_number: 42,
});

// 2. Reply to fixed thread
await reply_to_pull_request_comment({
  owner: "myorg",
  repo: "myrepo",
  pull_number: 42,
  comment_id: "PRRC_kwDOP3aAEM5knHc7",
  body: "Fixed in commit 186e28a. Replaced setTimeout with requestAnimationFrame.",
});

// 3. Resolve the thread
await resolve_pull_request_review_thread({
  thread_id: "PRRT_kwDOP3aAEM5knHc7",
});

// 4. Reply to design question without resolving
await reply_to_pull_request_comment({
  owner: "myorg",
  repo: "myrepo",
  pull_number: 42,
  comment_id: "PRRC_kwDOP3aAEM5knHco",
  body: "The current approach optimizes by checking sort_order before updating. A batch API would require interface changes beyond this PR's scope.",
});

// 5. Verify all resolutions
await check_pull_request_review_resolution({
  owner: "myorg",
  repo: "myrepo",
  pull_number: 42,
});
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
- Reply to the latest comment in a thread.
- Batch related replies to avoid notification spam.
- Use `check_pull_request_review_resolution` after batch updates.

## Common Issues

| Problem | Fix |
| --- | --- |
| `Thread not found` | Verify the thread ID starts with `PRRT_`, refresh with `get_pull_request_threads`, and check whether it was deleted or already resolved. |
| `Comment not found` | Use the comment ID (`PRRC_`), not the thread ID; pending comments may not have IDs yet. |
| `Cannot resolve thread` | Check permissions; some repos require reviewers to resolve their own threads. |

## User Input

```text
$ARGUMENTS
```
