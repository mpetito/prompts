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

You are resolving review threads on a pull request after `/feedback` has addressed the feedback and the user has confirmed the changes. Use the github-pr-review-tools functions when available (preferred over GH CLI/GraphQL shell commands) to reply to comments and resolve threads.

## Prerequisites

- Changes have been committed and pushed (from `/feedback` confirmation)
- User has confirmed which feedback items were addressed if clarification was needed

## Process

### Step 1: Get Current PR Context

Identify the current PR using the repo metadata that is already available to the agent (owner/repo/branch) or ask the user for the PR number if unclear.

### Step 2: Fetch All Review Threads

Use `get_pull_request_threads` (preferred) or `get_pull_request_review_threads` to retrieve threads, IDs, resolution status, file/line, and comments. Provide `owner`, `repo`, and `pullRequestNumber`.

### Step 3: Reply to Each Thread

For threads that were addressed, call `reply_to_pull_request_comment` with the specific comment ID you are replying to and the reply body. If you need full thread detail first, call `get_pull_request_thread` to pick the correct comment ID.

**Reply templates by resolution type:**

| Type      | Template                                                                       |
| --------- | ------------------------------------------------------------------------------ |
| Fixed     | "Fixed in commit {sha} — {brief description of change}."                       |
| Explained | "This is intentional because {reason}. The current approach {justification}."  |
| Deferred  | "Created issue #{num} to track this. Out of scope for this PR."                |
| Outdated  | "This code was removed/refactored in {commit}. The concern no longer applies." |

### Step 4: Resolve Fixed Threads

For threads where the issue was fixed, call `resolve_pull_request_review_thread` with the thread ID. Use `check_pull_request_review_resolution` if you need to verify all threads are resolved for a review.

**When to resolve vs. leave open:**

| Situation                 | Action                             |
| ------------------------- | ---------------------------------- |
| Code fix applied          | ✅ Resolve                         |
| Explained design decision | ❌ Leave open (let reviewer close) |
| Deferred to future issue  | ❌ Leave open                      |
| Disagreement              | ❌ Leave open for discussion       |

### Step 5: Add Summary Comment

Add a PR comment summarizing all resolutions using the available GitHub comment tooling. Keep the table format below for clarity.

### Step 6: Update PR Description (If Needed)

If significant changes were made, append to the PR description using the GitHub UI or available automation tools instead of shelling out to `gh`.

## Example Session

```bash
# 1. Get review threads
tools.get_pull_request_threads({ owner: "myorg", repo: "myrepo", pullRequestNumber: 42 })

# 2. Reply to fixed thread (reply to the latest comment in the thread)
tools.reply_to_pull_request_comment({ owner: "myorg", repo: "myrepo", commentId: "PRRC_kwDOP3aAEM5knHc7", body: "Fixed in commit 186e28a. Replaced nested setTimeout with requestAnimationFrame for reliable DOM settling." })

# 3. Resolve the thread
tools.resolve_pull_request_review_thread({ owner: "myorg", repo: "myrepo", threadId: "PRRT_kwDOP3aAEM5knHc7" })

# 4. Reply to design decision (don't resolve)
tools.reply_to_pull_request_comment({ owner: "myorg", repo: "myrepo", commentId: "PRRC_kwDOP3aAEM5knHco", body: "The current implementation already optimizes by checking sort_order before updating. A batch method would require interface changes beyond this PR scope." })

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

- Always reply before resolving—explain what was done
- Only resolve threads where the code was actually changed or the issue fixed (or made obsolete)
- Leave design discussions open for the reviewer to close
- Keep replies concise but informative
- Reference commit SHAs for traceability
- Be professional and appreciative of feedback

## User Input

If the user provided specific thread IDs or context about which feedback was addressed, it is provided below.

```text
$ARGUMENTS
```
