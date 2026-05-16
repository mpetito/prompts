---
name: review
description: Review staged or just-implemented changes for correctness, maintainability, and quality
---

# Review

Perform a structured code review of the current changes.

Follow the `code-review` skill: inventory the diff via `#changes`, run linters and tests, analyze each applicable dimension (correctness, maintainability, DRY, error handling, tests, security, performance, documentation, observability), and produce a verdict.

If the changes belong to an open PR, fetch existing review threads and incorporate outstanding comments into the review scope (see the `pr-management` skill).

Fix minor issues (typos, formatting, dead code) directly; surface anything larger for discussion before changing.

End with the standard review output and suggest `/commit` or `/tweak` as next steps.

## User Input

If the user provided specific focus areas or context below, prioritize those aspects in the review. Otherwise, perform a comprehensive review of all staged changes.

```text
$ARGUMENTS
```
