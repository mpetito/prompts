---
name: implement
description: "Execute a numbered spec from specs/{NNN-slug}/ end-to-end: apply answers to its open questions, create or review plan.md, then build every phase and check off its steps. Use whenever a request points at a spec folder or number (042, spec 042, 058-some-feature) and asks for the work to be done, even in plain words: implement or build an approved or signed-off design doc, spec, or step list; work through a plan.md, task list, or checklist until every step is done; resume, pick up, or finish a partly done spec or its remaining phases; or answer a spec's open questions and then continue building. Load it first, before searching for or opening the spec folder, even when that folder is not located yet. Not for drafting or writing up a new spec or plan before coding starts: this skill holds no spec.md or plan.md template, so use spec and do not open this skill for its format. Not for reviewing finished spec work before merge (review), or a fix or change with no numbered spec (code-authoring)."
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

Load [code-authoring](../code-authoring/SKILL.md), including its standards and required
self-review steps, and loop through every phase of `plan.md`. When delegating phases or
generating a workflow, apply [agent model selection](../skill-authoring/references/agent-model-selection.md)
before launch; set a model for every worker/stage.

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
