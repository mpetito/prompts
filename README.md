# Agentic Coding Prompts

A collection of VS Code prompt files designed for reliable agentic coding workflows.

## Prompts

| Prompt       | Purpose                                                         | Model                            |
| ------------ | --------------------------------------------------------------- | -------------------------------- |
| `/refine`    | Refine and clarify user input into a comprehensive prompt       | Gemini 3 Pro (Preview) (copilot) |
| `/plan`      | Create a detailed implementation plan                           | Claude Opus 4.5 (copilot)        |
| `/exec`      | Execute comprehensive implementations end-to-end                | Claude Opus 4.5 (copilot)        |
| `/tweak`     | Execute small, focused modifications without structural changes | GPT-5.1-Codex-Max (copilot)      |
| `/review`    | Code review for correctness, maintainability, and quality       | Claude Opus 4.5 (copilot)        |
| `/feedback`  | Address PR feedback from reviews, CI, and analysis tools        | Claude Opus 4.5 (copilot)        |
| `/resolve`   | Reply to and resolve PR review threads via GH CLI               | GPT-5.1-Codex-Max (Preview)      |
| `/commit`    | Commit, push, and create/update pull request                    | Claude Sonnet 4.5 (copilot)      |
| `/summarize` | Compress conversation history into an actionable summary        | Claude Sonnet 4.5 (copilot)      |
| `/research`  | Deep technical research and option evaluation                   | Claude Opus 4.5 (copilot)        |
| `/upgrade`   | Review and upgrade dependencies safely end-to-end               | GPT-5.1-Codex-Max (copilot)      |

## Fragments

Reusable prompt fragments for specialized workflows:

| Fragment              | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `snyk-upgrade-review` | Review and complete Snyk dependency upgrade PRs |

## Workflow

### Standard Feature Development

```
/refine → /plan → /exec → /review → /commit
```

1. **Refine**: Start with your idea, get clarifying questions answered
2. **Plan**: Generate a detailed implementation plan with research
3. **Exec**: Implement the feature completely with tests
4. **Review**: Get a senior engineer review of the code
5. **Commit**: Create branch, commit, and open PR

### PR Feedback Loop

After receiving review feedback:

```
/feedback → /resolve
```

1. **Feedback**: Address all review comments locally, present summary for confirmation
2. **Resolve**: After confirmation, commit/push and reply to/resolve threads

Repeat until approved.

### Quick Fixes

```
/refine → /tweak → /commit
```

Or for obvious changes:

```
/tweak → /commit
```

### Direct Implementation (Clear Requirements)

```
/exec → /review → /commit
```

## Setup

1. Ensure `chat.promptFiles` is enabled in VS Code settings
2. Copy the `.github/prompts/` folder to your project root
3. Prompts will appear when typing `/` in Copilot Chat

## Customization

### Model Selection

Update the `model` field in each prompt's frontmatter to match your preferred model IDs.

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced in prompts that benefit from research capabilities. If you don't have these configured, remove those tool references—the prompts will still work with reduced functionality.

### Extending Prompts

You can reference shared instructions using Markdown links:

```markdown
See [coding-standards](../instructions/coding-standards.md) for style guidelines.
```

## Requirements

- VS Code with GitHub Copilot
- Recommended: Claude Opus 4.5 access (for `/exec` and `/review`)
- Optional: MCP servers (Context7, Perplexity, GitHub)
