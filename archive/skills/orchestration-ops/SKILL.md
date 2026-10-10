---
name: orchestration-ops
description: "Scripts and hooks that mechanise an orchestrator's recurring moves: stamp the state file with date -u, keep the decision queue with self-applying defaults, read the Codex meter, arm a timed wake at a limit reset, land an approved PR with the carry-over proof, watch a PR's gates, archive and remove a lane worktree, launch a background codex exec with a timeout, watch a shared inbox file. Use whenever a coordinator is about to do one of those by hand, even in plain words: log what just happened in the state file, note a decision the owner has not answered, check the Codex budget, merge this approved PR when CI is green, wait for Copilot and CI on this head, clean up a finished lane, start a Codex lane in the background, or install the hooks that refuse pattern kills, raw worktree removal and hand-typed timestamps. Load it at kickoff of any orchestrated build and after a compaction. Not for what to delegate or how to rule (agent-orchestration), a brief (agent-briefs), or Herdr panes (herdr-delegation)."
---

# Orchestration Ops

In one 173-PR build, every rule that became a script or a check held (the carry-over proof, the
head-match merge, the attribution grep), and every rule that stayed in a skill paragraph decayed
within hours under load (timestamps from `date -u`, 40-line hand-backs, the three-round cap,
"read the meter"). This skill is the mechanised set. The policy behind each script is in
[agent-orchestration](../agent-orchestration/SKILL.md); this file says how to run it.

## When to Use

- At kickoff of an orchestrated build, and again at the first wake after a compaction
- Any time the orchestrator is about to type a timestamp, a merge command, a `pkill`, a
  `worktree remove`, or a "waiting on you" footer by hand

## Prerequisites

- bash 5, GNU coreutils (`date -d`), `jq`, `python3`, `gh` (authenticated), `git`, `rsync`;
  `codex` for the launcher. Linux; on macOS install coreutils, on Windows use WSL
- Scripts live beside this file under `scripts/`; hooks under `hooks/`. Call them by absolute
  path from this skill's folder. Set `OPS=<this skill folder>/scripts` once per session

## Procedure

### 1. Install the hooks (once per project)

Copy the snippet in [references/hooks.md](references/hooks.md) into the project's
`.claude/settings.json` (or the user settings). They refuse `pkill -f`, `killall`, raw
`git worktree remove`, deletion under `.orchestration/lanes` or `.orchestration/tmp`, and any new
hand-typed clock time in an `.orchestration/` file, and they warn when `/tmp` passes 70% of its
inodes. Check they fire:

```bash
printf '%s' 'killall node' | jq -Rs '{tool_input:{command:.}}' | "$OPS/../hooks/guard-bash.sh"
```

### 2. Every wake

```bash
"$OPS/meter.sh"                      # codex=<n>% resets=<UTC> verdict=normal|economy|stop, plus the rule
"$OPS/decisions.sh" due              # defaults whose deadline passed: apply each one, then close it
"$OPS/state.sh" log "<what changed>" # one line per state change; the helper stamps it
```

Record the meter line in the state file with `state.sh log`. On `economy`, switch authors to the
smaller model and drop second reviewers in this turn. On `stop`, arm the timed wake:

```bash
"$OPS/wake-at.sh" <resets UTC from meter.sh> codex-reset   # run in the background
```

### 3. Decisions the owner has not answered

```bash
"$OPS/decisions.sh" add "<what>" "<why now>" "<what it blocks>" "<default>" <hours until it applies>
"$OPS/decisions.sh" list
"$OPS/decisions.sh" close D3 "<outcome>"
```

Post the `list` output once at the top of a message, and again only when it changes or the owner
returns. Never add an owner-before item (spend, trust roots, production, safety rules) with a
self-applying default; give it a deadline of 0 and leave it open.

### 4. Launch and watch lanes

```bash
"$OPS/codex-exec.sh" <worktree> <brief.md> <result.md> --model <id> --effort high \
  --strip OP_SERVICE_ACCOUNT_TOKEN --strip <other secret var> [--network]    # background; 2 h cap
"$OPS/watch-gates.sh" <pr> <head sha> --check ci --bot copilot               # background; exits if the head moves
"$OPS/watch-inbox.sh" <shared file> "<prefix of your own lines>"             # background; prints the new lines
```

Each prints one line on exit, which is the wake. Read the result file, not the log, unless the
line says `timeout` or `failed`.

### 5. Land an approved PR

```bash
"$OPS/land.sh" <pr> <worktree> --check ci --subject "<conventional subject>" --body-file <pr-body.md>
```

Run it in the background. It merges the base if it moved, proves the carry-over (first parent is
the previous head, second parent is on the base, `--remerge-diff` is empty), pushes once, records
the proof as a PR comment, waits for the named check on that exact head and squash-merges with
`--match-head-commit`. It prints `LANDED` or `STOPPED <reason>` with the merge state, unresolved
thread count and failing checks, and never retries a stopped cause. Give append-only files such as
a decision log a `merge=union` attribute so a base merge stays conflict-free.

### 6. Finish a lane

```bash
"$OPS/finish-lane.sh" <worktree> <archive dir>     # archives <worktree>/.orchestration/tmp first
```

It refuses while a Herdr agent runs in the worktree or the tree has uncommitted changes outside
the scratch directory.

### 7. Edit the state file

```bash
"$OPS/state.sh" set <lane> "<column>" "<value>"    # one cell of the Lanes table
"$OPS/state.sh" backup                             # before a rewrite
```

The file is `.orchestration/state.md` in the current directory, or `$ORCHESTRATION_STATE`. Its
layout is the template in
[agent-orchestration's state-file reference](../agent-orchestration/references/state-file.md).

## Common Issues

| Problem | Solution |
| --- | --- |
| `meter.sh` prints `codex=unknown` | No Codex session log holds a meter yet; run one `codex exec` or set `CODEX_SESSIONS` to the sessions root |
| `state.sh set` says `no column` | The Lanes table header differs from the template; pass the header text exactly, quoted |
| `land.sh` stops with `remerge-diff touches:` | The base merge needed conflict edits; send that range to the reviewer as a delta, then rerun |
| `land.sh` stops with `merge of main conflicts in: docs/decision-log.md` | Add `docs/decision-log.md merge=union` to `.gitattributes` on the base |
| The timestamps hook denied an edit that only moved existing lines | It compares against the file on disk; re-read the file, keep the existing stamps verbatim, and put the new event through `state.sh log` |
| `finish-lane.sh` refuses: agent still runs there | Move or stop the peer first (herdr-delegation, *Teardown order*) |
| `codex-exec.sh` prints `timeout` | The lane ran past the cap; read the log tail, then resume with `--resume <session id>` and a narrower brief |

## Tests

```bash
bash tests/run.sh    # from this folder; offline, uses a throwaway directory
```
