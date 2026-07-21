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

## Tooling

Use the PowerShell scripts in `../pr-scripts/` (sibling folder within the skills tree; resolve the path relative to this skill's folder). They wrap `gh api graphql` and require only an authenticated `gh` CLI. All scripts auto-resolve `owner/repo` and PR number from the current branch when omitted.

```powershell
# One-shot feedback collection: unresolved threads + failing CI (with log excerpts) + code-scanning alerts
../pr-scripts/Get-PrFeedback.ps1 -Pr 123 [-Repo owner/name]

# List all review threads (thread IDs, resolution state, file/line, full comments)
../pr-scripts/Get-PrThreads.ps1 -Pr 123 [-Repo owner/name] [-Unresolved]

# Reply to a thread (by thread ID — no comment-ID lookup needed)
../pr-scripts/Send-PrThreadReply.ps1 -ThreadId PRRT_... -Body "Fixed in commit abc1234."

# Reply and resolve in one call (omit -Body to resolve only)
../pr-scripts/Resolve-PrThread.ps1 -ThreadId PRRT_... -Body "Fixed in commit abc1234."

# Verify: exit 0 when all threads resolved, otherwise prints remaining threads
../pr-scripts/Test-PrThreadsResolved.ps1 -Pr 123
```

Thread IDs start with `PRRT_`. Replies target threads directly.

Fallback: if the scripts are unavailable (e.g., non-Windows agent), use GitHub MCP PR tools if configured (`pull_request_read`, `reply_to_pull_request_comment` or its consolidated successor, `resolve_pull_request_review_thread`), or issue the same GraphQL via `gh api graphql` directly.

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
2. For fixed, answered, or outdated threads, reply and resolve in one step with `Resolve-PrThread.ps1 -ThreadId ... -Body "..."`.
3. For threads that should stay open (design discussion, deferred work), reply only with `Send-PrThreadReply.ps1`.
4. Leave design disagreements or deferred work open for the reviewer unless explicitly told otherwise.
5. Verify resolution state with `Test-PrThreadsResolved.ps1`.
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
- Batch related replies to avoid notification spam.
- Never resolve without replying first.

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
