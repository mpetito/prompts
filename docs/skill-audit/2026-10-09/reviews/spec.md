# spec

Verdict: **needs-work** · SKILL.md body 331 lines · description 270 chars

The skill has a clear phased workflow with a hard gate on blocking open questions, well-specified templates, and checkable acceptance-criteria rules backed by two strong behaviour evals and six trigger cases. Its main gap is a description that stops short of the rest of the collection's trigger precision: it has no "Not for" clause, although its own evals test near-misses for implement and story. It also hands off to the wrong next skill, and about a third of the body restates rules or generic planning advice.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Names spec.md, plan.md and specs/{NNN-slug}/, but at 270 chars it lacks the collection's 'Not for … (other-skill)' disambiguation, while the evals test implement and story near-misses |
| Description includes both what the Skill does and when to use it | pass | 'Write a spec.md … Use when creating an implementation plan, writing a spec …' |
| SKILL.md body is under 500 lines | pass | 331 body lines (335 total) |
| Additional details are in separate files (if needed) | partial | No references/ folder; about 160 lines of spec and plan templates sit inline, and the plan template is not needed on the spec-only (blocked) path |
| No time-sensitive information (or in an 'old patterns' section) | pass |  |
| Consistent terminology throughout | partial | The same gate is called 'blocking ambiguities', 'blocking unknowns', 'blocking questions' and 'Pre-spec clarifications'; the skill's own 'Phase 1–6' process collides with the plan template's 'Phase N' implementation phases |
| Examples are concrete, not abstract | pass | Blocking versus non-blocking examples, measured criterion example, grep verification example |
| File references are one level deep | partial | The state-by-event event list is deferred to the Testing standards of ../code-authoring/SKILL.md instead of being stated inline |
| Progressive disclosure used appropriately | partial | Everything is inline; acceptable at 331 lines, but the plan template could load only at Phase 6 |
| Workflows have clear steps | pass | Phases 1–6 with explicit gates at Phase 3 and Phase 5 |
| Validation/verification steps for critical operations | pass | Phase 5 open-question gate; every requirement must map to a plan step; each plan phase ends with a Verification list |
| Feedback loops included for quality-critical tasks | partial | No explicit final check that every FR/NFR and acceptance criterion maps to a plan step before output; the rule is stated but not run as a check |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts |
| No Windows-style paths (all forward slashes) | pass |  |
| At least three evaluations created | partial | 8 cases in evals/shared-benchmark.json, but only 2 are behaviour cases; the remaining 6 are trigger cases. The Tier 1 short-spec path and sibling-style matching are untested |
| Tested with real usage scenarios | pass | Fixtures use realistic requests with traps: newest-modified versus highest spec number, an unconfirmed safety claim, and release pressure |

## Findings

1. **high** · Use consistent terminology / Workflows have clear steps · SKILL.md, Output (line 328)
   > Suggest next step: implementation (the `code-authoring` skill will pick up automatically when the user asks to build it).

   Fix: Name `implement` as the next step ("build it with the `implement` skill: `/implement spec NNN`"). code-authoring's own description says "Not for executing a numbered spec's plan (implement)", and the README workflow is /spec → /implement.

