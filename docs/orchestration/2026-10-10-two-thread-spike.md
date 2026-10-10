# Two-thread orchestration spike (2026-10-10)

Question: can a main thread that talks to the owner run an orchestration thread in a separate
Claude Code session, steer it, rotate it and get decisions back, with nothing but built-in
features? Claude Code 2.1.296 on Linux, both sessions in `auto` permission mode.

## Setup

- **Orchestration thread**: a background session started with
  `claude --agent spike-orchestrator --bg --name spike-orch-1 "<brief>"` from a non-git folder
  under a trusted parent (a scratch folder; a git repo would have moved it into a
  worktree, and `/tmp` is not trusted, so `--bg` refuses it).
- **The agent** was thin: `model: sonnet`, an empty body (so the default system prompt stays), and
  `initialPrompt: /spike-orchestration`, which loads the protocol skill on the first turn. The
  `skills:` field does not preload in session mode; `initialPrompt` does (probes 3 and 4).
- **Protocol skill**, eight rules: never ask the owner directly; messages from MAIN carry the
  owner's steer; every message up starts `STATUS: <working|need-decision|rotating|done> - …`;
  decisions carry a default and an `applies at <UTC>` deadline; state file timestamped with
  `date -u`; lane work goes to Sonnet subagents; `ROTATE` means write RESUME and stop; a resume
  brief means read state first.
- **Main thread**: an ordinary interactive session using `SendMessage` and `ListAgents`.

## What happened

| Time (UTC) | Event |
| --- | --- |
| 03:35:06 | Thread 1 launched |
| 03:35:19 | `STATUS: working` and a `need-decision` (tea/coffee, default tea at 03:45:10Z) arrive at main |
| 03:35:33 | Main's answer, sent with `notify_when_idle`, is acted on within seconds |
| 03:35:39 | `STATUS: done`; idle notice arrives |
| 03:35:57 | `ROTATE` answered with `STATUS: rotating` and a clean RESUME |
| 03:36:05 | Thread 1 stopped (`claude stop`); thread 2 launched with a resume brief |
| 03:36:18 | Thread 2 finishes new lane C; lanes A and B untouched (mtimes checked) |
| 03:36:39 | Lane D asked with a 2-minute default; main does not answer |
| 03:38:46 | Default applied 8 s after its deadline, reported as such |

## Findings

Worked as designed:

- Messages arrive as new turns when the receiver is idle and between tool calls when it is busy.
  Steer-to-action took seconds.
- Zero `AskUserQuestion` calls in either thread; every question went to main in protocol form.
- Rotation from the state file was clean: the fresh thread skipped finished work and continued.
- Orchestration context stayed near 50K tokens per call (about 1.1–1.2M cache-read tokens over
  22–24 calls per thread), against a 517K median in a past orchestrated build.
- Subagent workers ran on the model the protocol named.

Did not hold, or needs a mechanism rather than a rule:

- **Waiting on a deadline blocked the thread.** Thread 2 waited with a foreground
  `until … sleep 5` loop: for two minutes it could not read a message from main or serve another
  lane. Use a background timer that re-invokes the thread (the archived `wake-at.sh`).
- **State edits by hand.** Thread 1 rewrote RESUME with `sed -i` and inline Python, and its first
  RESUME carried a stale "Next" line until `ROTATE` forced a rewrite. Use a state helper (the
  archived `state.sh`).
- **Time zones differ by channel.** The idle notice reports local time (23:35) while the protocol
  and the state file use UTC.

Constraints from the docs that the design has to respect:

- A message from another session never counts as the owner's consent, cannot change
  configuration, and a slash command in it arrives as plain text. Rotation, not `/compact`, is
  how main manages an orchestrator's context.
- Messages are plain text, rapid bursts to one session are refused, and at most 50 queue.
- Only the main conversation can subscribe to idle notices, and only for local sessions.
- A background session can still ask the owner directly in agent view; the protocol must forbid
  it.

## Implications

- The two-thread shape works with built-in features; Herdr is not needed between Claude
  sessions. It stays useful for Codex and Copilot lanes and for visible panes.
- Each thread is a thin session agent plus a skill. The protocol (message format, decision
  defaults, rotation) is shared and belongs in one reference both skills link to.
