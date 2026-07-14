---
name: spec
description: "Methodology for producing a `spec.md` (what + why) and `plan.md` (how) for a feature or change, using research and codebase analysis. Use when creating an implementation plan, writing a spec, breaking down a complex feature into phases, or scoping work before coding begins."
---

# Spec & Plan Authoring Skill

Procedural knowledge for turning a request into an actionable spec + plan pair under `specs/{NNN-slug}/`.

## When to Use

- The user asks for a plan, spec, design, breakdown, or roadmap for a non-trivial feature
- Work spans multiple files, components, or systems and benefits from upfront design

For small, obvious changes go straight to implementation (no spec needed).

## Context Sources (priority order)

1. **Direct user input**

## Process

### Phase 1: Understand the Request

Decompose the request into:

- Core objectives and success criteria
- Implicit requirements and assumptions
- Ambiguities or gaps that need clarification
- Suggested scope boundaries (in-scope vs out-of-scope)

### Phase 2: Research

Investigate in parallel as needed:

- **Codebase architecture**: folders, modules, key abstractions, integration points
- **Pattern discovery**: similar existing features and their conventions
- **Dependency analysis**: imports, integration points, breaking-change risks
- **API / library research**: official docs and constraints (reference the `research` skill)
- **Impact assessment**: affected files, migrations, backwards-compat concerns

Delegate independent research tasks to subagents (e.g. `Explore` for codebase mapping, a research-capable subagent for docs) to preserve planning context.

### Phase 3: Clarify Blocking Ambiguities

If blocking ambiguities remain after research, ask 3–5 numbered questions, each with the decision it unlocks. Do not write the spec on top of unresolved blocking unknowns.

### Phase 4: Write the Spec

- Determine the next folder: scan `specs/` for existing numbered folders and pick the next zero-padded prefix + kebab slug (e.g. after `012-x` → `013-new-feature/`)
- Create `specs/{NNN-slug}/spec.md` from the template below
- The spec defines **what** and **why** — requirements, constraints, decisions, acceptance criteria
- Capture every unresolved uncertainty in an **Open Questions** section
- Do **not** include implementation details — those belong in the plan
- Calibrate depth to the **complexity tier** (see below); a fix spec is short, a greenfield feature is long

Heavy research outputs that informed the spec can be saved alongside it (see **Supporting Documents** below).

#### Spec Complexity Tiers

Use these as a sanity check, not a hard contract:

| Tier | Typical use                         | Requirements | Sections to include                                                       |
| ---- | ----------------------------------- | ------------ | ------------------------------------------------------------------------- |
| 1    | Fix, follow-up, small enhancement   | 2–6          | Metadata, Context, Objective, Scope, Requirements, Acceptance Criteria    |
| 2    | Medium feature                      | 8–20         | Tier 1 + Design Constraints, Decisions, Current vs Proposed State         |
| 3    | Large feature, infrastructure, perf | 20–40+       | Tier 2 + Supporting Documents, Risks (in plan), Success Metrics (in plan) |

#### Supporting Documents Convention

Split analysis into a sibling file when it exceeds ~400 words or is reusable by implementers (route audits, RCAs, baseline metrics, inventory). Common names:

- `research-findings.md` — API docs research, library comparisons
- `phase-1-analysis.md` — baseline metrics, route audit, RCA, inventory
- `architecture-analysis.md` — existing-pattern review, dependency mapping

Reference them from the spec's Context and list them under `## Supporting Documents`.

### Phase 5: Gate on Open Questions

After writing the spec, review its Open Questions:

- **Blocking questions remain**: stop. Present them to the user. Do not write a plan on top of unresolved decisions.
- **Only minor/low-risk uncertainty**: proceed immediately to Phase 6.

A question is **blocking** if it changes architecture, scope, or which systems are touched. It is **not blocking** if an implementer can pick a sensible default within existing conventions (e.g. exact spacing values, copy wording). Examples:

- ❌ Blocking: "Do we add a real-time notification service, or defer to v2?" (changes architecture)
- ✅ Non-blocking: "What exact border-radius for cards?" (implementer decides within design system)

### Phase 6: Write the Plan

- Create `specs/{NNN-slug}/plan.md` from the template below
- Plan defines **how** — phases, ordered steps, file targets, verification
- Every requirement and acceptance criterion in the spec must map to at least one step
- Steps must be specific and actionable (name files, components, functions)
- Group steps into logical phases each with a verification checkpoint
- Do **not** introduce new requirements in the plan — those belong in the spec

## Spec Folder Convention

```
specs/
  001-user-auth/
    spec.md          # What and why
    plan.md          # How (phases + steps)
  002-api-caching/
    spec.md
    plan.md
  003-notification-service/
    spec.md          # May exist without plan.md if blocking questions remain
    research-findings.md   # Optional supporting docs
```

- Root: `specs/`
- Subfolder: 3-digit zero-padded prefix + kebab slug
- Match style/structure of existing siblings if present

## Document Roles

| Document  | Contains                                                                                                      | Does NOT contain                                  |
| --------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `spec.md` | Requirements, constraints, decisions, acceptance criteria, scope, open questions                              | Implementation details, file paths, code patterns |
| `plan.md` | Phases, ordered steps with file/component targets, architecture decisions, file change manifest, tests, risks | New requirements (those belong in the spec)       |

