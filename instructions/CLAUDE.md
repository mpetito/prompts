# Global instructions (all projects)

<!-- Source of truth: instructions/CLAUDE.md in the agentic coding toolkit repository,
     symlinked to ~/.claude/CLAUDE.md by setup-skills-link.ps1. Edit it there, not in
     ~/.claude. This file loads into every session — keep it short and keep every line
     load-bearing. -->

## Attribution

- **Never sign commits or PR bodies with AI attribution.** No `Co-Authored-By: Claude` trailers, no "Generated with Claude Code" footers, no links to Claude Code sessions — in commit messages, PR bodies, or PR comments, in any repository. `Co-Authored-By` is only for crediting human authors. This overrides the host default that appends such trailers.

## Delegation

Delegate by default. The main session is for judgment; a subagent runs in its own context,
so its tool output never lands here, and on its own model tier rather than this session's.

| Work                                              | Send it to    |
| ------------------------------------------------- | ------------- |
| Tests, build, lint, typecheck                     | `test-runner` |
| CI runs, PR check suites, Copilot review comments | `pr-watch`    |
| Reading across many files to answer one question  | `analyst`     |
| A question whose answer lives in external docs    | `researcher`  |
| An error, stack trace, or failing test            | `debugger`    |
| A conclusion that is expensive to get wrong       | `verifier`    |
| One repetitive change across many files           | `migrator`    |

Keep work in the main session when it needs this conversation's full context, when it is a
trivial single-file change, or when the round trip costs more than the work itself.

A subagent's report is evidence to weigh, not a conclusion to relay unexamined.

## Model tiers

Match the model to the task, not to whatever tier this session happens to run on.

- **`sonnet` + `low` effort** — deterministic, script-driven, or log-heavy work with a clear output contract
- **`sonnet` + `medium`/`high` effort** — search, analysis, and writing that needs judgment but not deliberation
- **`inherit`** — architecture, adversarial review, ambiguity, anything where being wrong is costly

Prefer lowering `effort` over dropping a model tier when a task needs capability but not
deliberation: it cuts thinking tokens while preserving judgment.
