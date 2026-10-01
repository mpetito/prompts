---
name: review
description: "Review a diff, prove its tests and guards can fail, report findings by severity, and give a merge verdict. Use when reviewing code, auditing local or staged changes, checking coding standards, simplifying overengineered code or verbose comments, mutation-testing a test or flake fix, acting as a delegated or adversarial reviewer that reports without editing, or before reporting a fix, refactor, or implementation complete."
---

# Code Review Skill

Procedural knowledge for performing structured, multi-dimensional code reviews on a diff or pull request.

## When to Use

- A user asks to review changes, a PR, or a diff
- Before reporting implementation complete, as the self-review step of code-authoring
- Before merging, to produce an APPROVE / REQUEST CHANGES / NEEDS DISCUSSION verdict
- When an orchestrator or another agent delegates a review to you: use
  [Delegated Report-Only Mode](#delegated-report-only-mode)

Scale review depth to the risk of the change. Check that findings cite project convention reuse
and concrete evidence. For someone else's GitHub PR, when you will post comments after user
approval, use `pr-review`; for incoming reviewer or Copilot feedback on your own PR use
`pr-feedback`.

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
| **Tests**           | Coverage of new paths and edge cases; assertions that fail when the code breaks      |
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
4. **Prove the change can fail** when the diff adds or changes a test, guard, fix, gate, or
   secret path: run the matching probes in [Prove the Change Can Fail](#prove-the-change-can-fail)
5. **Record findings** by severity:
   - 🔴 **Critical** — must fix; blocks approval
   - 🟡 **Important** — should fix
   - 🟢 **Suggestion** — optional improvement
6. **Cite by file + function/section**, not by line number. A delegated report also gives the
   line at the reviewed head SHA
7. **Fix minor items directly** (typos, formatting, dead-code removal). Surface anything larger
   for discussion before changing. In delegated mode, report them instead.

## Prove the Change Can Fail

Green checks show that the change passes, not that its tests or guards can fail. Run the probes
that match the diff in a scratch copy or worktree, never in the author's tree. Procedures and the
mutant table format are in [adversarial probes](references/adversarial-probes.md).

| The diff…                             | Required proof                                                                     |
| ------------------------------------- | ---------------------------------------------------------------------------------- |
| Adds or changes tests or proofs       | Mutants of the code under test; restore each targeted bug; compare test counts     |
| Fixes a flaky or timing-bound test    | Reproduce on unfixed code under CI-like load; before/after rates; ablate the fix   |
| Relaxes a shared test helper          | Old helper's real-code mutants still caught; relaxation scoped to the flaky engine |
| Enables or depends on another change  | Overlay it; run count rises with no skips; full gate on the other lanes' heads     |
| Adds a gate, validator, or parser     | Threat model stated; one mutant per bypass class; fails closed on bad input        |
| Touches secrets, tokens, or redaction | Synthetic secret scanned in every sink; each protection layer disabled in turn     |
| Claims no behavior change             | Mechanical identity proof re-run independently; comments checked against code      |

Across every probe:

- **A surviving mutant is a finding.** Report it with a probe or assertion that kills it.
- **The author's mutants and numbers are a floor, not evidence.** Re-run them, then add your own.
- **Audit the evidence, not only the code.** CI evidence counts only for a merge ref that includes
  recent merges touching the same files; a re-run does not retest a moved base (mechanics in
  [autonomous-loops](../autonomous-loops/SKILL.md)). Check every causal, numeric, and coverage
  claim in the PR body, README, and linked issues.
- **A stated root cause is unproven** until an instrumented probe confirms it.
- **Validate any fix you suggest** on every project or engine CI runs, under load, before it goes
  in the report. Withdraw a wrong finding explicitly in the next round, with the evidence.
- **Cite docs for vendor behavior,** or a probe pinned to the installed version; write "docs
  silent" when they are.
- **"Close, don't merge" is a valid verdict** when evidence shows the change does not fix what
  it claims, or removes coverage.
- **Approval of a timing-bound test is provisional** until it passes in CI on the exact base.

## Coding Standards (verify against)

Apply the canonical standards linked above. In particular, check that the change reuses
existing project patterns and helpers, avoids speculative abstractions and redundant guards,
and keeps comments proportionate and useful. Preserve comments about real contracts and
constraints; remove narration and duplicated rationale. Require a concrete code path or
maintenance problem for each finding, not a preference presented as a defect.

## Output Format

For interactive reviews. A delegated review returns the report in
[Delegated Report-Only Mode](#delegated-report-only-mode) instead.

```markdown
## Review Summary

**Overall Assessment**: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION

### Critical Issues 🔴

- [Issue with file + function/section reference and recommended fix]

### Important Issues 🟡

- [Issue with file + function/section reference and recommendation]

### Suggestions 🟢

- [Suggestion with brief context]

### Proofs Run

- [Mutant or probe, result, and the assertion that caught it; survivors listed first]

### Changes Made

- [Minor fixes applied directly during review]

### Questions for Author

- [Open question or design clarification]
```

After presenting, suggest next steps:

- `/commit` — commit and open/update the PR

## Delegated Report-Only Mode

Use this mode when an orchestrator or another agent delegates the review, for example as the
independent adversarial reviewer of another agent's PR. The caller relays your findings, so you
leave the change itself untouched. The caller's brief wins where it differs; how callers write
reviewer briefs is in [agent-briefs](../agent-briefs/SKILL.md).

- **Edit only in the scratch worktree or folder the brief names.** Mutants, overlays, and probe
  scripts live there. If none is named, create one with a unique name; never use a shared
  scratch path or the author's worktree.
- **Do not post, push, commit, reply to or resolve threads, or start subagents.**
- **Report minor issues instead of fixing them,** and skip Handling In-Review Change Requests.
- **Rate severity on the finding alone,** never on the round number; the caller decides escalation.
- **Bind the verdict to the head SHA you reviewed.** A new push needs a new verdict.
- **Return at most about 40 lines** in this shape. Write the long form (full mutant table, logs,
  probe scripts) to the file the brief names, or to your scratch folder.

```text
VERDICT: approve | changes-required | close for <head-sha>

Blocking
- B1 <file>:<line> <defect>. Evidence: <probe, log, or quote>. Fix: <validated suggestion>
Should fix
- S1 <file>:<line> <issue and suggestion>
Mutants (mutant | result | killing assertion), survivors first:
- M3 <change> | survived | none, see B1
Claims checked: <PR-body and report claims, verified or refuted>
Not verified: <check, and why>
Outside this PR: <item, proposed as an issue>
Long form: <path>
```

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
- ✅ Mutate and experiment in a scratch copy or worktree
- ✅ Fix minor issues directly (typos, formatting, obvious dead code), except in delegated mode
- ⚠️ Ask first: major rewrites or architectural changes
- 🚫 Never approve code with critical issues, failing tests, or unexplained surviving mutants
- 🚫 Never commit or push — defer to `/commit`
- 🚫 Delegated mode: never edit the change, post, or start subagents
