---
name: project-setup
description: "Set a repository up for agentic development, or bootstrap an existing one: size, complexity and type limits as lint config with a CI job and a commit hook, plus the files agents read (AGENTS.md, a CLAUDE.md that imports it, copilot-instructions.md for review, REVIEW.md, CONTRIBUTING.md, specs/ and scripts/). Use when asked to set up a new repo for agents or agentic DX, bootstrap or onboard an existing project for Claude Code, Codex or Copilot, add complexity or file-length lint rules, make a repo work for Codex and Copilot too, or write, trim or fix AGENTS.md, CLAUDE.md or copilot-instructions.md. Not for writing or fixing a SKILL.md (skill-authoring), writing code that fits the lint limits (code-style), or reviewing a plan or spec (plan-review)."
---

# Project setup

Role: domain reference. Loaded when a repository is set up or bootstrapped for agents, or when its
agent files are written or trimmed; configs and templates live in `references/`.

Two ideas carry the whole skill. A limit a linter can enforce is config that fails CI, never a
sentence in AGENTS.md. A rule an agent must follow lives in exactly one file, AGENTS.md, and every
other agent file points to it. How to write code under the limits is
[code-style](../code-style/SKILL.md)'s job, not this skill's.

## Procedure

| Path | Steps |
| --- | --- |
| New project | 1-8, then 10 |
| Bootstrap an existing project | 1-8, then 10; step 3 holds its existing violations |
| Trim an existing AGENTS.md or CLAUDE.md | 1, 9, then 10 |

1. **Survey.** Read the agent files that exist (AGENTS.md, CLAUDE.md,
   `.github/copilot-instructions.md`, REVIEW.md, CONTRIBUTING.md), the lint config, CI workflows,
   commit hooks and package manifest. Run the build, lint and test commands and note what passes.
   For the codebase facts AGENTS.md needs (commands, layout, conventions), Claude Code's `/init`
   explores and drafts them ([docs](https://code.claude.com/docs/en/memory#set-up-a-project-claude-md));
   move what it writes into AGENTS.md (step 6).
2. **Write the lint config** from [lint-typescript.md](references/lint-typescript.md) or
   [lint-python.md](references/lint-python.md). Always install the caps, even when nobody asked:
   - complexity 10, cognitive complexity 15, nesting depth 4;
   - 4 parameters (an options object beyond that);
   - 60 lines per function, off in tests; 300 lines per file, 800 per test file; blank and
     comment lines skipped;
   - no `any`, no `as` casts, no inline `import()` types, no TODO or FIXME comments;
   - doc comments present on exports; duplication through sonarjs and jscpd.
   Every rule is `error`, and lint runs with `--max-warnings 0`. Architecture bans (a layer that
   must not import another) go in as `no-restricted-imports` or a check script, not prose.
3. **Hold existing violations without loosening anything.** Never set a rule to `warn`, never
   raise a threshold, never add `eslint-disable` or `# noqa`. With the rules at `error`, run
   `pnpm exec eslint . --suppress-all` and commit `eslint-suppressions.json`
   ([ESLint docs](https://eslint.org/docs/latest/use/suppressions)). The file may only shrink:
   after a fix, run `pnpm exec eslint . --prune-suppressions` and commit the smaller file. ruff
   has no suppressions file: ask the owner before bootstrapping a Python repository with
   violations.
4. **Wire the checks.** One CI job runs typecheck, lint, format check, duplication and tests on
   every PR; docs-only PRs skip the job, never the workflow, so a required check cannot hang. A
   commit hook (husky plus lint-staged) fixes formatting at commit. Both are in
   [lint-typescript.md](references/lint-typescript.md#ci-job).
5. **Create the folders.** New work starts as `specs/001-kebab-slug/spec.md` and `plan.md` at the
   root, never under `docs/`; `docs/` holds current truth and a decision log. Helper scripts go
   in `scripts/` behind package scripts. Templates: [agent-files.md](references/agent-files.md#specs).
6. **Write AGENTS.md** from [the template](references/agent-files.md#agentsmd): Commands, Where
   things live, Sources of truth, Standing rules, Do Not, See also. It is the one home for every
   rule; copy each command from a run that worked.
7. **Point the other files at it.**
   - CLAUDE.md is `@AGENTS.md` plus Claude-only lines; never a copy, never a symlink. When an
     existing CLAUDE.md holds the rules, move them into AGENTS.md and leave the import
     ([template](references/agent-files.md#claudemd)).
   - `.github/copilot-instructions.md` is review guidance: it links AGENTS.md and `specs/`, lists
     review priorities, then "What not to flag". It never restates AGENTS.md, and Copilot code
     review stays on ([template](references/agent-files.md#githubcopilot-instructionsmd)).
   - REVIEW.md follows [review-scope.md](../review/references/review-scope.md#derive-it); its
     "Do not report" names the gates from steps 2-4.
   - CONTRIBUTING.md holds the commit and PR policy and the exact check commands
     ([template](references/agent-files.md#contributingmd)).
   - Specs are reviewed with [plan-review](../plan-review/SKILL.md) before code is written.
8. **Run everything once.** Lint, typecheck, format check, duplication and tests pass locally;
   push a branch and confirm the CI job runs.
9. **Trim an existing file.** Measure it (`wc -l AGENTS.md CLAUDE.md`) against the hosts' limits:
   [Claude Code](https://code.claude.com/docs/en/memory#write-effective-instructions),
   [Codex](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
   [Copilot](https://docs.github.com/en/copilot/tutorials/customize-code-review). Move each kind
   of content to its home by [the routing table](references/agent-files.md#trimming-and-nesting),
   turn any lint-enforceable rule into config, delete explanations of the language or framework,
   rerun every remaining command, and report unlabelled contradictions between nested files.
10. **Check, fix, repeat** until every item holds:
    - [ ] Lint exits 0 with every rule at `error`; no threshold looser than step 2; no new
      `warn`, `eslint-disable` or `# noqa`.
    - [ ] Every command in AGENTS.md and CONTRIBUTING.md ran as written.
    - [ ] Each rule appears in one file; CLAUDE.md, if present, contains `@AGENTS.md`.
    - [ ] copilot-instructions.md has a "What not to flag" section and repeats no AGENTS.md rule.
    - [ ] Every relative link in the agent files resolves.
    - [ ] Each agent file is within its host's limit.
