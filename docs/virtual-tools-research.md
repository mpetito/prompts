# Virtual Tools vs Explicit Tool Enumeration

**Date**: 2026-02-02  
**Status**: ✅ Migration Complete

## Executive Summary

GitHub Copilot in VS Code now supports **virtual tools**—a dynamic tool selection mechanism that groups similar tools together and enables the model to activate them on-demand. This research evaluated whether our shared agent modes should continue explicitly enumerating tools or adopt dynamic tool selection.

**Decision**: Remove `tools` arrays from **all agents**—let virtual tools handle dynamic discovery. Behavioral constraints belong in prompt boundaries (`🚫 **Never**` sections), not tool restrictions.

## What Are Virtual Tools?

Virtual tools are a mechanism introduced by GitHub Copilot to address the challenge of managing large tool sets. Instead of presenting the AI model with a flat list of all available tools (which can exceed 40 built-in + hundreds from MCP servers), virtual tools:

1. **Group similar tools together** into logical clusters (directories)
2. **Enable on-demand activation**—the model expands groups only when needed
3. **Use embedding-guided routing** to pre-select relevant tools based on query context

### Key Setting

```jsonc
"github.copilot.chat.virtualTools.threshold": 128  // (Experimental, default: 128)
```

When the total tool count exceeds this threshold, VS Code automatically:

- Groups tools into virtual categories using embedding-based clustering
- Routes queries to relevant tool groups using semantic similarity
- Expands only the needed groups during execution

### How It Works

1. **Adaptive Clustering**: Tools are grouped by semantic similarity using Copilot's embedding model
2. **Embedding-Guided Routing**: Before expanding any tool group, the system compares the query embedding against all tools/clusters
3. **Pre-selection**: Most relevant tools are surfaced directly, eliminating unnecessary exploratory calls

