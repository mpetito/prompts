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
- `tally-011-tick-order.md`: the probe's F2 repository with spec 011 approved, steps 1-4 ticked
  and landed, and `npm test` shown passing. Steps 5-8 are open, and each touches different files:
  `src/totals.ts` and its test, `src/format.ts` and its test, `README.md`, `package.json`.

## Behaviour cases

| id | Rule | Trap | Assertions (objective first) | Unaided result |
|---|---|---|---|---|
| r1-numbered-defaults | 1: each open question is numbered, with a default | The F1 request with four undecided points, three of them minor: heading, column position, JSON name | `numbered-open-questions`: a heading of open questions or decisions still to make ("Open decisions", "Decisions needed"), with at least 3 items numbered `1.`, `Q1` or `D1`. `cosmetic-questions-listed`: CCY is in that section. `column-position-listed`: before or after Total is in that section. `no-question-without-default` (not_regex): no item lacks a default or recommendation. Judge: each question is answerable by its number | Fails 5 of 6 on a real gap; all 6 fail once adapted (see below). claude-1 `answer.md`: "2. **Table column heading: "Currency" or "CCY"?**" has no default. claude-2: "1. **Totals: subtotals per currency, or conversion to USD?**" has no pick. Codex 1-3 have no questions section: "## Totals policy — owner decision required" |
| r3-unproven-claim | 3: an unproven claim is an open question, not a fact | "Our bank's CSV exports always include an ISO 4217 code in the fifth column" | `spec-written`. `claim-is-open-question`: an item (numbered as in r1, or a plain bullet) under r1's kind of heading names the claim and asks for confirmation; numbering is r1's check. `claim-not-stated-as-fact` (not_regex, inside spec.md): the probe's and smoke runs' fact forms (guarantee, supplies, carries, includes, puts, has, sends), matched per sentence across wrapped lines; a sentence that asks, conditions or attributes the claim is skipped. Judge: claim held open everywhere | Fails 6 of 6. claude-1: "Bank exports now carry an ISO 4217 currency code in the fifth column of every row". claude-2: "The bank's CSV exports now carry an ISO 4217 currency code in a fifth column". claude-3: "Bank exports now carry an ISO 4217 currency code in a fifth column". codex-1: "Every bank row supplies a valid ISO 4217 code in the fifth column." codex-2: "Every bank row supplies an ISO 4217 currency code". codex-3: "The bank guarantees a valid ISO 4217 code on every row." |
| r4-what-how | 4: spec.md says what and why; plan.md steps name files and end with a check | The request names `src/parser.ts` and `parseRow()`. The sibling plans have no paths and no checks | `spec-written`, `plan-has-steps` (3 or more numbered steps). `spec-has-no-code` (not_regex, `ci: false`, inside spec.md): fixture identifiers, `name()`, `src/` or `test/` paths, `.ts`. A step is a list item (`- [ ] N.`, `N.`, `N)`) at the indent of the plan's first step; wrapped or deeper lines belong to the step above. `every-step-names-files` (not_regex): a step without a path. `every-step-has-check` (not_regex): a step without `Check:`, `npm test` or `node --test`. Judge: each check can fail | Fails 6 of 6. claude-1 step "1. Parser (`src/parser.ts`)" has no check. claude-2 and claude-3 name no path: "1. Parser: add `currency: string` to `Expense`". claude-3 spec has "(`amountCents`)". codex 1-3 specs have "`Expense` gains a required `currency: string`, populated by `parseRow()`", and step 1 is "1. Resolve the totals policy ..." with no file or check |
| r5-tick-order | 5: tick each step in the change that lands it, never in a batch | Four open steps with distinct files; the answer is the complete ordered list of edits, one per line, each starting with its path | `every-step-edited`: a line for each step's files (the list reaches step 8). `every-step-ticked`: a plan.md line ticking each of 5-8; the step a line ticks is the first it names. `tick-before-next-step` (not_regex): an edit to step N+1's files before the tick of N. `no-edit-after-own-tick` (not_regex): an edit to step N's files after its tick | The probe's 4 of 4 tool runs ticked 5-8 in one batch after all the code. As a text list it does not reproduce: the smoke run (2 runs each) interleaved every tick on Opus and Codex. No gap in this form |

**Adapted.** r1's probe prompt asked two questions, not four, so `column-position-listed` fails
for every run by construction. The failures cited above are the others. claude-3 fails only on
that one.

**Interface with SKILL.md.** These assertions assume the skill's own format, which `spec`'s
SKILL.md must state:
- a heading such as "Open questions" (or "Open decisions"), with items `1.`, `Q1` or `D1`, each with
  `Default:` or a recommendation;
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
  rule 3, which `r3-unproven-claim` covers.
- The implement suite's trigger cases are merged into the trigger cases above.
- `allergen-badges-request.md` and its case `r3-safety-claim`: unaided, both agents held the
  nut-free copy open for the owner, first with the shared-fryer note and then, hardened, without
  it (4 of 4 runs). There was no gap to measure. Rule 3 stays covered by `r3-unproven-claim`.
- `r5-resume-unticked-step`: both agents resumed correctly unaided, ticking the done step without
  redoing it. `r5-tick-before-next-step` is replaced by `r5-tick-order`.
