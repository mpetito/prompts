---
name: resolve
description: Reply to and resolve PR review threads using GH CLI
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
    "github.vscode-pull-request-github/*",
  ]
---

# PR Thread Resolution Prompt

You are resolving review threads on a pull request after `/feedback` has addressed the feedback and the user has confirmed the changes. Use the GH CLI with GraphQL to reply to comments and resolve threads.

## Prerequisites

- Changes have been committed and pushed (from `/feedback` confirmation)
- User has confirmed which feedback items were addressed

## Process

### Step 1: Get Current PR Context

Identify the current PR:

```bash
# Get current branch and PR number
gh pr view --json number,url,title
```

### Step 2: Fetch All Review Threads

Get all review threads with their IDs and resolution status:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            path
            line
            comments(first: 50) {
              nodes {
                id
                body
                author { login }
                createdAt
              }
            }
          }
        }
      }
    }
  }
' -f owner=OWNER -f repo=REPO -F pr=PR_NUMBER
```

### Step 3: Reply to Each Thread

For threads that were addressed, reply with what was done:

```bash
# Reply to a review thread
gh api graphql -f query='
  mutation($threadId: ID!, $body: String!) {
    addPullRequestReviewThreadReply(input: {
      pullRequestReviewThreadId: $threadId,
      body: $body
    }) {
      comment { id }
    }
  }
' -f threadId="PRRT_xxx" -f body="Fixed in commit abc123 — description of fix."
```

**Reply templates by resolution type:**

| Type      | Template                                                                       |
| --------- | ------------------------------------------------------------------------------ |
| Fixed     | "Fixed in commit {sha} — {brief description of change}."                       |
| Explained | "This is intentional because {reason}. The current approach {justification}."  |
| Deferred  | "Created issue #{num} to track this. Out of scope for this PR."                |
| Outdated  | "This code was removed/refactored in {commit}. The concern no longer applies." |

### Step 4: Resolve Fixed Threads

For threads where the issue was fixed, resolve them:

```bash
# Resolve a review thread
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { isResolved }
    }
  }
' -f threadId="PRRT_xxx"
```

**When to resolve vs. leave open:**

| Situation                 | Action                             |
| ------------------------- | ---------------------------------- |
| Code fix applied          | ✅ Resolve                         |
| Explained design decision | ❌ Leave open (let reviewer close) |
| Deferred to future issue  | ❌ Leave open                      |
| Disagreement              | ❌ Leave open for discussion       |

### Step 5: Add Summary Comment

Add a PR comment summarizing all resolutions:

```bash
gh pr comment --body "## Review Feedback Addressed

| Thread | File | Resolution | Status |
|--------|------|------------|--------|
| [Description] | \`path/to/file.ts\` | Fixed in abc123 | ✅ Resolved |
| [Description] | \`path/to/file.ts\` | Explained rationale | 💬 Replied |

All automated checks passing. Ready for re-review."
```

### Step 6: Update PR Description (If Needed)

If significant changes were made, append to the PR description:

```bash
# Get current description
gh pr view --json body -q '.body' > pr_body.md

# Append update section
echo "
---

## Updates from Review Feedback

**Commit:** abc123

- Fixed: [description]
- Fixed: [description]
- Addressed: [description]
" >> pr_body.md

# Update PR
gh pr edit --body-file pr_body.md

# Cleanup
rm pr_body.md
```

## Example Session

```bash
# 1. Get review threads
gh api graphql -f query='query { repository(owner: "myorg", name: "myrepo") { pullRequest(number: 42) { reviewThreads(first: 100) { nodes { id isResolved path comments(first: 1) { nodes { body } } } } } } }'

# 2. Reply to fixed thread
gh api graphql -f query='mutation { addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: "PRRT_kwDOP3aAEM5knHc7", body: "Fixed in commit 186e28a. Replaced nested setTimeout with requestAnimationFrame for reliable DOM settling."}) { comment { id } } }'

# 3. Resolve the thread
gh api graphql -f query='mutation { resolveReviewThread(input: {threadId: "PRRT_kwDOP3aAEM5knHc7"}) { thread { isResolved } } }'

# 4. Reply to design decision (don't resolve)
gh api graphql -f query='mutation { addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: "PRRT_kwDOP3aAEM5knHco", body: "The current implementation already optimizes by checking sort_order before updating. A batch method would require interface changes beyond this PR scope."}) { comment { id } } }'

# 5. Add summary comment
gh pr comment --body "## Review Feedback Addressed

| Thread | Resolution | Status |
|--------|------------|--------|
| setTimeout pattern | Fixed with requestAnimationFrame | ✅ Resolved |
| Batch update method | Explained current optimization | 💬 Replied |

Ready for re-review."
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
