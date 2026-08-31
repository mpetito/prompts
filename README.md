# Agentic Coding Toolkit

A collection of agent skills for reliable agentic coding workflows, shared across GitHub Copilot (VS Code + Copilot CLI) and Claude Code.

Skills are the single unit of reusable workflow guidance in this repository: they auto-load when relevant, and both VS Code and Claude Code expose each skill as an explicit `/name` entry point. There is no separate `prompts/` concept; former prompt slugs are preserved as skill names.

## Skills

| Skill                     | `/slash` invocation        | Purpose                                                                                         |
| ------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------- |
| `commit`                  | `/commit`                  | Validate changes, create conventional commits, push branches, and open or update pull requests  |
| `implement`               | `/implement`               | Execute a spec or clear request end-to-end, from planning through implementation and validation |
| `pr-feedback`             | `/pr-feedback`             | Address PR feedback from reviews, CI, and code analysis tools                                   |
| `pr-resolve`              | `/pr-resolve`              | Reply to and resolve PR review threads                                                          |
| `pr-consolidate`          | `/pr-consolidate`          | Consolidate multiple PRs or branches into a unified integration branch                          |
| `review`                  | `/review`                  | Run a structured code review of staged or recently implemented changes                          |
| `spec`                    | `/spec`                    | Produce `spec.md` (what + why) and `plan.md` (how) under `specs/{NNN-slug}/`                    |
| `tt`                      | `/tt`                      | Log or update a Harvest time entry for current work, linked to an ADO item                      |
| `story`                   | `/story`                   | Create a user story, issue, or bug in Azure DevOps                                              |
| `research`                | `/research`                | Conduct deep technical research using documentation, search, and GitHub resources               |
| `pr-review`               | `/pr-review`               | Review someone else's PR by number and draft/post feedback with approval                        |
| `pr-authoring`            | `/pr-authoring`            | Write concise, motivation-led pull request descriptions                                         |
| `upgrade`                 | `/upgrade`                 | Safely upgrade dependencies with research, risk assessment, and validation                      |
| `code-authoring`          | `/code-authoring`          | Implementation methodology: prepare, implement, test, self-review, and validate                 |
| `agents-md-authoring`     | `/agents-md-authoring`     | Author AGENTS.md / CLAUDE.md project-wide context files                                         |
| `skill-authoring`         | `/skill-authoring`         | Author, split, and tune SKILL.md files and skill folders                                        |
| `autonomous-loops`        | `/autonomous-loops`        | Run iterative loops against asynchronous external evaluators such as CI or deploys              |
| `code-quality-standards`  | `/code-quality-standards`  | Detailed Next.js, React, and TypeScript code quality review standards                           |
| `design-review-standards` | `/design-review-standards` | UI/UX and accessibility review standards for brand, responsive design, and conversion           |
| `ecommerce-patterns`      | `/ecommerce-patterns`      | Cart, checkout, payments, orders, and conversion patterns for React/Next.js apps                |
| `playwright-e2e`          | `/playwright-e2e`          | Playwright end-to-end testing: Page Object Models, locators, and monorepo setup                 |
| `seo-aeo-structured-data` | `/seo-aeo-structured-data` | SEO, AEO, structured data, metadata, sitemap, and Core Web Vitals guidance                      |
| `agentmail`               | `/agentmail`               | Use the AgentMail MCP server as a test mailbox when verifying email send/receive flows          |
| `word-doc-editing`        | `/word-doc-editing`        | Edit Word .docx files via Word COM automation: tracked changes, structural ops, verification    |
| `firecrawl`               | `/firecrawl`               | Search, scrape, crawl, map, and extract from the live web; developer and research indexes       |

When you already have a spec in `specs/{NNN-slug}/`, use `/implement spec NNN` to execute it end-to-end. For ad-hoc implementation requests without a spec, describe the work directly or invoke `/implement`.

## Agents

Subagent definitions for delegated work. Each runs in its own context with its own model, so verbose output — test logs, CI logs, fetched documentation, wide code reads — never reaches the calling session, and mechanical work runs on a cheaper tier than the session orchestrating it.

