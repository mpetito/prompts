# Skills Orientation for the OpenClaw Coordinator

**Produced:** 2026-09-19 · **Source checkout:** `/home/mpetito/dev/prompts` (branch `main`, uncommitted work present and untouched)
**Audience:** the OpenClaw coordinator (`openai/gpt-6-astra`) and any coding worker it directs into this workspace.
**Status of claims:** everything below was read from this checkout and this machine's home directory on the date above. Items I could not verify are marked **UNKNOWN** rather than guessed.

---

## 1. Repository purpose and structure

`/home/mpetito/dev/prompts` is titled **"Agentic Coding Toolkit"** (`README.md`). It is not an application. It is the version-controlled *source of truth* for agent configuration that is then **symlinked into user-level client directories**. Editing a file here changes the behaviour of every agent session on this machine immediately — there is no build step.

The repository's stated goal: share one set of agent skills across **GitHub Copilot (VS Code + Copilot CLI), Claude Code, Codex, and OpenCode** (`README.md`, opening paragraph).

### Layout (verified by `find`, 2026-09-19)

| Path | Contents | Linked to |
| --- | --- | --- |
| `skills/` | 27 skill folders (each with `SKILL.md`) + `pr-scripts/` | `~/.claude/skills/*`, `~/.agents/skills/*`, `~/.copilot/skills/*` (Copilot not set up here) |
| `agents/` | 7 Claude Code subagent definitions (`*.md`) | `~/.claude/agents` (whole folder) |
| `instructions/CLAUDE.md` | user-level always-loaded global instructions | `~/.claude/CLAUDE.md` |
| `statusline/statusline.js` | Claude Code status line script | `~/.claude/statusline.js` |
| `mcp/` | MCP profile registry + PowerShell bootstrap (`core-dev`, `envative`) | not linked; opt-in install |
| `fragments/` | `snyk-upgrade-review.prompt.md` — reusable snippet, not a skill | not linked |
| `docs/` | design/history docs (`agents-prompts-skills.md`, `virtual-tools-research.md`) | not linked |
| `scripts/Setup.Common.psm1` | shared installer module | — |
| `tests/` | `Setup.Tests.ps1`, `Mcp.Tests.ps1` (offline Pester-style checks) | — |
| `setup-skills-link.ps1`, `verify-setup.ps1` | installer and verifier (PowerShell 7.4+) | — |
| `.github/workflows/validate.yml` | CI: runs the two test scripts on Windows + Ubuntu | — |

**Key structural fact:** the repository has **no project-level agent config of its own** — no `CLAUDE.md`, no `AGENTS.md`, no `.claude/`, no `.github/skills/` (verified: `ls` returns "No such file or directory" for all four). The only always-loaded instruction file in play is the *user-level* `instructions/CLAUDE.md`, which applies to **every** project on this machine, not just this one.

### Conventions that constrain any edit here

From `README.md` → *Cross-Tool Authoring Notes* and `skills/skill-authoring/SKILL.md`:

- `name` and `description` are the only **portable** frontmatter keys. Everything else is Claude-Code-only and silently ignored elsewhere.
- Directory name **must** equal the frontmatter `name`.
- Cross-references between skills are **skill-relative** (`../other-skill/SKILL.md`), never repo-root-relative — because the tree is symlinked into `~/.claude/skills/` where no repo root exists.
- `SKILL.md` stays **under 500 lines**; overflow goes to `references/` (progressive disclosure). Current max is `code-quality-standards` at 475 lines.
- Tools are referenced as **capabilities** ("Context7 docs", "IDE diagnostics"), not literal tool IDs, since IDs differ per host.
- After **adding or renaming** a top-level skill directory, `setup-skills-link.ps1` must be rerun. Editing inside an existing linked skill needs nothing.

---

## 2. Available skills

`skills/` holds **28 directories: 27 real skills** (each with a `SKILL.md`) **plus `pr-scripts/`**, a helper folder that is linked but is not a skill. Each lives at `/home/mpetito/dev/prompts/skills/<name>/` and is installed (verified by `ls -la`) at:

- `~/.claude/skills/<name>` → symlink → `/home/mpetito/dev/prompts/skills/<name>` (all 28 links, plus a tool-managed `synced/` directory Claude Code owns)
- `~/.agents/skills/<name>` → the same 28 links
- `~/.copilot/skills/` — **does not exist on this machine.** Copilot was not selected during setup.

Destinations are defined in `scripts/Setup.Common.psm1` → `Get-SkillTargets` / `Get-SetupPaths`.

### 2a. Workflow skills (the development spine)

