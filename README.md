# Agentic Coding Toolkit

A collection of Copilot skills for reliable agentic coding workflows.

Skills are the single unit of reusable workflow guidance in this repository: they auto-load when relevant and VS Code exposes each skill as an explicit `/name` entry point. There is no separate `prompts/` concept; former prompt slugs are preserved as skill names.

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
| `agent-authoring` | `/agent-authoring` | Author AGENTS.md files, SKILL.md files, and agentic coding instructions |
| `autonomous-loops` | `/autonomous-loops` | Run iterative loops against asynchronous external evaluators such as CI or deploys |
| `code-quality-standards` | `/code-quality-standards` | Detailed Next.js, React, and TypeScript code quality review standards |
| `design-review-standards` | `/design-review-standards` | UI/UX review standards for brand, accessibility, responsive design, and conversion |
| `ecommerce-patterns` | `/ecommerce-patterns` | Cart, checkout, payments, orders, and conversion patterns for React/Next.js apps |
| `playwright-e2e-monorepo` | `/playwright-e2e-monorepo` | Playwright end-to-end setup with Page Object Models in an npm monorepo |
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

### VS Code + GitHub Copilot (Windows)

1. Ensure VS Code 1.106+ with GitHub Copilot
2. Run `setup-skills-link.ps1` (as Admin or with Developer Mode enabled) to symlink `skills/` → `~/.copilot/skills/`
3. Skills auto-load when relevant and can be invoked explicitly via `/name` in chat

### Cross-Tool Skills (WSL / Linux / macOS)

For tools that support the generalized `~/.agents/skills/` convention (e.g., opencode, Claude Code):

1. Run `./setup-opencode.sh` to symlink `skills/` → `~/.agents/skills/`
2. Skills are auto-discovered by any compatible tool

## Customization

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced from skills that benefit from research or PR capabilities. Skills still work with reduced functionality if those tools are not configured.

### Skill Descriptions

Skills auto-load based on their `description` frontmatter. To make a skill trigger on different phrasing, edit its description to include the trigger phrases you use.

## Requirements

- VS Code 1.106+ with GitHub Copilot
- Optional: MCP servers (Context7, Perplexity, GitHub) for richer research and PR workflows
