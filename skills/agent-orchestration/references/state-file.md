# State file

The thread's resume point. A rotated thread starts from it with nothing else, so anything not in
this file is lost at rotation. It lives in the coordination worktree, `../<repo>-orch-<build>`, at
`.orchestration/state.md`, beside `decisions.md`, `plan.md`, `briefs/` and `results/`. The folder
is untracked; the scripts find it from the worktree's top level, and `$ORCHESTRATION_STATE`
overrides that.

## Sections

`state.sh init <build> <MAIN>` writes them in this order. Edit them only through `state.sh`
(`log`, `set`, `resume`, `backup`), so no time is ever typed by hand; the orchestrator's hooks
refuse a hand-typed stamp in `.orchestration/` files.

| Section | Holds | Changed by |
| --- | --- | --- |
| Thread | `MAIN: <name>`, the start time, the plan path | `init`, once |
| RESUME | What a fresh thread needs to continue (checklist below) | `resume`, at each rotation and phase end |
| Lanes | One row per lane: agent, PR, head SHA, next action | `set <lane> <column> <value>` |
| Decisions | A pointer to `decisions.md`, which `decisions.sh` keeps | `decisions.sh` |
| Log | One stamped line per event | `log "<event>"` |

Add a section only when the build needs one, for example the owner's standing approvals
(quoted, with the time given) or standing rulings on flakes.

## RESUME checklist

Write it with `state.sh resume -` from a heredoc. A fresh thread reads it before anything else and
must not have to reconstruct any of this:

1. **Goal and plan:** the build in one line, the plan file, the visible-first order of lanes.
2. **Every open lane:** id, agent kind and model, worktree, branch, PR, head SHA, review round and
   verdict, and its next action.
3. **What died with the session:** subagents still running, background watchers and timers. Each
   one is listed with the command or brief that restarts it.
4. **Open decisions:** each id with its default and deadline, or `owner-before`.
5. **Grants and rulings:** approvals the owner gave (quoted, with the time), standing rulings.
6. **Budget:** the last meter readings, Codex and Claude.
7. **Finished:** merged lanes in one line each, so nothing is redone.

## After a rotation

1. `date -u`, then read this file in full. Act on no ID, SHA or number until it is checked.
2. Re-verify each open lane against its source: `gh pr view <PR> --json headRefOid,state,statusCheckRollup`,
   `git rev-parse <branch>`, each result file.
3. Restart what died (item 3 of the checklist), then run the normal wake.
