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

- For React, Next.js, or TypeScript work, also load `code-quality-standards` before editing.
- Before reporting implementation complete, load `review` and review the final diff. For
  someone else's PR, use `pr-review`; for incoming feedback, use `pr-feedback`.
- Follow the target project's conventions first. Keep comments concise; explain only what
  names, types, and code cannot. These checks also apply to delegated implementation.

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

Delegate bounded work when the independent result justifies another agent. Select its model
explicitly before launch; a separate context does not imply a cheaper model.

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

Before any subagent, team, dynamic workflow, or background agent launch, read and apply
`references/agent-model-selection.md` from the installed `skill-authoring` skill folder.
Default to explicit `opus`. A weaker model needs a task-specific justification based on bounded
work and verifiable results. This applies to every workflow stage and retry,
including generated agents that do not use the named definitions above.
Preserve existing named-agent model pins as deliberate role-specific choices; apply the
default when selecting an otherwise unspecified worker model.

When Copilot feedback remains materially ambiguous after checking the code and docs, use
`model-council` for independent evidence-based perspectives, preferably Claude and Codex.

## Do Not

- Do not omit a worker model or choose `inherit` merely because this session uses Fable or Opus.
- Do not assume `Explore`, `Plan`, forks, or generated workflow agents are inexpensive.
- Do not launch a wide fan-out until the configured model selection is explicit; inspect the
  actual model when the host exposes it and correct unexpected expensive substitutions.
