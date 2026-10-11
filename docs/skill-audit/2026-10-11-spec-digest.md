# Spec digest (2026-10-11)

**Skill name:** `spec`, which readmits the archived `spec` and `implement` as one skill.
**Role (worker):** loaded by the session or by a lane worker that writes a spec and plan, or
carries one out. Target under 80 lines.

**Sources:**
- **Evidence (E):** 302 typed or queued Claude messages from the owner, about 150 Codex turns the
  owner typed, 30 spec folders across 4 projects, and 13 PR comments judged to be the owner's.
- **Probe (P):** unaided Opus 5.5 (effort high) and Codex gpt-6-astra (effort xhigh), run under
  the eval harness's own conditions. Opus had no user skills; Codex still loads
  `~/.agents/skills`. F1 asked for a spec and plan for a medium feature (3 runs per agent). F2
  asked the model to carry on with a half-done plan, with tools (2 runs per agent).
- **Tags:** P1-P4 are opaque per-project tags, local to this file. Project names, sessions and
  links are in the private evidence store.

## What the probe and the evidence say together

- **The format rules mostly hold already.**
  - All 6 F1 runs picked the next number (`specs/011-…`), avoiding the gap and the
    newest-dated trap.
  - All 6 asked for review before code.
  - No run gave a time estimate.
  - The 30 real spec folders follow the archived template's sections closely.
  - The owner never corrected numbering, sections, estimates or length.
  - **Numbering, the templates and the complexity tiers are dropped.**
- **The owner's real corrections are about questions.** Each question gets a default and its own
  context, and the work proceeds instead of waiting. The archived "blocking questions remain:
  stop" gate runs against all 8 owner corrections. Two project briefs overrode it.
- **The models fail on separation and on claims.**
  - All 6 runs stated the requester's unproven claim as fact.
  - All 6 leaked how into the what: Codex put code identifiers in spec.md, and Opus wrote plans
    with no file targets or checks.
  - Codex ticked plan.md once, at the end, for all steps.

## Proposed rules

| # | Rule | Owner evidence | Unaided model (P) | Eval | Scope |
|---|---|---|---|---|---|
| 1 | **Every open question in spec.md is numbered and gives a recommended default, with enough context that the owner can answer "agreed" by number.** | 11 replies by number to defaults. One: "I agree with all your defaults and recommendations." (this repository, 2026-10-11). 6 asked for missing context, for example "I need more info / context on 1-3." (P2, 2026-10-08). The archived template has no default field. | Opus: 2 of 3 runs left the cosmetic question without a default. Codex: 3 of 3 gave defaults. | Yes. It's weak on Opus, so the trap needs several minor questions. | general |
| 2 | **Write the plan on the defaults, rather than stopping. Stop only for what the owner reserved: money, access, destructive or production changes, and legal or product facts.** | 8 corrections, all toward proceeding. "try not to block yourself on questions … proceed, using decision logs and handoffs" (P1, 2026-09-28). "I need to be able to observe your progress" was the answer to a model that wrote "Nothing else moves until you answer" (P2, 2026-10-06). None asked the model to stop. | 6 of 6 already plan on their own default. There's no gap. The archived gate would make it worse. | None. One line replaces the archived gate. | general |
| 3 | **A claim the request asserts without proof goes under Open Questions for the owner to confirm, not into the spec as fact.** Such claims are a product fact, a safety, legal or money claim, or a guarantee about another system. | No owner quote. The rule comes from the archived skill. | 6 of 6 (both agents) wrote "The bank guarantees a valid ISO 4217 code on every row" as a requirement. | Yes, strong. | general |
| 4 | **spec.md says what and why, with no file paths, identifiers or code. plan.md says how: ordered steps that each name the files they touch and end with a check that can fail.** | The owner's scope for this build: "spec.md (what and why) and plan.md (how)". No correction of a leak in 30 folders, though leakage is heavy in one project. | Codex: 3 of 3 put `parseRow()` and type names in spec.md. Opus: 3 of 3 plans had no file paths or no checks. | Yes, strong on both. | general |
| 5 | **When carrying out a plan, tick each step in plan.md in the same change that lands it, never in a batch at the end. Resume at the first unticked step: tick a step that is already done once its check passes, and don't redo or re-plan it.** | The owner's scope: "ticking off steps in plan.md as they land". "It now cannot check off the elements of the plan it has completed." (this repository, 2026-10-10). The files show 21 of 562 plan boxes ticked. | Codex: 2 of 2 runs ticked steps 4-8 in one edit after all the code. Both resumed correctly. Opus: rerun pending. | Yes, as a snapshot. Live interleaving is a probe-only signal. | general |
| 6 | **Links, not rules:** review with [plan-review](../plan-review/SKILL.md) before code; `specs/` layout is [project-setup](../project-setup/SKILL.md)'s; code under [code-style](../code-style/SKILL.md); a plan with several lanes seeds an [agent-orchestration](../agent-orchestration/SKILL.md) build. | The owner's scope. "when we restore the spec writing skill, it would be useful for it to run the same adversarial review" (this repository, 2026-10-10). | 6 of 6 named a review, but none named plan-review. | None, since the arms have no Agent tool or skills. | links |

**Dropped:**
- **Numbering:** no gap, no owner quote.
- **Spec and plan templates, complexity tiers, supporting-docs convention:** the models already
  write these sections, and no owner quote asks for them.
- **No estimates:** no gap.
- **Status fields and specs/README.md upkeep:** the owner never maintained either.
- **The archived blocking gate:** rule 2 replaces it.
- **Plan order (the owner sees something real early):** plan-review checks it, and
  agent-orchestration owns it for builds.
- **Simplicity:** owned by code-style and plan-review.
- **Re-read after compaction:** both agents already resumed correctly from plan.md.
- **"Don't stop between phases":** no gap.

## Does implement survive?

**As one section, about 5 lines: carry out the plan.** It holds rule 5, "under code-style",
"spec edits go back to the owner, never silently" (evidence: an owner brief, P1), and "update
plan.md in place when a step proves wrong, and say so". There is no owner correction either way
on re-planning; in practice the agents in 3 of 4 projects updated plans in place. Nothing else
from implement adds behaviour: locating the folder, the report list and the phase loop are
already what the models do.

## Questions for the owner

1. **Rules 1-5 and the dropped list as proposed?** Default: yes.
2. **Rule 2, the gate:** proceed on defaults and stop only for what the owner reserved, or keep
   the archived stop at blocking questions? Default: proceed (8 corrections, 0 the other way).
3. **Rule 3 has no owner quote, only a 6 of 6 probe failure.** Keep it? Default: keep it, as
   the strongest trap on both agents.
4. **Checkbox format for plan.md.** The owner's files use `1. [ ]` for steps and `- [ ]` for
   checks; the newest project uses none. Default: `- [ ]` per step, matching each project's
   existing plans when there are any.

## Spend so far

- Claude: $1.09 of $30 (probe).
- Codex: about 0.7M tokens (probe).
- No rule-specific eval spend before the owner confirms.