## Spec Template

```markdown
# Spec: [Name]

| Field   | Value                                          |
| ------- | ---------------------------------------------- |
| Spec    | NNN                                            |
| Date    | YYYY-MM-DD                                     |
| Status  | Draft \| In Progress \| Done                   |
| Domain  | [area tags, e.g. checkout, infra, perf]        |
| Depends | NNN (what it provides), NNN (what it provides) |

## Context

[Short background — what prompted this work and why now. Reference supporting documents if applicable.]

## Objective

[Primary goal in 1–2 sentences]

## Current vs Proposed State

| Aspect       | Current              | Proposed                             |
| ------------ | -------------------- | ------------------------------------ |
| [Behavior]   | [How it works today] | [How it should work after this spec] |
| [Data model] | [Current shape]      | [New shape]                          |
| [User flow]  | [Current steps]      | [New steps]                          |

## Scope

### In Scope

- [item]

### Out of Scope

- [item — note the deferral reason: "deferred to spec NNN", "add if X grows", "requires infra investment"]

## Requirements

Number requirements (FR-1, NFR-1) so acceptance criteria and plan steps can reference them. Omit numbering for Tier 1 specs with very few requirements.

### Functional

#### FR-1: [Short title]

[Detailed requirement]

#### FR-2: [Short title]

[Detailed requirement]

### Non-Functional

#### NFR-1: [Short title]

[Performance, reliability, security, observability, accessibility, etc.]

## Design Constraints

| Constraint  | Rationale                     |
| ----------- | ----------------------------- |
| [Invariant] | [Why this cannot be violated] |

## Acceptance Criteria

Each criterion should map to one or more requirements. Reference requirement IDs where possible.

- [ ] [Verifiable criterion] (FR-1, FR-2)
- [ ] [Verifiable criterion] (NFR-1)

## Decisions

| Decision | Choice   | Rationale                      |
| -------- | -------- | ------------------------------ |
| [Area]   | [Choice] | [Why chosen over alternatives] |

## Open Questions

**Gate**: Do not write the plan if blocking questions remain.

- [ ] [Question] — **Why it matters**: [decision it unlocks]. **Blocks**: [phase/step]

## Supporting Documents

(Optional; omit if none.)

- `phase-1-analysis.md` — [brief description]
- `research-findings.md` — [brief description]
```

## Plan Template

```markdown
# Plan: [Feature/Task Name]

**Spec**: [specs/NNN-slug/spec.md](specs/NNN-slug/spec.md) | **Date**: [YYYY-MM-DD]

## Summary

[2–3 sentence overview of what will be implemented and the approach]

## Architecture Decisions

| Decision | Choice   | Rationale |
| -------- | -------- | --------- |
| [Area]   | [Choice] | [Why]     |

## Implementation Phases

Each phase ends with concrete verification — specific checkable outcomes, not generic "run tests".

### Phase 1: [Name]

**Goal**: [1-sentence outcome]

1. [ ] Step with specific file/component targets
2. [ ] Step with specific file/component targets

**Verification**:

- [ ] [Specific checkable outcome, e.g. "`grep -r 'networkidle'` returns zero matches"]
- [ ] [Build/lint/typecheck passes]

### Phase 2: [Name]

**Goal**: [1-sentence outcome]

1. [ ] Step with specific file/component targets

**Verification**:

- [ ] ...

## File Changes

| File         | Action               | Purpose        |
| ------------ | -------------------- | -------------- |
| path/to/file | Create/Modify/Delete | [What and why] |

## Testing Strategy

- [ ] Unit tests for [component/function]
- [ ] E2E tests for [user flow]
- [ ] Manual validation: [scenario]

## Success Metrics

(Optional; use for perf/optimization/infra specs where binary acceptance criteria are insufficient.)

- [ ] [Quantitative target, e.g. "LCP < 2.0s on /shop", "build time < 10 min"]

## Risks & Mitigations

Required for plans touching infrastructure, deployment, data migration, or external integrations. Optional otherwise.

| Risk   | Likelihood | Mitigation      |
| ------ | ---------- | --------------- |
| [Risk] | [H/M/L]    | [How to handle] |
```

## Guidelines

- Ground recommendations in actual research, not assumptions
- Cite specific files with brief context (function/class names, key snippets)
- Verify libraries/patterns are compatible with the current project stack
- Each plan step must be implementable as-is
- Identify dependencies between steps
- Consider backwards compatibility and migration paths
- Do **not** include time or effort estimates unless explicitly requested

## Output

- **Spec only** (blocking open questions): present the questions; include path to `spec.md`
- **Spec + Plan**: brief summary with paths to both files, highlighting goal, phases, key decisions
- **Pre-spec clarifications**: short numbered questions when the request is too ambiguous to even spec

Suggest next step: implementation (the `code-authoring` skill will pick up automatically when the user asks to build it).

## Boundaries

- ✅ Research codebase, write spec and plan files
- ⚠️ Ask first: major architectural decisions, new dependency introductions
- 🚫 Never implement code directly — produce plans, not code
- 🚫 Never skip research for non-trivial features
