---
name: tweak
description: Execute small, focused modifications without structural changes
---

# Tweak

Small, surgical code changes only. No architecture or structure changes without confirmation.

## Scope

**For:**

- UI text/label changes
- Minor styling adjustments
- Small bug fixes with obvious solutions
- Renaming variables/functions
- Adding/removing simple properties
- Updating configuration values
- Documentation updates

**NOT for:**

- New features
- Architectural changes
- Changes affecting multiple systems
- Complex refactoring

## Protocol

1. **Locate**: Find target files and line ranges
2. **Verify**: Confirm change is minor and localized
3. **Execute**: Apply change with minimal footprint
4. **Validate**: Run linters/tests, check `#problems`

## Guidelines

- Make minimal, surgical changes
- Don't refactor surrounding code
- Preserve existing formatting and style
- If change seems larger than expected, stop and clarify
- For package operations, use CLI (`npm install`, `dotnet add package`)

## Boundaries

- ✅ Locate targets, validate scope, run linters
- ✅ Preserve existing formatting and code style
- ⚠️ Ask first: Changes affecting >3 files or >50 lines
- 🚫 Never: Architectural changes or refactoring
- 🚫 Never: Add dependencies without explicit request

## Output

Briefly confirm:

- What was changed
- Where it was changed

## User Input

```text
$ARGUMENTS
```
