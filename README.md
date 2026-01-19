# Agentic Coding Agents

A collection of VS Code Custom Agents designed for reliable agentic coding workflows with seamless handoffs between specialized agents.

## Agents

| Agent             | Purpose                                                         | Model                            | Handoffs To        |
| ----------------- | --------------------------------------------------------------- | -------------------------------- | ------------------ |
| `@refine`         | Refine and clarify user input into a comprehensive prompt       | Gemini 3 Pro (Preview) (copilot) | plan, exec, tweak  |
| `@plan`           | Create a detailed implementation plan                           | Claude Opus 4.5 (copilot)        | exec               |
| `@exec`           | Execute comprehensive implementations end-to-end                | Claude Opus 4.5 (copilot)        | review, commit     |
| `@tweak`          | Execute small, focused modifications without structural changes | Claude Opus 4.5 (copilot)        | review, commit     |
| `@review`         | Code review for correctness, maintainability, and quality       | Claude Opus 4.5 (copilot)        | commit, tweak      |
| `@pr-feedback`    | Address PR feedback from reviews, CI, and analysis tools        | Claude Opus 4.5 (copilot)        | pr-resolve, commit |
| `@pr-resolve`     | Reply to and resolve PR review threads via GH CLI               | Claude Opus 4.5 (copilot)        | commit             |
| `@pr-consolidate` | Consolidate multiple PRs or branches into a unified branch      | Claude Opus 4.5 (copilot)        | commit             |
| `@commit`         | Commit, push, and create/update pull request                    | Claude Opus 4.5 (copilot)        | pr-feedback        |
| `@summarize`      | Compress conversation history into an actionable summary        | Claude Sonnet 4.5 (copilot)      | exec               |
| `@research`       | Deep technical research and option evaluation                   | Claude Opus 4.5 (copilot)        | plan, exec         |
| `@upgrade`        | Review and upgrade dependencies safely end-to-end               | Claude Opus 4.5 (copilot)        | commit, review     |
| `@agents`         | Analyze codebase and create/update AGENTS.md and SKILL.md files | Claude Opus 4.5 (copilot)        | commit             |
| `@story`          | Create a new user story, issue, or bug in Azure DevOps          | Claude Opus 4.5 (copilot)        | plan               |

## Handoffs

Agents now support **handoffs**—interactive buttons that appear after an agent completes, allowing you to seamlessly transition to the next agent in the workflow with pre-filled context. This enables guided, step-by-step development flows.

Example handoff flow:

```
@refine → [Create Plan] → @plan → [Implement Plan] → @exec → [Review Changes] → @review → [Commit & PR] → @commit
```

## Fragments

Reusable prompt fragments for specialized workflows:

| Fragment              | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `snyk-upgrade-review` | Review and complete Snyk dependency upgrade PRs |

## Workflow

### Standard Feature Development

```
@refine → @plan → @exec → @review → @commit
```

1. **Refine**: Start with your idea, get clarifying questions answered → click **"Create Plan"**
2. **Plan**: Generate a detailed implementation plan with research → click **"Implement Plan"**
3. **Exec**: Implement the feature completely with tests → click **"Review Changes"**
4. **Review**: Get a senior engineer review of the code → click **"Commit & PR"**
5. **Commit**: Create branch, commit, and open PR

### PR Feedback Loop

After receiving review feedback:

```
@pr-feedback → @pr-resolve
```

1. **Feedback**: Address all review comments locally → click **"Resolve Threads"**
2. **Resolve**: Reply to and resolve threads, then push

Repeat until approved.

### Quick Fixes

```
@refine → @tweak → @commit
```

Or for obvious changes:

```
@tweak → @commit
```

### Direct Implementation (Clear Requirements)

```
@exec → @review → @commit
```

### Branch Consolidation

When merging multiple PRs or agent branches:

```
@pr-consolidate → @commit
```

1. **Consolidate**: Merge multiple PRs/branches, resolve conflicts → click **"Commit & PR"**
2. **Commit**: Create unified PR with references to closed PRs

Use cases:

- Merge overlapping PRs before review
- Combine independent agent work
- Incorporate PR dependencies into current branch

## Setup

1. Ensure VS Code 1.106+ (custom agents support)
2. Copy the `.github/agents/` folder to your project root
3. Agents will appear in the agents dropdown in Copilot Chat (use `@agent-name`)

## Customization

### Model Selection

Update the `model` field in each agent's frontmatter to match your preferred model IDs.

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced in agents that benefit from research capabilities. If you don't have these configured, remove those tool references—the agents will still work with reduced functionality.

### Handoffs

Customize handoffs in the YAML frontmatter of each agent:

```yaml
handoffs:
  - label: Button Text
    agent: target-agent-name
    prompt: Context to pass to the next agent.
    send: false # true = auto-submit, false = pre-fill only
```

### Extending Agents

You can reference shared instructions using Markdown links:

```markdown
See [coding-standards](../instructions/coding-standards.md) for style guidelines.
```

## Requirements

- VS Code 1.106+ with GitHub Copilot
- Recommended: Claude Opus 4.5 access (for `@exec` and `@review`)
- Optional: MCP servers (Context7, Perplexity, GitHub)
