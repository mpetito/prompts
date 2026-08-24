# VS Code Copilot: Agents and Skills Research

**Date**: 2025-01-19  
**Status update**: 2026-07-13 — this repository has consolidated prompt files into skills. Skills are now the single reusable workflow unit: they can auto-load when relevant and VS Code exposes each skill as a `/name` command.  
**Purpose**: Record the concepts and repository direction for agents and skills.

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

### Skills (`SKILL.md`)

**Definition**: Folders of instructions, scripts, and resources that Copilot loads automatically when relevant. In this repository, skills also preserve the former slash-command entry points, so each skill can be invoked explicitly via **`/skill-name`** in VS Code.

**Key characteristics**:

- Stored in `.github/skills/<skill-name>/` (workspace) or `~/.copilot/skills/<skill-name>/` (user)
- Defined via `SKILL.md` with YAML frontmatter (`name` + `description` required)
- **Automatically discovered** based on prompt relevance (progressive disclosure)
- **Explicitly invocable** by slash command in VS Code using the skill name
- Can include supporting scripts, examples, and reference files
- Portable across VS Code, GitHub Copilot CLI, and GitHub Copilot coding agent

**Correction (2026-07-26)**: an earlier revision of this document stated that skills cannot
select a model or restrict tools. That is no longer accurate for Claude Code, which accepts
`model`, `effort`, `allowed-tools`, `disable-model-invocation`, `argument-hint`, `context`, and
`agent` in `SKILL.md` frontmatter. Other hosts ignore unknown keys, so these are additive rather
than portability-breaking — but they only take effect in Claude Code. See the `skill-authoring`
skill for the full list and selection guidance.

**Best for**: Bounded procedures with supporting resources that should auto-load when relevant while remaining callable on demand.

### Legacy Prompt Files (`.prompt.md`)

**Definition**: VS Code supports reusable prompt files for common development tasks, invoked on demand in chat.

**Repository status**: This repository no longer keeps prompt files as a separate workflow layer. Former prompt tasks such as `implement`, `review`, and `commit` have been converted to skills with the same slash-command slugs.

### Custom Instructions (`.instructions.md`)

**Definition**: Coding guidelines that automatically apply based on file patterns.

**Key characteristics**:

- Stored in `.github/instructions/` or `.github/copilot-instructions.md`
- Use `applyTo` glob patterns for conditional application
- **Automatically applied** based on file context
- Do not define tools or agents

**Best for**: Project-wide coding standards that should always apply.

## Comparison Table

| Feature | Agents | Skills | Legacy Prompt Files | Instructions |
| --- | --- | --- | --- | --- |
| **Primary Purpose** | Specialized AI personas | Auto-discovered procedures and `/name` task entry points | Reusable task templates | Coding standards |
| **File Extension** | `.agent.md` | `SKILL.md` | `.prompt.md` | `.instructions.md` |
| **Tool Access** | ✅ Explicit tool list | ⚠️ `allowed-tools` in Claude Code; not portable | ✅ Can specify tools | ❌ No |
| **Model Selection** | ✅ Yes | ⚠️ `model` / `effort` in Claude Code; not portable | ✅ Yes | ❌ No |
| **Invocation** | Switch via agent picker | Automatic or `/skill-name` in VS Code | Type `/name` in chat | Automatic (via glob) |
| **Discovery** | Manual selection | Auto-discovered by relevance; visible as slash commands | Manual (`/`) invocation | Auto-applied by context |
| **Can Include Resources** | ❌ Instructions only | ✅ Scripts, examples, docs | ❌ Instructions only | ❌ Instructions only |
| **Handoffs** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Portability** | VS Code only | Open standard (cross-agent) | VS Code & GitHub.com | VS Code & GitHub.com |

## Decision Framework

| Use **Agent** when... | Use **Skill** when... | Use **Instructions** when... |
| --- | --- | --- |
| Need a specialized **persona/mode** | Need a **repeatable task template** invocable by `/name` | Need project-wide standards |
| Need specific **tool restrictions** | Need **auto-discovery** by relevance | Need file-pattern based guidance |
| Need **model selection** | Procedure includes **supporting files** | Guidance should apply quietly |
| Need **handoffs** between modes | Want **portability** across tools | No slash command is needed |

## Current Repository Direction

### Consolidated as Skills ✅

Former prompt-style entry points are now skills so the slug is preserved while the procedure can also auto-load:

