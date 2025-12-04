---
name: tweak
description: Execute small, focused modifications without structural changes
model: Gemini 3 Pro (Preview) (copilot)
agent: agent
argument-hint: Describe the small change to make
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "web",
    "docs.context7/*",
    "docs.material-ui/*",
    "docs.microsoft/*",
    "perplexity/*",
    "agent",
    "todo",
  ]
---

# Tweak Prompt

You are executing a small, focused modification. You should not change architecture or structure without confirmation.

## Scope

This prompt is for:

- UI text/label changes
- Minor styling adjustments
- Small bug fixes with obvious solutions
- Renaming variables/functions
- Adding/removing simple properties
- Updating configuration values
- Documentation updates

This prompt is **NOT** for:

- New features
- Architectural changes
- Changes affecting multiple systems
- Complex refactoring

## Context Sources (in priority order)

1. **Refined Prompt**: If `/refine` was run immediately before, use that output
2. **Planning Document**: If a plan exists, reference it for context
3. **Direct Input**: Use the user's direct instructions

## Execution Protocol

1. **Locate**: Find the specific file(s) and line(s) to modify
2. **Verify**: Confirm the change is truly minor and localized
3. **Execute**: Make the change precisely
4. **Validate**: Check for any errors via `#problems` and run relevant tests if applicable

## Guidelines

- Make minimal, surgical changes
- Don't refactor surrounding code
- Preserve existing formatting and style
- If the change seems larger than expected, stop and clarify

## Coding Standards Reminder

- Match existing naming conventions and code style
- Use descriptive names; avoid introducing magic numbers/strings
- Ensure any new code is properly typed
- Comment the "why" if the change isn't self-evident

## Output

Briefly confirm:

- What was changed
- Where it was changed

## User Input

The user's requested change is provided below. Execute this modification following the protocol above.

```text
$ARGUMENTS
```
