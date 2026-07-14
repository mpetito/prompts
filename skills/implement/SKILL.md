---
name: implement
description: "Execute a spec end-to-end from `specs/{NNN-slug}/`: locate spec, apply clarifications, create or review the plan, then build all phases. Use when implementing a spec by number, running an existing spec plan, or completing all phases from `specs/`."
---
# Implement

Execute a spec from `specs/{NNN-slug}/` end-to-end.

## Inputs

- **Spec reference** (required): a number like `040`, `spec 040`, or a full slug like `040-feature-name`
- **Clarifications** (optional): answers to Open Questions from the spec

## Workflow

### 1. Locate the Spec

- Resolve the spec folder under `specs/` by matching the zero-padded prefix (e.g. `040` → `specs/040-*/`)
- If no folder matches, stop and report
- Read `spec.md`

### 2. Apply Clarifications

If the user provided answers to Open Questions:

- Update `spec.md`: move resolved questions out of **Open Questions** into **Decisions** (with rationale) or into the relevant Requirements/Constraints section
- Leave unresolved questions in place

If any **blocking** Open Questions remain unresolved, stop and surface them. Do not proceed to planning or implementation on top of unresolved blockers.

### 3. Plan: Create or Review

Check for `plan.md` in the spec folder.

- **No plan exists** → follow the `spec` skill (Phase 6) to create `plan.md` from `spec.md`
- **Plan exists** → review it for consistency with the (possibly updated) spec:
  - Every requirement and acceptance criterion maps to at least one step
  - No steps reference removed or contradicted requirements
  - Phases and verification checkpoints are coherent
  - Update `plan.md` in place if drift is found; note what changed

### 4. Implement All Phases

Follow the `code-authoring` skill, looping through every phase of `plan.md`:

For each phase: **Prepare → Implement → Test → Self-Review → Validate**, then check off the phase's steps in `plan.md` as they complete.

Do not stop between phases unless a blocker requires user input. Persist through context compaction by re-reading `spec.md` and `plan.md` after summarization.

### 5. Report

After all phases complete:

1. Spec + plan paths
2. Summary of what was implemented
3. Files created / modified
4. Test results
5. Any deferred items or follow-ups

Suggest `/review` for an independent quality pass or `/commit` to commit and open a PR.
