# Retrospective: review-lenses evals and sibling regressions (2026-10-15)

Plan steps 8–10 of [review-lenses](review-lenses/plan.md): the paid eval runs for the new skill,
the no-regression runs for plan-review and review, and what they showed. All runs used Opus at
`--effort high` unless noted. Run directories are under `.eval-runs/<skill>/` (gitignored), and
every rate below is that run's `benchmark.json` (or `benchmark-regraded.json` where named).

## Outcome

- **Step 8 passes on the 2-of-3 rule.** In each behaviour case, the skill passes every assertion
  in every run. The baseline (the sibling procedure alone) falls into a `trap-*` in at least 2 of 3
  runs. Reversibility clears that bar narrowly (see Known gaps).
- **Step 9: no regression** in plan-review or review against the pre-wiring revision `e646294`,
  read by hand.
- **Codex:** the skill helps there too. One genuine miss with the skill: Adopt didn't name `zod`.
- **Known gaps, accepted by the owner:** Reversibility (spec decision, and borderline here) and
  Reuse (decision D3), both re-checked at the 30-day load check.

## Step 8: review-lenses

The trap criterion is read from each run's `combined_pass_rate` and `results[].qualitative_assertions`.
The prose traps are gating judges, which don't count in the objective rate the runner's summary prints.

| Run | What | with_skill (objective / combined) | without_skill (objective / combined) |
| --- | --- | --- | --- |
| `20261015-105838`, `benchmark-regraded.json` | 6 cases × 3 runs, judge manifest `e92c9de` | 1.00 / 0.993 | 0.657 / 0.686 |
| `20261015-114405` | `pos-trust-boundary-diff` only, × 3, after the skill fix | 1.00 / 1.00 | 0.778 / 0.667 |

Triggering (`20261015-105838`, Opus, 3 runs per query): should-fire 9/9, should-not-fire 12/12.

The baseline falls into a trap in this many runs, by judge and by hand-read (they agree on every
deciding verdict). The skill passes every assertion in all three runs of every row.

| Case | Baseline falls | Source run |
| --- | --- | --- |
| `pos-adopt-diff` | 2/3 (runs 1 and 2 hand-roll the month-end clamp; run 3 uses `date-fns`) | 105838 |
| `pos-reversibility-plan` | 2/3, borderline | 105838 |
| `pos-trust-boundary-diff` | 3/3 | 114405 |
| `pos-pick-lenses` | 3/3 (it picks Reuse too, or names no model for the briefs) | 105838 |
| `pos-reuse-plan`, `pos-reuse-diff` | excluded from the trap criterion (A11, D3) | 105838 |