| Skill | Rationale |
| --- | --- |
| `implement` | End-to-end implementation can be invoked explicitly or triggered by implementation requests. |
| `review` | Code review methodology is reusable as `/review` and as a review-triggered skill. |
| `commit` | Git/PR authoring workflow remains `/commit` while sharing supporting skill context. |
| `story`, `spec`, `tt` | Renamed skills preserve the existing `/story`, `/spec`, and `/tt` slugs. |

### PR Workflow Split ✅

The former broad PR-management procedure has been split into focused skills:

| Skill | Scope |
| --- | --- |
| `pr-feedback` | Address review, CI, and code-analysis feedback. |
| `pr-resolve` | Reply to and resolve review threads. |
| `pr-consolidate` | Consolidate multiple PRs or branches. |

### Existing Skills Kept ✅

Research, PR review/authorship, upgrades, authoring guidance, autonomous loops, quality/design standards, e-commerce patterns, Playwright, and SEO/AEO structured-data workflows remain skills.

### Authoring Skills Split ✅ (2026-07-26)

`agent-authoring` covered two audiences with two template sets and two checklists. It is now:

| Skill                | Scope                                                      |
| -------------------- | ---------------------------------------------------------- |
| `agents-md-authoring`| AGENTS.md / CLAUDE.md always-loaded project context        |
| `skill-authoring`    | SKILL.md on-demand procedures, frontmatter, and splitting  |

`playwright-e2e-monorepo` was renamed `playwright-e2e`: monorepo wiring is one section of a
skill that is otherwise stack-agnostic.

## Folder Structure

The repository setup links skills for every tool, plus Claude Code subagent definitions and global instructions:

```
skills/                               # Symlinked into each tool's user-level skills folder
└── <skill-name>/
    ├── SKILL.md                      # Workflow, decisions, pitfalls — kept under 500 lines
    ├── references/                   # Loaded on demand: code libraries, command tables, examples
    ├── scripts/                      # Executable helpers (see skills/pr-scripts/)
    └── assets/                       # Files used in output rather than read into context

agents/                               # Symlinked into ~/.claude/agents (Claude Code format only)
└── <agent-name>.md                   # name, description, tools, model, effort, permissionMode,
                                      #   maxTurns, memory, isolation, skills, color

instructions/                         # User-level global instructions
└── CLAUDE.md                         # Symlinked to ~/.claude/CLAUDE.md; always loaded

fragments/                            # Reusable fragments such as snyk-upgrade-review
```

The PowerShell setup script is `setup-skills-link.ps1`. It maps `skills/` to `~/.copilot/skills/` (Copilot), `~/.claude/skills/` (Claude Code), and `~/.agents/skills/` (opencode and other tools using that convention), `agents/` to `~/.claude/agents/`, and `instructions/CLAUDE.md` to `~/.claude/CLAUDE.md`. The last two are not linked into the other tools: their agent and instruction formats are incompatible, so a shared location would be read as malformed rather than ignored.

## Skill Authoring Notes

When adding or converting a workflow, create or rename a skill instead of adding a prompt file:

1. **Create folder** in `skills/<skill-name>/`
2. **Create SKILL.md** with trigger-clear description:
   ```yaml
   ---
   name: agent-authoring
   description: |
     Use when creating AGENTS.md files, writing SKILL.md files, or improving
     agentic coding developer experience.
   ---
   ```
3. **Preserve the slug** by matching the skill folder/name to the intended `/name` command
4. **Extract templates or references** into supporting files in the skill folder
5. **Reference supporting files** from the SKILL.md body

## Trade-offs

| Change | Benefit | Cost |
| --- | --- | --- |
| Consolidate prompts into skills | One source of truth; auto-load plus `/name` invocation; better cross-tool reuse | Skill names must preserve user-facing slash-command slugs |
| Split PR management into focused skills | Smaller procedures with clearer triggers and commands | More skill folders to maintain |
| Keep fragments separate | Lightweight reuse for specialized snippets | Fragments are not full procedures |

## References

| Document | URL |
| --- | --- |
| Custom agents | https://code.visualstudio.com/docs/copilot/customization/custom-agents |
| Prompt files | https://code.visualstudio.com/docs/copilot/customization/prompt-files |
| Agent Skills | https://code.visualstudio.com/docs/copilot/customization/agent-skills |
| Custom instructions | https://code.visualstudio.com/docs/copilot/customization/custom-instructions |
| Agent Skills Standard | https://agentskills.io/ |
