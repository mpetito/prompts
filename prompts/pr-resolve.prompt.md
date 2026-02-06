---
name: pr-resolve
description: Reply to and resolve PR review threads
---

# Resolve PR Review Threads

Reply to and resolve pull request review threads. This prompt references the **pr-management** skill for detailed tool usage.

## Prerequisites

- Changes committed and pushed
- User has confirmed which items were addressed

## Process

1. **Get PR Context**: Identify owner, repo, and PR number from context.

2. **Fetch Threads**: Use `get_pull_request_threads` to get all review threads with IDs, status, and content.

3. **Reply to Threads**: Use `reply_to_pull_request_comment` for each addressed thread.

4. **Resolve Fixed Threads**: Use `resolve_pull_request_review_thread` for threads where code was fixed.

5. **Add Summary Comment**: Post summary of all resolutions to the PR.

## Reply Templates

| Type      | Template                                                        |
| --------- | --------------------------------------------------------------- |
| Fixed     | "Fixed in commit {sha} — {brief description}."                  |
| Explained | "This is intentional because {reason}."                         |
| Deferred  | "Created issue #{num} to track this. Out of scope for this PR." |
| Outdated  | "This code was removed/refactored in {commit}."                 |

## Resolution Rules

| Situation    | Action                          |
| ------------ | ------------------------------- |
| Code fixed   | ✅ Resolve                      |
| Explained    | ❌ Leave open (reviewer closes) |
| Deferred     | ❌ Leave open                   |
| Disagreement | ❌ Leave open for discussion    |

## Output Format

```markdown
## Thread Resolution Summary

| Thread        | File           | Response            | Status      |
| ------------- | -------------- | ------------------- | ----------- |
| [Description] | `path/file.ts` | Fixed in {commit}   | ✅ Resolved |
| [Description] | `path/file.ts` | Explained rationale | 💬 Replied  |

### PR Updates

- [ ] Summary comment added
- [ ] PR description updated (if applicable)
```

If further changes were pushed, suggest `/commit` to update the PR.

## Guidelines

- Reply before resolving; explain the change
- Resolve only when fixed/obsolete
- Keep replies concise; reference commit SHAs; be professional

## User Input

```text
$ARGUMENTS
```
