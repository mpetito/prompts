# Agentic Coding Toolkit

A collection of VS Code prompts and skills for reliable agentic coding workflows.

Skills capture procedural knowledge and load on-demand when relevant; prompts are the explicit entry points you invoke via `/name` in chat. There are no custom agents — auto tool-narrowing and auto model routing make persona-switching unnecessary.

## Prompts

Reusable task entry points invoked via `/name` in chat.

| Prompt            | Purpose                                                                      | Activates Skill                   |
| ----------------- | ---------------------------------------------------------------------------- | --------------------------------- |
| `/refine`         | Refine and clarify user input into a comprehensive prompt                    | —                                 |
| `/research`       | Deep technical research and option evaluation                                | `research`                        |
| `/spec`           | Produce `spec.md` (what + why) and `plan.md` (how) under `specs/{NNN-slug}/` | `spec-planning`                   |
| `/implement`      | Execute a spec end-to-end: apply clarifications, create/review plan, build   | `spec-planning`, `code-authoring` |
| `/review`         | Structured code review of staged or just-implemented changes                 | `code-review`                     |
| `/tweak`          | Small, surgical modifications without structural changes                     | —                                 |
| `/commit`         | Validate, commit with conventional messages, push, and open/update a PR      | `pr-authoring`                    |
| `/summarize`      | Compress conversation history into an actionable summary                     | —                                 |
| `/story`          | Create a user story, issue, or bug in Azure DevOps                           | `story-writing`                   |
| `/upgrade`        | Review and upgrade outdated dependencies safely                              | `upgrade`                         |
| `/pr-review`      | Review someone else's PR by number; collaboratively draft and post comments  | `pr-review`                       |
| `/pr-feedback`    | Address PR feedback from reviews, CI, and code analysis tools                | `pr-management`                   |
| `/pr-resolve`     | Reply to and resolve PR review threads                                       | `pr-management`                   |
| `/pr-consolidate` | Consolidate multiple PRs or branches into a unified integration branch       | `pr-management`                   |
| `/tt`             | Log or update a Harvest time entry for current work, linked to an ADO item    | `time-tracking`                   |

When you already have a spec in `specs/{NNN-slug}/`, use `/implement spec NNN` to execute it end-to-end. For ad-hoc implementation requests without a spec, just describe the work — the `code-authoring` skill picks up automatically.

## Skills

Auto-discovered procedures loaded on-demand when the user's task matches the skill description. Stored in `skills/` and symlinked to `~/.copilot/skills/`.

| Skill                     | Purpose                                                                     |
| ------------------------- | --------------------------------------------------------------------------- |
| `code-authoring`          | Implementation methodology: prepare, implement, test, self-review, validate |
| `spec-planning`           | Produce `spec.md` + `plan.md` for non-trivial features                      |
| `code-review`             | Multi-dimensional code review methodology and verdict format                |
| `research`                | Deep technical research using docs, Perplexity, and GitHub                  |
| `agent-authoring`         | Authoring AGENTS.md and SKILL.md files                                      |
| `pr-management`           | PR review lifecycle: feedback, thread resolution, consolidation             |
| `pr-review`               | Review another author's PR; draft feedback, post only after user approval   |
| `pr-authoring`            | Writing concise, motivation-led PR descriptions                             |
| `story-writing`           | User story and work item creation for Azure DevOps                          |
| `upgrade`                 | Dependency upgrade workflow with validation                                 |
| `code-quality-standards`  | Detailed Next.js / React / TypeScript code quality reference                |
| `design-review-standards` | UI/UX review reference                                                      |
| `ecommerce-patterns`      | Cart, checkout, payments, and order patterns for Next.js                    |
| `playwright-e2e-monorepo` | Playwright e2e setup with POM in an npm monorepo                            |
| `seo-aeo-structured-data` | SEO, AEO, and structured data implementation                                |
| `autonomous-loops`        | Iterative agent loops against async external evaluators (CI, PSI, deploys)  |
| `time-tracking`           | Log/update Harvest time entries linked to ADO work items (create, never delete) |

## Fragments

Reusable prompt fragments for specialized workflows.

| Fragment              | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `snyk-upgrade-review` | Review and complete Snyk dependency upgrade PRs |

## Workflows

### Standard Feature Development

```
/refine → /spec → /implement spec NNN → /review → /commit
```

1. **Refine** (`/refine`): clarify requirements into a comprehensive prompt
2. **Spec** (`/spec`): produce `spec.md` + `plan.md` under `specs/{NNN-slug}/`
3. **Implement** (`/implement spec NNN`): apply any clarifications, create or review the plan, build all phases
4. **Review** (`/review`): independent quality pass
5. **Commit** (`/commit`): branch, commit, push, open/update PR

### Direct Implementation (Clear Requirements, No Spec)

```
(describe the work) → /review → /commit
```

### Quick Fixes

```
/tweak → /commit
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
2. Run `setup-prompts-link.ps1` (as Admin or with Developer Mode enabled) to symlink:
   - `prompts/` → VS Code user prompts folder
   - `skills/` → `~/.copilot/skills/`
3. Prompts are invoked via `/name` in chat; skills activate automatically when relevant

### Cross-Tool Skills (WSL / Linux / macOS)

For tools that support the generalized `~/.agents/skills/` convention (e.g., opencode, Claude Code):

1. Run `./setup-opencode.sh` to symlink `skills/` → `~/.agents/skills/`
2. Skills are auto-discovered by any compatible tool

**Note:** The prompts in `prompts/` use VS Code Copilot-specific context variables (`#changes`, `#problems`) and are not converted for cross-tool use. They remain VS Code Copilot-only.

## Customization

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced from skills that benefit from research or PR capabilities. Skills still work with reduced functionality if those tools are not configured.

### Skill Descriptions

Skills auto-load based on their `description` frontmatter. To make a skill trigger on different phrasing, edit its description to include the trigger phrases you use.

## Requirements

- VS Code 1.106+ with GitHub Copilot
- Optional: MCP servers (Context7, Perplexity, GitHub) for richer research and PR workflows
