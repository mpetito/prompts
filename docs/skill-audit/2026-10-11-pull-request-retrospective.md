# Retrospective: readmit the PR skills as pull-request (2026-10-11)

## Outcome

- **pull-request: readmitted** as one worker skill in `skills/pull-request/`.
  - SKILL.md is 76 lines, with two PowerShell scripts (fetch feedback; reply, then resolve) and
    their offline tests, which CI runs.
  - It carries five rules from the owner-confirmed digest
    ([2026-10-11-pull-request-digest.md](2026-10-11-pull-request-digest.md)): F1, F3, F4, A1 and R1.
    - F1: an ambiguous claim goes to model-council or the owner.
    - F3: the resolve policy.
    - F4: read the review bodies, and a body-only finding gets no new public comment.
    - A1: the PR body, plus the owner's D4 line, "a PR title follows the commit convention".
    - R1: post a review only after the owner approves the exact text, as one COMMENT review.
- **Skill, not agent.** In the owner's transcripts a feedback loop's own `gh` traffic was a median
  of about 1.4k tokens per PR, and the probe showed no bloat. No agent definition was written.
- **Archived folders:** pr-feedback's SKILL.md and its two kept scripts were moved with `git mv`
  and rewritten. pr-resolve, pr-scripts (the rest), pr-authoring, commit, pr-review and
  pr-consolidate were removed.
- **Dropped for lack of a failing trap:** F2 (reply only after the push), F5 (`isOutdated` is not
  "addressed"), F6 (fix a defect's siblings), A2 (refresh a stale body), A3 (closing keywords) and
  R2 (approving your own PR). Unaided Opus and Codex passed each of their cases. The digest keeps
  them as the proposal of record.
- **Evals:** 7 behaviour cases (f2 is regression-only) and 10 trigger cases, with 90 planted
  answers that a check script grades without a model.

## Measured delta

The full runs used 3 runs per arm on the skill before the targeted round. The rerun used 3 runs
per arm on f1, a1 and f4 after it.

| Agent | Cases that fail in every unaided run and pass in every skill run |
| --- | --- |
| Opus 5.5, effort high | r1, f4, a1 (a1 on its objective checks, the title check included) |
| Codex gpt-6-astra, effort xhigh | f3, r1, f4, a1 |

- **Plugins (Claude only, owner's D1):**
  - a1, judge: the skill scored 0.88 and the staged plugin text 0.30. The plugin failed
    "validation claims only what was run" in every run.
  - r1, objective checks: the skill passed 3/3 and the plugins 0/3. That result is by
    construction, since the code-review command posts without asking.
- **Triggers on Opus:**
  - Should-fire: 15 of 15, all real Skill calls.
  - Should-not-fire: the harness counted 5 false fires in 15. None was a Skill call; each was a
    read of the mounted file while the model explored.
- **Weak spots that remain:**
  - F1 discriminates on neither model. Unaided Codex already holds the ambiguous thread. On Opus
    the targeted round lifted the judge mean from 0.30 to 0.92, but only 1 of 3 runs passed. F1
    stays because it is the owner's core ask.
  - One Opus skill run claimed "pytest passed locally" in a body whose tests were never run.

## What the gates caught

- **Plan review:**
  - The owner's `gh` is logged in with repo scope, so a probe with a shell could post to GitHub.
    The probe became text-in, text-out.
  - The harness denies Bash and Agent and rejects a baseline without SKILL.md. So the cases are
    text-only, and the plugins are staged as one folder of their command text.
  - Only interactive Codex sessions can hold the owner's own words.
- **The probe ($0.76):**
  - Neither model sent an ambiguous thread to a council, even with the global rule loaded.
  - Neither offered a gated "post after you approve" step.
- **Cases review, three rounds:**
  - The first assertions rewarded wording. Negated "no need for council" and "posted, then asks"
    answers passed.
  - The class fix: objective checks read only one structural place, and phrasing goes to judge
    criteria with calibration examples.
  - Real runs then exposed two more false fails: the skill's own script form, and forbidden
    commands named in prose. Both were fixed for every case.
- **Unaided smoke ($3.15):** six of the eleven traps passed unaided on at least one model, which
  is where the drops came from. A lane's report that unaided Opus "resolved the still-broken
  thread" was wrong. Its failure was not resolving the thread it had fixed, so F5 was dropped and
  the case relabelled to F3.
- **Skill review, two rounds:**
  - GraphQL pagination had no test (two mutants survived).
  - The raw fallback could resolve a thread after its reply failed.
  - `databaseId` is deprecated in favour of `fullDatabaseId`.
- **Full runs:** the bar was missed on objective checks alone, which led to D5's targeted round.

## What it cost

- **Claude:** about $29.6 of the $50 cap.
  - Probe: $0.76.
  - Smoke: $3.15.
  - Skill lane: $2.75.
  - Full runs: $18.66.
  - Rerun: $4.28.
- **Codex:** about 5.6M tokens.
- **Time:** the full runs took about 5.4 hours of wall time.

## What to reuse

- Probe unaided before writing the cases, and smoke them unaided before writing the body. Most
  digest rules turned out to be things the models already do.
- Plant each rule's real unaided output as a wrong answer, and a reviewer's own correct answers
  as right ones, before any model run.
- The runner has no case filter. A rerun of a few cases uses an untracked copy of the skill
  folder with a subset manifest.
- Judge cost appears only once the judge files are written, so a cap check during a run reads
  low.
- The plugin arm's handicaps (D1):
  - The plugins ran as text, without Bash, Agent or `!` context.
  - They ran on Claude only.
  - commit-push-pr asks for tool calls only.
  These favour the skill on format, so read the plugin numbers as indicative.
- Orchestration scripts:
  - `state.sh` has no add-row command.
  - `set` cannot address a row whose Agent cell is `-`.
