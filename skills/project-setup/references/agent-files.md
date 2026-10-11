# Agent files: templates and placement

Contents: [Who reads what](#who-reads-what) · [AGENTS.md](#agentsmd) · [CLAUDE.md](#claudemd) ·
[copilot-instructions.md](#githubcopilot-instructionsmd) · [REVIEW.md](#reviewmd) ·
[CONTRIBUTING.md](#contributingmd) · [specs/](#specs) · [scripts/](#scripts) ·
[Trimming and nesting](#trimming-and-nesting)

## Who reads what

| File | Read by |
| --- | --- |
| `AGENTS.md` | Codex; Copilot cloud agent and code review; Claude Code only when no `CLAUDE.md` exists in the directory or above it |
| `CLAUDE.md` | Claude Code; the code-review plugin (CLAUDE.md files only); Copilot, root file only |
| `.github/copilot-instructions.md` | Copilot code review, cloud agent and Chat; the only file VS Code code review reads |
| `REVIEW.md` | Claude Code managed Code Review, Copilot code review, the review skill |

Sources: [Claude Code memory](https://code.claude.com/docs/en/memory#agents-md),
[Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md),
[Copilot instruction support](https://docs.github.com/en/copilot/reference/custom-instructions-support).
Size limits are the hosts': Claude Code's [per-file target](https://code.claude.com/docs/en/memory#write-effective-instructions),
Codex's `project_doc_max_bytes` on all files combined
([config reference](https://learn.chatgpt.com/docs/config-file/config-reference)), Copilot's
[per-file guidance](https://docs.github.com/en/copilot/tutorials/customize-code-review).

No `.github/instructions/` path-specific files unless the owner asks for them.

## AGENTS.md

The one home for every rule an agent follows here. 50 to 115 lines. Every command is copied from
a run that worked; every path exists.

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
| Test | `pnpm test` |

## Where things live

| Path | Contents |
| --- | --- |
| `src/` | <...> |
| `specs/` | Dated specs and plans, `NNN-slug/spec.md` and `plan.md` |
| `docs/` | Current truth and the decision log |
| `scripts/` | Helper scripts, run through package scripts |

## Sources of truth

- `docs/` describes the system as it is; a behaviour change updates its doc in the same PR.
- <Which spec or ruling wins when two disagree.>

## Standing rules

- <A rule specific to this repository, with the path or doc it protects.>

## Do Not

- Never relax a lint rule or threshold, add `eslint-disable`, or set a rule to `warn`; change the code.
- Never weaken, skip or delete a test to get green.
- <A project prohibition, each naming the alternative.>

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
project (never runtime instructions for the product's own agents), and it points to AGENTS.md
rather than restating it. 26 to 60 lines.

~~~~markdown
# <Project> review priorities

Review against [AGENTS.md](../AGENTS.md) and the specs in [specs/](../specs/). For each finding,
name the path, the concrete failure and the rule or contract it breaks.

## Review priorities

- <The repository's riskiest paths: data loss, access, money, secrets, concurrency.>
- <Contracts others build on: exported types, endpoints, schemas, config keys.>
- Tests that cannot fail for the regression they claim to cover.

## What not to flag

- Formatting, and anything lint, typecheck or CI already enforces.
- Generated, vendored and lock files.
- Prose style in docs; report factual contradictions only.
~~~~

## REVIEW.md

Write it by [Derive it](../../review/references/review-scope.md#derive-it) and its
[Template](../../review/references/review-scope.md#template). At setup, its "Do not report"
section lists the lint and CI gates just installed.

## CONTRIBUTING.md

The process agents and people both follow, so no one relies on memories.

~~~~markdown
# Contributing

## Checks

Run before every push; CI runs the same:

```bash
pnpm typecheck && pnpm lint && pnpm format:check && pnpm test
```

## Commits and pull requests

- One topic per branch; open a PR against `main`; never push to `main`.
- <Commit message convention.>
- A behaviour change updates its doc in `docs/` in the same PR.
- New work starts as `specs/NNN-slug/spec.md`, reviewed before code.
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
| A rule a linter can enforce | the lint config, plus one line in AGENTS.md |
| Explanations of the language or framework | nowhere |

Add a nested AGENTS.md only where a directory's commands or conventions differ from the root's.
The nearest file wins on Codex and Copilot, so label a deliberate override in the nested file
(`> Overrides root AGENTS.md: uses npm, not pnpm`) and report any unlabelled contradiction.
