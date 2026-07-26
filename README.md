# Agentic Coding Toolkit

A collection of agent skills for reliable agentic coding workflows, shared across GitHub Copilot (VS Code + Copilot CLI) and Claude Code.

Skills are the single unit of reusable workflow guidance in this repository: they auto-load when relevant, and both VS Code and Claude Code expose each skill as an explicit `/name` entry point. There is no separate `prompts/` concept; former prompt slugs are preserved as skill names.

## Skills

| Skill | `/slash` invocation | Purpose |
| --- | --- | --- |
| `commit` | `/commit` | Validate changes, create conventional commits, push branches, and open or update pull requests |
| `implement` | `/implement` | Execute a spec or clear request end-to-end, from planning through implementation and validation |
| `pr-feedback` | `/pr-feedback` | Address PR feedback from reviews, CI, and code analysis tools |
| `pr-resolve` | `/pr-resolve` | Reply to and resolve PR review threads |
| `pr-consolidate` | `/pr-consolidate` | Consolidate multiple PRs or branches into a unified integration branch |
| `review` | `/review` | Run a structured code review of staged or recently implemented changes |
| `spec` | `/spec` | Produce `spec.md` (what + why) and `plan.md` (how) under `specs/{NNN-slug}/` |
| `tt` | `/tt` | Log or update a Harvest time entry for current work, linked to an ADO item |
| `story` | `/story` | Create a user story, issue, or bug in Azure DevOps |
| `research` | `/research` | Conduct deep technical research using documentation, search, and GitHub resources |
| `pr-review` | `/pr-review` | Review someone else's PR by number and draft/post feedback with approval |
| `pr-authoring` | `/pr-authoring` | Write concise, motivation-led pull request descriptions |
| `upgrade` | `/upgrade` | Safely upgrade dependencies with research, risk assessment, and validation |
| `code-authoring` | `/code-authoring` | Implementation methodology: prepare, implement, test, self-review, and validate |
| `agents-md-authoring` | `/agents-md-authoring` | Author AGENTS.md / CLAUDE.md project-wide context files |
| `skill-authoring` | `/skill-authoring` | Author, split, and tune SKILL.md files and skill folders |
| `autonomous-loops` | `/autonomous-loops` | Run iterative loops against asynchronous external evaluators such as CI or deploys |
| `code-quality-standards` | `/code-quality-standards` | Detailed Next.js, React, and TypeScript code quality review standards |
| `design-review-standards` | `/design-review-standards` | UI/UX and accessibility review standards for brand, responsive design, and conversion |
| `ecommerce-patterns` | `/ecommerce-patterns` | Cart, checkout, payments, orders, and conversion patterns for React/Next.js apps |
| `playwright-e2e` | `/playwright-e2e` | Playwright end-to-end testing: Page Object Models, locators, and monorepo setup |
| `seo-aeo-structured-data` | `/seo-aeo-structured-data` | SEO, AEO, structured data, metadata, sitemap, and Core Web Vitals guidance |

When you already have a spec in `specs/{NNN-slug}/`, use `/implement spec NNN` to execute it end-to-end. For ad-hoc implementation requests without a spec, describe the work directly or invoke `/implement`.

## Fragments

Reusable prompt fragments for specialized workflows.

| Fragment | Purpose |
| --- | --- |
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

Each tool reads skills from its own user-level folder. `setup-skills-link.ps1` symlinks every one of them back to this repository's `skills/` directory, so a single edit here reaches all tools.

| Tool                          | User-level skills folder |
| ----------------------------- | ------------------------ |
| GitHub Copilot (VS Code, CLI) | `~/.copilot/skills/`     |
| Claude Code                   | `~/.claude/skills/`      |
| opencode and similar          | `~/.agents/skills/`      |

1. Ensure VS Code 1.106+ with GitHub Copilot, and/or Claude Code
2. Run `setup-skills-link.ps1` (as Admin or with Developer Mode enabled)
3. Skills auto-load when relevant and can be invoked explicitly via `/name` in chat

The script is idempotent and never replaces anything without asking: a link already pointing at this repository is left alone, a link pointing elsewhere prompts before replacement, and a real directory is listed and confirmed before being renamed to `<name>_old`. Decline any target you don't want — `~/.agents/skills/` in particular may already be managed by another skill installer.

### Cross-Tool Authoring Notes

Skills here target the lowest common denominator so they work everywhere:

- `name` and `description` are the only required and universally-honored frontmatter keys
- Directory names match the frontmatter `name`
- Tool references are described as capabilities (e.g. "Context7 docs", "IDE diagnostics") rather than literal tool IDs, which differ per host
- Cross-references are **skill-relative** (`../other-skill/SKILL.md`), never repo-root-relative — the tree is symlinked into user-level folders where no repo root exists
- `skills/pr-scripts/` holds shared PowerShell helpers rather than a skill. `README.md` there is the script inventory; `REFERENCE.md` is the shared agent-facing usage, decision matrix, and reply templates that `pr-feedback`, `pr-resolve`, and `pr-review` all link to

### Progressive Disclosure

Large skills keep `SKILL.md` lean and push detail into a `references/` subfolder, which loads
only when `SKILL.md` points at it. `SKILL.md` carries the workflow, decisions, and pitfalls;
`references/` carries code libraries, command tables, and long worked examples. Currently used
by `ecommerce-patterns`, `seo-aeo-structured-data`, `story`, and `upgrade`.

### Host-Specific Frontmatter

Claude Code accepts extra frontmatter keys; other hosts ignore unknown keys, so using them does
not break portability. Several skills set them:

| Key                        | Used for                                                       |
| -------------------------- | -------------------------------------------------------------- |
| `model`                    | Pinning a cheaper tier on mechanical skills (`commit`, `tt`, `story`, `pr-resolve`, `pr-authoring`) |
| `effort`                   | Tuning reasoning depth without changing model tier             |
| `disable-model-invocation` | User-typed `/name` only (`pr-consolidate`, whose merges are destructive) |

Skills that are *consumed inside another task* rather than invoked directly — the standards and
pattern skills — deliberately set no `model`, so they inherit whatever the calling workflow uses.
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
