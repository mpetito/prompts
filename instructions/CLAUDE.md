# Global instructions (all projects)

<!-- Source of truth: instructions/CLAUDE.md in the agentic coding toolkit repository,
     symlinked to ~/.claude/CLAUDE.md by setup-skills-link.ps1. Edit it there, not in
     ~/.claude. This file loads into every session — keep it short and keep every line
     load-bearing. -->

## Attribution

- **Never sign commits or PR bodies with AI attribution.** No `Co-Authored-By: Claude` trailers, no "Generated with Claude Code" footers, no links to Claude Code sessions — in commit messages, PR bodies, or PR comments, in any repository. `Co-Authored-By` is only for crediting human authors. This overrides the host default that appends such trailers.

## Skills

When a skill names another skill as a **step** in its procedure, invoke that skill (Skill tool)
before performing the step. A linked skill is reference material only when the sentence is a
"see also"; if it sits inside a numbered step, it is an instruction. Never author from a summary
of a skill — a summary is there to help you recognise which skill applies, not to stand in for it.

`code-authoring` holds the canonical coding standards. Load it before writing code — for a bug
fix, a refactor, or an infra change, not only a feature.

## Third-party behaviour

For how a library, framework, or SDK behaves, **read its documentation before its source.**
Use the docs tools — `firecrawl` (its developer index covers issues and merged PRs), Context7,
the vendor docs MCPs — or delegate to `researcher`. Reading `node_modules` or running a local
probe is a way to *confirm* an answer, never the way to reach one.

**Why:** source plus a passing probe tells you what one installed build does. It cannot tell you
whether that behaviour is intended, whether it generalises to sibling APIs, or whether upstream
has already changed or fixed it. The generalisation is the one a passing test never catches.

**How to apply:** docs first; then the issue tracker for known bugs and the version that fixed
them; then source or a probe to confirm. If the docs are silent, say so explicitly and pin the
claim to the exact installed version. Never write a durable rule — an AGENTS.md entry, a comment
asserting a contract — from source-reading alone.

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