| Skill | Path | Triggers on | Outcome | Prerequisites / boundaries |
| --- | --- | --- | --- | --- |
| `spec` | `skills/spec/SKILL.md` | "plan", "spec", "design", "breakdown", "roadmap" for non-trivial work | `specs/{NNN-slug}/spec.md` (what+why) then `plan.md` (how) | **Gates on blocking Open Questions** — will not write a plan over unresolved architecture/scope questions. Skip entirely for small obvious changes. |
| `implement` | `skills/implement/SKILL.md` | a **numbered** spec: "implement 040", "run plan.md", "finish the spec" | all phases executed, `plan.md` checkboxes ticked, report | Requires `specs/{NNN-*}/` to exist. Without a numbered spec it explicitly redirects to `code-authoring`. Loads `code-authoring` for the actual work. |
| `code-authoring` | `skills/code-authoring/SKILL.md` | **any** code change: feature, bug fix, refactor, script, infra, tests | validated change + report (summary, files, test results, follow-ups) | **The canonical coding standards live here** — other skills link to this section rather than restating it. Runs a 5-step loop: Prepare → Implement → Test → Self-Review → Validate. 🚫 never skip Test or Validate; 🚫 never commit to a protected branch. |
| `code-quality-standards` | `skills/code-quality-standards/SKILL.md` | React / Next.js / TypeScript work; security or quality audits | checklist applied (security, DRY, correctness, perf, a11y) | A **reference** skill — read inside another task, sets no `model`. Complements `code-authoring`; does not replace its workflow. |
| `review` | `skills/review/SKILL.md` | "review this", auditing local/staged changes, **before reporting any implementation complete** | findings by severity (🔴/🟡/🟢) + verdict APPROVE / REQUEST CHANGES / NEEDS DISCUSSION | ✅ may fix typos/formatting/dead code directly. ⚠️ asks first for rewrites. 🚫 **never commits or pushes** — defers to `commit`. For someone else's PR use `pr-review` instead. |
| `commit` | `skills/commit/SKILL.md` | "commit", "open a PR", "finalize" | validated commit(s), pushed feature branch, draft PR | `model: sonnet`, `effort: low`. Runs lint/test/typecheck/build first and **stops on failure**. Never commits to `main`/`master`/`develop`. Envative branch naming `users/mpetito/…`. ADO `AB#<id>` in the PR **body**. Invokes `pr-authoring` (Skill tool) before writing a body, then `tt` after the PR exists. |
| `pr-authoring` | `skills/pr-authoring/SKILL.md` | creating/updating a PR description | title + body: motivation first, grouped by purpose, concrete validation | `model: sonnet`, `effort: high`. **No AI attribution, ever.** `commit` deliberately carries no summary of its rules so it cannot be used instead of the skill. |
| `pr-feedback` | `skills/pr-feedback/SKILL.md` | Copilot/reviewer comments, CI failures, CodeQL findings on **your own** PR | triaged dispositions + local fixes + drafted replies | `model: sonnet`, `effort: high`. **Hard approval gate at step 5**: presents a Feedback Resolution Summary and waits before committing, pushing, replying, or resolving. Must inspect suppressed/`<details>` sections in review bodies — an empty unresolved-threads list is *not* proof of coverage. |
| `pr-resolve` | `skills/pr-resolve/SKILL.md` | replying to / resolving PR review threads after a push | threads replied and selectively resolved, state verified | `model: sonnet`, `effort: medium`. Prerequisite: fixes already **committed and pushed**. Never resolve without replying. Design disagreements and deferrals stay **open**. |
| `pr-review` | `skills/pr-review/SKILL.md` | reviewing **someone else's** PR by number/URL | a draft review presented locally; posted only after approval | 🚫 **Never calls a posting tool before explicit user approval of the exact text.** Default event `COMMENT`; `APPROVE`/`REQUEST_CHANGES` only when the user chooses. Never pushes to the author's branch or resolves other reviewers' threads. |
| `pr-consolidate` | `skills/pr-consolidate/SKILL.md` | combining several PRs/branches into an integration branch | integration branch with all work preserved | **`disable-model-invocation: true`** — user must type `/pr-consolidate`. Merges are destructive, so the model may not auto-invoke it. Uses `--no-commit`, creates a backup branch, never force-pushes without confirmation. |
| `model-council` | `skills/model-council/SKILL.md` | "second opinions", reviewers disagree, a Copilot claim stays ambiguous after local checks | a recommendation with evidence + remaining uncertainty | Two independent members (preferably one Claude + one Codex), read-only, same pinned code snapshot. **Not a vote** and **not permission to post, merge, or change scope** — control returns to `pr-feedback`. |
| `research` | `skills/research/SKILL.md` | evaluating libraries, comparing options, chasing dependency bugs | sourced synthesis + recommendation | Maps *capabilities* (Context7, Firecrawl developer index, Perplexity, GitHub search, web) to whatever the host actually has; skips unavailable ones rather than failing. |
| `upgrade` | `skills/upgrade/SKILL.md` | dependency bumps, CVEs, major-version planning | staged upgrades with lockfiles in sync + validation evidence | 4 phases: Inventory & Plan → Research & Risk → Implement → Validation. Per-ecosystem commands in `references/ecosystem-commands.md` — consult, don't recall flags. |
| `autonomous-loops` | `skills/autonomous-loops/SKILL.md` | a measurable target verified by an external async system (CI green, PSI ≥ 90, no open Copilot threads) | an iteration loop with explicit budget | Explicitly **not** for single-shot edits. Must record explicit models per worker/stage alongside the iteration budget. |
| `tt` | `skills/tt/SKILL.md` | "log time", "/tt", after a PR is created/updated | a Harvest time entry linked best-effort to an ADO item | `model: sonnet`, `effort: low`. **Absolute rule: create or update, never delete or zero out. Never timers** — `log_time` / `update_time_entry` only. Repo→Harvest-project mapping lives in agent memory as `harvest-time-tracking.md`, not in the repo. |
| `story` | `skills/story/SKILL.md` | writing a user story, filing a bug, estimating points | a correctly typed ADO work item with fields + acceptance criteria | `model: sonnet`, `effort: low`. Defaults to **User Story** unless clearly an Issue or Bug. Fibonacci points. Field examples in `references/ado-field-examples.md`. |

