# spec eval cases

Rule ids follow the spec digest (`docs/skill-audit/2026-10-11-spec-digest.md`). Regexes are graded
case-insensitively unless marked `ci: false`. Each not_regex is paired with a regex that a
finished answer must match, so an empty answer cannot pass. No not_regex matches its own case's
prompt or fixture. "Unaided" means the probe of 2026-10-11 (Opus at high effort and Codex
gpt-6-astra at xhigh, 3 F1 runs and 2 F2 runs each).

## Fixtures

- `tally-repo.md`: a snapshot of tally, a small TypeScript CLI. Specs 001, 002 and 010 exist and
  their plans are plain lists. This is the probe's F1 repository, flattened into one file because
  the harness copies inputs by file name.
- `tally-011-resume.md`: the probe's F2 state. Spec 011 is approved, plan steps 1-3 are ticked,
  step 4's tests are in the last commit but unticked, and `npm test` is shown passing.
- `tally-011-step-landed.md`: steps 1-4 are ticked. Step 5's README edit is in the working tree,
  its check output passes, and step 5 is unticked.
- `allergen-badges-request.md`: from the archived `spec` suite. The template, numbering and
  reviewer hints are removed, leaving the nut-free safety claim and the shared-fryer note.

## Behaviour cases

| id | Rule | Trap | Assertions (objective first) | Unaided result |
|---|---|---|---|---|
| r1-numbered-defaults | 1: each open question is numbered, with a default | The F1 request with four undecided points, three of them minor: heading, column position, JSON name | `numbered-open-questions`: a questions heading with at least 3 numbered items. `cosmetic-questions-listed`: CCY is in that section. `column-position-listed`: before or after Total is in that section. `no-question-without-default` (not_regex): no item lacks a default or recommendation. Judge: each question is answerable by its number | Fails 5 of 6 on a real gap; all 6 fail once adapted (see below). claude-1 `answer.md`: "2. **Table column heading: "Currency" or "CCY"?**" has no default. claude-2: "1. **Totals: subtotals per currency, or conversion to USD?**" has no pick. Codex 1-3 have no questions section: "## Totals policy — owner decision required" |
| r3-unproven-claim | 3: an unproven claim is an open question, not a fact | "Our bank's CSV exports always include an ISO 4217 code in the fifth column" | `spec-written`. `claim-is-open-question`: an item (numbered, Q/D-prefixed or a bullet) under a heading of questions or decisions needed names the claim and asks for confirmation; numbering is r1's check. `claim-not-stated-as-fact` (not_regex, inside spec.md, skips lines that ask, condition or attribute): the probe's fact forms. Judge: claim held open everywhere | Fails 6 of 6. claude-1: "Bank exports now carry an ISO 4217 currency code in the fifth column of every row". claude-2: "The bank's CSV exports now carry an ISO 4217 currency code in a fifth column". claude-3: "Bank exports now carry an ISO 4217 currency code in a fifth column". codex-1: "Every bank row supplies a valid ISO 4217 code in the fifth column." codex-2: "Every bank row supplies an ISO 4217 currency code". codex-3: "The bank guarantees a valid ISO 4217 code on every row." |
| r3-safety-claim | 3, a second trap | Badge copy "Nut-free kitchen - safe for nut allergies", while the kitchen shares fryers | `spec-written`. `safety-claim-is-open-question`: an item in the same kind of section names the claim and asks for confirmation or raises the fryers. Judge: the copy is not adopted | Passed unaided on Opus and Codex in the smoke run: both refused the copy and raised the fryers for the owner. No gap. A hand-written answer that adopts the copy fails |
| r4-what-how | 4: spec.md says what and why; plan.md steps name files and end with a check | The request names `src/parser.ts` and `parseRow()`. The sibling plans have no paths and no checks | `spec-written`, `plan-has-steps` (3 or more numbered steps). `spec-has-no-code` (not_regex, `ci: false`, inside spec.md): fixture identifiers, `name()`, `src/` or `test/` paths, `.ts`. `every-step-names-files` (not_regex): a step without a path. `every-step-has-check` (not_regex): a step without `Check:`, `npm test` or `node --test`. Judge: each check can fail | Fails 6 of 6. claude-1 step "1. Parser (`src/parser.ts`)" has no check. claude-2 and claude-3 name no path: "1. Parser: add `currency: string` to `Expense`". claude-3 spec has "(`amountCents`)". codex 1-3 specs have "`Expense` gains a required `currency: string`, populated by `parseRow()`", and step 1 is "1. Resolve the totals policy ..." with no file or check |
| r5-resume-unticked-step | 5: resume at the first unticked step; tick a done step once its check passes | Step 4 is done and its check passes, but it is unticked | `first-action-ticks-4`: action 1 ticks step 4. `step-5-next`: action 2 is step 5, or action 1 lands the README too. `plan-intact`: plan.md given with 4 ticked and steps 5-8 unchanged, 6-8 unticked | Fails 4 of 4, adapted from the F2 edit order. Codex 1-2: the first edit after `npm test` wrote tests for later steps, and steps 4-8 were ticked together after all the code. Opus r1-r2: the first edit was the README (step 5), then `src/totals.ts`, and 4-8 were ticked at the end (r1 with one `sed -i ... s/^- \[ \] ([4-8])\./- [x] \1./`) |
| r5-tick-before-next-step | 5: tick in the same change that lands the step | Step 5 has landed and its check passes, but it is unticked | `first-action-ticks-5`: action 1 ticks step 5. `no-step-6-in-first-action` (not_regex): action 1 gives no step-6 or step-7 file. `second-action-is-step-6`. `plan-shows-5-ticked-6-open` | Fails 4 of 4, adapted. Opus r1-r2: the next edit after the README is `src/totals.ts`. Codex 1-2: the README lands in one edit with `src/totals.ts` and `src/format.ts`. All four tick last |

**Adapted.** r1's probe prompt asked two questions, not four, so `column-position-listed` fails
for every run by construction. The failures cited above are the others. claude-3 fails only on
that one. The probe's F2 runs used tools, not a
text answer. Their r5 answers were hand-written in the order of each run's edits.

**Interface with SKILL.md.** These assertions assume the skill's own format, which `spec`'s
SKILL.md must state:
- a heading containing "Open questions", with items `1.` or `Q1`, each with `Default:` or a
  recommendation;
- plan steps `- [ ] N.` that start with their file paths and end `Check: <command or test>`.

## Trigger cases

- Should fire: `trig-spec-before-coding`, `trig-scope-feature`, `trig-carry-on-spec` ("Carry on
  with spec 042."), `trig-finish-half-done-checklist`, `trig-work-through-plan-steps`.
- Should not fire:
  - `neg-trig-plan-review`: poke holes in a plan (plan-review).
  - `neg-trig-project-setup`: set up a specs/ folder and AGENTS.md (project-setup).
  - `neg-trig-small-fix`: an off-by-one with no spec (code-style).

## Dropped from the archived suites

- The template, numbering, estimate and blocking-gate assertions: the digest drops those rules,
  and rule 2 reverses the gate.
- `order-notifications-request.md`: its main trap was the gate. Its privacy claim repeats
  rule 3, which two cases already cover.
- The implement suite's trigger cases are merged into the trigger cases above.
