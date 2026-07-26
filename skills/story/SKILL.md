---
name: story
description: "Guidelines for creating well-structured Azure DevOps work items including User Stories, Issues, and Bugs with proper formatting, story points, and acceptance criteria. Use when creating user stories, writing acceptance criteria, formatting work items for Azure DevOps, or estimating story points."
# Claude Code only; other hosts ignore these keys.
model: sonnet
effort: low
---

# Story Writing Skill

## Overview

This skill provides guidelines for creating well-structured Azure DevOps work items including User Stories, Issues, and Bugs. It covers work item type selection, required fields, description formats, story point estimation, and acceptance criteria best practices.

---

## Work Item Type Selection

| Type           | When to Use                                                               |
| -------------- | ------------------------------------------------------------------------- |
| **User Story** | Default for new functionality, features, or user-facing changes           |
| **Issue**      | Technical debt, infrastructure work, or non-functional improvements       |
| **Bug**        | Defects, broken functionality, or behavior that doesn't match expectation |

**Default to User Story** unless the request clearly describes an issue or bug.

---

## Required Fields by Work Item Type

### User Story Fields

| Field               | Description                                             |
| ------------------- | ------------------------------------------------------- |
| Title               | Concise description of the feature                      |
| Description         | "As a [user], I want [action] so that [benefit]" format |
| Story Points        | Fibonacci estimate (1, 2, 3, 5, 8, 13)                  |
| Acceptance Criteria | Specific, measurable, verifiable criteria               |
| Iteration Path      | Sprint assignment                                       |

### Issue Fields

| Field               | Description                                |
| ------------------- | ------------------------------------------ |
| Title               | Concise description of the technical work  |
| Description         | "We need [capability] to [purpose]" format |
| Story Points        | Fibonacci estimate (1, 2, 3, 5, 8, 13)     |
| Acceptance Criteria | Definition of done for the technical work  |
| Iteration Path      | Sprint assignment                          |

### Bug Fields

| Field             | Description                               |
| ----------------- | ----------------------------------------- |
| Title             | Brief description of the defect           |
| Repro Steps       | Step-by-step instructions to reproduce    |
| System Info       | Environment, browser, OS where bug occurs |
| Expected Behavior | What should happen                        |
| Actual Behavior   | What actually happens                     |
| Severity          | 1-Critical, 2-High, 3-Medium, 4-Low       |
| Priority          | 1-High, 2-Medium, 3-Low                   |
| Iteration Path    | Sprint assignment                         |

---

## Description Formats

### User Story Format

For user-facing functionality:

```markdown
As a [type of user], I want to [action] so that [benefit].

## Additional Context

[Implementation constraints, dependencies, non-functional requirements, edge cases]
```

### Technical Requirement Format

For infrastructure, refactoring, or backend work (Issues):

```markdown
We need [technical capability] to [purpose/benefit].

## Additional Context

[Implementation constraints, dependencies, non-functional requirements, edge cases]
```

### Bug Description Format

```markdown
## Expected Behavior

[What should happen]

## Actual Behavior

[What actually happens]

## Reproduction Steps

1. [First step]
2. [Second step]
3. [Step where bug occurs]

## Environment

- OS: [Operating system]
- Browser: [Browser and version]
- Version: [Application version]
```

---

## Story Points Estimation (Fibonacci Scale)

| Points | Complexity                                 | Time Indication              |
| ------ | ------------------------------------------ | ---------------------------- |
| 1      | Trivial task, can be done in minutes       | Less than half a day         |
| 2      | Small task, straightforward implementation | Half day to one day          |
| 3      | Medium task, some complexity               | One to two days              |
| 5      | Larger task, moderate complexity           | Two to three days            |
| 8      | Complex task, requires significant effort  | Three to five days           |
| 13     | Very complex, should consider splitting    | One week or more - split it! |

### Estimation Guidelines

- **Maximum is 13 points** - If larger, split into multiple stories
- **Relative sizing** - Compare to previously completed stories
- **Include all work** - Development, testing, code review, documentation
- **Account for unknowns** - Add buffer for research or exploration

### When to Split Stories

Split a story when:

- Estimate exceeds 13 points
- Multiple distinct user outcomes exist
- Different technical components can be delivered independently
- Story spans multiple sprints

---

## Acceptance Criteria Guidelines

Each criterion must be **specific, measurable, and verifiable**.

### Good Patterns

| Pattern                                            | Example                                            |
| -------------------------------------------------- | -------------------------------------------------- |
| User can [action] and sees [result]                | User can upload a file and sees a success message  |
| System returns [response] when [condition]         | System returns 404 when resource not found         |
| API responds within [X]ms for [Y] concurrent users | API responds within 200ms for 100 concurrent users |
| Error message '[text]' displays when [condition]   | Error "File too large" displays when file > 10MB   |
| [Feature] supports [specific formats/values]       | Upload accepts JPG, PNG, and GIF files up to 10MB  |

### Good Examples

