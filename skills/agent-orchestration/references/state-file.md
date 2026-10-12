# State file

The thread's memory. A fresh thread that takes over (a rotation) starts from this file and nothing
else, so anything not written here is lost. It is `.orchestration/state.md` in the thread's
worktree, `../<repo>-orch-<build>`, next to `decisions.md`, `plan.md`, `briefs/` and `results/`.
The folder isn't committed. The scripts find it from the worktree's root; `$ORCHESTRATION_STATE`
points them at another file.

The build's name, the base branch and how lanes land are not in this file. They are in `thread.md`,
which MAIN writes; read them with `state.sh thread <key>` (`BUILD`, `BASE`, `LANE-BASE`, `LANDING`).

## Sections

`state.sh init <build>` writes these, in this order. Change them only with `state.sh` (`log`,
`set`, `resume`, `backup`): it stamps the time itself, so you never type one, and a hook reminds
you if you do.

| Section | Holds | Changed with |
| --- | --- | --- |
| Thread | A pointer to `thread.md`, the start time, the plan's path | `init`, once |
| RESUME | What a fresh thread needs to carry on (checklist below) | `resume`, at each rotation and the end of each phase |
| Lanes | One row per lane: worker, pull request, head commit, next step | `set <lane> <column> <value>` |
| Decisions | A pointer to `decisions.md`, which `decisions.sh` keeps | `decisions.sh` |
| Log | One time-stamped line per event | `log "<event>"` |

Add a section only when the build needs one, such as approvals the owner gave (quoted, with the
time) or standing decisions on flaky tests.

## RESUME checklist

Write it with `state.sh resume -` from a heredoc. A fresh thread reads it first and must not have
to work any of this out again:

1. **Goal and plan:** the build in one line, the plan file, the order of the lanes.
2. **Every open lane:** its name, its kind (Claude or Codex) and model, its herdr agent, worktree,
   branch, pull request, head commit, review round and verdict, and its next step. Lanes are herdr
   agents and keep running across a rotation.
3. **What stopped with the session:** running subagents, the mail wait and its watch list, and
   timers, each with the command or brief that restarts it.
4. **Mail in hand:** each message read but not yet acted on, quoted.
5. **Open decisions:** each id with its default and deadline, or `owner-before`.
6. **Approvals and rulings:** what the owner approved (quoted, with the time), and standing
   rulings.
7. **Budget:** the last meter readings, Codex and Claude.
8. **Done:** merged lanes, one line each, so nothing is redone.

## After a rotation

1. Run `date -u`, then read this file in full. Trust no ID, commit or number until you have
   checked it.
2. Check each open lane against its source: `gh pr view <PR> --json headRefOid,state,statusCheckRollup`,
   `git rev-parse <branch>`, and each result file.
3. Restart what stopped (checklist item 3), act on the mail in hand, then carry on as in a normal
   turn.
