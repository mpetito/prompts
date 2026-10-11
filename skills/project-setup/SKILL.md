---
name: project-setup
description: "Set a repository up for agentic development, or bootstrap an existing one: size, complexity and type limits as lint config with a CI job and a commit hook, plus the files agents read (AGENTS.md, a CLAUDE.md that imports it, copilot-instructions.md for review, REVIEW.md, CONTRIBUTING.md, specs/ and scripts/). Use when asked to set up a new repo for agents or agentic DX, bootstrap or onboard an existing project for Claude Code, Codex or Copilot, add complexity or file-length lint rules, make a repo work for Codex and Copilot too, or write, trim or fix AGENTS.md, CLAUDE.md or copilot-instructions.md. Not for writing or fixing a SKILL.md (skill-authoring), writing code that fits the lint limits (code-style), or reviewing a plan or spec (plan-review)."
---

# Project setup

Role: domain reference. Loaded when a repository is set up or bootstrapped for agents, or when its
agent files are written or trimmed; configs and templates live in `references/`.

Two ideas carry the whole skill. A limit a linter can enforce is config that fails CI, never a
sentence in AGENTS.md. A rule an agent must follow lives in exactly one file, AGENTS.md, and every
other agent file points to it. Code that breaks a limit: never relax a limit; decompose the code
([code-style](../code-style/SKILL.md)).

## Procedure

| Path | Steps |
| --- | --- |
| New project | 1-7, then 9 |
| Bootstrap an existing project | 1-7, then 9; step 3 holds its existing violations |
| Trim an existing AGENTS.md or CLAUDE.md | 1, 8, then 9 |

1. **Survey.** Read the agent files that exist (AGENTS.md, CLAUDE.md,
   `.github/copilot-instructions.md`, REVIEW.md, CONTRIBUTING.md), the lint config, CI workflows,
   commit hooks and package manifest.
   For the codebase facts AGENTS.md needs (commands, layout, conventions), Claude Code's `/init`
   explores and drafts them ([docs](https://code.claude.com/docs/en/memory#set-up-a-project-claude-md));
   move what it writes into AGENTS.md (step 6).
2. **Write the lint config** from [lint-typescript.md](references/lint-typescript.md) or
   [lint-python.md](references/lint-python.md). Install the caps on every new or bootstrapped
   repository, even when nobody asked for them:
   - complexity 10, cognitive complexity 15, nesting depth 4;
   - 4 parameters (an options object beyond that);
   - 60 lines per function, off in tests; 300 lines per source file;
   - test files keep a file cap of 800 lines, never `off`; blank and comment lines skipped;
   - no `any`, no `as` casts, no inline `import()` types, no TODO or FIXME comments;
   - doc comments present on exports; duplication through sonarjs and jscpd.
   Every rule is `error`, and the `lint` package script itself is `eslint . --max-warnings 0`,
   so a warning fails locally and in CI alike.
3. **Hold existing violations without loosening anything.** Never set a rule to `warn`, never
   raise a threshold, never add `eslint-disable` or `# noqa`. TypeScript: ESLint bulk suppressions
   that may only shrink ([how](references/lint-typescript.md#existing-violations)). Python: a
   `per-file-ignores` baseline in `pyproject.toml` that may only shrink
   ([how](references/lint-python.md#existing-violations)).
4. **Wire the checks.** One CI job runs typecheck, lint, format check, duplication and tests on
   every PR; docs-only PRs skip the job, never the workflow, so a required check cannot hang. A
   commit hook fixes formatting at commit: husky plus lint-staged, or pre-commit in a Python-only
   repository. See [lint-typescript.md](references/lint-typescript.md#ci-job) and
   [lint-python.md](references/lint-python.md#commit-hook).
5. **Create the folders.** Design work goes in `specs/001-kebab-slug/spec.md` and `plan.md` at
   the repository root: never `docs/design/`, `docs/specs/` or any folder under `docs/`. `docs/`
   holds current truth and a decision log. Helper scripts go in `scripts/` behind package
   scripts. Templates: [agent-files.md](references/agent-files.md#specs).
6. **Write AGENTS.md** from [the template](references/agent-files.md#agentsmd): Commands, Where
   things live, Sources of truth, Standing rules, Do Not, See also. It is the one home for every
   rule.
7. **Write the files that point at it.** On every new or bootstrapped repository, create all four:
   - CLAUDE.md: `@AGENTS.md` plus Claude-only lines ([template](references/agent-files.md#claudemd)).
   - `.github/copilot-instructions.md`: links AGENTS.md, REVIEW.md and `specs/`, and keeps only
     the finding format and Copilot-only noise; "What not to flag" points to REVIEW.md's Do not
     report. It never restates an AGENTS.md rule or a REVIEW.md section, not even as a review
     item. Copilot code review stays on ([template](references/agent-files.md#githubcopilot-instructionsmd)).
   - REVIEW.md, by [review-scope.md](../review/references/review-scope.md#derive-it); its
     "Do not report" names the gates from steps 2-4.
   - CONTRIBUTING.md: the commit and PR policy and the exact check commands
     ([template](references/agent-files.md#contributingmd)).
   Specs are reviewed with [plan-review](../plan-review/SKILL.md) before code is written.
8. **Trim an existing file.** Measure it (`wc -l AGENTS.md CLAUDE.md`) against the hosts' limits:
   [Claude Code](https://code.claude.com/docs/en/memory#write-effective-instructions),
   [Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
   [Copilot](https://docs.github.com/en/copilot/tutorials/customize-code-review). Move each kind
   of content to its home by [the routing table](references/agent-files.md#trimming-and-nesting),
   turn any lint-enforceable rule into config, delete explanations of the language or framework,
   and report unlabelled contradictions between nested files.
9. **Check, fix, repeat** until every item holds:
    - [ ] Lint exits 0 with every rule at `error`; no threshold looser than step 2; no new
      `warn`, `eslint-disable` or `# noqa`.
    - [ ] One rule, one bullet: each rule appears once, in one file and one section, never as both
      a positive line and its negation; CLAUDE.md, if present, contains `@AGENTS.md`.
    - [ ] REVIEW.md and CONTRIBUTING.md exist; `specs/` is at the root; the lint script has
      `--max-warnings 0`.
    - [ ] copilot-instructions.md has a "What not to flag" section and repeats no AGENTS.md rule
      or REVIEW.md section.
    - [ ] Each agent file is within its host's limit.
