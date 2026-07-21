---
name: pr-review
description: "Methodology for reviewing someone else's GitHub pull request by number: gathering PR context, learning project standards, drafting high-level review feedback, and posting review comments only after user approval. Use when asked to review a PR by number, review a teammate's pull request, or post code review comments on GitHub."
---

# PR Review Skill

Procedural knowledge for reviewing another author's pull request and posting review feedback on GitHub. This is a **collaborative reviewer**, not a linter — it surfaces design, code quality, DRY, and maintainability concerns, and it never posts anything without the user's explicit approval.

## When to Use

- The user provides a PR number (or URL) and asks for a review of someone else's work
- The user wants help drafting or posting GitHub review comments
- An external PR needs evaluation against personal and project standards

For reviewing **your own** staged/local changes, use the `review` skill instead.

## Core Principles

1. **Collaborate before posting** — draft everything locally, present it to the user, iterate, and only post after explicit approval. No exceptions.
2. **Be genuinely helpful, not nit-picky** — focus on design, architecture, code quality, DRY, maintainability, correctness, and testability. Skip anything a linter or formatter would catch.
3. **Respect the author** — phrase concerns as questions or suggestions, acknowledge good work, and assume competence. The goal is a better codebase and a good working relationship.
4. **Standards-aware** — review against both the user's personal coding standards and the target project's own conventions, which take precedence for that repo.

## Workflow

### Step 1: Resolve PR Context

1. Determine `owner`/`repo` from the workspace git remote, or from the PR URL/user input if the PR is in another repository
2. Run `../pr-scripts/Get-PrContext.ps1 -Pr {n} -Repo {owner}/{repo}` (sibling folder within the skills tree) — one call returns metadata, description, changed files, existing reviews, review threads, and CI status. Fetch the diff itself with `gh pr diff {n}`.
3. From the returned reviews/threads, note feedback already given — do not duplicate it
4. Treat CI failures in the returned checks as context, not as findings to repeat

### Step 2: Learn Project Standards

Before judging anything, understand how **this project** does things:

1. Read the repo's standards docs if present: `AGENTS.md`, `.github/copilot-instructions.md`, `CONTRIBUTING.md`, `.github/instructions/*.instructions.md`, architecture docs
2. Skim files adjacent to the changed code to learn local idioms (naming, error handling, layering, test patterns)
3. Note lint/format configs only to know what NOT to comment on — tooling-enforced style is out of scope

Project conventions override personal preferences. Never flag code for differing from personal style when it matches the surrounding codebase.

### Step 3: Review the Diff

Read every changed file — do not rely on the diff summary alone. Pull surrounding file content (`get_file_contents` or local checkout) when the diff lacks context.

Focus dimensions, in priority order:

| Priority | Dimension           | What to Look For                                                              |
| -------- | ------------------- | ----------------------------------------------------------------------------- |
| 1        | **Design**          | Wrong abstraction, misplaced responsibility, leaky boundaries, API shape      |
| 2        | **Correctness**     | Logic errors, edge cases, race conditions, state bugs, security issues        |
| 3        | **Maintainability** | Unclear naming, poor decomposition, hidden coupling, future-change cost       |
| 4        | **DRY**             | Meaningful duplication, missed reuse of existing utilities/patterns            |
| 5        | **Error handling**  | Swallowed exceptions, missing recovery paths, unhelpful failure modes         |
| 6        | **Tests**           | Missing coverage for new behavior, superficial assertions                     |

Explicitly **out of scope** (do not comment on):

- Formatting, whitespace, import order — linters exist
- Style choices consistent with the surrounding codebase
- Personal preference with no concrete maintainability or correctness impact
- Pre-existing issues in untouched code (mention to the user verbally if notable, but don't comment on the PR)

### Step 4: Draft the Review

Compose findings locally. For each, classify:

- 🔴 **Blocking** — correctness, security, or design problems that should be fixed before merge
- 🟡 **Worth discussing** — meaningful quality/maintainability concerns; often phrased as questions
- 🟢 **Optional** — take-it-or-leave-it suggestions; include sparingly (max 2–3)

Comment quality bar:

- Every comment explains **why** it matters, not just what to change
- Offer a concrete alternative or example where possible
- Use questions for design concerns: "Was X considered here? It would avoid Y."
- Cap total comments — a review with 5 substantive comments lands better than 20 mixed ones
- Include at least one genuine positive observation in the summary when deserved

### Step 5: Collaborate with the User (Gate)

Present the full draft using the Output Format below, then **stop and wait**. The user may:

- Approve as-is, edit, reorder, or drop comments
- Reclassify severity or change the review verdict
- Ask for deeper investigation of a specific finding

Iterate until the user explicitly says to post. **Never call any posting tool before approval.**

### Step 6: Post (After Approval Only)

Submit the summary and all approved inline comments atomically with `../pr-scripts/Submit-PrReview.ps1` (sibling folder within the skills tree). Write the inline comments to a JSON file first:

```powershell
# review-comments.json: [{ "path": "src/services/order.ts", "line": 42, "body": "Comment text...",
#                          "side": "RIGHT" (default), "start_line": 40 (optional, multi-line) }]
../pr-scripts/Submit-PrReview.ps1 -Pr 123 -Event COMMENT `
  -Body "Review summary..." -CommentsFile review-comments.json
```

- Default event is `COMMENT`; only use `APPROVE` or `REQUEST_CHANGES` when the user explicitly chooses it
- For a standalone PR-level comment (no inline notes), use `gh pr comment {n} --body-file ...` instead
- To reply within existing threads, use `../pr-scripts/Send-PrThreadReply.ps1` (see the `pr-resolve` skill)
- After posting, confirm what was published and link the review (the script outputs `html_url`)

## Output Format (Draft for User)

```markdown
## PR Review Draft — #{number}: {title}

**Author**: {author} · **Target**: {base} ← {head} · **CI**: {status}

### Summary (proposed review body)

{2–4 sentence overall assessment, including what's done well}

**Proposed verdict**: COMMENT / APPROVE / REQUEST_CHANGES

### Proposed Inline Comments

| #   | Severity | File:Line | Comment (draft text)         |
| --- | -------- | --------- | ---------------------------- |
| 1   | 🔴       | path:line | {exact text to be posted}    |

### Observations NOT Being Posted

- {notable but out-of-scope or too-minor items, for the user's awareness}

---

**Nothing has been posted.** Edit, drop, or approve the above — which comments should I post, and with what verdict?
```

## Guidelines

- Match comment tone to a respected senior colleague: direct, kind, specific
- If the PR is fundamentally misdirected, recommend a conversation with the author over a wall of comments
- If existing reviewers already raised an issue, don't pile on — note alignment to the user instead
- When unsure whether something is intentional, ask the author via a question rather than asserting a defect

## Boundaries

- ✅ Fetch PR data, read repo files, run read-only analysis, draft comments
- ✅ Post comments/reviews **after** explicit user approval of the exact content
- ⚠️ Ask first: any posting, any review verdict, replying to existing threads
- 🚫 Never post, approve, or request changes without user sign-off on the specific text
- 🚫 Never push commits to the author's branch
- 🚫 Never resolve other reviewers' threads
