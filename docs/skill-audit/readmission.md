# Skill readmission

Every skill was archived on 2026-10-09. The collection had grown over nine months, from a single
Copilot agent in VS Code to orchestrated agents across projects, and most skills still carried
the shape of the first era. Rather than prune, the whole set earns its place back. This file is
the bar. The evidence that set it is in [2026-10-09/](2026-10-09/).

## Why a zero base

- The real consumers changed. In the 60 days before the archive, three skills (review,
  code-authoring, code-quality-standards) were loaded about 750 times by subagents and about
  2,900 times by Codex workers, while the main session loaded any skill 48 times in 336 sessions
  and the user typed `/commit` twice. Worker skills pay their full body on every load.
- 28 of 32 skills had no behaviour eval, so nothing measured what any skill was worth.
- Three enabled Claude Code plugins (commit-commands, code-review, pr-review-toolkit) overlap
  the commit, review and pr-review skills.
- The best-practice review found the same deviations across the collection: rules restated in
  two to four places per skill, generic knowledge the model already has, "When to Use" sections
  that repeat the description, and build anecdotes in the instructions.

## The bar

A skill enters `skills/` only when all five hold. Start from the archived text and its review in
[2026-10-09/reviews/](2026-10-09/reviews/), never from a blank file.

1. **A recorded gap.** An entry in [candidates.md](candidates.md): the date, the project, the
   session, what the model did wrong without the skill, and the wrong output quoted. A skill
   nobody missed stays archived.
2. **Three behaviour evals** in the `skill-eval-harness` manifest format used by
   `scripts/run-skill-eval.ps1`, each with a fixture trap, each failing without the skill and
   passing with it. Trigger cases come after, not instead. Use `archive/skills/pr-authoring/evals/`
   as the reference suite.
3. **One consumer role**, named in the first line of the body: orchestrator (loaded once per
   session; may be long), worker (loaded once per lane by subagents or Codex; under about 120
   lines), human (slash-invoked; short, procedural) or domain reference (loaded when a project
   needs it; progressive disclosure into `references/`). The line budget follows the role.
4. **No overlap** with the harness, an enabled plugin, or a sibling skill. commit, review and
   pr-review must beat the official plugins on the same fixtures (`-Baseline`, see
   [evaluating-skills.md](../evaluating-skills.md)) or stay archived. A rule has one home.
5. **Loads within 30 days** of readmission, measured by `python3 scripts/skill-usage.py`, or
   it returns to the archive. Run the script monthly.

## What the audit said to change on the way back

From [2026-10-09/synthesis.md](2026-10-09/synthesis.md), the fixes that apply to almost every
skill:

- Delete "When to Use", intro and "Related Skills" sections that repeat the description; the
  description has already fired by the time the body loads.
- Keep only rules a model without the skill gets wrong, each backed by an eval trap. Turn
  WRONG/RIGHT example blocks into one-line rules; move code worth keeping to `references/`.
- One checklist, inside the procedure. No Common Issues or Pitfalls table whose rows restate the
  body; keep only rows with a symptom the body does not state, such as an exact error string.
- Keep the rule, drop the story. Build anecdotes go to a `references/evidence.md` the skill
  never asks the model to load.
- Prefer a script with one fixed-format output line over prose for any fragile sequence.
- Descriptions under about 900 characters, with plain-language triggers and a "Not for …
  (sibling)" clause written from the negative eval cases.
- Reference files over 100 lines start with a table of contents; references stay one level
  deep from SKILL.md.
- No host-specific tool IDs or version-bound facts stated as current.

## Testing rules that only show up in long-running work

Most orchestration rules are a decision at one wake with state on disk, so they decompose:

1. Anything mechanised (scripts, hooks) gets an ordinary test, no model needed.
2. Single-wake decisions get snapshot fixtures: a state file, a decision queue with an expired
   default, a meter reading, a reviewer hand-back, an interim notification. The assertion is
   the next action. Real snapshots exist in the session transcripts.
3. Script-plus-skill paths that cost a merge if wrong get a mocked `gh` in a sandbox.
4. The build itself is the eval: compactions, median context, idle gaps, rounds per lane,
   decision latency, from the transcripts (`2026-10-09/build-retrospective.md` is the
   first baseline).

A rule that fits none of these becomes a measured signal or is dropped.
