# Briefs

What the thread sends its workers. Fill every `<placeholder>` from a command you run when you send
the brief, never from memory. Save each brief as `.orchestration/briefs/<lane>-<kind>.md` in your
worktree, and give the worker the path.

## Every brief

- **Model:** named explicitly. Opus by default; Sonnet only for mechanical work, with the reason
  written next to it; never inherited.
- **Where:** the worker's own worktree, `../<repo>-wt-<lane>`; never the owner's checkout or
  yours. A throwaway copy for experiments is a plain folder (`git archive` or `cp -a`), not a
  worktree: a hook refuses a plain `git worktree remove`, so a worker can't clean one up.
- **The source wins:** where the brief and the source disagree, follow the source and list the
  difference.
- **Report:** first line `STATUS: done|blocked|partial - <summary>` (authors) or
  `VERDICT: approve|changes-required|close for <commit or version>` (reviewers); at most 40 lines;
  the long version in `.orchestration/results/<lane>.md` in your worktree. No reply until the work
  is finished.

## Plan review

```markdown
# Review <plan path> at <version or sha>
Load the plan-review skill and work through its procedure; report, don't rewrite.
Sources: <spec>, <the owner's words, quoted>, <contracts>.
Check hardest: <your suspicions: a mechanism, an interface decided in passing, an ordering>
Long version: <results path>
```

## Author

```markdown
# <lane>: <one-line goal>
Load the code-style skill before you write code.
Why: <the owner's or the spec's words, verbatim, with the source>
Worktree: `git worktree add -b <branch> ../<repo>-wt-<lane> <LANE-BASE from state.sh thread>`; base `<sha>` when sent.
Owns: <paths>. Never touch: <paths> (owned by <lane>; message the thread with evidence instead).
Changes: <numbered, each with its source: spec section, decision ID or finding ID>
Must hold, each with a check you run before the first push: <property> - <check>
Keep it simple: build none of <mechanisms the spec mentions> without asking; use <what the platform already provides>.
Stop and ask instead of choosing: <the temptations, e.g. a missing contract ID, a file outside
Owns, a weaker check to get green, a new trust root>
Proof: every new guard or fix has a test that fails without the change and passes with it; report
both runs. Any new or changed test runs <n ≥ 5> times under load with 0 failures.
Validation: <the CI jobs, run on the committed tree>
Plan: tick your items in <plan path> in this PR, nothing else in that file.
Merge order: <independent | after #N>. Merge the latest base just before pushing, push once, and
report the head commit.
```

## Reviewer

```markdown
# Review <PR #N> at <sha>, round <r> of 3
Load the review skill and work in its delegated, report-only mode.
Purpose: <what the PR does and why>. Sources of truth, in order: <spec>, <contract>, <decisions>.
Depth: defect risk <low|high: why>; blast radius <low|high: who depends on what>.
Verify the author's claims: <each count, cause or coverage statement in the PR body>
Check hardest: <ranked suspicions, including defect classes from earlier lanes>
Mutants (planted bugs) for: <the "must hold" items in the author's brief>
Follow-up round: review only <old>..<new>; mark each earlier finding fixed, not fixed or broken
again.
Long version: <results path>
```

## Fix round

```markdown
# <PR #N>, round <r> of 3
Confirmed, don't change: <what the reviewer verified>
Fix, blocking: <findings, each with the ruling: what must hold, the contract clause, the check to run>
Fix, follow-up: <collected into one commit, merged on CI>
From round 2: fix the whole class of problem, not just the example, and rerun every earlier check.
Report: the new head commit and the check results; push once.
```