- Mechanise the two failures above before writing the full skills: a background deadline timer
  and a state helper.
- Evals: single-wake decisions of each thread fit snapshot fixtures; the protocol fits a lint
  test; launch, delivery, idle notice and rotation fit a scripted smoke test like this spike.

The spike's agent, skill, state file and lane outputs were removed from `~/dev` afterwards; the
background sessions were stopped and deleted with `claude rm`.

## Live smoke test of the built thread

Run at 2026-10-10T12:25Z, after linking the skills: `thread.sh launch` from a main session against
this repository (base `main`), a brief of probes instead of a build, two follow-up probes sent as a
`STEER`, then `ROTATE`.

| Probe | Result | Refused by |
| --- | --- | --- |
| Write inside the thread's worktree | allowed | |
| Write in the owner's checkout | denied | guard-writes |
| Hand-typed `14:30Z` in `.orchestration/` | denied | guard-timestamps |
| `pkill -0 -f …` | denied | guard-bash |
| `sleep 31` alone | denied | Claude Code's Bash tool, before any hook |
| `true; sleep 31`, and an `until` loop on `sleep` | denied | guard-bash |
| `git worktree remove …` | denied | guard-bash |
| `rm -rf .orchestration/results/…` | denied | guard-bash |
| Message to main without a `STATUS:` line | denied | guard-message |
| `pwd`, top level, branch | `../prompts-orch-smoke`, `orchestration/smoke` | |

- Hooks see the thread's worktree as `cwd`, and a `Write` there edits in place.
- The launch text arrives as the arguments of `/agent-orchestration`, so the skill loads on the
  first turn. Every turn ran `claude-opus-5-5` at effort `high` (the transcript records both).
- Protocol messages passed the message guard in both directions.
- `ROTATE` brought `STATUS: rotating` and a complete RESUME within a minute; `thread.sh rotate`
  started `smoke-hooks-r1`, whose first message was `STATUS: working - resumed from RESUME …`.
  `thread.sh list` run in the same second showed the new thread `not-running` until it
  registered; the next call showed `busy`.
- The thread's results file quoted a denial reason containing the probe's time, and the timestamp
  guard refused it too. The thread wrote a placeholder through the shell instead, which the hook
  allows by design.

The worktree, branch and both sessions were removed afterwards; the probe evidence was archived
outside the repository.

## Second live smoke test: addressing, branches, advice

Run at 2026-10-10T15:49Z on Claude Code 2.1.296, after the readmission build showed three faults:
MAIN's address went stale when MAIN was forked, the write guard refused workers in their own lane
worktrees, and lane cleanup deleted ignored eval runs. A thread was launched from an unpushed local
branch, so `thread.sh` chose `landing=local` and recorded MAIN's name and socket in
`.orchestration/thread.md`.

| Probe | Result |
| --- | --- |
| Message to MAIN by the recorded name | delivered, and copied to the outbox |
| Status message to a stale `uds:` address | refused, naming the recorded name and socket |
| Thread writes into the owner's checkout | refused |
| Thread writes outside its worktree, or a hand-typed time | allowed, with the hook's advice beside the result |
| Worker writes its lane worktree; waits 31 s in the foreground | allowed, no advice |
| Worker writes into the owner's checkout | refused, with the worker's reason |
| `land-local.sh` on the approved commit | `--no-ff` merge onto `orchestration/<build>` |
| `finish-lane.sh` with an ignored `.eval-runs/` | archived under `ignored/`, worktree and branch removed |

Then three moves of MAIN's address, made by editing the record:

- **The name no longer resolves:** the send by name failed ("No agent named …"); the thread read
  the socket from the record and the message arrived.
- **Name and socket both stale, as after a restart:** both sends failed and the thread logged it
  and carried on. MAIN's `thread.sh check` printed `MOVED` and recovered the message from the
  outbox. After `thread.sh adopt` and a steer, the next message arrived by name.
- The thread never answered to the `from` address of MAIN's messages.

Hook advice is returned as `additionalContext` with no permission decision. The docs say nothing
about that pairing for PreToolUse, so it was checked on 2.1.296: the advice reached Claude, and a
write in default permission mode was still refused for lack of permission.
