---
name: pr-feedback
description: |
  Address pull request feedback from reviews, CI, and code-analysis tools: collect threads, categorize, fix locally, present for review, then commit/reply/resolve.
  Use when resolving PR review feedback, addressing reviewer comments, fixing CI or CodeQL feedback on a PR, or preparing responses before updating a pull request.
---

# PR Feedback

Use this skill to resolve pull request feedback systematically before posting replies or resolving threads.

## Inputs and Context

- Prefer an explicitly provided PR number, URL, owner/repo, or branch.
- In VS Code, `#activePullRequest` or `#openPullRequest` may provide PR context; in other tools, infer context from the current branch, `gh pr status`, `gh pr view`, or user-provided arguments.
- Collect review threads, CI failures, code-analysis findings, and any user instructions before changing code.

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
  body: "Fixed in commit abc1234. Replaced the nested callback with async/await.",
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

### 1. Collect All Feedback

1. Identify the PR from explicit input, VS Code PR context, current branch, or `gh pr view`.
2. Use `get_pull_request_threads` to fetch all review threads.
3. Check CI status for build and test failures.
4. Review CodeQL, security scan, and code-analysis findings if present.
5. Note pending comments that have not been submitted yet.

### 2. Categorize Feedback

| Category | Description | Action Required |
| --- | --- | --- |
| Blocking | Must fix before merge | Implement fix |
| Improvement | Should fix, better code | Implement fix |
| Question | Needs clarification | Reply with explanation or question |
| Suggestion | Optional enhancement | Consider, implement, or defer |
| CI Failure | Build/test broken | Fix immediately |

If feedback is ambiguous, draft a clarification question before implementing. Do not guess reviewer intent when the requested change is unclear.

### 3. Implement Fixes Locally

For each blocking, improvement, accepted suggestion, CI failure, or analysis finding:

1. Make the code change locally.
2. Run the smallest relevant tests, linters, or checks for the touched area.
3. Verify the fix directly addresses the feedback.
4. Do not commit yet; batch all fixes together.

### 4. Prepare Responses

Draft replies for every thread before posting anything. Match the response type:

| Situation | Reply Template |
| --- | --- |
| Fixed | `Fixed in commit {sha} — {brief description}.` |
| Explained | `This is intentional because {reason}. {justification}.` |
| Deferred | `Created issue #{num} to track this. Out of scope for this PR.` |
| Declined | `Respectfully declining because {reason}. Happy to discuss.` |
| Outdated | `This code was removed/refactored in {commit}.` |

Use the detailed templates below when more context is useful.

### 5. Present for Review Before Committing

Before committing, pushing, replying, or resolving threads, present the planned outcome and ask for user approval using this output format:

```markdown
## Feedback Resolution Summary

### Feedback Addressed

| Source | Feedback Summary | Resolution | Planned Response |
| ------ | ---------------- | ---------- | ---------------- |
| [Reviewer] | [Description] | [What was done] | [Reply to post] |

### Questions (To Post)

- [Question for ambiguous feedback]

### Declined / Deferred

| Feedback | Reason | Planned Response |
| -------- | ------ | ---------------- |

### Tests Run

- [ ] All tests passing after changes

---

**Ready to commit, push, and respond?**
```

### 6. Commit, Reply, Resolve After Approval

After the user confirms:

1. Commit and push all fixes together.
2. Reply to each addressed thread using `reply_to_pull_request_comment`.
3. Resolve fixed, answered, or outdated threads using `resolve_pull_request_review_thread`.
4. Leave design disagreements or deferred work open for the reviewer unless explicitly told otherwise.
5. Verify resolution state with `check_pull_request_review_resolution`.
6. Suggest next steps:
   - `/pr-resolve` — reply to and resolve remaining PR review threads.
   - `/commit` — commit, push, and update the PR.

## Reply Templates

### Fixed Code

```text
Fixed in commit {sha}.

{Brief description of the change made to address the feedback.}
```

### Explained Design Decision

```text
This is intentional because {reason}.

{Details about why the current approach was chosen.}
{Optional: reference to design doc or prior discussion.}
```

### Deferred to Issue

```text
Good point. This is out of scope for this PR, but I've created #{issue_number} to track it.

We can address this in a follow-up.
```

### Declined with Rationale

```text
I respectfully disagree with this suggestion because {reason}.

{Explanation of tradeoffs considered.}
{Offer to discuss further if needed.}
```

### Acknowledging Suggestion

```text
Great suggestion! Implemented in commit {sha}.

{Brief note on how it improved the code.}
```

### Clarification Request

```text
Could you clarify what you mean by "{quote from feedback}"?

I want to make sure I address your concern correctly. Are you suggesting {interpretation A} or {interpretation B}?
```

## Guidelines

- Ask first, code second: clarify ambiguous feedback before implementing.
- Wait for user approval before committing, pushing, replying, or resolving.
- Be respectful; accept good suggestions and justify disagreements professionally.
- Reference commit SHAs for traceability after commits exist.
- Reply to the latest comment in each thread.
- Batch related replies to avoid notification spam.
- Never resolve without replying first.

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