### 2b. Authoring / meta skills

| Skill | Path | Triggers on | Outcome / boundary |
| --- | --- | --- | --- |
| `skill-authoring` | `skills/skill-authoring/SKILL.md` | writing or fixing a `SKILL.md`, tuning a description, pinning `model`/`effort` | Owns the frontmatter key table and the progressive-disclosure rules. **Also owns `references/agent-model-selection.md`, the canonical model policy referenced by nearly every other skill.** |
| `agents-md-authoring` | `skills/agents-md-authoring/SKILL.md` | writing `AGENTS.md` / `CLAUDE.md` / `copilot-instructions.md` | Always-loaded project context. Explicitly **not** `SKILL.md` — the two descriptions name each other to prevent mis-triggering. |
| `herdr-delegation` | `skills/herdr-delegation/SKILL.md` | delegating to a peer pane, cross-harness work, a stalled peer, parallel worktrees | **Prerequisite: `HERDR_ENV=1`. If the check fails, stop.** Carries a peer-vs-subagent decision table: prefer an in-process subagent unless the work must outlive the session, a human may need to answer a dialog, or a *different harness* is the point. Command syntax comes from `herdr --skill`, not from the skill body. |

### 2c. Domain / reference skills (consumed inside another task; no `model` pinned by design)

| Skill | Scope |
| --- | --- |
| `design-review-standards` | 10-dimension UI/UX + accessibility review framework, scored 1–5 |
| `ecommerce-patterns` | cart, checkout, payments, orders. **Money is always integer cents** — never floats |
| `playwright-e2e` | Page Object Model, locator choice, `data-testid` convention, npm-workspaces monorepo wiring, CI |
| `seo-aeo-structured-data` | Next.js metadata, JSON-LD, sitemaps/robots/RSS, AEO, Core Web Vitals |

### 2d. Tool-driving skills

| Skill | Prerequisites / boundaries |
| --- | --- |
| `firecrawl` | `model: sonnet`, `effort: high` — the only reference-ish skill that pins a model, because choosing the right rung of the search/scrape/crawl ladder is where its judgment goes. Routes library docs to Context7, MS docs to `microsoft-docs`, synthesis to `research`. |
| `agentmail` | **Test mailbox only.** Explicitly out of scope: sending as the user to a real person, anything with real-world consequence, bulk sending, triaging the user's real mail. Declines and says why rather than reinterpreting. |
| `word-doc-editing` | **Requires Windows + desktop Microsoft Word + PowerShell 7.** Reports that requirement explicitly on Linux/macOS — so it is **not usable in this Linux session**. Drives Word via COM; never hand-edits OOXML. 10 scripts under `scripts/` sharing `WordCom.psm1`. |

### 2e. `pr-scripts` — shared helpers, deliberately **not** a skill

`skills/pr-scripts/` has **no `SKILL.md`**, so it never enters any tool's skill catalog — but it *is* symlinked alongside the skills because `pr-feedback`, `pr-resolve`, and `pr-review` reference it sibling-relatively (`../pr-scripts/…`).

