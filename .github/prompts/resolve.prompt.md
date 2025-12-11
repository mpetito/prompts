---
name: resolve
description: Reply to and resolve PR review threads using github-pr-review-tools
model: GPT-5.1-Codex-Max (Preview) (copilot)
agent: agent
argument-hint: Optional thread IDs or feedback to focus on
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "agent",
    "todo",
    "github/*",
    "github-pr-review-tools/*",
    "github.vscode-pull-request-github/*",
  ]
---

# PR Thread Resolution Prompt

You are resolving PR review threads after `/feedback` changes are confirmed. Prefer github-pr-review-tools functions over GH CLI/GraphQL.

## Prerequisites

- Changes committed/pushed; user confirmed addressed items.

## Process

### Step 1: Get Current PR Context

Identify current PR from available repo metadata; ask for PR number if unclear.

### Step 2: Fetch All Review Threads

Use `get_pull_request_threads` (preferred) for threads/IDs/status/file/line/comments; use batch if IDs known; use review-scoped variant if needed.

### Step 3: Reply to Each Thread

For addressed threads, `reply_to_pull_request_comment` (owner/repo/pull_number/comment_id/body). If needed, fetch detail via `get_pull_request_thread` first.

**Reply templates:**

| Type      | Template                                                                       |
| --------- | ------------------------------------------------------------------------------ |
| Fixed     | "Fixed in commit {sha} — {brief description of change}."                       |
| Explained | "This is intentional because {reason}. The current approach {justification}."  |
| Deferred  | "Created issue #{num} to track this. Out of scope for this PR."                |
| Outdated  | "This code was removed/refactored in {commit}. The concern no longer applies." |

### Step 4: Resolve Fixed Threads

- Use `resolve_pull_request_review_thread` (or batch) for fixed items; use `check_pull_request_review_resolution` if needed.

| Situation    | Action                          |
| ------------ | ------------------------------- |
| Code fixed   | ✅ Resolve                      |
| Explained    | ❌ Leave open (reviewer closes) |
| Deferred     | ❌ Leave open                   |
| Disagreement | ❌ Leave open for discussion    |

### Step 5: Add Summary Comment

Add PR comment summarizing resolutions (table below optional but preferred).

### Step 6: Update PR Description (If Needed)

If significant changes, append to PR description using available tools (avoid shelling to `gh`).

## Example Session

```bash
# 1. Get review threads
tools.get_pull_request_threads({ owner: "myorg", repo: "myrepo", pull_number: 42 })

# 2. Reply to fixed thread (reply to the latest comment in the thread)
tools.reply_to_pull_request_comment({ owner: "myorg", repo: "myrepo", pull_number: 42, comment_id: "PRRC_kwDOP3aAEM5knHc7", body: "Fixed in commit 186e28a. Replaced nested setTimeout with requestAnimationFrame for reliable DOM settling." })

# 3. Resolve the thread
tools.resolve_pull_request_review_thread({ thread_id: "PRRT_kwDOP3aAEM5knHc7" })

# 4. Reply to design decision (don't resolve)
tools.reply_to_pull_request_comment({ owner: "myorg", repo: "myrepo", pull_number: 42, comment_id: "PRRC_kwDOP3aAEM5knHco", body: "The current implementation already optimizes by checking sort_order before updating. A batch method would require interface changes beyond this PR scope." })

# 5. Add summary comment
Use the PR comment tools available to post the summary block.
```

## Output Format

After completing all resolutions, provide a conversational summary of what was achieved.

Example:
"I've resolved the review threads for PR #123.

- Fixed the `setTimeout` issue in `utils.ts`.
- Replied to the comment about sorting in `list.ts` explaining the current optimization.
- Left the design discussion about the API open for you to close.

I also added a summary comment to the PR and updated the description."

Include the detailed table if it helps clarity, but feel free to be conversational and helpful.

```markdown
## Thread Resolution Summary

| Thread              | File              | Response             | Status      |
| ------------------- | ----------------- | -------------------- | ----------- |
| [Brief description] | `path/to/file.ts` | Fixed in {commit}    | ✅ Resolved |
| [Brief description] | `path/to/file.ts` | Explained rationale  | 💬 Replied  |
| [Brief description] | `path/to/file.ts` | Deferred to #{issue} | 💬 Replied  |

### PR Updates

- [ ] Summary comment added
- [ ] PR description updated (if applicable)

### Next Steps

- Request re-review if needed: `gh pr edit --add-reviewer username`
```

## Guidelines

- Reply before resolving; explain the change.
- Resolve only when fixed/obsolete; leave design discussions for reviewer.
- Keep replies concise; reference commit SHAs; be professional.

## User Input

If the user provided specific thread IDs or context about which feedback was addressed, it is provided below.

```text
$ARGUMENTS
```