| Agent         | Model / effort      | Use for                                                                                 |
| ------------- | ------------------- | --------------------------------------------------------------------------------------- |
| `test-runner` | `sonnet` / `low`    | Run tests, build, lint, or typecheck; report pass/fail with the failing output verbatim |
| `pr-watch`    | `sonnet` / `low`    | Watch a PR settle — CI runs and check suites, plus Copilot review comments              |
| `analyst`     | `sonnet` / `medium` | Explain how a subsystem, flow, or symbol actually works, with `file:line` citations     |
| `researcher`  | `sonnet` / `high`   | Investigate libraries, APIs, and external docs; return a sourced synthesis, not pages   |
| `debugger`    | `sonnet` / `xhigh`  | Reproduce a failure, isolate its root cause, propose a minimal fix with evidence        |
| `verifier`    | `inherit` / `high`  | Adversarially check one claim, diff, or fix; return CONFIRMED, REFUTED, or UNPROVEN     |
| `migrator`    | `sonnet` / `medium` | Apply one mechanical transformation across many files, in an isolated git worktree      |

Only `migrator` can edit files, and it works in a temporary git worktree so its changes cannot disturb the caller's working tree. The other six are granted neither `Edit` nor `Write`. Note that a `Bash` grant is not a read-only guarantee — `analyst`, `verifier`, and `debugger` are restricted to inspection by their instructions, not by their tool list.

**When to delegate.** Send deterministic, log-heavy work to `test-runner` and `pr-watch` by default. Send reading that spans many files to `analyst`, and anything answered by external documentation to `researcher`. Send a failure to `debugger`, a conclusion that is expensive to get wrong to `verifier`, and a repetitive change across many files to `migrator`. Keep work in the main session when it needs the conversation's full context or is a trivial single-file change.

**Why the model tiers.** `verifier` inherits the calling session's model on purpose: it is used exactly where being wrong costs more than the tokens. The rest pin `sonnet`, so they stay cheap whether the calling session is on Opus or Fable. `effort` is the finer lever — `debugger` runs at `xhigh` because root-cause analysis rewards thinking far more than it rewards a larger model.

Each agent defines a strict output contract. That is what makes a cheaper tier reliable: the agent reports evidence in a fixed shape rather than deciding for itself how much to say. Beyond `model` and `effort`, they set `permissionMode: auto` so background work does not stall on a prompt, `maxTurns` as a runaway guard, and `memory: project` where a project-specific fact is worth carrying between sessions — the test command, a repository's CI shape, a recurring failure mode. `analyst` and `verifier` deliberately keep no memory: both must answer from the code as it is now, and a remembered claim invites a stale one.

## Instructions

`instructions/CLAUDE.md` is the user-level global instruction file, symlinked to `~/.claude/CLAUDE.md`. Unlike skills and agents, it is **always loaded**, in every session and every project — so it holds only what must apply everywhere: attribution rules, the delegation routing table, and model-tier guidance. Anything narrower belongs in a skill, which loads on demand.

Keeping it here rather than in `~/.claude` puts it under version control alongside the agents it routes to, so the routing table and the agent definitions cannot drift apart.

## Fragments

Reusable prompt fragments for specialized workflows.

| Fragment              | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `snyk-upgrade-review` | Review and complete Snyk dependency upgrade PRs |

## Workflows

### Standard Feature Development

```
/spec → /implement spec NNN → /review → /commit
```

1. **Spec** (`/spec`): produce `spec.md` + `plan.md` under `specs/{NNN-slug}/`
2. **Implement** (`/implement spec NNN`): apply any clarifications, create or review the plan, build all phases
3. **Review** (`/review`): independent quality pass
4. **Commit** (`/commit`): branch, commit, push, open/update PR

### Direct Implementation (Clear Requirements, No Spec)

```
(describe the work) → /review → /commit
```

### Research Spike

```
/research → /spec → ...
```

### PR Feedback Loop

```
/pr-feedback → /pr-resolve → /commit
```

Repeat until approved.

### Dependency Upgrade

```
/upgrade → /commit
```

### Branch Consolidation

```
/pr-consolidate → /commit
```

## Setup

Each tool reads skills from its own user-level folder. `setup-skills-link.ps1` symlinks every one of them back to this repository's `skills/` directory, and links Claude Code's subagent folder to `agents/` and its user-level `CLAUDE.md` to `instructions/CLAUDE.md`, so a single edit here reaches every tool.

| Repository folder | Tool                          | User-level folder     |
| ----------------- | ----------------------------- | --------------------- |
| `skills/`         | GitHub Copilot (VS Code, CLI) | `~/.copilot/skills/`  |
| `skills/`         | Claude Code                   | `~/.claude/skills/`   |
| `skills/`         | opencode and similar          | `~/.agents/skills/`   |
| `agents/`         | Claude Code                   | `~/.claude/agents/`   |
| `instructions/`   | Claude Code                   | `~/.claude/CLAUDE.md` |

