---
name: review
description: "Methodology for reviewing your own local or staged code changes across correctness, maintainability, DRY, error handling, tests, security, performance, documentation, and observability. Use when reviewing a working-tree or staged diff, auditing changes you just implemented, or producing a structured code-review verdict before committing. To review someone else's PR by number and post comments on GitHub, use `pr-review` instead."
---

# Code Review Skill

Procedural knowledge for performing structured, multi-dimensional code reviews on a diff or pull request.

## When to Use

- A user asks to review changes, a PR, or a diff
- After implementation completes and an independent quality pass is wanted
- Before merging, to produce an APPROVE / REQUEST CHANGES / NEEDS DISCUSSION verdict

## Review Scope

Review what is currently staged or what was just implemented. Use `#changes` for the diff.

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

For complex diffs, delegate independent dimensions to subagents in parallel (e.g. `Explore` for pattern compliance, a dedicated subagent per high-cost dimension) and synthesize the findings. Subagents are stateless and do not auto-load skills — embed the relevant dimension's checklist and coding standards directly in each subagent prompt.

## Protocol

1. **Inventory the diff**: read every changed file; do not rely on summaries
2. **Run automated checks**: `npm run lint`, `npx tsc --noEmit`, `dotnet format --verify-no-changes`, full test suite; inspect `#problems`
3. **Analyze each applicable dimension** against the diff
4. **Record findings** by severity:
   - 🔴 **Critical** — must fix; blocks approval
   - 🟡 **Important** — should fix
   - 🟢 **Suggestion** — optional improvement
5. **Cite by file + function/section**, not by line number
6. **Fix minor items directly** (typos, formatting, dead-code removal). Surface anything larger for discussion before changing.

## Coding Standards (verify against)

Condensed from the canonical standards in the `code-authoring` skill.

- **Naming** descriptive; short only for iterators
- **Functions** small; guard clauses / early returns
- **Error Handling** fail fast; result objects when recoverable
- **Types** annotated; no `any`, no non-null assertions, no unsafe casts
- **Params** positional for few args; options objects for many or easily-confused
- **Control Flow** functional for transforms; loops for side effects
- **Tests** describe behavior, cover edge cases
- **Comments** explain the **why**, not the **what**
- **Logging** structured via the framework's idiom (.NET message templates, JS field objects); consistent field names

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
