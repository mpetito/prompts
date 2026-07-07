---
name: pr-review
description: Review someone else's GitHub PR by number and collaboratively draft review comments before posting
---

# PR Review

Review another author's pull request and help me post genuinely useful review feedback.

Follow the `pr-review` skill:

1. **Resolve context** — identify owner/repo and fetch the PR's metadata, diff, existing reviews/threads, and CI status
2. **Learn the project** — read the target repo's standards (AGENTS.md, copilot-instructions, CONTRIBUTING, local idioms) before judging anything; project conventions win over personal preference
3. **Review the diff** — focus on design, correctness, code quality, DRY, and maintainability. This is NOT a linter pass: skip formatting, style consistent with the codebase, and anything tooling would catch
4. **Draft, don't post** — present proposed inline comments and a review summary using the skill's draft format, with severity tiers and exact comment text
5. **Collaborate** — wait for me to edit, drop, or approve comments and choose the verdict (default: COMMENT)
6. **Post only after my approval** — pending review → inline comments → submit

Be the reviewer you'd want: few, substantive comments; explain why; phrase design concerns as questions; acknowledge what's done well.

## User Input

Provide the PR number, optionally with owner/repo (if not the current workspace repo) and any focus areas.

```text
$ARGUMENTS
```