2. **medium** · Writing effective descriptions (specific triggers; collection's 'Not for' disambiguation convention) · SKILL.md frontmatter description
   > Use when creating an implementation plan, writing a spec, designing a breakdown or roadmap, or phasing and scoping a non-trivial feature before coding begins.

   Fix: Add a closing clause such as "Not for executing an existing spec or plan (implement), ADO user stories or acceptance criteria on a work item (story), or small obvious fixes (code-authoring)." The evals already test these three near-misses (neg-trig-implement-plan, neg-trig-ado-story, neg-trig-small-fix), and sibling descriptions point back to `spec`.

3. **medium** · Concise is key (no duplicated content) · SKILL.md, When to Use (lines 10–15), Spec Folder Convention (123–140), Document Roles (142–147)
   > - Do **not** include implementation details — those belong in the plan
| `spec.md` | Requirements, constraints, … | Implementation details, file paths, code patterns |

   Fix: Delete When to Use, which repeats the description; keep its single 'small, obvious changes need no spec' line under Phase 1. Merge Document Roles into the Phase 4 and Phase 6 bullets, or drop the bullets and keep the table. Cut the Spec Folder Convention tree and bullets, since Phase 4 already states the 3-digit prefix and kebab slug and says to match siblings. (about 330 tokens saved)

4. **medium** · Concise is key ('Default assumption: Claude is already very smart') · SKILL.md, Phase 2: Research (lines 37–43), Guidelines (312–320), Boundaries (330–335)
   > - Ground recommendations in actual research, not assumptions
- Consider backwards compatibility and migration paths

   Fix: Cut the five-item research taxonomy to one line (patterns to match, integration points, affected files, library constraints via `research`). Reduce Guidelines to the only non-obvious rule, 'no time or effort estimates unless asked'. Drop the Boundaries lines that repeat Phase 2 ('Never skip research') or are implied ('Research codebase, write spec and plan files'). (about 250 tokens saved)

5. **medium** · Use consistent terminology · SKILL.md, Phase 3 (line 51), Phase 5 (104–109), Output (326), Open Questions template (230)
   > Do not write the spec on top of unresolved blocking unknowns.
**Pre-spec clarifications**: short numbered questions when the request is too ambiguous to even spec

   Fix: Use one term, 'blocking question', everywhere, and define it once, at Phase 5's definition (it changes architecture, scope or the systems touched). Have Phase 3 point to that definition. Rename the skill's own steps 'Step 1–6' so they cannot be confused with the plan template's 'Phase N' implementation phases that the implement skill checks off. (about 40 tokens saved)

6. **low** · Avoid deeply nested references (one level deep) · SKILL.md, Phase 4, acceptance-criteria bullets (lines 70–71)
   > for stateful logic, require a state-by-event table with one test per cell (the events to
    cover are in the Testing standards of [code-authoring](../code-authoring/SKILL.md))

   Fix: State the events inline, 'reruns, cancellations, races, malformed state, partial failure', and drop the link. This saves loading a 233-line sibling skill to find one list. (about 10 tokens saved)

7. **low** · Progressive disclosure patterns (Pattern 1: load details only when needed) · SKILL.md, Plan Template (lines 242–310)
   > ### Phase 6: Write the Plan
- Create `specs/{NNN-slug}/plan.md` from the template below

   Fix: Move the plan template to references/plan-template.md and link it from Phase 6. When the Phase 5 gate stops at a spec only, about 70 lines go unread. implement's 'follow the spec skill (Phase 6)' pointer still resolves through that link. (about 600 tokens saved)

8. **low** · Build evaluations first (at least three evaluations) · evals/shared-benchmark.json
   > "id": "pos-spec-and-plan-ui-feature" … "id": "pos-blocking-question-gate"

   Fix: Add a third behaviour case for the Tier 1 path: a small fix with existing sibling specs, asserting a short spec with only the Tier 1 sections and a plan. Tier calibration is the main untested instruction, and the case would show whether the tier table earns its tokens.

## Strengths

- Two behaviour evals are built around realistic traps: picking the most recently modified spec instead of the highest number, an unconfirmed safety claim offered as final copy, and release-date pressure that invites estimates. Regex assertions and a judge rubric check each trap.
- An explicit gate with a concrete blocking versus non-blocking test and one example of each ('changes architecture' versus 'implementer decides within design system') tells the model exactly when to stop before the plan.
- Acceptance-criteria rules turn subjective requests into named measures and thresholds, and require a state-by-event table, a threat model, or the main consumer's review where each applies. These are specific rules a model would not apply unprompted.

## Cut candidates

- When to Use (repeats the description)
- Spec Folder Convention (tree and bullets repeat Phase 4)
- Document Roles (repeats the Phase 4 and Phase 6 'Do not' bullets)
- Phase 2: Research bullet taxonomy (generic research advice)
- Guidelines (all but the no-time-estimates rule)
- Boundaries ('Research codebase, write spec and plan files' and 'Never skip research')