**Trust boundary ran on the skill one sentence later than the other cases.** In 105838, run 2's
proofs table still listed a mutant row for the gate it had cut ("`@require_known_caller` removed |
not run | … cut both"). Fix `b05f5ef` changed only the cut-gate rule in SKILL.md §3: a cut gate
gets no row at all in the mutants or proofs list. The case was then rerun alone as 114405,
routed through the holdout split. The case's `split` was set to `holdout` for that run and set
back afterwards; no assertion, prompt or rubric changed. The other cases ran on the skill before
that fix, which touches no rule they test.

**Codex** (`20261015-105847`, `gpt-6-astra`, `--effort high`, 1 run, `--skip-judge`): graded by
hand, because that run used the regex manifest `956d22c`. Its objective rates were 0.885 and 0.718.
- With the skill, Adopt fails genuinely: the reply validates "the complete provider contract once at
  entry" and names `date-fns`, but never `zod`, the dependency the project already has.
- Every other case passes with the skill, once four regex misgrades are corrected.
- The baseline falls on Adopt, Trust boundary and pick-lenses, but not on Reversibility. Its
  counter finding says "introduce persisted attempt tracking only when a defined retry policy
  requires it".
- No arm asked for the files to be pasted.

**Pilot.** The evals lane ran `20261015-102518`, `-103858` and `-104126` (USD 4.05). The runner's
pilot, `20261015-104537`, scored 0.979 against 0.676 and stopped on two regex misgrades. After the
first class fix (`c187800`) it regraded to 1.00 against 0.725.

## Step 9: plan-review and review against `e646294`

| Run | with_skill | old_skill (`e646294`) | without_skill |
| --- | --- | --- | --- |
| plan-review `20261015-111902` | 0.889 | 0.978 | 0.667 |
| review `20261015-112539` | 0.981 | 0.960 | 0.285 |

plan-review's lower rate is noise, not a regression. All five with-skill failures, and old_skill's
one, are wording misses on regex assertions. Read by hand, both arms pass every assertion:
- `pricing-page-earlier` (with, runs 1–3; old, run 1): each moves C first, as "run C first",
  "C starts immediately", "then C against a stub" or "do C first". None writes "pricing page", and
  the pattern's verb list has no "run" or "do".
- `measurable-acceptance` (with, run 1): "under N s on staging (… for example 10)", plus a row-count check.
- `contract-before-build` (with, run 3): "define the payload … before any workstream starts"
  and "Catalogue contract, days 1–2".

review's two with-skill failures are phrasing:
- `long-form-path-from-brief`: the path is named more than 80 characters into the line.
- `blocking-id-with-file-line`: `waitForDrain.ts:~8-11`, where the `~` breaks the pattern.

## The `/simplify` comparison

Not runnable (spec open question 1). `/simplify` is built into the host and has no folder on disk
to stage as a `--baseline` arm. Reuse on a diff is scoped to what the built-ins leave out: search
beyond the changed files, and deleting what the change makes obsolete.

## Known gaps

- **Reversibility.** The owner accepted this gap as known before the build: the ledger has no
  entry where a model missed a one-way door ([candidates](candidates.md), 2026-10-15).
  - The case discriminates in 2 of 3 runs, one phrasing away from 1 of 3.
  - Run 3's only return signal for the counter is "Add a counter in the plan that first reads it",
    which the rubric rules vague ("when something reads it").
  - The baseline already decides the payload now and defers the counter. The lens adds a concrete
    return signal.
- **Reuse (decision D3, owner, 2026-10-15T14:47Z).** Both Reuse cases saturate: plan-review's
  mechanisms step and review's cut list already find the duplicate helper and the obsolete path.
  - Reuse is kept as specified and recorded as a known gap like Reversibility's.
  - Both cases stay as no-regression checks. They are excluded from the trap criterion, and the
    skill must still pass every assertion (it does, 3/3 each).
  - Reuse is re-checked at the 30-day usage review.

## What changed during iteration

- **Evals.** The traps were tightened after two review rounds and the pilot.
- **`pos-reuse-diff` added (A11).** Its existing helper sits outside the changed files.
  `pos-pick-lenses`' explicit-model check became a trap.
- **First class fix (`c187800`).** The regex traps were narrowed to hit only proposals, never
  observations, hedges, probes or mutant rows.
- **Owner's steer: no regex for prose (relayed 15:23Z).** Every prose trap became a gating `judge`
  assertion (`75bcd63`), and regex stays only for fixed-format lines.
  - Judging was checked against hand labels: 64 of 64 agree.
  - Three of the runner's regex-era baseline labels were wrong.
- **Hand-read versus regex.** Hand-reading the regex grades found misgrades in both directions:
  - false fails, such as "none required, because the Trust boundary lens cuts that gate", or an
    action sentence that says "the legacy script" instead of naming it;
  - false traps, such as "the bus client may already … offer a dead-letter queue (unverified)".
- **Skill.** The only change was `b05f5ef`, the cut-gate rule above.

## What it cost

Eval spend for steps 8 and 9: USD 37.81 of the USD 60 cap.
- USD 4.05: the evals lane's pilots.
- USD 4.01: the runner's pilot.
- USD 13.60: step 8 (10.79 answers, 0.93 judge, 1.88 triggers).
- USD 2.94: the step 8 rejudge.
- USD 2.27: the Trust boundary rerun.
- USD 10.94: step 9 (plan-review 3.75, review 7.19).

The evals lane spent another USD 1.94 checking the judge conversion. Codex runs bill tokens, not dollars.

## What transfers

- **Grade prose with a model, not a regex.** Every regex over free prose here misgraded in both
  directions, and the fixes didn't converge. A gating judge with one yes/no question, the fixture
  facts it needs, and an explicit "doesn't count" list agreed with the hand labels on 64 of 64.
- **Read the trap criterion from `benchmark.json`.** Gate judges count in `combined_pass_rate`
  and `results[].qualitative_assertions`. `run_skill_eval.py`'s summary prints only the objective
  rate, and its "failed" lines list only objective assertions.
- **Rerun one case through the holdout split.** Mark the case `"split": "holdout"`, run
  `--split holdout`, then set it back. That is the documented single-case route; the runner takes
  no manifest path.

## 30-day load check

On 2026-11-14, run `python3 scripts/skill_usage.py` to see whether review-lenses loads in real
reviews, and re-check the Reuse and Reversibility gaps.

## Orchestration

Four lanes on Opus (skill, evals, wiring, eval-runner), landed locally one approved commit at a
time; reviews by Opus subagents in the review and plan-review skills.

- **The plan review caught the eval design before any run:** regexes on the lens names alone
  could never fail the baseline, a sibling `SKILL.md` in both arms contradicted the harness's
  "no skill files" note, the picking case's signals contradicted the spec's own table, and steps
  8–10 had no owner.
- **The skill review caught one spec change:** an Adopt exemption that would have excused
  hand-rolling over a stock tool, the shape of two ledger entries the lens exists for.
- **The wiring review caught a security-proof regression in wording:** review's gate row read as
  dropping the proofs whenever the Trust boundary lens was skipped.
- **The evals reviews cost the most and converged least:** three rounds on regex misgrades, ended
  by the owner's steer to grade prose with a judge. Start there next time.
- Owner decisions: D1 (finding prefix after the review's id), D2 (one line in the reviewer brief
  template), D3 (keep Reuse as a known gap); D4 was superseded by the steer.
- Not done in this build: review §2 prescribes `<file>:<line>` in a lens finding while review §7's
  interactive mode cites file and function; make it `<location>`. The skill link (plan step 7)
  waits for the owner.
