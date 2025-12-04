# Agentic Coding Prompts

A collection of VS Code prompt files designed for reliable agentic coding workflows.

## Prompts

| Prompt    | Purpose                                                   | Model           |
| --------- | --------------------------------------------------------- | --------------- |
| `/refine` | Clarify ambiguous requests into actionable specifications | Gemini 3 Pro    |
| `/plan`   | Research and create detailed implementation plans         | Gemini 3 Pro    |
| `/exec`   | Execute comprehensive implementations end-to-end          | Claude Opus 4.5 |
| `/tweak`  | Make small, focused modifications                         | Gemini 3 Pro    |
| `/review` | Senior engineer code review                               | Claude Opus 4.5 |
| `/commit` | Branch, commit, push, and create PR                       | Gemini 3 Pro    |

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
