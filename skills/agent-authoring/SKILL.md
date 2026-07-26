---
name: agent-authoring
description: "Use when creating AGENTS.md files, writing SKILL.md files, or improving agentic coding developer experience. Triggers include create AGENTS.md, write SKILL.md, agent configuration, agentic DX, AI assistant context, agent instructions, skill documentation, and onboarding AI agents."
---

# Agent Authoring Skill

## Overview

This skill provides the methodology for authoring AGENTS.md and SKILL.md files that give AI coding agents the context they need to work effectively. These files serve as "onboarding documentation" that helps agents understand project conventions, avoid common mistakes, and leverage existing patterns.

---

## Top Priorities (Apply First)

When authoring or reviewing these files, enforce these rules in order. Stop at the first violation, fix it, then continue applying the remaining rules in order.

1. **Frontmatter validity** (SKILL.md only): YAML must include `name` and `description` with explicit "Use when..." trigger phrases.
2. **Length budget**: AGENTS.md ≤ 150 lines; SKILL.md ≤ 500 lines.
3. **Concrete commands**: Every command must be copy-pasteable and verified to run.
4. **Explicit boundaries**: AGENTS.md must include a "Do Not" section with specific prohibitions.
5. **No README duplication**: Reference other docs instead of restating them.
6. **Correct placement**: Root AGENTS.md always; nested only where conventions differ; SKILL.md under `.github/skills/{skill-name}/`.

All other rules below provide additional details for these six. Apply rules in this hierarchy: (1) top priorities always override; (2) in cases not covered by a top priority, follow the conflict resolution rules; (3) only after both have been satisfied, apply the remaining detailed guidance.

---

## AGENTS.md Standards

### Purpose

AGENTS.md provides project-wide context, conventions, and explicit boundaries for AI agents. It is **distinct from README**—it contains technical details agents need but would clutter human documentation.

### Behavior

- Always loaded when agent works in that directory or below
- **Closest-ancestor precedence**: The AGENTS.md file in the closest parent directory (in the directory hierarchy) takes precedence over AGENTS.md files in higher-level directories. Modification time is irrelevant.
- Automatically included in agent context

### Conflict Resolution Between Nested Files

When a nested AGENTS.md and an ancestor AGENTS.md provide contradictory guidance, apply these rules in order:

1. **Closest ancestor wins** for any directly contradictory instruction (commands, conventions, prohibitions). The nested file is assumed to reflect intentional local overrides.
2. **Union, not override, for additive guidance**: Additive guidance refers to rules that expand on, rather than contradict, existing rules in ancestor files. "Do Not" prohibitions and safety rules from ancestor files still apply unless the nested file explicitly relaxes them with a statement such as `Override: this directory permits <X>`.
3. **Explicit overrides must be labeled**: Nested files that intentionally override an ancestor rule must call it out (e.g., `> Overrides root AGENTS.md: uses pnpm instead of npm`) so the conflict is visible to readers.
4. **When ambiguous and no top priority applies, prefer the stricter rule** and surface the conflict to the user rather than silently choosing.
5. **No explicit override provided**: If nested files contradict without an explicit override label, log a warning that identifies the conflicting rules and their source files, and suggest the author review the files for clarity before proceeding.

### Format Requirements

| Requirement    | Specification                             |
| -------------- | ----------------------------------------- |
| Format         | Pure Markdown                             |
| Maximum Length | ~150 lines                                |
| Content Style  | Concrete commands and examples, not prose |
| Commands       | Copy-pasteable, not pseudo-code           |

### Hierarchy Strategy

Use progressive disclosure through nested files:

```
repo/
├── AGENTS.md              ← Always (root context)
├── packages/
│   ├── api/
│   │   └── AGENTS.md      ← If distinct stack/conventions
│   └── web/
│       └── AGENTS.md      ← If distinct stack/conventions
├── scripts/
│   └── AGENTS.md          ← If scripts have special patterns
└── generated/
    └── AGENTS.md          ← "Do not edit" warning
```

### Placement Criteria

| Location             | When to Create                                                 |
| -------------------- | -------------------------------------------------------------- |
| **Root**             | Always—project-wide context, main build/test commands          |
| **Subdirectory**     | When directory has distinct conventions that differ from root  |
| **Package/Module**   | In monorepos, each package with its own build/test/conventions |
| **Generated/Vendor** | Directories agents should avoid modifying                      |

---

## SKILL.md Standards

### Purpose

SKILL.md files capture domain-specific, bounded procedures with reusable capabilities. They teach agents how to perform specific multi-step tasks.

### Location

The layout is always `{skills-root}/{skill-name}/SKILL.md`; only the root differs per tool:

| Tool                | Project-level skills root | User-level skills root |
| ------------------- | ------------------------- | ---------------------- |
| GitHub Copilot      | `.github/skills/`         | `~/.copilot/skills/`   |
| Claude Code         | `.claude/skills/`         | `~/.claude/skills/`    |
| opencode and others | —                         | `~/.agents/skills/`    |