- `README.md` = script inventory. `REFERENCE.md` = the shared agent-facing usage, resolution decision matrix, and reply templates (kept in one place because the same block previously lived in two skills and drifted).
- 8 scripts wrapping `gh api` / `gh api graphql`: `Get-PrFeedback.ps1`, `Get-PrContext.ps1`, `Get-PrThreads.ps1`, `Get-PrCheckFailures.ps1`, `Send-PrThreadReply.ps1`, `Resolve-PrThread.ps1`, `Test-PrThreadsResolved.ps1`, `Submit-PrReview.ps1`.
- **Prerequisites: PowerShell 7 (`pwsh`) and an authenticated `gh` CLI.** From Bash: `pwsh -NoProfile -File ../pr-scripts/<Script>.ps1 …`. Paths resolve relative to the *calling skill's folder*, never a repo root.
- Thread IDs start with `PRRT_`. Fallback when scripts are unavailable: GitHub MCP PR tools, or raw `gh api graphql`.

---

## 3. How the skills compose

### 3.1 The canonical routes

From `instructions/CLAUDE.md` (always loaded in every Claude Code session on this machine) and `README.md` → *Workflows*:

```
Standard feature:     /spec → /implement spec NNN → /review → /commit
Direct implementation: (describe work) → code-authoring → /review → /commit
Research spike:       /research → /spec → …
PR feedback loop:     /pr-feedback → /pr-resolve → /commit      (repeat until approved)
Dependency upgrade:   /upgrade → /commit
Branch consolidation: /pr-consolidate → /commit                 (user-typed only)
```

The **coding path** is stated verbatim in `README.md` → *Instructions*:

> `code-authoring` → applicable `code-quality-standards` → `review`, **including bug fixes and refactors without a spec.**

### 3.2 The composition rule that makes this work

`instructions/CLAUDE.md` → *Skills*:

> When a skill names another skill as a **step** in its procedure, invoke that skill (Skill tool) before performing the step. A linked skill is reference material only when the sentence is a "see also"; if it sits inside a numbered step, it is an instruction. **Never author from a summary of a skill** — a summary is there to help you recognise which skill applies, not to stand in for it.

This is load-bearing and visible in the sources. `commit` step 6 says outright: *"No summary of its rules appears here on purpose: a summary reads as self-contained and gets used instead of the skill."* A worker that paraphrases `pr-authoring` instead of loading it is violating a stated repository rule.

### 3.3 Who calls whom (verified from skill bodies)

```
spec ──────────────► (research skill for Phase 2 external research)
implement ─────────► code-authoring (step 4, per phase)
code-authoring ────► code-quality-standards (step 1, React/Next/TS)
               └───► review                 (step 4, self-review — NOT optional, NOT deferred)
review ────────────► code-quality-standards (React/Next/TS diffs)
               └───► pr-scripts/Get-PrThreads.ps1 (when the diff belongs to an open PR)
commit ────────────► pr-authoring (before writing any PR body)
          └────────► tt            (after the PR exists; non-blocking follow-up)
pr-feedback ───────► pr-scripts/*  (collection, replies, resolution)
          ├────────► code-authoring (step 3, implementing accepted findings)
          └────────► model-council  (step 2.5, only when actionability stays materially uncertain)
model-council ─────► herdr-delegation (peer transport) + agent-model-selection
pr-review ─────────► code-authoring (standards section, as reference) + code-quality-standards
almost everything ─► skills/skill-authoring/references/agent-model-selection.md (before any delegation)
```

### 3.4 Explicit approval and invocation boundaries

These are the hard stops. A worker that crosses one is misbehaving, not being helpful.

| Boundary | Where it is stated |
| --- | --- |
| **`pr-review` posts nothing before explicit approval of the exact text.** Never approve/request-changes without the user choosing it. Never push to the author's branch. Never resolve another reviewer's thread. | `pr-review/SKILL.md` → Step 5, *Boundaries* |
| **`pr-feedback` stops before committing, pushing, replying, or resolving** and presents a summary table ending "**Ready to commit, push, and respond?**" | `pr-feedback/SKILL.md` → step 5 |
| **`pr-consolidate` cannot be model-invoked** (`disable-model-invocation: true`). The user types `/pr-consolidate`. | `pr-consolidate/SKILL.md` frontmatter; `README.md` → *Host-Specific Frontmatter* |
| **`review` never commits or pushes**; `code-authoring` never commits to a protected branch; `commit` stops on validation failure. | respective *Boundaries* sections |
| **`pr-resolve` never resolves without replying first**; design disagreements/deferrals stay open for the reviewer. | `pr-resolve/SKILL.md` → *Guidelines* |
| **No AI attribution anywhere** — no `Co-Authored-By: Claude`, no "Generated with Claude Code", no session links, in commits, PR bodies, or PR comments, in any repository. Overrides host defaults. | `instructions/CLAUDE.md` → *Attribution*; `commit/SKILL.md` → *Authorship Rule*; `pr-authoring/SKILL.md` principle 6 |
| **`tt` never deletes or zeroes an entry; never uses timers.** | `tt/SKILL.md` |
| **`agentmail` declines real correspondence** rather than reinterpreting it as a test. | `agentmail/SKILL.md` → *Scope* |
| **`herdr-delegation` stops if `HERDR_ENV != 1`.** | `herdr-delegation/SKILL.md` → *Prerequisites* |
| **Docs before source** for third-party behaviour: read the library's documentation, then its issue tracker, and use source or a local probe only to *confirm*. Never write a durable rule (an AGENTS.md entry, a contract comment) from source-reading alone. | `instructions/CLAUDE.md` → *Third-party behaviour* |

