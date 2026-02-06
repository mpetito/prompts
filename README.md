# Agentic Coding Toolkit

A collection of VS Code custom agents, prompts, and skills for reliable agentic coding workflows.

## Agents

Specialized AI personas with tool access, model selection, and handoffs. Switch agents via the agent picker in Copilot Chat.

| Agent         | Purpose                                                        | Handoffs To |
| ------------- | -------------------------------------------------------------- | ----------- |
| `@exec`       | Execute comprehensive implementation tasks end-to-end          | review      |
| `@plan`       | Create a detailed implementation plan with research            | exec        |
| `@research`   | Deep technical research and option evaluation                  | plan, exec  |
| `@review`     | Code review for correctness, maintainability, and quality      | —           |
| `@agentic-dx` | Analyze codebases and create/update AGENTS.md, prompts, skills | —           |

## Prompts

Reusable task templates invoked on-demand via `/name` in chat. Run within any agent session.

| Prompt            | Purpose                                                                |
| ----------------- | ---------------------------------------------------------------------- |
| `/refine`         | Refine and clarify user input into a comprehensive prompt              |
| `/commit`         | Commit changes with conventional messages and create/update PR         |
| `/tweak`          | Execute small, focused modifications without structural changes        |
| `/summarize`      | Compress conversation history into an actionable summary               |
| `/story`          | Create a new user story, issue, or bug in Azure DevOps                 |
| `/upgrade`        | Review and upgrade outdated dependencies safely                        |
| `/pr-feedback`    | Address PR feedback from reviews, CI, and code analysis tools          |
| `/pr-resolve`     | Reply to and resolve PR review threads                                 |
| `/pr-consolidate` | Consolidate multiple PRs or branches into a unified integration branch |

## Skills

Auto-discovered procedures loaded on-demand when relevant to the user's task. Stored in `skills/` and symlinked to `~/.copilot/skills/`.

| Skill             | Purpose                                                         |
| ----------------- | --------------------------------------------------------------- |
| `agent-authoring` | Methodology for creating AGENTS.md and SKILL.md files           |
| `pr-management`   | PR review lifecycle: feedback, thread resolution, consolidation |
| `research`        | Deep technical research using Perplexity and documentation      |
| `story-writing`   | User story and work item creation for Azure DevOps              |
| `upgrade`         | Dependency upgrade workflow with validation                     |

## Fragments

Reusable prompt fragments for specialized workflows:

| Fragment              | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `snyk-upgrade-review` | Review and complete Snyk dependency upgrade PRs |

## Workflows

### Standard Feature Development

```
/refine → @plan → @exec → @review → /commit
```

1. **Refine** (`/refine`): Clarify requirements and generate a comprehensive prompt
2. **Plan** (`@plan`): Generate a detailed implementation plan → handoff to exec
3. **Exec** (`@exec`): Implement the feature with tests → handoff to review
4. **Review** (`@review`): Code review for correctness and quality
5. **Commit** (`/commit`): Create branch, commit, and open PR

### PR Feedback Loop

```
/pr-feedback → /pr-resolve → /commit
```

1. **Feedback** (`/pr-feedback`): Address review comments locally
2. **Resolve** (`/pr-resolve`): Reply to and resolve threads, then push
3. **Commit** (`/commit`): Push changes and update PR

Repeat until approved.

### Quick Fixes

```
/refine → /tweak → /commit
```

Or for obvious changes: `/tweak` → `/commit`

### Direct Implementation (Clear Requirements)

```
@exec → @review → /commit
```

### Dependency Upgrade

```
/upgrade → /commit
```

### Branch Consolidation

```
/pr-consolidate → /commit
```

## Setup

1. Ensure VS Code 1.106+ with GitHub Copilot
2. Run `setup-prompts-link.ps1` (as Admin or with Developer Mode enabled) to symlink:
   - `prompts/` → VS Code user prompts folder
   - `skills/` → `~/.copilot/skills/`
3. Agents appear in the agent picker; prompts are invoked via `/name` in chat

## Customization

### Model Selection

Update the `model` field in each agent's YAML frontmatter.

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced in agents that benefit from research capabilities. Remove those tool references if not configured—agents still work with reduced functionality.

### Handoffs (Agents only)

```yaml
handoffs:
  - label: Button Text
    agent: target-agent-name
    prompt: Context to pass to the next agent.
    send: false # true = auto-submit, false = pre-fill only
```

## Requirements

- VS Code 1.106+ with GitHub Copilot
- Recommended: Claude Opus 4.6 access (for `@exec` and `@review`)
- Optional: MCP servers (Context7, Perplexity, GitHub)
