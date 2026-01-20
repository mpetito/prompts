---
name: summarize
description: Compress conversation history into an actionable summary for the next session
---

# Summarize Session

Distill the conversation into a concise, actionable summary.

## What to Include

- **Completed Work**: What was implemented, created, or modified
- **Key Decisions**: Important technical decisions and rationale
- **Current State**: Where the project/feature stands now
- **Pending Items**: Unfinished tasks, open questions, or blockers
- **Context**: Important context that would be lost without this summary

## What to Exclude

- Exploratory discussions that didn't lead anywhere
- Failed attempts (unless lessons learned are valuable)
- Routine operations without unique insights
- Redundant information documented elsewhere

## Output Format

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
- Any blockers or dependencies

**Keep it brief and actionable.** The next agent should understand in ~30 seconds.

## User Input

```text
$ARGUMENTS
```
