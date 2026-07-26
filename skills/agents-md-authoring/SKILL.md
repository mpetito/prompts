---
name: agents-md-authoring
description: "Use when creating or reviewing AGENTS.md, CLAUDE.md, or copilot-instructions.md files that give AI coding agents project-wide context. Triggers include create AGENTS.md, write CLAUDE.md, agent configuration, project conventions for AI, AI assistant context, agent instructions, and onboarding AI agents to a repository. For authoring SKILL.md files, use the `skill-authoring` skill instead."
---

# AGENTS.md Authoring

Methodology for authoring the project-wide context file that AI coding agents load automatically. It is "onboarding documentation" for agents: conventions to follow, mistakes to avoid, patterns to reuse.

This skill covers **always-loaded project context**. For **on-demand procedures**, see [`skill-authoring`](../skill-authoring/SKILL.md).

---

## Top Priorities (Apply First)

Enforce these in order. Stop at the first violation, fix it, then continue.

1. **Length budget**: ≤ 150 lines. This file is loaded into every agent turn in that directory tree.
2. **Concrete commands**: every command copy-pasteable and verified to actually run.
3. **Explicit boundaries**: include a "Do Not" section with specific prohibitions.
4. **No README duplication**: reference other docs instead of restating them.
5. **Correct placement**: root always; nested only where conventions genuinely differ.

All other guidance below elaborates on these five.

---

## File Names by Tool

The content is the same; only the filename differs. Prefer `AGENTS.md` and add thin pointers for tools that need their own name.

| Tool           | File                                                      |
| -------------- | --------------------------------------------------------- |
| Cross-tool     | `AGENTS.md` (the emerging standard)                       |
| Claude Code    | `CLAUDE.md` (or a `CLAUDE.md` that says "see AGENTS.md")  |
| GitHub Copilot | `.github/copilot-instructions.md`                         |

---

## Behavior

- Always loaded when the agent works in that directory or below
- **Closest-ancestor precedence**: the file in the closest parent directory wins over ones higher up. Modification time is irrelevant.
- Automatically included in agent context — it costs tokens on every turn, which is why the length budget matters

## Conflict Resolution Between Nested Files

When a nested file and an ancestor give contradictory guidance, apply in order:

1. **Closest ancestor wins** for any directly contradictory instruction (commands, conventions, prohibitions). The nested file is assumed to reflect intentional local overrides.
2. **Union, not override, for additive guidance.** Additive guidance expands on rather than contradicts ancestor rules. "Do Not" prohibitions and safety rules from ancestors still apply unless the nested file explicitly relaxes them with a statement such as `Override: this directory permits <X>`.
3. **Explicit overrides must be labeled**, e.g. `> Overrides root AGENTS.md: uses pnpm instead of npm`, so the conflict is visible to readers.
4. **When ambiguous and no top priority applies, prefer the stricter rule** and surface the conflict to the user rather than silently choosing.
5. **No explicit override provided**: if nested files contradict without a label, warn with the conflicting rules and their source files, and suggest the author reconcile them before proceeding.

---

## Format Requirements

| Requirement    | Specification                             |
| -------------- | ----------------------------------------- |
| Format         | Pure Markdown                             |
| Maximum length | ~150 lines                                |
| Content style  | Concrete commands and examples, not prose |
| Commands       | Copy-pasteable, not pseudo-code           |

## Hierarchy Strategy

Use progressive disclosure through nested files:

```text
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
| **Root**             | Always — project-wide context, main build/test commands        |
| **Subdirectory**     | When the directory has conventions that differ from root       |
| **Package/Module**   | In monorepos, each package with its own build/test/conventions |
| **Generated/Vendor** | Directories agents should avoid modifying                      |

---

## Template

````markdown
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

- ❌ Hard-code colors — use design tokens
- ❌ Use `any` types — add proper type annotations
- ❌ Modify files in `generated/` or `vendor/`
- ❌ Install packages without asking first

## Safety

- ✅ **Can do**: Read files, run type checks, run tests
- ⚠️ **Ask first**: Install packages, git operations, delete files

## See Also

- [README.md](README.md) - Project overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
````

---

## Quality Checklist

- [ ] **Concise**: under 150 lines, no walls of text
- [ ] **Concrete**: commands are copy-pasteable, not pseudo-code
- [ ] **Current**: matches actual project state (commands work, paths exist)
- [ ] **Complete**: covers build, test, lint, and key conventions
- [ ] **Non-redundant**: doesn't duplicate README content (references it instead)
- [ ] **Actionable**: every statement helps agents make correct decisions
- [ ] **Boundary-setting**: clear "Do Not" section with ❌ markers
- [ ] **Hierarchical**: nested files only where truly needed

## Anti-Patterns

| Anti-Pattern           | Problem                           | Fix                                   |
| ---------------------- | --------------------------------- | ------------------------------------- |
| **Duplicating README** | Wastes tokens, goes stale         | Reference with `See [README.md]`      |
| **Vague guidance**     | "Write good code" is useless      | "Use guard clauses for early returns" |
| **Stale commands**     | Commands that don't work          | Test every command before documenting |
| **Over-nesting**       | AGENTS.md in every folder         | Only where conventions truly differ   |
| **Mega-files**         | A single 500-line AGENTS.md       | Split into a hierarchy                |
| **Missing boundaries** | No "Do Not" section               | Always include explicit prohibitions  |
| **Implicit knowledge** | Assumes agents know project terms | Define project-specific terminology   |

---

## Content Deduplication

| Content Type                   | Belongs In                             |
| ------------------------------ | -------------------------------------- |
| Project overview               | README.md                              |
| Build/test commands for agents | AGENTS.md                              |
| Code conventions               | AGENTS.md                              |
| Multi-step procedures          | SKILL.md (see `skill-authoring`)       |
| API documentation              | Dedicated docs (reference from AGENTS) |
| Contributing guidelines        | CONTRIBUTING.md (reference from AGENTS)|

Instead of duplicating, reference:

```markdown
## See Also

- [README.md](README.md) - Project overview and setup
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow
- [docs/api.md](docs/api.md) - API reference
```

### Effective "Do Not" Section

```markdown
## Do Not

- ❌ Hard-code colors — use design tokens from `src/theme/tokens.ts`
- ❌ Use `any` types — add proper type annotations
- ❌ Modify files in `generated/` or `vendor/`
- ❌ Create new API endpoints without updating OpenAPI spec
```

**Why it works**: specific prohibitions, each with an alternative.

---

## Core Principles

**Context window is a public good.** This file is loaded on every turn and shares the window with everything else the agent needs. Every line must earn its place.

**Agents are already competent.** Only add context they don't already have — project-specific terminology, non-obvious constraints, local conventions. Do not explain the language or the framework.

**Write for agents, not humans.** Assume technical competence, provide exact commands rather than concepts, and define project-specific terms.

---

## Validation Checklist

Before finalizing:

1. [ ] Commands actually work when executed
2. [ ] File paths exist in the repository
3. [ ] No content duplicated from README
4. [ ] Under 150 lines
5. [ ] "Do Not" section has specific prohibitions
6. [ ] All project-specific terms are defined
