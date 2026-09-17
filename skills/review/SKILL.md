---
name: review
description: "Review a diff, report findings by severity, and give a merge verdict. Use when reviewing code, auditing local or staged changes, checking coding standards, simplifying overengineered code or verbose comments, or before reporting a fix, refactor, or implementation complete."
---

# Code Review Skill

Procedural knowledge for performing structured, multi-dimensional code reviews on a diff or pull request.

## When to Use

- A user asks to review changes, a PR, or a diff
- Before reporting implementation complete, as the self-review step of code-authoring
- Before merging, to produce an APPROVE / REQUEST CHANGES / NEEDS DISCUSSION verdict

Scale review depth to the risk of the change. Check that findings cite project convention reuse
and concrete evidence. For someone else's GitHub PR use `pr-review`; for incoming reviewer or
Copilot feedback on your own PR use `pr-feedback`.

## Review Scope

Review what is currently staged or what was just implemented. Use `#changes` where available,
otherwise `git diff`, `git diff --cached`, and the relevant untracked files. Separate the task's
changes from pre-existing user work.

Read applicable project instructions, configuration, and comparable neighboring code before
judging style. Read the Coding Standards section of [code-authoring](../code-authoring/SKILL.md)
as reference; do not recursively run its implementation workflow. Project conventions win.

### PR Context Check

Before starting, detect open PR context:

1. Use `#activePullRequest` / `#openPullRequest` to identify if changes belong to a PR
2. If the changes belong to an open PR, fetch existing review threads (`../pr-scripts/Get-PrThreads.ps1`, resolved relative to this skill's folder) and incorporate outstanding comments into the review scope
3. Reference the `pr-feedback` and `pr-resolve` skills for detailed PR feedback and thread tooling

## Review Dimensions

Cover each relevant dimension. Skip those that do not apply to the diff (e.g. no security review needed for a docs-only change).

| Dimension           | What to Check                                                                        |
| ------------------- | ------------------------------------------------------------------------------------ |
| **Correctness**     | Logic errors, edge cases, null/empty/boundary handling, concurrency, state           |
| **Maintainability** | Clarity, naming, organization, type safety, consistency with codebase                |
| **DRY / Clean**     | Duplication, missed abstractions, unnecessary complexity                             |
| **Error Handling**  | Graceful handling, useful messages, recovery paths, no swallowed exceptions          |
| **Tests**           | Coverage of new paths, edge cases, meaningful assertions (not superficial)           |
| **Security**        | Input validation, auth checks, injection (SQL/XSS/cmd), secret handling, deps (Snyk) |
| **Performance**     | Hot paths, N+1, memory churn, query efficiency, render cost                          |
| **Documentation**   | API docs, README, inline comments where the **why** is non-obvious                   |
| **Observability**   | Logging coverage and levels, structured fields, traceability                         |

For React/Next.js/TypeScript diffs, additionally apply the `code-quality-standards` skill checklist (security, DRY, correctness, performance, accessibility).

For complex diffs, delegate independent dimensions only when useful and synthesize findings.
Apply [agent model selection](../skill-authoring/references/agent-model-selection.md) to each
worker. Provide the relevant checklist and project conventions; do not assume loaded skills
are inherited. Start on explicit Opus (or a high-capability model in another host); a weaker
reviewer needs a task-specific justification under the selection policy.

## Protocol

1. **Inventory the diff**: read every changed file; do not rely on summaries
2. **Check validation evidence**: use the project's relevant lint, typecheck, and test commands.
   Reuse results for the same code state; rerun when changes, failures, or coverage gaps warrant it.
3. **Analyze each applicable dimension** against the diff
4. **Record findings** by severity:
   - 🔴 **Critical** — must fix; blocks approval
   - 🟡 **Important** — should fix
   - 🟢 **Suggestion** — optional improvement
5. **Cite by file + function/section**, not by line number
6. **Fix minor items directly** (typos, formatting, dead-code removal). Surface anything larger for discussion before changing.

## Coding Standards (verify against)

Apply the canonical standards linked above. In particular, check that the change reuses
existing project patterns and helpers, avoids speculative abstractions and redundant guards,
and keeps comments proportionate and useful. Preserve comments about real contracts and
constraints; remove narration and duplicated rationale. Require a concrete code path or
maintenance problem for each finding, not a preference presented as a defect.

## Output Format

```markdown
## Review Summary

**Overall Assessment**: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION

### Critical Issues 🔴

- [Issue with file + function/section reference and recommended fix]

### Important Issues 🟡

- [Issue with file + function/section reference and recommendation]

### Suggestions 🟢

- [Suggestion with brief context]

### Changes Made

- [Minor fixes applied directly during review]

### Questions for Author

- [Open question or design clarification]
```

After presenting, suggest next steps:

- `/commit` — commit and open/update the PR

## Handling In-Review Change Requests

If the user, mid-review, asks for code changes, apply this decision tree:

1. **Implementing prior review recommendations** — proceed
2. **Quick / trivial change** (typo, rename, single-line fix) — apply directly
3. **Anything else** — do not implement immediately. Evaluate scope/impact, surface risks and tradeoffs, present analysis, wait for confirmation.

Default posture is **deliberation before action**; only bypass for cases 1 and 2.

## Guidelines

- Be constructive, not critical
- Explain **why** something is an issue
- Provide specific suggested fixes
- Do not nitpick style if it matches the surrounding codebase
- Focus on substance over style
- If the implementation is fundamentally wrong, explain the issue and discuss before rewriting

## Boundaries

- ✅ Run linters/tests, check `#problems`, read every changed file
- ✅ Fix minor issues directly (typos, formatting, obvious dead code)
- ⚠️ Ask first: major rewrites or architectural changes
- 🚫 Never approve code with critical issues or failing tests
- 🚫 Never commit or push — defer to `/commit`
