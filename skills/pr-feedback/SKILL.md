---
name: pr-feedback
description: |
  Address pull request feedback from reviews, CI, and code-analysis tools: collect threads, categorize, fix locally, present for review, then commit/reply/resolve.
  Use when resolving PR review feedback, addressing reviewer comments, fixing CI or CodeQL feedback on a PR, or preparing responses before updating a pull request.
# Claude Code only; other hosts ignore this key. Model inherits — categorizing and fixing
# reviewer feedback is reasoning work.
effort: high
---

# PR Feedback

Use this skill to resolve pull request feedback systematically before posting replies or resolving threads.

## Inputs and Context

- Prefer an explicitly provided PR number, URL, owner/repo, or branch.
- In VS Code, `#activePullRequest` or `#openPullRequest` may provide PR context; in other tools, infer context from the current branch, `gh pr status`, `gh pr view`, or user-provided arguments.
- Collect review threads, CI failures, code-analysis findings, and any user instructions before changing code.

## Tooling

Script invocation, the fallback path when the scripts are unavailable, the resolution decision
matrix, and the reply templates are in
[`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md). Read it before the first call.

This skill leans on `Get-PrFeedback.ps1` (one-shot collection), then the thread scripts
(`Get-PrThreads.ps1`, `Send-PrThreadReply.ps1`, `Resolve-PrThread.ps1`,
`Test-PrThreadsResolved.ps1`).

## Process

### 1. Collect All Feedback

1. Identify the PR from explicit input, VS Code PR context, current branch, or `gh pr view`.
2. Run `Get-PrFeedback.ps1` — one call returns unresolved review threads, failing CI checks with log excerpts, and open code-scanning alerts.
3. Note pending comments that have not been submitted yet.

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

Draft replies for every thread before posting anything. Match the response type to the situation
using the templates in [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) — fixed,
explained, deferred, declined, outdated, or a clarification request.

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
2. For fixed, answered, or outdated threads, reply and resolve in one step with `Resolve-PrThread.ps1 -ThreadId ... -Body "..."`.
3. For threads that should stay open (design discussion, deferred work), reply only with `Send-PrThreadReply.ps1`.
4. Leave design disagreements or deferred work open for the reviewer unless explicitly told otherwise.
5. Verify resolution state with `Test-PrThreadsResolved.ps1`.
6. Suggest next steps:
   - `/pr-resolve` — reply to and resolve remaining PR review threads.
   - `/commit` — commit, push, and update the PR.

## Guidelines

- Ask first, code second: clarify ambiguous feedback before implementing.
- Wait for user approval before committing, pushing, replying, or resolving.
- Be respectful; accept good suggestions and justify disagreements professionally.
- Reference commit SHAs for traceability after commits exist.
- Batch related replies to avoid notification spam.
- Never resolve without replying first.

## Common Issues

See [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) for `Could not resolve to a node`,
`gh: Not Found`, `Cannot resolve thread`, and the script-unavailable fallback.