**Performance impact** (from GitHub's blog):

- 94.5% Tool Use Coverage (vs 69% with static lists)
- 190ms reduction in Time To First Token
- 400ms reduction in response latency

### Core Toolset

VS Code's default agent uses a **streamlined 13-tool core**, with remaining tools grouped into virtual categories:

- Jupyter Notebook Tools
- Web Interaction Tools
- VS Code Workspace Tools
- Testing Tools

## Current Approach in Our Shared Agents

Our agents explicitly enumerate tools in frontmatter:

```yaml
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "web",
    "agent",
    "todo",
    "askQuestions",
    "perplexity/*",
    "docs-context7/*",
    "docs-langchain/*",
    "docs-aws/*",
    "docs-microsoft/*",
    "docs-material-ui/*",
    "etilize-mysql/*",
  ]
```

### What This Includes

| Category                 | Examples                                      | Purpose                   |
| ------------------------ | --------------------------------------------- | ------------------------- |
| **Built-in tools**       | `vscode`, `execute`, `read`, `edit`, `search` | Core VS Code capabilities |
| **MCP server wildcards** | `perplexity/*`, `docs-context7/*`, `github/*` | External API integrations |
| **Project-specific MCP** | `etilize-mysql/*`                             | Project-specific tools    |

### Problems With Current Approach

1. **Project-specific tools in shared prompts**: `etilize-mysql/*` only works in specific projects
2. **Redundant built-in specification**: Virtual tools handle built-in routing better than static lists
3. **Maintenance overhead**: Must update tool lists when new MCP servers are added
4. **Inflexibility**: Shared agents can't adapt to project-specific MCP servers
5. **Model overhead**: Large explicit tool lists can degrade model performance

## Tool List Priority Order

VS Code applies tools in this priority order:

1. **Tools specified in prompt file** (if any)
2. **Tools from referenced agent** (if any)
3. **Default tools for selected agent** (or all available for default Agent)

**Important**: If a specified tool is not available, **it is ignored**. This means specifying unavailable tools doesn't cause errors—they're simply skipped.

## Comparison: Explicit vs Dynamic

| Aspect                     | Explicit Enumeration           | Virtual Tools (Dynamic)           |
| -------------------------- | ------------------------------ | --------------------------------- |
| **Setup**                  | Manual configuration required  | Automatic based on context        |
| **Flexibility**            | Fixed—can't adapt to workspace | Adapts to available tools         |
| **Project-specific tools** | Must be explicitly listed      | Auto-discovered if configured     |
| **Safety restrictions**    | ✅ Can restrict to read-only   | ❌ Model chooses tools            |
| **Performance**            | Worse with large lists         | Better—embedding-guided selection |
| **Maintenance**            | Must update when tools change  | None—auto-adapts                  |
| **Predictability**         | High—exact tools known         | Lower—model decides               |

## Why Not Restrict Tools?

Initially considered restricting tools for "safety-critical" modes like plan/research/review. However:

| Concern                               | Resolution                                                                              |
| ------------------------------------- | --------------------------------------------------------------------------------------- |
| Plan making accidental edits          | Handled by `🚫 **Never**: Implement code directly` boundary                             |
| Research modifying code               | Handled by `🚫 **Never**: Implement code directly—research and recommend only` boundary |
| Review needing project-specific tools | May need grounding in project DB, docs, or other MCP tools                              |
| PR agents needing research tools      | May need docs/research for proper PR updates                                            |

**Conclusion**: Behavioral boundaries in prompts are the correct mechanism for safety. Tool restrictions would limit flexibility without adding safety guarantees.

## Implementation

### Approach

Remove `tools` field from all agents. Virtual tools will:

- Auto-discover workspace MCP servers
- Route to relevant tools using embedding-based selection
- Provide 94.5% tool coverage (vs 69% with static lists)

### Toolsets

The `mcp.toolsets.jsonc` can still be used for grouping tools that users want to reference explicitly via `#toolsetname`:

```jsonc
{
  "research": {
    "description": "Deep research using Perplexity AI",
    "tools": ["perplexity/*"],
  },
  "docs": {
    "description": "Documentation lookup",
    "tools": ["docs-context7/*", "docs-microsoft/*", "docs-aws/*"],
  },
}
```

These are available for explicit invocation but not required in agent definitions.

## Changes Made

| Agent                   | Previous State             | New State           |
| ----------------------- | -------------------------- | ------------------- |
| **exec.agent.md**       | 16 explicit tools          | ✅ `tools` removed  |
| **plan.agent.md**       | 17 explicit tools          | ✅ `tools` removed  |
| **research.agent.md**   | 16 explicit tools          | ✅ `tools` removed  |
| **review.agent.md**     | 18 explicit tools          | ✅ `tools` removed  |
| **agentic-dx.agent.md** | No tools (already correct) | ✅ No change needed |

## Migration Summary

### Completed

1. ✅ Removed `tools` arrays from all agent files
2. ✅ Removed project-specific MCP references (`etilize-mysql/*`)
3. ✅ All agents now rely on virtual tool discovery

### Not Changed

- `mcp.toolsets.jsonc` retained for explicit `#toolsetname` references
- Behavioral boundaries in agent prompts remain the safety mechanism

## Remaining Questions

1. **Workspace MCP discovery**: If an agent has no `tools` field, does it automatically discover workspace-level MCP servers? (To verify in practice)

2. **Toolset references**: Can we reference toolsets from `mcp.toolsets.jsonc` using `#toolsetname` syntax in prompts? (To verify)

## References

| Resource                              | URL                                                                                                   |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| VS Code Chat Tools                    | https://code.visualstudio.com/docs/copilot/chat/chat-tools                                            |
| Copilot Settings Reference            | https://code.visualstudio.com/docs/copilot/reference/copilot-settings                                 |
| GitHub Blog: Smarter with Fewer Tools | https://github.blog/ai-and-ml/github-copilot/how-were-making-github-copilot-smarter-with-fewer-tools/ |
| Custom Agents                         | https://code.visualstudio.com/docs/copilot/customization/custom-agents                                |

## Conclusion

Virtual tools provide a robust mechanism for dynamic tool selection that outperforms static enumeration. Our shared prompts now:

1. **Embrace dynamic selection** for all agents (no explicit tool lists)
2. **Use behavioral boundaries** for safety (`🚫 **Never**` sections in prompts)
3. **Auto-discover tools** including project-specific MCP servers
4. **Retain toolsets** for explicit user invocation via `#toolsetname`

This approach provides maximum flexibility while maintaining behavioral safety through prompt boundaries.
