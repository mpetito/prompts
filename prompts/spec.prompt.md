---
name: spec
description: Produce a spec.md (what + why) and plan.md (how) under specs/{NNN-slug}/ for a feature or change
---

# Spec & Plan

Turn the request below into a `spec.md` and (when ready) `plan.md` under `specs/{NNN-slug}/`.

Follow the `spec-planning` skill:

1. Decompose the request into objectives, assumptions, ambiguities, and scope
2. Research the codebase and any relevant docs in parallel via subagents
3. Ask blocking clarifying questions only when truly needed (max 3–5)
4. Write `spec.md` (what + why, with Open Questions)
5. Gate: if blocking open questions remain, stop and surface them
6. Otherwise write `plan.md` (how — phases, steps, file targets, verification)

Output paths to both files (or to the spec alone with open questions), plus a brief summary of goal, phases, and key decisions.

## User Input

If the user provided additional context below, use it as the starting input. Otherwise, refer to the refined prompt from the preceding `/refine`.

```text
$ARGUMENTS
```
