---
name: skill-authoring
description: "Use when creating, reviewing, splitting, or improving SKILL.md files and skill folders. Triggers include write SKILL.md, create a skill, skill frontmatter, skill description tuning, skill is too large, progressive disclosure, references folder, and choosing a model or effort for a skill. For project-wide AGENTS.md context files, use the `agents-md-authoring` skill instead."
---

# Skill Authoring

Methodology for authoring SKILL.md files: bounded, on-demand procedures that agents load when their description matches the task.

For **always-loaded project context**, see [`agents-md-authoring`](../agents-md-authoring/SKILL.md).

---

## Top Priorities (Apply First)

Enforce these in order. Stop at the first violation, fix it, then continue.

1. **Frontmatter validity**: YAML must include `name` and `description`, and the description must carry explicit "Use when…" trigger phrases.
2. **Length budget**: SKILL.md < 500 lines. Detail goes in `references/`.
3. **Concrete commands**: every command copy-pasteable and verified to run.
4. **Bounded scope**: one procedure with a clear start and end state.
5. **Correct placement**: directory name must match the frontmatter `name`.

---

## Anatomy

```text
skill-name/
├── SKILL.md          (required)  Frontmatter + procedural instructions
├── references/       (optional)  Loaded on demand — schemas, examples, deep detail
├── scripts/          (optional)  Executable helpers; run without entering context
└── assets/           (optional)  Files used in output — templates, boilerplate, fonts
```

### Progressive Disclosure

Skills load in three levels. Design for it deliberately:

| Level | What loads                 | When                                 |
| ----- | -------------------------- | ------------------------------------ |
| 1     | Frontmatter only           | Always — this is what triggers a match |
| 2     | Full SKILL.md body         | When the description matches intent  |
| 3     | `references/` files        | Only when SKILL.md points at them    |

**This is the main lever for oversized skills.** A 600-line SKILL.md loads all 600 lines on every match. The same content as a 150-line SKILL.md plus three reference files loads 150 lines, and pulls the rest only when needed.

Move to `references/` when content is:

- A code library rather than a procedure (generator functions, boilerplate templates)
- A command reference (per-ecosystem CLI tables)
- Long worked examples (JSON payloads, field specifications)
- Detail only some invocations need

Keep in SKILL.md: the workflow, the decision points, the pitfalls, and the pointers to references.

**Avoid duplication.** Information lives in SKILL.md *or* a reference file, never both.

---

## Location

The layout is always `{skills-root}/{skill-name}/SKILL.md`; only the root differs per tool.

| Tool                | Project-level skills root | User-level skills root |
| ------------------- | ------------------------- | ---------------------- |
| GitHub Copilot      | `.github/skills/`         | `~/.copilot/skills/`   |
| Claude Code         | `.claude/skills/`         | `~/.claude/skills/`    |
| Codex               | `.agents/skills/`         | `~/.agents/skills/`    |
| opencode and others | —                         | `~/.agents/skills/`    |

For a repo-committed skill, default to `.github/skills/` and add `.claude/skills/` (or a symlink) when the repo is also worked on with Claude Code. Either way the directory name must match the `name` in the frontmatter.

In this shared prompt repository, also rerun `setup-skills-link.ps1` after adding or renaming a top-level directory under `skills/`. The installer creates per-child links in `~/.codex/skills/` without replacing Codex's managed `.system` directory. Edits inside an existing linked skill propagate immediately.

**Cross-skill references** must be relative to the skill's own folder (`../other-skill/SKILL.md`, `../pr-scripts/Script.ps1`), never relative to a repository root. A skills folder is frequently symlinked into a user-level location where no repo root exists.

---

## Frontmatter

`name` and `description` are the only required — and only portable — keys.

```yaml
---
name: database-migration
description: |
  Run database migrations, create new migrations, and rollback changes.
  Use when working with database schema changes, when the user mentions
  migrations, or when database errors reference missing columns or tables.
---
```

| Field       | Specification                                                             |
| ----------- | ------------------------------------------------------------------------- |
| Name        | Lowercase letters, digits, hyphens; ≤64 chars; must match the folder name |
| Description | Must include "Use when…" with trigger phrases; ≤1024 chars                |

The `description` is **critical** — it is the only thing loaded until a match occurs, so it alone decides whether the skill fires. Make it trigger-clear with specific scenarios and the phrasings you actually use. When two skills are adjacent in scope, have each description name the other and say which case belongs where.

### Host-Specific Keys

Claude Code accepts additional frontmatter keys. Other hosts ignore unknown keys, so adding them does not break portability — but they only take effect in Claude Code.

