---
name: summarize
description: Compress conversation history into an actionable summary for the next session.
model: Claude Sonnet 4.5 (copilot)
agent: agent
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
    "perplexity/*",
    "docs-context7/*",
    "github/*",
    "azure.devops/*",
  ]
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the above user input before proceeding (if not empty).

## Your Task

Review the conversation and distill it into a concise, actionable summary.

## What to Include

- **Completed Work**: What was actually implemented, created, or modified
- **Key Decisions**: Important technical decisions and their rationale
- **Current State**: Where the project/feature stands right now
- **Pending Items**: Unfinished tasks, open questions, or blockers
- **Context**: Any important context that would be lost without this summary

## What to Exclude

- Exploratory discussions that didn't lead anywhere
- Failed attempts or dead ends (unless the lessons learned are valuable)
- Routine operations without unique insights
- Redundant information already documented elsewhere

## Output Format

Provide a concise summary using this structure:

**Session Overview**  
Brief 1-2 sentence description of what was accomplished.

**Completed Work**

- List of concrete deliverables and changes made

**Key Decisions & Insights**

- Important technical decisions or discoveries

**Current State**

- Where things stand now

**Next Steps**

- What should be tackled next
- Any blockers or dependencies to be aware of

**Keep it brief and actionable.** The next agent should understand in ~30 seconds.
