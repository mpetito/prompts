# Project-setup digest (2026-10-11)

**Skill name:** `project-setup`. **Role:** domain reference, loaded when a project is set up
or bootstrapped for agents, or when its agent files are written or trimmed. Body: a short
procedure (about 100 lines). Per-ecosystem lint config and file templates go in `references/`.
It also takes over AGENTS.md/CLAUDE.md upkeep from the archived `agents-md-authoring`, whose seed
it is. skill-authoring's "Not for AGENTS.md" clause then names it.

Evidence files (in the thread worktree, `.orchestration/results/`): ev-transcripts (T),
ev-gh (G), ev-repos (R), overlap (O). S1-S4 are opaque session tags local to this file, and
"PR review" marks an owner comment on a pull request. **Provenance:**
- **typed:** `promptSource` typed or queued;
- **typed-likely:** an owner GitHub comment from before agent tooling, or an `@copilot` directive;
- **approved:** a file a model wrote after an owner request or ruling shown in a transcript;
- **merged:** an agent PR the owner merged, with no request on record;
- **inferred:** a repo pattern only.

Commits after 2026-08-24 count as agent-written: AI trailers have been forbidden since then.

## What the skill covers, and the boundary with code-style

- **project-setup:** one-time configuration. It covers:
  - every rule that a stock linter or compiler rule enforces through an option or threshold,
    written as config;
  - where checks run (commit hook, CI);
  - the files agents read: AGENTS.md, CLAUDE.md, `.github/copilot-instructions.md`, REVIEW.md,
    CONTRIBUTING.md, `specs/`, and a folder for agent helper scripts.
- **code-style (worker, every lane):** judgment rules no linter enforces, plus "never relax a
  lint rule or threshold; decompose instead". It keeps:
  - rule 7 whole (this skill may ship a doc-presence lint as config, but never restates the rule);
  - custom `no-restricted-syntax` selectors that encode judgment (rules 5, 10, 13);
  - prose rules (FIXMEs and history in Markdown).
- **Moved from code-style to config here** (docs-checked, O §5):
  - rule 11: `no-explicit-any`, `consistent-type-assertions` `assertionStyle: "never"`,
    `consistent-type-imports` `disallowTypeAnnotations` (inline `import()` types), ruff ANN401;
  - rule 12, TODO/FIXME in code: ESLint `no-warning-comments`, ruff FIX/TD;
  - rule 8's line-cap numbers.
- **Linked, never restated:**
  - REVIEW.md's format: `skills/review/references/review-scope.md`;
  - spec review: `skills/plan-review`;
  - `.orchestration/`: the orchestration skills;
  - writing CLAUDE.md content from exploring the code: the built-in `/init`;
  - each host's size limit: the host docs (Claude "under 200 lines per CLAUDE.md file"; Codex
    `project_doc_max_bytes` 32 KiB for all files combined).

## Defaults, with evidence

### Lint thresholds (TypeScript, ESLint flat config)

| Rule | Default | Evidence | Provenance |
| --- | --- | --- | --- |
| Ask for size and complexity caps at all | yes | "add some eslint complexity rules that will catch overly long modules or high complexity routines too that should be decomposed further" (S1, 2026-10-03T00:15:46Z); the model had proposed none | typed |
| `complexity` | 10 | 3 repos use 10; "I agree with recommendations" (S1, 00:16:49Z) | approved; 3 repos agree |
| `sonarjs/cognitive-complexity` | 15 | "I'm fine with adding cognitive complexity rule" (00:16:49Z); 2 repos | typed + approved |
| `max-depth` | 4 | 3 repos | approved; 3 repos agree |
| `max-params` | 4, with an options object beyond that | 2 repos (1 approved); a third uses 5; the owner's 2025-12-04 prompt file says an options object past 3 (`731fea2`, uncertain author), as does a fourth repo's AGENTS.md | approved; conflict (3, 4 or 5) |
| `max-lines-per-function` | 60, skipping blank lines and comments; off in tests | 1 repo (approved); two others use 50 and 80 | approved; conflict |
| `max-lines` | 300 per source file, 800 per test file, skipping blanks and comments | 1 repo only. The owner asked for "overly long modules" rules and accepted the model's numbers. "so that this file isn't so long" (PR review, 2025-11-12) | typed ask + approved values |
| sonarjs | a curated subset (`no-identical-functions` and others), not `recommended` | "Is there additional value to the other sonarjs rules?" → "All agreed." (00:17:19Z, 00:18:53Z) | typed + approved |
| Types | `strictTypeChecked`, `no-explicit-any`, no `as` casts, no inline `import()` types | "casting types to `any` is lazy." (PR review, 2025-11-12); 4 repos | typed-likely |
| `no-warning-comments` | error | "i also caught a few fixmes left in test suites" (S2, 2026-09-29T09:17:45Z, code-style rule 12) | typed |
| Severity | every rule `error`, plus `--max-warnings 0`; never `eslint-disable` | "this PR cannot be accepted because it modifies eslint rules to relax coding standards." (PR review, 2025-11-24); "Need to address linter complexity warning." (PR review, 2026-02-24, a warning left in place); one repo's AGENTS.md | typed-likely + approved; older repos use warn |
| Existing violations | rules at error, with current violations held in ESLint bulk suppressions (`--suppress-all`, ESLint ≥ 9.24); never raise a threshold | inferred from the severity row; mechanism per eslint.org/docs/latest/use/suppressions (O §5) | inferred, **D1-c** |
| Duplication | **no owner default.** Proposed: sonarjs `no-identical-functions` plus jscpd in CI (`--min-tokens 50`, threshold chosen from the first report) | owner names "duplication estimates" (2026-10-11); 0 of 21 repos run jscpd; DRY complaints (PR review, 2025-12-07: "113-line schemas.ts duplicating registry schemas") | typed want; tool inferred, **D1-d** |
| Doc-presence lint (`jsdoc/require-jsdoc` publicOnly) | on for exported contracts. The comment rule itself stays in code-style | "Public contracts should have doc comments" then "I agree with the eslint rule" (S1, 2026-10-03); another project's "a lack of high level commenting" (S2, 2026-09-29) was fixed without lint | typed + approved in 1 repo, **D1-e** |
| Architecture bans | as lint (`no-restricted-imports`) or a check script, not prose | 4 repos | inferred |

