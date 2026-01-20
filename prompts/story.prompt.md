---
name: story
description: Create a new user story, issue, or bug in Azure DevOps
---

# Create Work Item

Transform requirements into Azure DevOps work items. This prompt references the **story-writing** skill for detailed formatting guidelines.

## Clarification First

Ask clarifying questions if:

- User type or persona is unclear (for stories)
- Benefit or purpose is not evident
- Scope is ambiguous
- Acceptance criteria cannot be inferred
- For bugs: expected vs actual behavior is missing
- For bugs: reproduction steps are unclear

## Work Item Type Selection

| Type           | When to Use                                                  |
| -------------- | ------------------------------------------------------------ |
| **User Story** | Default for new functionality, features, user-facing changes |
| **Issue**      | Technical debt, infrastructure, non-functional improvements  |
| **Bug**        | Defects, broken functionality, behavior mismatch             |

## Workflow

1. **Gather Context**: Get project, team, and current sprint via `azure-devops/*` tools.

2. **Analyze Request**: Determine type, title, description, story points, acceptance criteria.

3. **Construct Work Item**: Use appropriate format from story-writing skill.

4. **Create**: Use `azure-devops/wit_create_work_item` with proper fields.

5. **Add Design Context** (if applicable): Use `wit_add_work_item_comment` for architectural notes.

## Story Points (Fibonacci)

| Points | Complexity                       |
| ------ | -------------------------------- |
| 1      | Trivial, minutes                 |
| 2      | Small, straightforward           |
| 3      | Medium, some complexity          |
| 5      | Larger, moderate complexity      |
| 8      | Complex, significant effort      |
| 13     | Very complex, consider splitting |

## Description Formats

**User Story:**

```
As a [type of user], I want to [action] so that [benefit].
```

**Technical:**

```
We need [technical capability] to [purpose/benefit].
```

## Output

- Work Item ID and Title
- Type and Sprint
- Story Points (or Severity/Priority for bugs)
- Summary of description and acceptance criteria
- Link to work item (if available)

## User Input

```text
$ARGUMENTS
```