### 3.5 Delegation and model policy — read this before spawning anything

`instructions/CLAUDE.md` → *Delegation* routing table, backed by `skills/skill-authoring/references/agent-model-selection.md`:

| Work | Send it to |
| --- | --- |
| Tests, build, lint, typecheck | `test-runner` (sonnet/low) |
| CI runs, PR check suites, Copilot review comments | `pr-watch` (sonnet/low) |
| Reading across many files to answer one question | `analyst` (sonnet/medium) |
| A question whose answer lives in external docs | `researcher` (sonnet/high, preloads the `research` skill) |
| An error, stack trace, or failing test | `debugger` (sonnet/xhigh) |
| A conclusion that is expensive to get wrong | `verifier` (**opus**/high) |
| One repetitive change across many files | `migrator` (sonnet/medium, **runs in an isolated git worktree**) |

Definitions: `agents/*.md`, symlinked to `~/.claude/agents`. Only `migrator` has `Edit`/`Write`. The other six do not — though `README.md` notes honestly that *"a `Bash` grant is not a read-only guarantee"*; `analyst`, `verifier`, and `debugger` are restricted by instruction, not by tool list. `analyst` and `verifier` deliberately keep **no memory** so they answer from the code as it is now.

The model rule, stated in three places (`instructions/CLAUDE.md` → *Model tiers*, `README.md` → *Agents*, and the policy file):

- **Default to explicit `opus`** for any subagent, team member, workflow stage, background worker, or retry. In non-Anthropic hosts: an explicitly selected high-capability model from *that host's actual catalog* — **do not pass Anthropic aliases such as `opus` to Codex.**
- A weaker model requires a **task-specific written justification** naming the bounded work and how the result is verified. *"Routine", "read-only", and "save tokens" are explicitly insufficient.*
- Existing named-agent pins (the table above) are deliberate role-specific choices — preserve them; the Opus default fills *unspecified* worker choices.
- Never use `inherit` as a convenience, and never assume `Explore`, `Plan`, forks, or generated workflow agents are cheap.
- Workers do **not** inherit the caller's loaded skills. Carry the relevant standards and this policy into the delegated prompt.
- A skill's own `model:` never selects its workers' models. A Sonnet skill can and should dispatch an Opus worker.

Also: *"A subagent's report is evidence to weigh, not a conclusion to relay unexamined."*

---

## 4. Task → skill mapping, with wording to use

### 4.1 Mapping table