1. Ensure VS Code 1.106+ with GitHub Copilot, and/or Claude Code
2. Run `setup-skills-link.ps1` (as Admin or with Developer Mode enabled)
3. Skills auto-load when relevant and can be invoked explicitly via `/name` in chat
4. Agents become available to Claude Code as subagent types for delegated work
5. Global instructions load into every Claude Code session, in every project

The script is idempotent and never replaces anything without asking: a link already pointing at this repository is left alone, a link pointing elsewhere prompts before replacement, and a real directory is listed and confirmed before being renamed to `<name>_old`. Decline any target you don't want — `~/.agents/skills/` in particular may already be managed by another skill installer.

### Cross-Tool Authoring Notes

Skills here target the lowest common denominator so they work everywhere:

- `name` and `description` are the only required and universally-honored frontmatter keys
- Directory names match the frontmatter `name`
- Tool references are described as capabilities (e.g. "Context7 docs", "IDE diagnostics") rather than literal tool IDs, which differ per host
- Cross-references are **skill-relative** (`../other-skill/SKILL.md`), never repo-root-relative — the tree is symlinked into user-level folders where no repo root exists
- `skills/pr-scripts/` holds shared PowerShell helpers rather than a skill. `README.md` there is the script inventory; `REFERENCE.md` is the shared agent-facing usage, decision matrix, and reply templates that `pr-feedback`, `pr-resolve`, and `pr-review` all link to
- `instructions/CLAUDE.md` is the user-level global instruction file, linked only into Claude Code for the same reason. It loads into every session in every project, so keep it short and keep every line load-bearing
- `agents/` is Claude Code's subagent format and is deliberately **not** cross-tool — other hosts use incompatible agent formats, so the setup script links it into Claude Code only. Keep agent bodies host-generic and project-agnostic (no employer, stack, or repository specifics) so they behave the same in every project. Agents may depend on `skills/` two ways — a relative path such as `../skills/pr-scripts/…`, which resolves in both the repository and `~/.claude/`, and a `skills:` frontmatter entry naming a skill to preload. `researcher` also names specific documentation MCP servers in its `tools` list; adjust that line on a machine where those servers are not configured

### Progressive Disclosure

Large skills keep `SKILL.md` lean and push detail into a `references/` subfolder, which loads
only when `SKILL.md` points at it. `SKILL.md` carries the workflow, decisions, and pitfalls;
`references/` carries code libraries, command tables, and long worked examples. Currently used
by `ecommerce-patterns`, `firecrawl`, `seo-aeo-structured-data`, `story`, and `upgrade`.

### Host-Specific Frontmatter

Claude Code accepts extra frontmatter keys; other hosts ignore unknown keys, so using them does
not break portability. Several skills set them:

| Key                        | Used for                                                                                            |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| `model`                    | Pinning a cheaper tier on mechanical skills (`commit`, `tt`, `story`, `pr-resolve`, `pr-authoring`) |
| `effort`                   | Tuning reasoning depth without changing model tier (`firecrawl` runs `sonnet` at `high`)            |
| `disable-model-invocation` | User-typed `/name` only (`pr-consolidate`, whose merges are destructive)                            |

Skills that are _consumed inside another task_ rather than invoked directly — the standards and
pattern skills — deliberately set no `model`, so they inherit whatever the calling workflow uses.
`firecrawl` is the exception: it is tool-driving work, so it pins `sonnet` to stay cheap under an
Opus session while keeping `effort: high`, because choosing the right rung of the search/scrape/crawl
ladder and writing a good query is where its judgment actually goes.
See the `skill-authoring` skill for the full key list and selection guidance.

## Customization

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced from skills that benefit from research or PR capabilities. Skills still work with reduced functionality if those tools are not configured.

### Skill Descriptions

Skills auto-load based on their `description` frontmatter. To make a skill trigger on different phrasing, edit its description to include the trigger phrases you use.

## Requirements

- VS Code 1.106+ with GitHub Copilot, and/or Claude Code
- `gh` CLI (authenticated) and PowerShell for the PR workflows
- Optional: MCP servers (Context7, Perplexity, GitHub) for richer research and PR workflows
