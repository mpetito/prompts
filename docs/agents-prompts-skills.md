# VS Code Copilot: Agents, Prompts, and Skills Research

**Date**: 2025-01-19  
**Purpose**: Evaluate recategorization of current agent files to better utilize prompts and skills

## Concepts Overview

### Agents (`.agent.md`)

**Definition**: Specialized AI personas that combine instructions with specific tools, model selection, and optional handoffs for workflow transitions.

**Key characteristics**:

- Stored in `.github/agents/` (workspace) or user profile
- Configure which **tools are available** for the agent
- Specify a **language model** to use
- Include **handoffs** to transition between agents
- Invoked by **switching agents** in the agent picker

**Best for**: Mode-switching workflows where you need a distinct persona with specific capabilities.

### Prompts (`.prompt.md`)

**Definition**: Reusable task templates for common development tasks that you run on-demand in chat.

**Key characteristics**:

- Stored in `.github/prompts/` (workspace) or user profile
- Invoked via **`/promptname`** in chat or Command Palette
- Can specify an **agent** to run with (inherits that agent's tools)
- Can specify **tools** available for the prompt
- Support **variables** like `${selection}`, `${file}`, `${input:variableName}`

**Best for**: Standardized, repeatable tasks that can be invoked from within any agent session.

### Skills (`SKILL.md`)

**Definition**: Folders of instructions, scripts, and resources that Copilot loads automatically when relevant.

**Key characteristics**:

- Stored in `.github/skills/<skill-name>/` (workspace) or `~/.copilot/skills/<skill-name>/` (user)
- Defined via `SKILL.md` with YAML frontmatter (`name` + `description` required)
- **Automatically discovered** based on prompt relevance (progressive disclosure)
- Can include supporting scripts, examples, and reference files
- Portable across VS Code, GitHub Copilot CLI, and GitHub Copilot coding agent

**Best for**: Bounded procedures with supporting resources that should auto-load when relevant.

### Custom Instructions (`.instructions.md`)

**Definition**: Coding guidelines that automatically apply based on file patterns.

**Key characteristics**:

- Stored in `.github/instructions/` or `.github/copilot-instructions.md`
- Use `applyTo` glob patterns for conditional application
- **Automatically applied** based on file context
- Do not define tools or agents

**Best for**: Project-wide coding standards that should always apply.

## Comparison Table

| Feature                   | Agents                  | Prompts                 | Skills                       | Instructions            |
| ------------------------- | ----------------------- | ----------------------- | ---------------------------- | ----------------------- |
| **Primary Purpose**       | Specialized AI personas | Reusable task templates | Auto-discovered procedures   | Coding standards        |
| **File Extension**        | `.agent.md`             | `.prompt.md`            | `SKILL.md`                   | `.instructions.md`      |
| **Tool Access**           | ✅ Explicit tool list   | ✅ Can specify tools    | ❌ No direct tool access     | ❌ No                   |
| **Model Selection**       | ✅ Yes                  | ✅ Yes                  | ❌ No                        | ❌ No                   |
| **Invocation**            | Switch via agent picker | Type `/name` in chat    | Automatic (on-demand)        | Automatic (via glob)    |
| **Discovery**             | Manual selection        | Manual (`/`) invocation | Auto-discovered by relevance | Auto-applied by context |
| **Can Include Resources** | ❌ Instructions only    | ❌ Instructions only    | ✅ Scripts, examples, docs   | ❌ Instructions only    |
| **Handoffs**              | ✅ Yes                  | ❌ No                   | ❌ No                        | ❌ No                   |
| **Portability**           | VS Code only            | VS Code & GitHub.com    | Open standard (cross-agent)  | VS Code & GitHub.com    |

## Decision Framework

| Use **Agent** when...               | Use **Prompt** when...                   | Use **Skill** when...                     |
| ----------------------------------- | ---------------------------------------- | ----------------------------------------- |
| Need a specialized **persona/mode** | Need a **repeatable task template**      | Need **auto-discovery** by relevance      |
| Need specific **tool restrictions** | Task runs **on-demand** via `/name`      | Procedure includes **supporting files**   |
| Need **model selection**            | Want to **standardize** common workflows | Task is **bounded** with clear completion |
| Need **handoffs** between modes     | Flexibility to run **within any agent**  | Want **portability** across tools         |

## Recommendations for Current Agents

### Keep as Agents ✅

These need persona switching, specific tools, handoffs, or model selection:

| Agent              | Rationale                                                                           |
| ------------------ | ----------------------------------------------------------------------------------- |
| **exec**           | Core implementation coordinator—needs full tool access, handoffs to review/commit   |
| **plan**           | Architectural planning requires specific tools (perplexity, docs), handoffs to exec |
| **research**       | Deep research mode with specific tools, handoffs to plan/exec                       |
| **review**         | Review persona with restricted tools, handoffs to commit/tweak                      |
| **commit**         | Git workflow persona with GitHub tools, handoffs to pr-feedback                     |
| **pr-feedback**    | PR workflow requiring GitHub PR tools, handoffs to pr-resolve/commit                |
| **pr-resolve**     | PR thread resolution requiring GitHub PR tools                                      |
| **pr-consolidate** | Complex git operations requiring specific tools                                     |
| **upgrade**        | Dependency management mode with validation tools                                    |

### Convert to Prompts 📝

These are task-oriented and would work well as `/name` invocations within any agent:

| Current Agent | → Prompt              | Rationale                                                                          |
| ------------- | --------------------- | ---------------------------------------------------------------------------------- |
| **refine**    | `refine.prompt.md`    | Task-oriented clarification. `/refine` usable within any agent session.            |
| **tweak**     | `tweak.prompt.md`     | Simple task template for small changes. `/tweak` from within exec or other agents. |
| **story**     | `story.prompt.md`     | Work item creation is a discrete task. `/story` to create items from any context.  |
| **summarize** | `summarize.prompt.md` | Conversation summarization utility. `/summarize` at end of any session.            |

### Convert to Skills 🔧

This is a perfect skill candidate with supporting resources:

| Current Agent | → Skill                      | Rationale                                                                                                                                            |
| ------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| **agents**    | `agents-md-creator/SKILL.md` | Bounded procedure for creating AGENTS.md/SKILL.md. Auto-discovered when user mentions "create AGENTS.md". Can include templates as supporting files. |

## Folder Structure

Given the symbolic link setup in this repository, we need flat folder structures:

```
prompts/                              # Symlinked to VS Code user profile
├── exec.agent.md                     # Agents (personas)
├── plan.agent.md
├── research.agent.md
├── review.agent.md
├── commit.agent.md
├── pr-feedback.agent.md
├── pr-resolve.agent.md
├── pr-consolidate.agent.md
├── upgrade.agent.md
├── refine.prompt.md                  # Prompts (task templates)
├── tweak.prompt.md
├── story.prompt.md
├── summarize.prompt.md
└── mcp.toolsets.jsonc

skills/                               # Symlinked to ~/.copilot/skills/
└── agents-md-creator/
    ├── SKILL.md
    └── templates/
        ├── agents-md-template.md
        └── skill-md-template.md
```

**Note**: The PowerShell setup script will need to be updated to:

1. Map `skills/` folder contents to `~/.copilot/skills/` (outside VS Code user folder, inside Windows profile home)
2. Enable the `chat.useAgentSkills` setting if using skills (currently Preview)

## Prompt Conversion Notes

When converting agents to prompts:

1. **Rename** from `.agent.md` to `.prompt.md`
2. **Update frontmatter**:
   ```yaml
   ---
   name: refine
   description: Refine and clarify user input into a comprehensive prompt
   agent: agent # Optional: specify agent for tool access
   tools: ["search", "read"] # Optional: tool restrictions
   ---
   ```
3. **Remove** `handoffs` (prompts don't support them)
4. **Remove** `model` (prompts inherit from current agent)
5. **Add "Next Steps" guidance** in output section to replace handoff functionality

## Skill Conversion Notes

When converting to a skill:

1. **Create folder** in `skills/<skill-name>/`
2. **Create SKILL.md** with trigger-clear description:
   ```yaml
   ---
   name: agents-md-creator
   description: |
     Guide for creating AGENTS.md and SKILL.md files. Use when the user asks to 
     create agent configuration files, improve agentic coding experience, or 
     set up AGENTS.md for a repository.
   ---
   ```
3. **Extract templates** into supporting files in the skill folder
4. **Reference supporting files** from SKILL.md body

## Trade-offs

| Change                                   | Benefit                                 | Cost                                           |
| ---------------------------------------- | --------------------------------------- | ---------------------------------------------- |
| Prompts for refine/tweak/story/summarize | Usable **within** any agent via `/name` | Lose handoffs (must manually invoke next step) |
| Skill for agents-md-creator              | Auto-discovery when relevant, portable  | Requires preview setting, script update        |
| Fewer agents                             | Cleaner agent picker, clearer purpose   | More manual navigation                         |

## Open Questions

1. **Prompt tool access**: Should prompts specify `agent: exec` to get implementation tools, or remain tool-agnostic?
2. **Skill preview**: Comfortable enabling `chat.useAgentSkills` preview setting?
3. **Handoff replacement**: For converted prompts, add "Next Steps" section to guide users, or trust they know the workflow?

## References

| Document              | URL                                                                          |
| --------------------- | ---------------------------------------------------------------------------- |
| Custom agents         | https://code.visualstudio.com/docs/copilot/customization/custom-agents       |
| Prompt files          | https://code.visualstudio.com/docs/copilot/customization/prompt-files        |
| Agent Skills          | https://code.visualstudio.com/docs/copilot/customization/agent-skills        |
| Custom instructions   | https://code.visualstudio.com/docs/copilot/customization/custom-instructions |
| Agent Skills Standard | https://agentskills.io/                                                      |