| Incoming request | Route | First skill to name |
| --- | --- | --- |
| "Add feature X" (non-trivial, multi-file) | spec → implement → review → commit | `spec` |
| "Implement spec 040" / "finish the plan" | implement (which loads code-authoring per phase) | `implement` |
| "Fix this bug" / "refactor Y" / "update the build script" | code-authoring → review → commit | `code-authoring` |
| "Rename this variable" (one-line, surgical) | proportionate edit/check pass — the skill itself says no formal plan or new test is needed | `code-authoring` (load standards, skip ceremony) |
| Touching React / Next.js / TypeScript | add the standards **before** editing | `code-quality-standards` |
| "Is this change good?" / before declaring done | self-review the final diff | `review` |
| "Review PR #123" (someone else's) | draft locally, post only after approval | `pr-review` |
| "Address the Copilot comments on my PR" | triage → fix → **approval gate** → reply/resolve | `pr-feedback` |
| "Reply to and close out the review threads" (already pushed) | `pr-resolve` | `pr-resolve` |
| "Commit and open a PR" | validate → branch → commit → push → PR → log time | `commit` |
| "Write the PR description" | `pr-authoring` | `pr-authoring` |
| "Should we use library A or B?" / "why does this API behave this way?" | docs first, then issues, then source | `research` (or delegate to `researcher`) |
| "Bump dependencies" / "fix this CVE" | `upgrade` → commit | `upgrade` |
| "Get CI green" / "keep iterating until the score is ≥ 90" | `autonomous-loops` | `autonomous-loops` |
| "Reviewers disagree" / "is this Copilot claim real?" (after local checks) | `model-council` | `model-council` |
| "Write a user story / file a bug" | `story` | `story` |
| "Log my time" | `tt` | `tt` |
| "Write/fix a SKILL.md" | `skill-authoring` | `skill-authoring` |
| "Write the AGENTS.md for this repo" | `agents-md-authoring` | `agents-md-authoring` |
| "Combine these three PRs" | **ask the user to type `/pr-consolidate`** — a model may not invoke it | — |
| Editing a `.docx` | `word-doc-editing` — **unavailable on this Linux host** (needs Windows + Word) | — |

### 4.2 Suggested wording when directing a coding worker

The skills auto-load from their `description`, so naming the skill explicitly is belt-and-braces, not required — but it removes ambiguity and makes the worker's obligations legible. Useful patterns:

**Implementation (no spec):**
> "Load the `code-authoring` skill and follow its Prepare → Implement → Test → Self-Review → Validate loop for <change>. This is TypeScript/React, so load `code-quality-standards` before editing. Run the self-review step with the `review` skill against the final diff — do not defer it. Report files changed and test results. Do not commit."

**Implementation (spec exists):**
> "Use the `implement` skill for spec 040. Work through every phase of `plan.md` without stopping between phases unless a blocker needs my input, ticking off steps as you go. Report the spec/plan paths, files changed, and test results at the end."

**Planning:**
> "Use the `spec` skill to produce `specs/{NNN-slug}/spec.md` and `plan.md` for <feature>. Research the codebase patterns first. If blocking Open Questions remain after research, stop and give them to me as numbered questions rather than writing the plan."

**Review:**
> "Use the `review` skill on the current working-tree diff. Give findings by severity with a merge verdict. Fix typos and dead code directly; surface anything larger before changing it. Do not commit or push."

**PR feedback:**
> "Use the `pr-feedback` skill on PR #123. Collect everything with `Get-PrFeedback.ps1`, including suppressed and low-confidence sections inside review bodies. Triage each claim with evidence before editing anything. Stop at the Feedback Resolution Summary and wait for my approval before committing, replying, or resolving."

**Reviewing someone else's PR:**
> "Use the `pr-review` skill on PR #456. Draft the review and present it to me. Post nothing until I approve the exact comment text and the verdict."

**Commit:**
> "Use the `commit` skill. Run the project's validation first and stop if anything fails. Conventional commit message, feature branch, draft PR. Load the `pr-authoring` skill for the body — don't write it from memory. No AI attribution anywhere."

**Delegation inside a worker:**
> "Before spawning any subagent or workflow stage, apply `skills/skill-authoring/references/agent-model-selection.md`. Set every worker's model explicitly — default to Opus (or this host's equivalent high-capability model, chosen from its own catalog). If you pick anything weaker, write the task-specific justification next to it. Don't assume workers inherit the skills you've loaded — restate the standards in their prompt."

**Anything touching a third-party library's behaviour:**
> "Read the library's documentation before its source. Use the docs tools or the `research` skill; a local probe only confirms an answer, it never establishes one. If the docs are silent, say so and pin the claim to the installed version."

**Two phrasings worth avoiding:**
- *"Just quickly commit this"* — `commit` runs validation and stops on failure by design; asking it to skip is asking it to break a stated rule.
- *"Summarise what the skill says and apply it"* — explicitly forbidden by `instructions/CLAUDE.md`. Ask the worker to **load** the skill.

---

## 5. What is available to whom — verified vs. unknown

This section is deliberately conservative. Skill *installation* is a filesystem fact I checked. Skill *activation* in a given agent runtime is a property of that runtime, and I can only observe my own.

### 5.1 Available to me (this Claude Code session), verified

This session's skill catalog listed **26 of the 27 repo skills**, plus a large set of unrelated skills from other sources.

- **Present:** `agentmail`, `agents-md-authoring`, `autonomous-loops`, `code-authoring`, `code-quality-standards`, `commit`, `design-review-standards`, `ecommerce-patterns`, `firecrawl`, `herdr-delegation`, `implement`, `model-council`, `playwright-e2e`, `pr-authoring`, `pr-feedback`, `pr-resolve`, `pr-review`, `research`, `review`, `seo-aeo-structured-data`, `skill-authoring`, `spec`, `story`, `tt`, `upgrade`, `word-doc-editing`.
- **Installed but absent from my catalog:** `pr-consolidate`. This is the `disable-model-invocation: true` key working exactly as designed — the symlink exists at `~/.claude/skills/pr-consolidate`, but the model is not offered the skill. Only the user typing `/pr-consolidate` reaches it.
- **Never a skill:** `pr-scripts` (no `SKILL.md`), and `fragments/snyk-upgrade-review.prompt.md`.
- Also loaded into this session, and **not from this repository**: plugin skills namespaced `design:`, `marketing:`, `engineering:`, `product-management:` (from `~/.claude/plugins/marketplaces/claude-plugins-official`), `anthropic-skills:*` and others from `~/.claude/skills/synced/…`, and Claude Code built-ins (`code-review`, `simplify`, `loop`, `schedule`, `update-config`, …). **Do not assume any of these exist in another harness** — they are Claude Code plumbing, not repository content. Note the name collisions: the built-in `/code-review` and the plugin `engineering:code-review` are **not** this repo's `review` or `pr-review`.

Also active in this session and relevant to any worker here: `instructions/CLAUDE.md` is loaded in full, and this session's harness additionally instructs work through Bash where possible.

### 5.2 Available to the OpenClaw coordinator — what I can and cannot say

**Verified filesystem facts:**
- All 28 directories under `skills/` are symlinked into both `~/.claude/skills/` and `~/.agents/skills/`. `~/.agents/skills` is the shared root that `README.md` documents as the discovery path for **Codex and OpenCode**.
- `~/.copilot/skills/` **does not exist**. If OpenClaw drives a Copilot worker on this machine, that worker has **no** repository skills until `setup-skills-link.ps1` is rerun with `-Tools copilot`. *(That is a configuration change and outside this task's authorization — flagging, not doing.)*
- `agents/` is linked **only** into `~/.claude/agents`. `README.md` states plainly that Codex custom agents are standalone TOML under `~/.codex/agents/` and that the Claude Markdown files **cannot** be linked there. `~/.codex/agents/` was not part of this inspection.
- `instructions/CLAUDE.md` is linked only into `~/.claude/CLAUDE.md`. `README.md` acknowledges this: *"These routes are explicit in skill bodies for other hosts, which do not load this Claude-only global file."* The skill bodies were written to carry the routing themselves for exactly this reason.

**UNKNOWN — do not assume:**
- **Whether OpenClaw reads `~/.agents/skills` at all.** OpenClaw is not OpenCode. The repository documents `~/.agents/skills` for Codex and OpenCode; nothing here mentions OpenClaw. I found no OpenClaw configuration in this checkout or in `~/.claude`.
- **Whether OpenClaw auto-loads skills by description** the way Claude Code and Copilot do, or requires explicit invocation.
- **Whether the `/name` slash form resolves in OpenClaw.** `README.md` documents it for VS Code and Claude Code only.
- **Which worker harnesses OpenClaw will spawn**, and therefore which of the above applies per worker.

**What holds regardless of harness** (because it is written into the portable `name`/`description`/body of each skill, not into Claude-only keys):
- The procedures, boundaries, approval gates, and cross-skill routing in every `SKILL.md`.
- The `pr-scripts` helpers (PowerShell 7 + authenticated `gh`, any OS).

**What does *not* survive the crossing into a non-Claude harness:**
- `model:`, `effort:`, `disable-model-invocation:`, `allowed-tools:`, `context:`, `agent:` — all Claude-Code-only. `README.md` is explicit: *"Codex ignores Claude-only skill keys such as `model: sonnet`, `effort`, and `disable-model-invocation`; they do not select an Anthropic model or prevent the skill from loading."*
  - **Practical consequence for you:** `pr-consolidate`'s protection is *Claude-specific*. In a Codex or OpenCode worker the skill can load implicitly. The repo's stated Codex equivalent is `policy.allow_implicit_invocation: false` in an optional `agents/openai.yaml` — and **no skill in this checkout currently has an `agents/openai.yaml`** (verified: the only skills with subfolders have `references/`, `scripts/`, or `tests/`). So treat "don't auto-consolidate branches" as a rule you enforce by instruction when directing a non-Claude worker.
- The seven named subagents (`test-runner`, `pr-watch`, `analyst`, `researcher`, `debugger`, `verifier`, `migrator`) and their model pins. In a non-Claude worker, name the *role and the model* in the prompt instead of the agent.
- The always-loaded `instructions/CLAUDE.md`, including the attribution rule and the delegation table. **When directing a non-Claude worker, restate the attribution rule and the model policy explicitly** — they will not be loaded for you.

---

## 6. Verification evidence

### Files read in full or in substantial part

| File | Used for |
| --- | --- |
| `README.md` | purpose, skill/agent tables, workflows, setup, cross-tool authoring, host-specific frontmatter |
| `instructions/CLAUDE.md` | attribution, skill-composition rule, coding path, third-party-docs rule, delegation table, model tiers |
| `docs/agents-prompts-skills.md` | history (prompts→skills consolidation), concept comparison, folder structure, the 2026-07-26 correction about Claude frontmatter keys |
| `skills/*/SKILL.md` (frontmatter of all 27) | exact names, descriptions/triggers, and every `model` / `effort` / `disable-model-invocation` pin |
| `skills/code-authoring/SKILL.md` (full) | the 5-step protocol, canonical coding standards, boundaries, delegation section |
| `skills/implement/SKILL.md` (full) | spec resolution, clarification gate, per-phase loop |
| `skills/spec/SKILL.md` (Phases 1–6) | research, blocking-question gate, complexity tiers, supporting-doc convention |
| `skills/review/SKILL.md` (full) | dimensions, severity scheme, PR-context check, boundaries |
| `skills/commit/SKILL.md` (full) | validation, branch naming, `AB#` linking, `pr-authoring` and `tt` invocation |
| `skills/pr-feedback/SKILL.md` (full) | collection, triage matrix, model-council hook, the step-5 approval gate |
| `skills/pr-review/SKILL.md` (full) | the posting gate, out-of-scope list, `Submit-PrReview.ps1` usage |
| `skills/pr-resolve/SKILL.md` (full) | prerequisites, resolution procedure, verification |
| `skills/pr-authoring/SKILL.md` (head) | principles incl. the no-AI-attribution rule, title format |
| `skills/pr-consolidate/SKILL.md` (head) | `disable-model-invocation` rationale, safety rules, target determination |
| `skills/model-council/SKILL.md` (full) | framing, member/model selection, dispatch, synthesis, return-of-control |
| `skills/herdr-delegation/SKILL.md` (head) | `HERDR_ENV` prerequisite, peer-vs-subagent table, cross-harness prompt contract |
| `skills/skill-authoring/SKILL.md` (lines 1–140) | anatomy, progressive disclosure, per-tool skills roots, full frontmatter key table, model/effort selection |
| `skills/skill-authoring/references/agent-model-selection.md` (full) | the Opus default, justification requirement, workflow-stage rule, Claude Code runtime checks |
| `skills/pr-scripts/README.md`, `REFERENCE.md` (lines 1–120) | script inventory, invocation, resolution matrix, reply templates, fallbacks |
| `skills/{research,upgrade,tt,story,autonomous-loops}/SKILL.md` (heads) | tools, phases, absolute rules, work-item types, loop criteria |
| `skills/{agents-md-authoring,agentmail,firecrawl,word-doc-editing,code-quality-standards,design-review-standards,ecommerce-patterns,playwright-e2e,seo-aeo-structured-data}/SKILL.md` (scope sections) | triggers, scope, prerequisites |
| `agents/*.md` (frontmatter of all 7) | model, effort, tools, `permissionMode`, `maxTurns`, `memory`, `isolation`, `skills` |
| `scripts/Setup.Common.psm1` (`Get-SetupPaths`, `Get-SkillTargets`) | authoritative destination mapping |
| `verify-setup.ps1` (full) | what "verified setup" checks; the Windows-only Word notice |
| `mcp/README.md` (head) | MCP profiles, Docker MCP Toolkit prerequisites, opt-in status |
| `.gitignore`, `.gitattributes`, `.github/workflows/validate.yml` (listing) | runtime-memory exclusion, EOL policy, CI presence |

### Live-system checks performed

| Check | Result |
| --- | --- |
| `ls -la ~/.claude/skills` | 28 symlinks into this checkout (27 skills + `pr-scripts`) + a tool-managed `synced/` directory |
| `ls -la ~/.agents/skills` | the same 28 symlinks |
| `ls -la ~/.copilot/skills` | **does not exist** |
| `ls -la ~/.claude` | `CLAUDE.md`, `agents`, `statusline.js` all symlinked into this checkout |
| `ls ~/.claude/plugins`, `~/.claude/skills/synced/…` | confirmed the non-repo origin of the plugin and `anthropic-skills:*` catalog entries |
| Repo skills vs. this session's skill catalog | 26/27 present; `pr-consolidate` absent, consistent with `disable-model-invocation: true` |
| `ls .claude AGENTS.md CLAUDE.md .github/skills` in the repo | none exist — no project-level agent config |
| `git status --short` before and after | identical; 10 modified + 6 untracked entries preserved |

### Constraints honoured

Nothing was committed, stashed, pushed, installed, or reconfigured. No existing file was edited. No skill source was touched. The single write is this file. `setup-skills-link.ps1` and `verify-setup.ps1` were **read, not run**.

### Limits of this guide

- Skill bodies were read in full for the workflow spine and in part (scope/trigger sections) for the domain and tool skills; `references/` files other than `agent-model-selection.md` were identified but not read through.
- Everything about OpenClaw's own skill discovery is unverified, as set out in §5.2.
- The repository has uncommitted modifications to `README.md`, `docs/agents-prompts-skills.md`, `setup-skills-link.ps1`, `skills/pr-scripts/REFERENCE.md`, and others. This guide describes the **working tree as it stands today**, which is what agents on this machine actually load — not the last commit (`1798ec3`).
