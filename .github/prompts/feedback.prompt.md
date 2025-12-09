---
name: feedback
description: Address PR feedback from reviews, CI, and code analysis tools
model: Claude Opus 4.5 (Preview) (copilot)
agent: agent
argument-hint: Optional specific feedback to focus on
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "web",
    "agent",
    "todo",
    "perplexity/*",
    "docs-context7/*",
    "github/*",
    "github-pr-review-tools/*",
    "github.vscode-pull-request-github/*",
  ]
---

# PR Feedback Resolution Prompt

You are addressing feedback on the current pull request. Your goal is to resolve all actionable feedback while maintaining the original design intent.

**IMPORTANT**: Do NOT commit, push, or respond to PR feedback until the user has reviewed and explicitly confirmed your changes. Prepare all changes locally, present them for review, and wait for confirmation before finalizing.

## Feedback Sources

Gather feedback from all available sources:

1. **Copilot Review Comments** — Automated suggestions from GitHub Copilot
2. **Human Review Comments** — Feedback from team members
3. **CodeQL Findings** — Security and code quality issues from CodeQL analysis
4. **SonarQube Findings** — Code smells, bugs, and vulnerabilities from SonarQube
5. **CI Failures** — Build, test, or pipeline failures

## Process

### Step 1: Collect All Feedback

- Use `#activePullRequest` or `#openPullRequest` to access PR details
- Fetch review threads with `get_pull_request_threads` (or `get_pull_request_review_threads` for a specific review); if you already have thread IDs, use `get_pull_request_threads_batch`. Provide `owner`, `repo`, and `pull_number`.
- Review all pending comments and thread statuses from the retrieved data
- Check CI/CD status for failures
- Identify CodeQL and SonarQube findings if available

### Step 2: Categorize Feedback

Organize feedback by type:

| Category        | Action Required                          |
| --------------- | ---------------------------------------- |
| **Blocking**    | Must resolve before merge                |
| **Improvement** | Should address, reviewer expects changes |
| **Question**    | Needs clarification or response          |
| **Suggestion**  | Optional, can discuss or defer           |
| **CI Failure**  | Must fix—build/test must pass            |

### Step 3: Clarify Ambiguity FIRST

**Before making any changes**, if feedback is ambiguous:

- Ask clarifying questions in the PR thread
- Confirm understanding of the expected change
- Do NOT guess at intent—ask the reviewer

Examples of ambiguity requiring clarification:

- "This could be improved" (How?)
- "Consider refactoring this" (What approach?)
- "Is this the right pattern?" (What alternative is suggested?)

### Step 4: Reference Design Documents

Before addressing feedback:

- Review any planning documents or refined prompts from earlier steps
- Ensure proposed changes align with the original design intent
- If feedback conflicts with the design, discuss before changing

### Step 5: Address Feedback (Local Only)

For each piece of feedback:

1. Implement the requested change locally (if clear and aligned with design)
2. Run relevant tests to verify the fix
3. **Do NOT commit, push, or respond to comments yet**

### Step 6: Present Changes for User Review

**STOP and present a summary to the user before proceeding:**

- List all changes made
- Show the planned responses to each feedback item
- Ask the user to review and confirm

**Wait for explicit user confirmation before proceeding to Step 7.**

### Step 7: Finalize (After User Confirmation)

Once the user confirms:

1. Commit and push all changes
2. Reply to each comment using `reply_to_pull_request_comment` (provide `owner`, `repo`, `pull_number`, `comment_id`) explaining what was done
3. Resolve fixed threads with `resolve_pull_request_review_thread` or `resolve_pull_request_review_threads_batch`; use `check_pull_request_review_resolution` if you need to confirm review-wide resolution

## Subagent Delegation

Use `runSubagent` to preserve your context window for the feedback workflow while delegating analysis and resolution:

| Scenario                         | Subagent Task                                                    | What to Request Back                                             |
| -------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Parallel feedback resolution** | Address a group of related feedback items independently          | Changes made, issues encountered, files modified                 |
| **CI failure investigation**     | Investigate specific build or test failures blocking merge       | Root cause, affected code, suggested fix                         |
| **CodeQL/SonarQube analysis**    | Deep-dive into security or quality findings                      | Detailed explanation of issue, remediation options, code changes |
| **Large diff understanding**     | Analyze extensive changes to understand context for feedback     | Summary of changes, intent of modifications, affected areas      |
| **Test coverage analysis**       | Verify that feedback-related changes have adequate test coverage | Coverage gaps, suggested test cases                              |

**When to delegate**:

- For multiple independent feedback items: Delegate groups of related feedback in parallel
- For CI failures: Delegate investigation to get actionable fix recommendations
- For complex findings: Delegate deep analysis of security or quality issues
- For context gathering: Delegate understanding of large diffs to inform responses

**Feedback efficiency pattern**: Group related feedback items and delegate each group to a subagent for parallel resolution. Synthesize results and present to user for confirmation.

**Example delegations**:

_Parallel feedback resolution_:

```
Address the following review feedback items:
[List of related feedback items with file/line references]

For each item:
1. Implement the requested change
2. Verify the fix doesn't break related code
3. Report what was changed and any concerns

Do NOT commit or respond to comments - just implement the fixes locally.
```

_CI failure investigation_:

```
Investigate the CI failure in [workflow/job]. Analyze:
1. The error message and stack trace
2. Which code changes likely caused the failure
3. Root cause analysis
4. Suggested fix with specific code changes
```

## Output Format

Present this summary for user review before committing:

```markdown
## Feedback Resolution Summary

### Feedback Addressed

| Source     | Feedback Summary    | Resolution         | Planned Response |
| ---------- | ------------------- | ------------------ | ---------------- |
| [Reviewer] | [Brief description] | [What was done]    | [Reply to post]  |
| CodeQL     | [Finding]           | [Fix applied]      | [Reply to post]  |
| CI         | [Failure]           | [How it was fixed] | N/A              |

### Questions Asked (Already Posted)

- [Question posted to reviewer about ambiguous feedback]

### Declined / Deferred

| Feedback     | Reason                            | Planned Response |
| ------------ | --------------------------------- | ---------------- |
| [Suggestion] | [Why it was declined or deferred] | [Reply to post]  |

### Remaining Issues

- [Any unresolved items requiring further discussion]

### Tests Run

- [ ] All tests passing after changes

---

**Ready to commit, push, and respond to feedback?**
Please review the changes and confirm to proceed.
```

## Guidelines

- **Ask first, code second** — Never guess at ambiguous feedback
- **User confirms before finalizing** — Do not commit, push, or respond until user approves
- Preserve the original design intent unless explicitly told to change it
- Be respectful and professional in all responses
- If a suggestion improves the code, accept it graciously
- If you disagree, explain your reasoning constructively
- Mark threads resolved only after the change is verified
- Run tests after every change to catch regressions

## User Input

If the user provided specific feedback to focus on or additional context, it is provided below. Otherwise, gather all feedback from the current PR.

```text
$ARGUMENTS
```