- ✅ "Upload accepts JPG, PNG, and GIF files up to 10MB"
- ✅ "Error message displays when file exceeds 10MB"
- ✅ "Thumbnail generates at 150x150 pixels"
- ✅ "Page loads in under 2 seconds on 3G connection"
- ✅ "User receives email confirmation within 5 minutes"
- ✅ "Form validates email format before submission"
- ✅ "Search returns results within 500ms for up to 10,000 records"

### Bad Examples (Avoid)

- ❌ "Performance is good"
- ❌ "User experience is intuitive"
- ❌ "System handles errors gracefully"
- ❌ "Code is clean"
- ❌ "Application is fast"
- ❌ "Design looks nice"
- ❌ "It works correctly"

### Acceptance Criteria Structure Template

```markdown
### 1. Functional Requirements

- [ ] User can [specific action]
- [ ] System [specific behavior] when [condition]

### 2. Validation

- [ ] Input validates [specific rules]
- [ ] Error message "[text]" displays when [condition]

### 3. Performance

- [ ] [Action] completes within [X] seconds
- [ ] System supports [Y] concurrent users

### 4. Edge Cases

- [ ] System handles [edge case] by [behavior]
```

---

## Markdown Formatting for Azure DevOps

### Formatting Rules

1. **Use Markdown format** for all rich text fields
2. **No bold fragments** - Avoid `**bold**` within sentences; use headers instead
3. **Use numbered section headers** with checklists for acceptance criteria
4. **Use plain paragraphs** with markdown headers for descriptions

### Description Structure

```markdown
As a [user], I want [action] so that [benefit].

#### Additional Context

- Bullet point context
- Another point

#### Dependencies

Related items or references.
```

### Acceptance Criteria Structure

```markdown
### 1. Category Name

- [ ] First criterion
- [ ] Second criterion

### 2. Another Category

- [ ] Third criterion
- [ ] Fourth criterion
```

---

## Azure DevOps Creation Workflow

When the user wants the work item created in Azure DevOps:

1. **Gather context**: Use available `azure-devops/*` MCP tools to identify the project, team, and current sprint/iteration.
2. **Analyze the request**: Select User Story, Issue, or Bug; draft the title, fields, estimate, and acceptance criteria using this skill.
3. **Create the work item**: Call `azure-devops/wit_create_work_item` with the appropriate Azure DevOps fields and Markdown-formatted rich text.
4. **Add design context when useful**: Call `azure-devops/wit_add_work_item_comment` for architectural notes, design constraints, dependencies, or implementation context that should not live in the main description.
5. **Return a concise summary** using the output format below.

---

## Example Field Specifications

Concrete `wit_create_work_item` payloads for User Story, Bug, and Issue — including the
Azure DevOps field reference names and Markdown escaping rules — are in
[`references/ado-field-examples.md`](references/ado-field-examples.md). Read that file
before composing a create call.

---

## Clarification Checklist

### Clarification First Gate

Ask clarifying questions before creating or finalizing a work item when any required detail is unclear:

- For stories: user type/persona, benefit or purpose, scope, or acceptance criteria cannot be inferred.
- For issues: technical purpose, scope boundaries, or definition of done is unclear.
- For bugs: expected-vs-actual behavior is missing, reproduction steps are missing or unclear, environment details are unavailable, or severity cannot be assessed.

Before creating a work item, verify you have:

### For User Stories

- [ ] Clear user type or persona
- [ ] Defined action the user wants to perform
- [ ] Stated benefit or purpose
- [ ] Unambiguous scope
- [ ] Enough information for acceptance criteria

### For Bugs

- [ ] Expected behavior described
- [ ] Actual behavior described
- [ ] Reproduction steps provided
- [ ] Environment/system info available
- [ ] Severity assessment possible

### For Issues

- [ ] Technical capability defined
- [ ] Purpose or benefit stated
- [ ] Scope boundaries clear
- [ ] Definition of done determinable

---

## Output Summary Format

After creating or drafting a work item, return:

- Work Item ID and Title
- Type and Sprint
- Story Points, or Severity/Priority for bugs
- Brief summary of the description and acceptance criteria
- Link to the work item, if available

## Quick Reference Card

### Title Guidelines

- Concise and action-oriented
- Written from feature/capability perspective
- Avoids technical jargon when possible

### Story Format

```
As a [user type], I want to [action] so that [benefit].
```

### Issue Format

```
We need [capability] to [purpose].
```

### Acceptance Criteria Format

```
[Subject] [action/state] [measurable outcome] when [condition].
```

### Story Points Quick Guide

- **1-2**: Simple, well-understood tasks
- **3-5**: Moderate complexity, some unknowns
- **8**: Complex, multiple components
- **13**: Very complex - consider splitting

---

## Common Mistakes

1. **Vague acceptance criteria**: "Performance is good" → "Page loads in under 2 seconds on 3G connection"
2. **Missing user context**: Omitting the "so that [benefit]" clause makes it impossible to evaluate whether the implementation satisfies the need
3. **Wrong work item type**: Using a Bug for missing features (should be Story) or a Story for technical debt (should be Issue)
4. **Overloaded stories**: Single story spanning multiple components or concerns — split when estimated above 8 points
5. **Untestable criteria**: Criteria that require subjective judgment ("looks good", "feels fast") instead of measurable outcomes