For a repo-committed skill, default to `.github/skills/` and add `.claude/skills/` (or a symlink) when the repo is also worked on with Claude Code. Either way the directory name must match the `name` in the frontmatter.

```
repo/
├── .github/
│   └── skills/
│       ├── database-migration/
│       │   ├── SKILL.md              ← Migration procedure
│       │   └── migrate.sh            ← Supporting script
│       ├── deployment/
│       │   ├── SKILL.md              ← Deploy procedure
│       │   └── deploy-checklist.md   ← Reference doc
│       └── api-versioning/
│           └── SKILL.md              ← Versioning procedure
```

### Behavior

- Auto-discovered but loaded **on-demand**
- Only YAML frontmatter loaded initially (saves tokens)
- Full content loaded when description matches user intent

### Format Requirements

| Requirement    | Specification                                                             |
| -------------- | ------------------------------------------------------------------------- |
| Frontmatter    | YAML with `name` and `description` **required**                           |
| Name           | Lowercase letters, digits, hyphens; ≤64 chars; must match the folder name |
| Description    | Must include "Use when..." with trigger phrases; ≤1024 chars              |
| Maximum Length | <500 lines                                                                |
| Structure      | SKILL.md + optional scripts and reference files                           |

Keep frontmatter to `name` and `description` for portability. Tool-specific keys (Claude Code's `allowed-tools`, `model`, `disable-model-invocation`) are ignored by other hosts, so only add them when the skill is Claude-Code-only.

### YAML Frontmatter

The `description` field is **critical**—it determines when agents load the skill:

```yaml
---
name: database-migration
description: |
  Run database migrations, create new migrations, and rollback changes.
  Use when working with database schema changes, when the user mentions
  migrations, or when database errors reference missing columns or tables.
---
```

**Key insight**: Make descriptions **trigger-clear** with specific scenarios.

---

## AGENTS.md Template

`````markdown
# AGENTS.md

> Agent instructions for [project-name]

## Commands

```bash
# Install dependencies
[exact command]

# Run tests
[exact command]

# Type checking
[exact command]

# Linting
[exact command]
```

## Code Style

- [Specific style rule with example]
- [Another concrete convention]
- Import design tokens from `src/lib/theme/tokens.ts`

## Architecture

### Key Components

- `src/components/` - React components using [pattern]
- `src/api/` - API routes following [convention]

### Module Boundaries

- [Explain key architectural decisions]

## Do Not

- ❌ Hard-code colors—use design tokens
- ❌ Use `any` types—add proper type annotations
- ❌ Modify files in `generated/` or `vendor/`
- ❌ Install packages without asking first

## Safety

- ✅ **Can do**: Read files, run type checks, run tests
- ⚠️ **Ask first**: Install packages, git operations, delete files

## See Also

- [README.md](README.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

---

## SKILL.md Template

````markdown
---
name: [skill-name]
description: |
  [What the skill does in one sentence].
  Use when [specific trigger scenario 1], when [trigger scenario 2],
  or when [trigger scenario 3].
---

# [Skill Name]

## When to Use

- User asks to [specific action]
- [Condition] requires this procedure
- Errors reference [specific symptoms]

## Prerequisites

- [Required setup item]
- [Environment configuration]

## Procedure

1. Check current state:
   ```bash
   [exact command]
   ```
````
`````

2. Perform main action:

   ```bash
   [exact command]
   ```

3. Verify success:
   ```bash
   [exact command]
   ```

## Rollback

If something fails:

```bash
[recovery command]
```

## Common Issues

| Problem               | Solution           |
| --------------------- | ------------------ |
| "[Error message]"     | [Specific fix]     |
| [Symptom description] | [Resolution steps] |

````

---

## Quality Criteria

### AGENTS.md Quality Checklist

- [ ] **Concise**: Under 150 lines, no walls of text
- [ ] **Concrete**: Commands are copy-pasteable, not pseudo-code
- [ ] **Current**: Matches actual project state (commands work, paths exist)
- [ ] **Complete**: Covers build, test, lint, and key conventions
- [ ] **Non-redundant**: Doesn't duplicate README content (references it instead)
- [ ] **Actionable**: Every statement helps agents make correct decisions
- [ ] **Boundary-setting**: Clear "Do Not" section with ❌ markers
- [ ] **Hierarchical**: Nested files only where truly needed

### SKILL.md Quality Checklist

- [ ] **YAML frontmatter**: Has required `name` and `description` fields
- [ ] **Trigger-clear description**: Includes "Use when..." with specific scenarios
- [ ] **Bounded**: Task has clear start and end states
- [ ] **Procedural**: Numbered steps with exact commands
- [ ] **Self-contained**: References supporting files in same skill folder
- [ ] **Under 500 lines**: Detailed content goes in referenced files
- [ ] **Problem/Solution pairs**: Common issues documented with fixes

---

## Anti-Patterns to Avoid

### AGENTS.md Anti-Patterns

| Anti-Pattern              | Problem                                | Fix                                      |
| ------------------------- | -------------------------------------- | ---------------------------------------- |
| **Duplicating README**    | Wastes tokens, goes stale              | Reference with `See [README.md]`         |
| **Vague guidance**        | "Write good code" is useless           | "Use guard clauses for early returns"    |
| **Stale commands**        | Commands that don't work               | Test every command before documenting    |
| **Over-nesting**          | AGENTS.md in every folder              | Only where conventions truly differ      |
| **Mega-files**            | Single 500-line AGENTS.md              | Split into hierarchy                     |
| **Missing boundaries**    | No "Do Not" section                    | Always include explicit prohibitions     |
| **Implicit knowledge**    | Assumes agents know project terms      | Define project-specific terminology      |

### SKILL.md Anti-Patterns

| Anti-Pattern              | Problem                                | Fix                                      |
| ------------------------- | -------------------------------------- | ---------------------------------------- |
| **Missing frontmatter**   | Skill won't be discovered              | Always include YAML with name/description|
| **Weak descriptions**     | Description lacks trigger phrases      | Add "Use when..." with specific scenarios|
| **Skill sprawl**          | SKILL.md for trivial procedures        | Only multi-step, bounded tasks           |
| **Unbounded scope**       | No clear start/end states              | Define prerequisites and success criteria|
| **Abstract principles**   | General knowledge, not procedures      | Use AGENTS.md for conventions instead    |

---

## Good vs Poor Skill Candidates

| Good SKILL.md Candidates                           | Poor Candidates                          |
| -------------------------------------------------- | ---------------------------------------- |
| Multi-step workflows (deploy, release, migration)  | Simple one-liners                        |
| Procedures with scripts or tooling                 | General knowledge                        |
| Domain-specific tasks (database ops, API patterns) | Project-wide conventions (use AGENTS.md) |
| Bounded, completable tasks                         | Open-ended guidance                      |
| Tasks requiring specific file references           | Abstract principles                      |

---

## Content Deduplication Guidelines

### What Belongs Where

| Content Type                  | Location                               |
| ----------------------------- | -------------------------------------- |
| Project overview              | README.md                              |
| Build/test commands for agents| AGENTS.md                              |
| Code conventions              | AGENTS.md                              |
| Multi-step procedures         | SKILL.md                               |
| API documentation             | Dedicated docs (reference from AGENTS) |
| Contributing guidelines       | CONTRIBUTING.md (reference from AGENTS)|

### Reference Pattern

Instead of duplicating, reference existing docs:

```markdown
## See Also

- [README.md](README.md) - Project overview and setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow
- [docs/api.md](docs/api.md) - API reference
```

---

## Exemplary Patterns

### Effective Description (Trigger-Clear)

```yaml
description: |
  Guide for creating effective skills. Use when users want to create a new skill
  (or update an existing skill) that extends Claude's capabilities with specialized
  knowledge, workflows, or tool integrations.
```

**Why it works**: Includes specific trigger phrases ("create a new skill", "update an existing skill")

### Effective Do Not Section

```markdown
## Do Not

- ❌ Hard-code colors—use design tokens from `src/theme/tokens.ts`
- ❌ Use `any` types—add proper type annotations
- ❌ Modify files in `generated/` or `vendor/`
- ❌ Create new API endpoints without updating OpenAPI spec
```

**Why it works**: Specific prohibitions with alternatives provided

### Effective Gotchas Documentation

```markdown
## Development Gotchas

### 1. SDK Version
**Problem**: `container` parameter not recognized
**Solution**: Use `client.beta.messages.create()` instead of `client.messages.create()`

### 2. Beta Namespace Required
```python
# ❌ Wrong
response = client.messages.create(container={...})

# ✅ Correct
response = client.beta.messages.create(...)
```

**Why it works**: Problem/Solution pairs with concrete code examples

---

## Core Principles

### Context Window is a Public Good

Skills share the context window with everything else the agent needs. Keep files concise.

**Default assumption**: AI agents are already very smart. Only add context they don't already have.

### Calibrate Freedom to Fragility

Match specificity to the task's risk level:

| Freedom Level | When to Use                              | Format                           |
| ------------- | ---------------------------------------- | -------------------------------- |
| **High**      | Multiple valid approaches                | Text instructions                |
| **Medium**    | Preferred pattern exists                 | Pseudocode, parameterized scripts|
| **Low**       | Fragile, error-prone operations          | Specific scripts, exact commands |

### Agent Perspective

Write for AI assistants, not human developers:
- Assume technical competence
- Provide exact commands, not concepts
- Include error messages agents might encounter
- Define project-specific terminology

---

## Validation Checklist

Before finalizing any AGENTS.md or SKILL.md:

1. [ ] Commands actually work when executed
2. [ ] File paths exist in the repository
3. [ ] No content duplicated from README
4. [ ] Line count within limits (150 for AGENTS, 500 for SKILL)
5. [ ] SKILL.md has valid YAML frontmatter
6. [ ] Description includes trigger phrases
7. [ ] "Do Not" section has specific prohibitions
8. [ ] All project-specific terms are defined
````