| Key                        | Values                                        | Use for                                                       |
| -------------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| `model`                    | `inherit`, `haiku`, `sonnet`, `opus`, model id | Pinning a cheaper tier on mechanical skills                    |
| `effort`                   | `low`, `medium`, `high`, `xhigh`, `max`       | Tuning reasoning depth without changing model tier             |
| `allowed-tools`            | tool list                                     | Restricting a skill to read-only or a narrow tool set          |
| `disable-model-invocation` | `true`                                        | User-typed `/name` only — never auto-invoked by the model      |
| `argument-hint`            | string                                        | Slash-command argument hint                                    |
| `context`                  | `fork`                                        | Run in a forked context so it does not pollute the main thread |
| `agent`                    | agent name                                    | Run the skill inside a named subagent                          |

### Choosing `model` and `effort`

| Skill character                                                        | Recommendation                     |
| ---------------------------------------------------------------------- | ---------------------------------- |
| Mechanical: templating, script-driven, deterministic steps             | `model: sonnet` + `effort: low`    |
| Writing-heavy but not reasoning-heavy (summaries, descriptions)        | `model: sonnet` + `effort: high`   |
| Architecture, adversarial review, ambiguity gating, conflict resolution | Leave `model` unset; inherit       |
| Destructive or outward-facing operations                               | Consider `disable-model-invocation`|

**Do not set `model` on reference skills** — ones consumed *inside* another task rather than invoked directly. Pinning a model there fights whatever workflow loaded them.

Prefer `effort` over dropping a model tier when the skill needs capability but not deliberation: it cuts thinking tokens while preserving judgment.

---

## Template

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

> **Fencing note**: when a skill embeds a Markdown template that itself contains fenced code, the outer fence must use *more* backticks than any inner fence (four outside, three inside). Mismatched fences silently leak template content into the instruction stream — a common and hard-to-spot defect.

---

## Quality Checklist

- [ ] **YAML frontmatter**: has required `name` and `description`
- [ ] **Trigger-clear description**: includes "Use when…" with specific scenarios
- [ ] **Disambiguated**: names any adjacent skill and says which case goes where
- [ ] **Bounded**: task has clear start and end states
- [ ] **Procedural**: numbered steps with exact commands
- [ ] **Self-contained**: references supporting files with skill-relative paths
- [ ] **Under 500 lines**: detailed content moved to `references/`
- [ ] **Problem/Solution pairs**: common issues documented with fixes
- [ ] **Fences balanced**: embedded templates use wider outer fences

## Anti-Patterns

| Anti-Pattern            | Problem                            | Fix                                        |
| ----------------------- | ---------------------------------- | ------------------------------------------ |
| **Missing frontmatter** | Skill won't be discovered          | Always include YAML with name/description  |
| **Weak descriptions**   | Description lacks trigger phrases  | Add "Use when…" with specific scenarios    |
| **Skill sprawl**        | SKILL.md for trivial procedures    | Only multi-step, bounded tasks             |
| **Unbounded scope**     | No clear start/end states          | Define prerequisites and success criteria  |
| **Abstract principles** | General knowledge, not procedures  | Use AGENTS.md for conventions instead      |
| **Code library**        | Hundreds of lines of boilerplate   | Move to `references/` or `assets/`         |
| **Repo-relative paths** | Breaks when symlinked to user root | Use `../other-skill/` from the skill folder|
| **Duplicated content**  | Same guidance in two skills drifts | One canonical home, cross-link the rest    |

## Good vs Poor Skill Candidates

| Good                                              | Poor                                     |
| ------------------------------------------------- | ---------------------------------------- |
| Multi-step workflows (deploy, release, migration) | Simple one-liners                        |
| Procedures with scripts or tooling                | General knowledge                        |
| Domain-specific tasks (database ops, API patterns)| Project-wide conventions (use AGENTS.md) |
| Bounded, completable tasks                        | Open-ended guidance                      |
| Tasks requiring specific file references          | Abstract principles                      |

---

## Core Principles

**Context window is a public good.** Skills share the window with everything else the agent needs. A skill that loads 600 lines to answer a 20-line question has made every other part of the task worse.

**Agents are already competent.** Only add context they don't already have. Do not explain the language, the framework, or general engineering practice.

**Calibrate freedom to fragility.** Match specificity to risk:

| Freedom | When                            | Format                            |
| ------- | ------------------------------- | --------------------------------- |
| High    | Multiple valid approaches       | Text instructions                 |
| Medium  | A preferred pattern exists      | Pseudocode, parameterized scripts |
| Low     | Fragile, error-prone operations | Specific scripts, exact commands  |

**Write for agents.** Assume technical competence, provide exact commands, include error messages agents will encounter, and define project-specific terminology.

---

## Validation Checklist

Before finalizing:

1. [ ] Commands actually work when executed
2. [ ] File paths exist and are skill-relative
3. [ ] Line count under 500
4. [ ] Valid YAML frontmatter with trigger phrases
5. [ ] Embedded template fences are balanced
6. [ ] No content duplicated from another skill
