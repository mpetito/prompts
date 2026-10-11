# Agent files: templates and placement

Contents: [Who reads what](#who-reads-what) · [AGENTS.md](#agentsmd) · [CLAUDE.md](#claudemd) ·
[copilot-instructions.md](#githubcopilot-instructionsmd) · [REVIEW.md](#reviewmd) ·
[CONTRIBUTING.md](#contributingmd) · [specs/](#specs) · [scripts/](#scripts) ·
[Trimming and nesting](#trimming-and-nesting)

## Who reads what

| Reader | Reads |
| --- | --- |
| Claude Code | `CLAUDE.md`; by default `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the directory or above it |
| Claude Code managed Code Review, the review skill | `REVIEW.md` |
| The code-review plugin | `CLAUDE.md` files only |
| Codex | `AGENTS.md`; never `CLAUDE.md` |
| Copilot code review on GitHub.com | `.github/copilot-instructions.md`, `AGENTS.md`, root `CLAUDE.md`, `REVIEW.md` |
| Copilot cloud agent on GitHub.com | `.github/copilot-instructions.md`, `AGENTS.md`, root `CLAUDE.md` |
| Copilot Chat on GitHub.com | `.github/copilot-instructions.md` |
| Copilot code review in VS Code and Visual Studio | `.github/copilot-instructions.md` only |
| Copilot Chat in VS Code | `.github/copilot-instructions.md`, `AGENTS.md` |

Sources: [Claude Code memory](https://code.claude.com/docs/en/memory#agents-md),
[Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[Copilot instruction support](https://docs.github.com/en/copilot/reference/custom-instructions-support).
Size limits are the hosts': Claude Code's [per-file target](https://code.claude.com/docs/en/memory#write-effective-instructions),
Codex's `project_doc_max_bytes` on all files combined
([config reference](https://learn.chatgpt.com/docs/config-file/config-reference)), Copilot's
[per-file guidance](https://docs.github.com/en/copilot/tutorials/customize-code-review).

No `.github/instructions/` path-specific files unless the owner asks for them.

## AGENTS.md

The one home for every rule an agent follows here. Observed in the owner's repos: 71 to 113
lines. Each rule appears once, in one section: a never-rule goes under Do Not only, and Standing
rules holds only positive rules.

~~~~markdown
# <Project> agent instructions

<One or two sentences: what the project is and who uses it.>

## Commands

| Purpose | Command |
| --- | --- |
| Install | `pnpm install` |
| Typecheck | `pnpm typecheck` |
| Lint | `pnpm lint` |
| Format check | `pnpm format:check` |
| Duplication | `pnpm check:dup` |
| Test | `pnpm test` |

## Where things live

| Path | Contents |
| --- | --- |
| `src/` | <...> |
| `specs/` | Specs and plans, one numbered folder each |
| `docs/` | Current truth and the decision log |
| `scripts/` | Helper scripts, run through package scripts |

## Sources of truth

- <Which spec, doc or ruling wins when two disagree.>

## Standing rules

- <A positive rule (what to do here), with the path or doc it protects; never-rules go under Do Not.>

## Do Not

- Never relax a lint rule or threshold, add an inline disable (`eslint-disable`, `# noqa`), or set
  a rule to `warn`; change the code.
- Never weaken, skip or delete a test to get green.
- <A never-rule, naming the alternative; it goes here only, never also under Standing rules.>

## See also

- [CONTRIBUTING.md](CONTRIBUTING.md): commit and PR policy, check commands
- [REVIEW.md](REVIEW.md): what review checks hardest
~~~~

## CLAUDE.md

An import plus the few lines only Claude Code needs. Never a copy of AGENTS.md (the rules would
live twice) and never a symlink (Claude Code's Edit and Write refuse to write through it, and a
Windows clone gets a one-line file). With a CLAUDE.md present, Claude Code skips AGENTS.md
unless CLAUDE.md imports it.

~~~~markdown
# Claude Code

@AGENTS.md

<Claude-only lines, for example which skill to load as coordinator. Nothing AGENTS.md says.>
~~~~

The code-review plugin is given CLAUDE.md paths; whether its agents follow `@AGENTS.md` is
undocumented. Check one review on the repository before relying on it.

## .github/copilot-instructions.md

Copilot code review stays on; this file shapes it. It is review guidance for developing the
project (never runtime instructions for the product's own agents). Copilot code review on
GitHub.com also reads AGENTS.md and REVIEW.md, so this file links them and keeps only what
Copilot alone needs: the finding format and noise only Copilot raises. It restates no AGENTS.md
rule and no REVIEW.md section. IDE review sees only this file, and the owner's review runs on
GitHub.com PRs. Observed in the owner's repos: 26 to 60 lines.

~~~~markdown
# <Project> review guidance for Copilot

Review against [AGENTS.md](../AGENTS.md), [REVIEW.md](../REVIEW.md) and the specs in
[specs/](../specs/). For each finding, name the path, the concrete failure and the AGENTS.md
rule, REVIEW.md entry or spec section it breaks.

## What not to flag

- Anything REVIEW.md lists under Do not report.
- <Noise Copilot has raised on this repository's PRs that REVIEW.md does not cover.>
~~~~

## REVIEW.md

Write it by [Derive it](../../review/references/review-scope.md#derive-it) and its
[Template](../../review/references/review-scope.md#template). At setup, its "Do not report"
section lists the lint and CI gates just installed; it is the one home for that list.

## CONTRIBUTING.md

The process agents and people both follow, so no one relies on memories.

~~~~markdown
# Contributing

## Checks

Run before every push; CI runs the same:

```bash
pnpm typecheck && pnpm lint && pnpm format:check && pnpm check:dup && pnpm test
```

## Commits and pull requests

- One topic per branch; open a PR against `main`; never push to `main`.
- <Commit message convention.>
- A behaviour change updates its doc in `docs/` in the same PR.
- New work starts as `specs/NNN-slug/spec.md` and `plan.md`, reviewed before code.
~~~~

## specs/

`specs/NNN-kebab-slug/` holds `spec.md` and `plan.md`, numbered from `001`. Specs are dated
records of a decision; `docs/` holds the current truth and a decision log, never review files or
findings snapshots. `specs/README.md` lists each spec with its status. Review a spec with
[plan-review](../../plan-review/SKILL.md) before code is written.

## scripts/

Agent helper scripts live in `scripts/` and run through package scripts (`check:*`, `guard`),
so the commands in AGENTS.md stay stable. Write them in Node or TypeScript (Python in a Python
repository), not shell, so they run on Linux CI and on Windows.

## Trimming and nesting

When an existing AGENTS.md or CLAUDE.md is over budget or repeats other files, move each kind
of content to its home, then link to it:

| Content | Home |
| --- | --- |
| Project overview | README.md |
| Commands, layout, standing rules, prohibitions | AGENTS.md |
| Commit and PR process | CONTRIBUTING.md |
| What review checks hardest | REVIEW.md |
| A multi-step procedure | a skill |
| A rule a linter can enforce | the lint config |
| Explanations of the language or framework | nowhere |

Add a nested AGENTS.md only where a directory's commands or conventions differ from the root's.
The nearest file wins on Codex and Copilot, so label a deliberate override in the nested file
(`> Overrides root AGENTS.md: uses npm, not pnpm`) and report any unlabelled contradiction.
