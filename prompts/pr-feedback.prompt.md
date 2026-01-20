---
name: pr-feedback
description: Address PR feedback from reviews, CI, and code analysis tools
---

# Address PR Feedback

Resolve pull request feedback systematically. This prompt references the **pr-management** skill for detailed tool usage.

## Process

1. **Collect Feedback**: Use `#activePullRequest` or `#openPullRequest` for context. Fetch threads via `get_pull_request_threads`.

2. **Categorize**: Classify each item as Blocking (must fix), Improvement (should fix), Question (needs reply), Suggestion (optional), or CI Failure (must fix).

3. **Clarify Ambiguity**: Draft clarification questions for unclear feedback before implementing.

4. **Implement Locally**: Apply fixes without committing. Run tests after changes.

5. **Present for Review**: Show summary of changes and planned responses before committing.

6. **Finalize** (after user confirms): Commit, push, reply to comments, resolve threads.

## Output Format

```markdown
## Feedback Resolution Summary

### Feedback Addressed

| Source     | Feedback Summary | Resolution      | Planned Response |
| ---------- | ---------------- | --------------- | ---------------- |
| [Reviewer] | [Description]    | [What was done] | [Reply to post]  |

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

## Guidelines

- Ask first, code second—don't guess intent
- Wait for user approval before committing/responding
- Be respectful; accept good suggestions; justify disagreements

## User Input

```text
$ARGUMENTS
```