### Lint thresholds (Python, ruff)

There is no owner default: no Python repo caps complexity (T §1a). Proposed, mirroring the TS
numbers: C901 `max-complexity` 10, PLR0913 `max-args` 4, PLR0912 and PLR0915 (statement and
branch caps), ANN401, FIX/TD. ruff has no module-length rule ("not compatible with the
formatter", astral-sh/ruff#970), so a 300-line cap needs a small check script. Provenance:
**inferred**, **D1-f**.

### Where checks run

| Item | Default | Evidence | Provenance |
| --- | --- | --- | --- |
| CI | one job runs lint, typecheck and format check on every PR | 2 local repos and all 8 GitHub repos | approved |
| CI path filters | expensive jobs skip docs-only PRs | "optimize the ci pipeline trigger. It runs on all PRs, like doc changes, where it doesn't need to" (S2, 2026-09-27T23:07:27Z) | typed |
| Commit hook | autofix formatting at commit (husky plus lint-staged on all staged types), with CI as the backstop | "it should just automatically fix during commit or if required, as part of a self-correcting CI step" (PR review); only the reviewed repo runs a hook, and 2 others have none | typed-likely; conflict, **D1-g** |

### Agent files

| File | Default | Evidence | Provenance |
| --- | --- | --- | --- |
| AGENTS.md | canonical, read by Codex and Copilot | 11 repos; every one of them agent-written, and no owner prompt asked for the shape | merged; 11 repos agree |
| CLAUDE.md | `@AGENTS.md` plus a few Claude-only lines; never a copy or a symlink | the same 3 repos. Claude Code reads AGENTS.md only when there is no CLAUDE.md (code.claude.com/docs/en/memory#agents-md), and the code-review plugin reads only CLAUDE.md files (O §1) | approved + host docs |
| AGENTS.md sections | Commands, Where things live, Sources of truth, Standing rules, Do Not, See also; 50-115 lines | 3 repos: 74, 113 and 71 lines | approved; inferred shape |
| `.github/copilot-instructions.md` | Copilot code review stays **on**. The file is development review guidance only: it points to AGENTS.md and specs, lists review priorities, then what not to flag; 26-60 lines | "copilot code reviews can stay on, and you commit copilot instructions to shape its review" (S1, 2026-10-02T15:19:59Z; the model had turned review off); "If you need to tune copilot review behavior, do so via copilot-instructions.md." (S2, 2026-09-27T17:22:05Z); "for development of the project and _not_ for use by the [project's] agents at runtime" (PR review, 2025-10-25) | typed ×2 + typed-likely |
| REVIEW.md | create it; its format is review-scope.md's (link) | no repo has one yet; the review skill defines it | approved (live skill) |
| CONTRIBUTING.md | process for agents and people: commit and PR policy, the exact check commands; replaces memories | "a CONTRIBUTING md file is appropriate for this repo … This way we don't have to rely on memories" (this repository, S4, 2026-09-20T14:42:01Z) | typed |
| `.github/instructions/` | none | 0 of 15 repos; one repo's PR deferred them on purpose | inferred |

### Folder layout

| Folder | Default | Evidence | Provenance |
| --- | --- | --- | --- |
| `specs/` | root `specs/NNN-kebab-slug/` holding `spec.md` and `plan.md`; dated design records, reviewed with plan-review; `docs/` holds current truth | "specs should be relocated from docs/design to specs/" (S3, 2026-09-20T15:02:46Z; the model had scaffolded `docs/design/001-…`); 11-12 repos, all from the archived spec skill, numbered from 001 (000 in 2 of them); one repo uses `docs/phases/` instead; one has a `specs/README.md` | typed; dated vs living is a conflict, **D1-h** |
| Agent helper scripts | `scripts/`, exposed as package scripts (`check:*`, `guard`); Node or TS so they run on Linux CI and on Windows | 9 of 9 repos use `scripts/`, 0 use `utils/`; the Node-vs-bash line comes from a pasted brief (uncertain author) | inferred vs the owner's "a utils folder", **D1-i** |
| `docs/` | current truth plus a decision log; no review files or findings snapshots | "docs folder is a mess of review files; clean it up" (S3) | typed |

## D1 (owner-before): confirm or change

**Confirmed 2026-10-11:** all items as recommended; i = `scripts/`; j = a project the owner chose; k = $15 Claude
(ask at $10), 3M Codex tokens.

- **a.** Name `project-setup`, role domain reference, and it also owns later AGENTS.md/CLAUDE.md
  upkeep. Default: yes.
- **b.** Thresholds as tabled: one repo's approved set (complexity 10, cognitive 15, depth 4, params 4,
  function 60 lines, file 300 lines with 800 for tests), all errors. Default: yes. Conflicts:
  params 3, 4 or 5; function lines 50, 60 or 80.
- **c.** Existing violations: errors plus bulk suppressions. Default: yes.
- **d.** Duplication: sonarjs `no-identical-functions` plus jscpd in CI. Default: yes, with the
  threshold set from the first run.
- **e.** Doc-presence lint on exports (`jsdoc/require-jsdoc` publicOnly). Default: on, as in the repo that approved it.
- **f.** Python: ruff mirroring the TS numbers, plus a line-count script. Default: yes, labelled
  inferred.
- **g.** Commit hook that autofixes formatting. Default: yes.
- **h.** `specs/` are dated records and `docs/` is current truth. Default: yes.
- **i.** "utils folder": does it mean `scripts/`, a new `utils/`, or a rename? Default: `scripts/`.
- **j.** A repository to bootstrap with the skill within 30 days (readmission item 5). No
  default; for example a Python repository with no lint.
- **k.** Eval spend: cap $15 on Claude for the whole readmission, asking at $10; Codex 3M tokens
  or 60 answer runs. Agents: Claude Opus, 3 runs per arm, plus one Codex smoke run. Judge on
  Sonnet. One full Claude pass is estimated at $4.50-7.50 (O §4). No default; nothing is spent
  until you confirm.

## Eval traps (one fixture each; the smoke run cuts any that pass without the skill)

1. **Bootstrap lint on an existing repo with violations.** The fixture is a TS repo described in
   one markdown file: 14 functions over complexity 10, plus an `eslint.config.mjs` with no caps.
   Without the skill, expect warn, raised thresholds or `eslint-disable`. Fail:
   `not_regex` `"warn"|eslint-disable|complexity["']?\s*:\s*\[\s*["']\w+["']\s*,\s*(1[1-9]|[2-9]\d)`.
   Pass: `regex` `--suppress-all|eslint-suppressions\.json` and `complexity.*10`.
2. **Agent files for Claude and Codex.** The fixture repo has a 180-line CLAUDE.md and no
   AGENTS.md; the task is "make this repo work for Codex and Copilot too". Without the skill,
   expect a copied AGENTS.md, a symlink, or a copilot-instructions file that restates AGENTS.md.
   Pass: CLAUDE.md contains `@AGENTS.md`, and the rules appear once. Judge: copilot-instructions
   is review guidance, not a copy.
3. **New project setup.** The task is "set this new repo up for agentic development". Without the
   skill, expect no size caps (K3), no copilot-instructions or review turned off (K2, K5), specs
   under `docs/` (K1), and process kept in memory (K6). Pass: `max-lines` and `max-params` in the
   config, a `specs/001-` path, copilot-instructions with "what not to flag", and a CONTRIBUTING
   with the check commands.

**Measured delta:** the without-skill arm fails at least one assertion in every run; the
with-skill arm scores 1.00 over 3 runs. Claude arms load `~/.claude/CLAUDE.md` in both arms
(it says nothing on lint or agent files). Codex prompts allow a read-only `cat` of the fixture.
