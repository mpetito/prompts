# Orchestration fixes retrospective (2026-10-12)

Four problems that the 2026-10-11 builds hit in the orchestration skills, fixed in one short build:
a research worker, a plan review, two author lanes, one script review and one eval rerun.

## What changed

- **`thread.sh close` keeps ignored files.** It archived `.orchestration/` and then forced the
  worktree's removal, so a build's gitignored eval run and its `.claude/agent-memory/` were lost.
  It now archives ignored files under `<archive>/ignored/` first, through one `lib.sh` helper
  shared with `finish-lane.sh` (whose output was compared old against new: byte-identical), and
  prints `FAILED` and keeps the worktree when git can't list them.
- **Scratch copies.** A reviewer copied a linked worktree with `cp -a`, as `briefs.md` suggested;
  the copy kept its `.git` pointer, so a test identity went into the live repository's config and
  five commits took it. `briefs.md` and `guard-bash.sh` now say `git clone --no-local` or
  `git archive`, never `cp -a` of a worktree, and `thread.sh check` prints
  `IDENTITY <repo> …` when the repository's local config sets an identity other than the global one.
- **Unseen permission waits.** A thread waited about 18 minutes on a permission prompt for a write
  outside its worktree; it couldn't message MAIN, and MAIN didn't know. Claude Code documents
  `claude agents --json` as the supported way to read session state from outside
  ([agent view](https://code.claude.com/docs/en/agent-view#read-session-state-from-a-script)):
  `state: blocked` and `waitingFor: permission prompt`. `thread.sh check` now prints
  `BLOCKED <thread> <waitingFor>`, and orchestration-main says to tell the owner to answer it in
  that session. Both skills and the worker briefs now keep writes inside the writer's worktree.
  No hook or settings change was needed. MAIN sees the line only when something else wakes it;
  a blocked thread can't.
- **`state.sh set` and a `-` agent cell.** The awk condition meant to skip the table separator
  also skipped every lane row with no agent yet. Dropped; the lane-name match already excludes the
  separator.

## What the reviews caught

- The plan review fixed the two new `check` lines' formats before either lane wrote against them,
  kept `BLOCKED` from being hardcoded to permission prompts (`waitingFor` has five values), and
  moved the thread's own write rule from the worker briefs into the skill the thread reads.
- The script review planted 24 mutants. None blocked. Five survived as test gaps in the new
  detector (state against status, a null `waitingFor`, output that isn't a JSON array); three
  were closed in one follow-up commit, two were ruled out as contrived or a cost property.
- The thread itself first reported the evidence store's `verify.sh` missing: a listing cut by
  `head` hid it, and the plan reviewer repeated the claim. MAIN caught it. Check a "missing"
  claim with the exact path before reporting it.

## Evals

Both suites, Opus high, three runs, no baseline arm (a third Opus arm would have crossed the
spend line): agent-orchestration with 0.99 / without 0.47, orchestration-main with 0.98 /
without 0.52. Each with-skill miss was one run in three and an assertion misreading a right
answer: a state helper called through a shell alias (`$S set …`), and a case-insensitive
`not_regex` matching the sentence that declined the edit. Both assertions could be widened in a
later round; neither was touched here.

## Cost

Claude evals $10.14 of $25. Codex: none. Workers: one research (Sonnet, the researcher's pin),
one plan review, two authors, one reviewer, one eval runner (Opus).

## Reuse

- `claude agents --json` (`state`, `status`, `waitingFor`) answers "is that session waiting on
  someone" without hooks.
- Open: `finish-lane.sh` also copies a lane's ignored `.orchestration/` into `ignored/`, beside
  the scratch archive. It duplicates evidence and loses none; left as it is.
