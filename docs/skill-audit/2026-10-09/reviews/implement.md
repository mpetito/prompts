# implement

Verdict: **good** · SKILL.md body 59 lines · description 1000 chars

implement is a tight 59-line skill. It names one sequence (locate the spec, apply answers, gate on blockers, plan, build every phase, report), stops at the right points, survives compaction by re-reading the spec and plan, and hands the per-phase protocol to code-authoring and plan creation to spec rather than repeating them. The biggest gap is the description: at 1,000 of the 1,024 allowed characters it has almost no room left, and its long "Not for drafting…" clause could be much shorter. Smaller issues are a closing /review suggestion that conflicts with code-authoring's required self-review, and an evals suite that tests triggering only.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names specs/{NNN-slug}/, plan.md, spec numbers (042, 058-some-feature), resume/finish/open-questions phrasings. |
| Description includes both what the Skill does and when to use it | pass | Opens with what it does, then 'Use whenever…', then Not-for disambiguation per collection convention. |
| SKILL.md body is under 500 lines | pass | 59 body lines. |
| Additional details are in separate files (if needed) | pass | Not needed; it delegates to code-authoring, spec Phase 6 and agent-model-selection.md instead of inlining them. |
| No time-sensitive information | pass |  |
| Consistent terminology throughout | partial | The same input is called 'Clarifications', 'answers to Open Questions' and (in the description) 'answers to its open questions'; spec is linked by name only while code-authoring gets a markdown link; review and commit are given as slash commands. |
| Examples are concrete, not abstract | pass | `040` → `specs/040-*/` resolution example. |
| File references are one level deep | pass | Direct links to ../code-authoring/SKILL.md and ../skill-authoring/references/agent-model-selection.md; no chained references. |
| Progressive disclosure used appropriately | pass | Workflow lives in this skill; coding protocol and plan format live in the skills that own them. |
| Workflows have clear steps | pass | Five numbered steps, explicit stop conditions, and plan.md checkboxes serve as the progress checklist. |
| Validation/verification steps for critical operations | pass | Blocking-question gate before planning; plan-vs-spec consistency review; per-phase Test/Self-Review/Validate. |
| Feedback loops included for quality-critical tasks | pass | Per-phase loop with checking off steps in plan.md; re-read the spec and plan after compaction. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No Windows-style paths | pass |  |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 should trigger, 3 should not) but no behaviour case with assertions; nothing tests the blocking-question stop, the spec.md edits, or checking off plan steps. |

## Findings

1. **medium** · Technical notes (description max 1,024 characters) / Writing effective descriptions · SKILL.md frontmatter description
   > Not for drafting or writing up a new spec or plan before coding starts: this skill holds no spec.md or plan.md template, so use spec and do not open this skill for its format.

   Fix: Shorten this clause to "Not for writing a new spec.md or plan.md before coding (spec)". That keeps the disambiguation the neg-trig-write-spec eval checks and frees about 110 of the 24 characters now left under the limit. Rerun the trigger evals after the edit. (about 25 tokens saved)

2. **low** · Use consistent terminology · SKILL.md ## 5. Report (line 63) vs ## 4. Implement All Phases
   > Suggest `/review` for an independent quality pass or `/commit` to commit and open a PR.

   Fix: Step 4 already loads code-authoring, which says to load review for self-review and 'do not defer self-review to an optional follow-up command'. Reword the line so it does not offer review as an optional extra, for example "Offer [commit](../commit/SKILL.md) to commit and open a PR". Use skill-relative links rather than slash commands, matching the other cross-references. (about 5 tokens saved)

3. **low** · Use consistent terminology · SKILL.md ## Inputs and ### 2. Apply Clarifications
   > - **Clarifications** (optional): answers to Open Questions from the spec … If the user provided answers to Open Questions:

   Fix: Pick one term, "answers to Open Questions", which matches the spec template's section name and the description. Rename the input and the step heading to it, for example '### 2. Apply Answers to Open Questions'.

4. **low** · Concise is key · SKILL.md ## Inputs (lines 9-12)
   > - **Spec reference** (required): a number like `040`, `spec 040`, or a full slug like `040-feature-name`

   Fix: Delete the Inputs section. Step 1 already explains how a spec reference resolves (`040` → `specs/040-*/`), and step 2 already covers optional answers, so the section repeats the description and the workflow. (about 55 tokens saved)

5. **low** · Use consistent terminology (cross-reference style) · SKILL.md ### 3. Plan: Create or Review
   > **No plan exists** → follow the `spec` skill (Phase 6) to create `plan.md` from `spec.md`

   Fix: Link it as [spec](../spec/SKILL.md) (Phase 6: Write the Plan), the same way code-authoring is linked in step 4. The collection's convention is skill-relative links, and a link makes the jump explicit instead of relying on a name lookup.

6. **low** · Build evaluations first / Checklist: At least three evaluations created · evals/shared-benchmark.json
   > "kind": "trigger" (all 8 cases); "assertions": []

   Fix: Add one or two behaviour cases with assertions for the steps that are easy to get wrong. For example, given answers that leave a blocking Open Question unresolved, the model must stop before planning. Given an existing plan.md, the model must check steps off as phases complete. Without these, a shortened skill cannot be checked for keeping its behaviour.

## Strengths

- Hands work to the skills that own it instead of copying them: the per-phase protocol goes to code-authoring, plan creation to spec Phase 6, and worker models to agent-model-selection.md. That keeps the body under 60 lines.
- Stop conditions are explicit at each gate: stop when no spec folder matches, and stop when a blocking Open Question remains, before any planning. The plan-review sub-checklist works as a feedback loop against spec drift.
- Recovery after compaction takes one sentence: re-read spec.md and plan.md after summarization. Checking off plan.md steps as they complete makes the plan the persistent progress checklist the best practices recommend.

## Cut candidates

- ## Inputs (restates the description and step 1's resolution rule)
- ### 5. Report closing line suggesting `/review` (code-authoring already requires the review self-review)
