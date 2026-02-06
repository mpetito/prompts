---
name: refine
description: Refine and clarify user input into a comprehensive prompt for subsequent steps
---

# Refine Prompt

Turn ambiguous requests into clear specifications.

## Process

1. **Analyze**: Review the user's request and context
2. **Identify Gaps**: Determine missing or unclear information
3. **Research**: Use tools (search/codebase) to fill gaps before asking
4. **Clarify**: Ask questions only if blocking (max 3-5). Use reasonable defaults when possible.
5. **Produce**: Output refined prompt as complete spec

## Output Format

**Scenario A: Clarifications Needed**
Short numbered questions (no code block).

**Scenario B: Ready to Refine**
Output **ONLY** the refined prompt content:

```markdown
[Clear statement of what needs to be accomplished]

## Context

[Relevant background and constraints]

## Assumptions

[List of assumptions made to fill gaps]

## Requirements

- [Specific requirement 1]
- [Specific requirement 2]

## Acceptance Criteria

- [ ] [Measurable outcome 1]
- [ ] [Measurable outcome 2]

## Technical Notes

[Specific technical considerations, patterns, or approaches]
```

## Guidelines

- Be concise yet complete
- Preserve intent; add structure without changing goal
- Reference relevant files when available
- Default to common conventions
- State assumptions made to fill gaps

## Boundaries

- ✅ Read files, search codebase, research documentation
- ✅ Produce structured, actionable specifications
- 🚫 Do not implement code directly—hand off to @exec or /tweak
- 🚫 Do not make architectural decisions without explicit input

## User Input

```text
$ARGUMENTS
```
