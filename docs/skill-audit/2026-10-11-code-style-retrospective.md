# Retrospective: readmit code-authoring and code-quality-standards as code-style (2026-10-11)

## Outcome

- **code-style: readmitted.** `skills/code-style/` is a 39-line worker skill with 7 rules. Each
  rule is in the owner's words, and each has a trap that fails without the skill:
  1. least mechanism
  2. use what exists
  3. trust your own callers
  4. registry dispatch
  5. contract comments
  6. delete what a change replaces
  7. tests never match copy

  Landed on `orchestration/code-style` as 08d6343.
- **Archived folders:** `archive/skills/code-authoring/SKILL.md` was moved by `git mv` (62cc1bf)
  and rewritten. The rest of code-authoring and all of code-quality-standards were removed.
- **Dropped for lack of a failing trap:** digest rules 4 (wrappers), 6 (fallbacks and mock data),
  8, 9 (never relax lint), 11 and 12. Rules 14 and 15 were cut by the owner (D2). The
  linter-enforceable halves of rules 8, 11 and 12 belong to the parallel project-setup build.
- **Inputs:** the digest (`2026-10-11-code-style-digest.md`) and the proposed owner-only diffs
  (`2026-10-11-code-style-owner-diffs.md`).

## Measured delta (final revision, 3 runs per arm)

| Agent | with_skill | without_skill | Cost or tokens |
| --- | --- | --- | --- |
| Opus, effort high | objective 1.00, judge 1.00 | objective 0.72, judge 0.33 | $2.33 vs $2.17 |
| Codex gpt-6-astra, effort xhigh | objective 1.00 | objective 0.61 | 2.7M tokens per three-arm run |

- **Without the skill:**
  - Opus fails r2, r3, r5, r7, r10 and r13 in 3 of 3 runs.
  - Codex fails those six plus r1 in 3 of 3 runs. The r1 trap is a counter for the second
    rejection; it discriminates on Codex only.
- **Triggers on Opus:**
  - Should-fire: 15 of 15.
  - Should-not-fire: 9 of 15 by the harness's count, but none of the six hits was a Skill call.
    Each was a read of the mounted file while the model explored an otherwise empty repo, so
    routing was 15 of 15.

## What the gates caught

- **Plan review (1 round)** found that the evidence lanes could not tell the owner's own words
  from generated text:
  - Transcripts carry `promptSource`. Only `typed` and `queued` entries are the owner's.
  - A missing AI trailer proves nothing after 2026-08-24, because the owner has banned those
    trailers since then.
  - Comments under the owner's GitHub login are partly agent-posted.

  It also split the skill lane into a cases lane and a skill lane, and set four rules for case
  design: an objective check in every case, a task-done regex paired with each `not_regex`, no
  forbidden pattern in the fixture, and an untrusted-boundary counter-case.
- **The $0.51 probe (D1).** Unaided Opus added no speculative guards (0 of 3). Line-level "trust
  internal code" is not a gap on Opus. The owner's real complaints are about design: stored
  counters instead of queue depth, hardening against a trusted caller, extra policies. Every trap
  was aimed at that level.
- **Harness lane.** Three findings:
  - Codex refuses to read a fixture under "read the input file, but do not run commands", because
    it has no file-read tool. Fixtures now allow a read-only `cat`.
  - `-Model sonnet` reached Codex unchanged.
  - `-Effort` was dropped for Codex; fcd7e83 fixes it.
- **Probe: CLAUDE.md in eval runs.** Claude eval arms load `~/.claude/CLAUDE.md` despite
  `--setting-sources project`. This build kept it, because subagents load it too; the note is in
  `docs/evaluating-skills.md`.
- **Cases review.** At first the assertions caught only 8 of 37 planted wrong answers. The harness
  grades regexes case-insensitively, and the author's own checker didn't. After the fix: 35 of 37.
- **Skill review, round 1:**
  - Rule 5 had been widened to "every file you touch gets a header" after one regex miss. That
    went beyond the owner's evidence and against D3, so it was narrowed to modules created or
    whose contract changes.
  - An inferred definition of "convention" had narrowed the owner's D3 condition; it was removed.
  - Three quotes had been lightly edited; they were made verbatim.
  - Four frozen assertions failed correct answers. They were fixed and every run was regraded,
    all arms alike: 7 flips from fail to pass, all in skill arms, 0 in the without-skill arm.
- **Skill review, round 2:** approved. Rule 1's "read it before your own write" is inferred and
  partly fitted to r1.

## What it cost

- **Claude eval and probe spend:** about $50 of the $75 cap.
  - Harness: $0.38
  - Probe: $0.51
  - Cases: $3.02
  - Skill: $34.05
  - Skill fix round: $12.41
- **Codex:** about 16M tokens. The Codex meter stayed at 5%. It reads the last interactive
  rollout, so it does not see eval runs.
- **Rounds:** plan 1; cases 1, plus one targeted Codex run for r1; skill 2.
- **Owner decisions:** D1 (allow the $3 probe), D2 (digest, cutting 14 and 15), D3 (CLAUDE.md
  diffs B and C plus the plugin), D4 (project-setup as its own build). There was also one steer
  (the lint split) and three boundary questions with project-setup.

## What transfers

- **Probe the unaided model before writing traps.** On the current models, generic style rules
  are already followed. The owner's style shows in design-level choices.
- **Measure on Codex as well as Opus.** Codex is the heavier consumer. Rule 1 failed only there,
  and r13 was 1 of 3 there against 3 of 3 on Opus.
- **Rule text can overfit to an assertion.** After each fix round, check every reworded rule
  against the owner's evidence, not the regex that missed.
- **Grade scratch answers with the harness's own `assertion_result`.** A local checker drifted on
  case-sensitivity.
- **`state.sh set` treats a lane row whose Agent cell is `-` as the table separator.** Give
  placeholder rows a non-dash Agent.

## Follow-ups

- **Owner-only:**
  - MAIN applies CLAUDE.md diffs B (revised with the owner's condition) and C after merge.
  - Run `setup-skills-link.ps1` so `~/.claude/skills/code-style` and `~/.agents/skills/code-style`
    exist (diff F).
- **A held-out rule-1 trap** with a different lagging source, such as a cache or a search index,
  so r1 stops measuring the inferred hint.
- **README.md still names the archived `pr-feedback`** (outside this build).
- **`docs/skill-audit/candidates.md` is appended to by project-setup too.** Expect a trivial merge.
- **Bar item 5:** check loads with `python3 scripts/skill-usage.py` within 30 days.

## Scope brief proposals

None. Both reviewers proposed no REVIEW.md change.
