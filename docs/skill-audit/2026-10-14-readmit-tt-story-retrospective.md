# Retrospective: readmit tt and story (2026-10-14)

## What the gates caught

- **Plan review (1 round, Opus).** Two blockers before any lane started:
  - "Works from a session in any repository" was false: the account mapping lived in per-project
    Claude memory, and ten disagreeing copies existed across projects. It became an owner decision;
    the owner chose one private user-level mapping file, keyed by repository plus an optional Azure
    DevOps area-path prefix, because one repository can bill to different projects by area path.
  - A tt pointer in the worker-loaded skills would have logged time once per lane, in parallel. The
    wiring proposal was narrowed to the main session and the build's done step.
  - It also found the archived "the server has no delete tool" claim false (the Harvest server now
    has one, and its descriptions steer toward deleting or zeroing), and the scanner's format traps:
    records without timestamps, out-of-order lines, local-dated Codex folders holding UTC records,
    resumed sessions repeating records.
- **tt reviews (3 rounds).**
  - Round 1: hours were computed per repository, so repositories sharing a project, or one repository
    split across two, could bill twice; resumed Codex sessions in older date folders were missed; two
    union-rule mutants survived 22 tests.
  - Round 2: grouping repositories through a shared project (including conflict rows) put one
    project's hours on another; three assertions widened after right answers failed them let planted
    wrong answers pass (a delete hidden in "Writes: none (…)", a second project logged, an invented
    work item id).
  - Round 3: the attribution held; two assertions still passed planted wrong answers (a cap case that
    only checked for "16 h", an ask case that passed a refusal and an invented id). Closed by one
    regrade-only commit; the verification found one more ("Bug 48305"), closed by a last commit after
    the owner chose to stop there. A thread-run regrade then showed most with-skill evidence predated
    the last two SKILL.md edits; a with-skill rerun on the final text passed all but one Sonnet run,
    whose right answer trips the id check through its example note format (left as a follow-up).
- **story reviews (2 rounds and one verified commit).** No blockers. Round 1: two assertions let vague
  or test-based acceptance criteria pass (quoted labels stopped the scan), with-skill evidence for
  three cases predated the last SKILL.md edit, nothing measured whether the model looks up in-flight
  work before proposing, and three fixture ticket keys kept real numbers. Round 2: a planted "right"
  answer proposed a Feature after the owner ruled against it.
- **What unaided models already do (dropped from story).** With both Azure DevOps connections' tool
  descriptions in the fixture, Opus and Sonnet placed items correctly (siblings' area path, the
  team's current iteration, the in-flight parent) and looked them up first. Kept as regression cases.
  The skill keeps only what they missed: user-facing acceptance criteria, splitting a multi-outcome
  request, the Markdown flag, the type and estimate rules.

## Outcome

- **tt:** PR #4 at e7a3ff1, merged as b02c5a5 by the main session on the owner's approval. A session
  scanner (Claude and Codex transcripts → active time per local day and repository; 39 tests), a
  65-line SKILL.md (from 191) with a live path and a confirm-first back-fill, six behaviour cases that
  fail unaided and pass with the skill on Opus and Sonnet, and three regression cases. The first real
  back-fill found a week with whole days unlogged.
- **story:** PR #5 at f1fba58 (main merged in as 631a33a), merged as 5204569 by the main session on
  the owner's approval, after one more change: refine or link an existing item only after
  confirmation (D7; not measured by a case). 103 lines, from 355. Five behaviour cases fail 3/3
  unaided and pass 3/3 with the skill on Opus and Sonnet.
- **Owner decisions:** D1 wiring narrowed, then revised (D10, D11) and applied on main as fbfb1a9; D2
  union per project per day with unattended time counted; D3 live events log directly; D4 one private
  mapping file; D5 five working days; D6 propose a split and create on confirmation, stories before
  Features. A 16-hour daily cap (logged plus proposed) came as a steer. The owner rejected the first
  wiring revision because it depended on knowing whether a PR came from a build; tt's own subtraction
  of time Harvest already holds made that rule unnecessary.

## What it cost

- Eval and probe spend: about $97 of $100 (tt about $38, story about $58; story's cap was raised from
  $45 to $60 out of tt's unused share).
- Codex meter: flat at 1%.
- Rounds: plan 1; tt 3 plus two verified commits; story 2 plus a verified commit.

## What transfers

- **A widened assertion is a new assertion.** Each time a pattern was widened because a right answer
  failed, a reviewer then found wrong answers it passed. Plant wrong answers against every widened
  pattern before regrading, and keep them as planted files.
- **Evidence goes stale with every SKILL.md edit.** Both lanes kept citing with-skill runs that started
  before the last edit; each review round's fixes edited the skill again. Name the run behind every
  with-skill cell, and rerun the with-skill arm on the final text before asking for a merge.
- **An owner-visible milestone early surfaces owner decisions.** The real back-fill table, sent before
  SKILL.md was written, exposed the conflicting mappings and the unattended-time question while the
  owner could still answer cheaply.
- **MCP elicitation prompts block a lane silently until the watch reports it.** An Azure DevOps server
  asked for a project in a dialog; briefs for MCP-backed lanes should say to pass every scoping
  parameter explicitly.
- **GitHub Actions hosted runners are disabled for this repository**, so every PR is red and
  `land.py` stops on the required check; the validate.yml steps were run locally, and the main
  session merged each PR on the owner's approval.
- **Concurrent Opus and Sonnet eval runners started in the same second fail a shard ("unsafe
  run_dir").** Start them one after the other.

## Scope brief proposals

None (the repository has no REVIEW.md).
