---
name: herdr-delegation
description: "Coordinate coding agents in Herdr panes across harnesses (Claude Code, Codex, Copilot). Use when delegating to a peer pane, starting or queueing work for a long-lived Codex peer, collecting its result, a peer stalls on an approval dialog or question, running parallel agents on git worktrees, or choosing a peer over an in-process subagent."
---

# Herdr Delegation

Herdr recognizes coding agents running inside panes and exposes them over the `herdr` CLI. Every managed pane inherits `HERDR_ENV`, `HERDR_PANE_ID`, and `HERDR_SOCKET_PATH`, so **an agent can drive other agents itself** — including agents from a different vendor.

This skill covers what that costs in practice: the handoff contract, the failure modes, and the safety rules.

**The CLI is documented elsewhere.** Run `herdr --skill` for command syntax, ID shapes, lifecycle state definitions, and layout rules. Do not restate them here.

---

## When to Use

- Delegating a task to an agent in another pane, or to a different harness
- Running several agents in parallel on isolated git worktrees
- A delegated peer has stalled, blocked, or returned an answer you cannot read
- Choosing between a Herdr peer and an in-process subagent

## Prerequisites

```bash
test "${HERDR_ENV:-}" = 1 || { echo "not inside Herdr"; exit 1; }
```

If the check fails, stop. Do not drive a Herdr session from outside it.

---

## Peer or Subagent?

| Use an in-process subagent | Use a Herdr peer |
| --- | --- |
| Work ends with this session | Work must outlive this session |
| Caller only needs the conclusion | User may want to watch or take over the terminal |
| Same harness is fine | A *different* harness is the point (second opinion, different model family, different tool access) |
| No human interaction expected | Task may need a human to answer a dialog |
| Cheap, frequent fan-out | Long-running, few, expensive |

A peer costs roughly 5s of startup plus a terminal, and its whole context is a screen you must parse. Prefer a subagent unless one of the right-hand reasons applies.

For an independent one-shot review or fix while a Codex peer is busy, run `codex exec` as a host
background task with `-o <result file>` instead of queueing it on the peer. Its flags and sandbox
notes are in [model-council's cross-harness reference](../model-council/references/cross-harness.md).

---

## Delegating to a Peer

Before creating a peer, apply
[agent model selection](../skill-authoring/references/agent-model-selection.md). Check
`herdr --skill` and the target harness's installed help for supported model configuration;
select and verify the peer's model before sending work. The startup example below identifies
the harness only, not a model tier. Include the policy when a peer may delegate further.

1. **Split a pane.** The new pane inherits the caller's working directory; `--cwd <path>` overrides it.

   ```bash
   split=$(herdr pane split --current --direction right --no-focus)
   peer_pane=$(printf '%s\n' "$split" | jq -r '.result.pane.pane_id')
   ```

   A peer that will run more than one task needs a directory that merges never delete, such as
   the main checkout. Never start it in a task worktree: once a merge removes that worktree, every
   later turn fails at once while the peer still settles as `idle`. Pass each task's worktree as
   an absolute path in the prompt instead.

2. **Start the agent.** Use `--no-focus` layout and a unique name matching `[a-z][a-z0-9_-]{0,31}`.

   ```bash
   herdr agent start reviewer --kind codex --pane "$peer_pane" --timeout 120000
   ```

   Startup ran ~5s for both `claude` and `codex` even with a large MCP config. A 120s timeout is ample; 30s (the default) is usually fine.

   For a long-lived Codex peer, pass its flags after `--`:

   ```bash
   herdr agent start tests --kind codex --pane "$peer_pane" --timeout 120000 -- \
     -m '<model>' --approve-for-me --add-dir '<worktrees root>' \
     -c sandbox_workspace_write.network_access=true
   ```

   - `--approve-for-me` sends approval requests to Codex's automatic reviewer and runs in the
     workspace-write sandbox. The CLI rejects it alongside `--sandbox` or `--ask-for-approval`.
   - `--add-dir` makes another directory writable: the worktree root, plus any cache the task
     writes, such as the package store or browser cache.
   - Workspace-write blocks network unless `sandbox_workspace_write.network_access=true` is set,
     and each blocked call becomes an approval request.
   - Codex keeps `<writable root>/.git` read-only, including the git directory that a worktree's
     `.git` file points to. A peer rooted in the main checkout therefore needs an approval for
     every commit, fetch or `git worktree` call in that repository's worktrees. The reviewer
     grants each in seconds; when that friction matters, give the peer its own clones. The docs
     don't say whether `--add-dir <repo>/.git` lifts the protection. Say which setup applies in
     the brief.

3. **Write the prompt for the target harness.** See *Cross-Harness Prompt Contract* below.

4. **Prompt and wait**, then **check the status, not the exit code**:

   ```bash
   herdr agent prompt reviewer "<task>" --wait --timeout 120000 > out.json 2>&1
   status=$(jq -r '.result.agent.agent_status // .error.code' out.json)
   ```

   Errors (`timeout`, `agent_prompt_stalled`, `agent_blocked`) are JSON on **stderr** with exit 1,
   so capture both streams. A task longer than a few minutes belongs in *Watching Long Tasks*.

5. **Collect the result from a file, not the screen.** See *Result Handoff*.

---

## Watching Long Tasks

**A peer never tells you it finished.** An in-process subagent re-invokes its caller on
completion; a Herdr peer only changes state in its pane. A foreground `--wait` holds your session
for the whole task and hits the shell tool's timeout, and a prompt sent without one leaves the
result unread until something makes you look.

Make the wait itself a background task, so its exit wakes you. In Claude Code, run it through
Bash with `run_in_background: true`. Keep the prompt short and point it at a brief file:

```bash
herdr agent prompt "$name" "Read <brief path>. Write your result to <result path>, then reply with only that path." \
  --wait --timeout 5400000 2>&1
```

- The timeout is a deadline for your attention, not a failure verdict. When it expires, read the
  pane and re-arm the wait with `herdr agent wait "$name" --timeout <ms>`.
- On exit, branch on `.result.agent.agent_status` (trap 1 below). Claude Code appends an
  `[exited with code N]` line to the task output, so parse only the first line as JSON. `idle` or `done` means
  the peer settled, not that it succeeded. `blocked` means read the dialog. An `.error.code` such as
  `agent_prompt_stalled` or `timeout` means inspect before acting (trap 3).
- **On `idle` or `done`, check that the result file exists before anything else.** If it doesn't,
  read the pane. A peer whose turn failed at once (a deleted working directory, a crashed tool) or
  that misread the task settles as `idle` too. A wait that returns seconds after you sent a long
  task is the same signal.
- **Every prompt gets its own watch**, including follow-ups and fix rounds. The one you forget is the
  one that sits finished. The exception is work added to a peer that is already working, through
  its queue file or a prompt queued to it: that extends its busy period, so keep one watch for the
  peer and re-arm it with `agent wait` when it times out. Stacked waits all expire together.
- **Keep a queue file per peer,** so it doesn't sit idle while you are busy elsewhere. List brief
  paths in priority order and tell the peer to take the next item after writing each result.
  Prefer it to prompts queued into a busy peer, which can be lost (*Blocked Agents*).
  - Review findings on the peer's own open work go to the top.
  - The brief defines the safe point at which the peer may switch to an urgent item: after the
    current test run finishes, or after a push.
  - When it pauses, the peer writes its resume state into the result file.
  - One watch now spans several tasks, so read new result files on every sweep.
- **When several agents are running,** sweep every one of them on each wake before replying to the
  user: the other peers' status, running subagents, and pending result files. Give an idle peer its
  next queued task.

---

## Cross-Harness Prompt Contract

A prompt crossing harnesses must carry what the target cannot infer.

- **Shell dialect.** The peer runs its own shell, not yours. On Windows, Codex has no working bash — every bash call fails once with `Bash/Service/CreateInstance/E_ACCESSDENIED` before it retries in PowerShell, wasting a turn. State the shell explicitly, or give shell-neutral instructions.
- **Absolute paths.** Peers may start in a different cwd, and worktree peers always do.
- **An exact reply contract.** Ask for a single token or a file path. Free-form prose is expensive to parse off a terminal snapshot.
- **Whether to do the work or delegate it.** An agent told to "get X" may do X itself. If it must delegate, say so.
- **A standing-rules file.** Keep the rules every task shares (branch and push rules, never weaken
  a test, never kill a process you didn't start, the reply contract) in one short file, and start
  each prompt with "re-read `<path>`". Never write "same rules as before": a long-lived peer
  compacts its context and loses them.
- **Explicit side-effect grants.** Name each side effect the task may perform (push to
  `<branch>`, open a PR, create a worktree under `<root>`, merge the base without rebasing) and
  the ones it may not. Codex's automatic reviewer reads the user messages in the transcript, so an
  explicit grant is what it approves on; an action the prompt never mentioned may be denied.
- **The budget, for a metered peer.** The peer can't see its own usage meter, so read it before
  each task: `/status` in an idle Codex session, or the newest `rate_limits.primary.used_percent`
  in the session log under `~/.codex/sessions/` (`window_minutes: 10080` is the weekly window).
  Put the remaining budget in the prompt, give open-ended investigations a time box and a stop
  percentage, and keep a slice back for reviews.

## Result Handoff

**Terminal snapshots are lossy in both directions.** Codex elides its own output (`… +31 lines (ctrl + t to view transcript)`), and full-screen agents render transcript history in the alternate screen, where it cannot be recovered once scrolled off.

For anything longer than a token, make the payload a file:

> Write your result as Markdown to `<absolute path>`. Then reply with only that path.

Then read the file directly. Herdr's own guidance treats this as a fallback; **across harnesses, make it the default** — it is the only channel that is not a screen scrape.

---

## Reading Peer State Correctly

Four traps, each observed in practice.

### 1. `--wait` exits 0 on `blocked`

`agent prompt --wait` treats `blocked` as a settled state, so it **succeeds** with exit 0 while the agent sits on a dialog. A script branching on `$?` will report the task complete.

Always branch on `.result.agent.agent_status`.

### 2. `agent wait` returns immediately when the state already matches

Waiting for `idle` on an agent that has not started working yet returns in milliseconds. After any input that has not yet been consumed, use a two-phase wait:

```bash
herdr agent wait "$name" --until working --timeout 15000   # observe it start
herdr agent wait "$name" --until idle --until done --timeout 180000
```

`agent prompt --wait` does not need this — it has its own lifecycle-change guard.

### 3. `agent_prompt_stalled` usually means "text landed, Enter did not"

The error reads *"produced no observed state change within 5000 ms"*. Check the screen before reacting: the prompt text is often sitting unsubmitted in the composer.

```bash
herdr agent read "$name" --source visible    # confirm text is in the input box
herdr agent send-keys "$name" enter
herdr agent wait "$name" --until working --timeout 15000
```

**Never re-issue `agent prompt` to recover.** It appends to the pending text and submits the concatenation.

### 4. Dim ghost text reads as real input

Claude Code renders suggested follow-ups in the input box. In a text read they are indistinguishable from queued user input; only the styling differs. When a peer's composer appears non-empty and it matters:

```bash
herdr agent read "$name" --source visible --format ansi | grep -a "<text>" | cat -v
```

An `ESC[2m` (dim) prefix means it is a suggestion, not pending input.

### Read sources

Use `--source visible` for a short reply — it returns the whole viewport in one call. `--lines N` on `recent` / `recent-unwrapped` counts **rendered rows from the bottom**, including blank padding, so a small `--lines` on a mostly-empty screen returns only the status bar and input box.

---

## Blocked Agents

`blocked` means Herdr recognized an approval or question UI.

- The agent stays addressable while blocked (`agent get`, `agent read`, `agent send-keys`); only prompting is refused.
- `agent prompt` against it returns `agent_blocked` and sends **nothing** — verified byte-identical screen afterward. The guard is safe to rely on.
- `agent start` returns `agent_not_ready` (exit 1) if the agent blocks during startup. The name still works for `read` and `send-keys`.

**Read the dialog before sending keys. Defaults differ, and some are destructive:**

| Dialog | Shape | Default selection |
| --- | --- | --- |
| Claude Code trust-folder | arrow list (`❯`) | **"No, exit"** — a blind Enter kills the agent |
| Claude Code tool permission | numbered (`1.` / `2.` / `3.`) | "Yes" |

Never send a blind `enter` to an agent you have not read.

**Unattended work:** on a tool-permission dialog, choose the option that also switches the session to accept-edits (option `2`). It converts per-call blocking into a session-wide auto-accept, so the interrupt is paid once.

**Ask the user before answering any dialog whose consequences reach outside a scratch directory** — trust-folder, credential, and network-access prompts are the user's decision, not the delegating agent's.

**A question about the task is yours to answer.** Herdr reports a Codex peer that asks one as
`blocked`, and the question may be collapsed. `send-keys` takes only named keys and rejects text
with `invalid_key`, so type the answer into the pane:

```bash
herdr agent send-keys "$name" alt+up             # expand the question, then read the pane
herdr pane send-text "$peer_pane" '<answer>'     # literal text; takes the pane ID
herdr agent send-keys "$name" enter
```

**No addenda to a busy or blocked peer.** A message queued while the peer works or waits on a
question can be lost when the question is answered. Send a question reply on its own and wait
for the peer to resume. Put any change to the current task in its brief file, and send a pointer
once the peer is idle. After any blocked episode, check the peer's result against everything you
asked it.

---

## Worktree Delegation

`herdr worktree create` is the clean way to run peers in parallel without them colliding. One call creates a git worktree **and** a new workspace, tab, and root pane already cwd'd into it:

```bash
herdr worktree create --cwd '<repo path>' --branch feat/agent-a --no-focus
```

- The checkout lands at `~/.herdr/worktrees/<repo>/<branch-slug>`, outside the repo — and on Windows, potentially on a **different drive** from the repo. Do not assume one filesystem.
- It also opens a second workspace for the *source* repo. Teardown must account for both.
- Isolation is real: a peer's edits land only on its branch; the main checkout stays clean.

**A fresh worktree triggers Claude Code's trust prompt**, because it is a new directory. `agent start --kind claude` into a new worktree therefore returns `agent_not_ready` by construction, not by accident. Expect it and handle the dialog.

### Teardown order

**Check that no peer lives in the worktree.** `herdr agent list` reports each agent's `cwd` and
`foreground_cwd`. Move any peer inside it first: note its session ID
(`.result.agent.agent_session.value` from `herdr agent get`), quit it at a safe point, and
restart it from a stable directory. `resume` keeps a Codex peer's context:

```bash
herdr pane run "$pane" "cd '<stable dir>'"
herdr agent start tests --kind codex --pane "$pane" -- resume '<session id>' <original flags>
```

Stop the agent **before** removing the worktree. Removing while an agent holds the directory as its cwd fails on Windows with `Permission denied` — and fails *partially*: the agent is killed, files are deleted, and git registration is removed, but the directory is orphaned. The retry then reports a misleading `fatal: ... is not a working tree` while actually completing the workspace removal.

```bash
herdr pane close "$pane"                       # or let the agent exit
herdr worktree remove --workspace "$ws" --force
herdr workspace close "$source_ws"             # the extra workspace from create
```

Verify with `herdr workspace list` and an `ls` of `~/.herdr/worktrees/`.

---

## Safety Rules

- **`herdr agent list` is global.** It returns every agent in every workspace, including the user's real in-flight work. Scope fan-out to `$HERDR_WORKSPACE_ID`, and only address agents this session started.
- **Never prompt, key, or close an agent you did not start** without explicit instruction. Another agent's `blocked` dialog belongs to its own operator.
- Use `--no-focus`; do not steal the user's focus for background work.
- Parse IDs from JSON responses. Never predict an ID or reuse one across sessions.
- Clean up what you created: `herdr pane close <pane_id>` for panes, and the teardown sequence above for worktrees.

---

## Common Issues

| Problem | Cause | Fix |
| --- | --- | --- |
| `agent_prompt_stalled` | Text in composer, unsubmitted | `agent send-keys <name> enter`; never re-prompt |
| Exit 0 but nothing happened | `--wait` settled on `blocked` | Branch on `.result.agent.agent_status` |
| `agent wait` returns instantly | Status already matches | Two-phase wait: `working`, then settled |
| `agent_not_ready` on start | Blocked during startup (often trust-folder) | `agent read` the dialog, answer, then wait for `idle` |
| `agent_blocked` on prompt | Agent is on an approval dialog | Read it, `send-keys` a deliberate answer |
| Read returns only the status bar | `--lines` counted blank rendered rows | Use `--source visible` |
| Peer's reply is truncated | Alternate-screen history is unrecoverable | Re-run with a file-based result contract |
| `E_ACCESSDENIED` in a Codex turn | No working bash on Windows | Write prompts in PowerShell dialect |
| `worktree remove` permission denied | A live agent holds the cwd | Stop the agent first, then retry |
| Status is `done`, not `idle` | Background work finished on an unfocused tab | Expected — accept both in `--until` |
| `idle` with no result file; every turn fails at once | The peer's cwd was a worktree a merge removed | Restart it from a stable directory with `resume` (*Teardown order*) |
| `'--approve-for-me' cannot be used with '--sandbox'` | Codex rejects the pair | Drop `--sandbox`; `--approve-for-me` already runs workspace-write |
| `invalid_key` from `send-keys` | Text sent as keys | `pane send-text`, then `send-keys <name> enter` |
| Codex `blocked`, no dialog on screen | The question is collapsed | `send-keys <name> alt+up`, then read the pane |
| Result misses part of what you asked | A message queued while the peer was busy or blocked was lost | Check the result against every message; put changes in the brief file |
| Each commit in a worktree needs an approval | Codex protects the workspace root's `.git` | Accept the reviewer's approvals, or give the peer clones |

---

## Verification Status

Behavior confirmed on Windows 11 with Herdr panes running Claude Code v2.1.x and Codex (`gpt-5.6-sol`). **Copilot, Gemini, and the other supported kinds were not exercised** — treat the harness-specific notes (shell dialect, dialog shapes, ghost text) as verified only for Claude Code and Codex, and re-check them before relying on them for another kind.

The Codex notes were observed with Codex CLI 0.157.1 on Linux, driven by herdr 0.9.1: start flags
and their conflicts (re-checked against the CLI's argument parser), the protected `.git`, collapsed
questions and `send-text`, the session-log usage meter, `resume` from a new directory, and the
lost queued message. The network setting, the `.git` protection, the auto-reviewer reading user
messages, and `/status` are documented in the Codex docs; the rest are observations only.

*Watching Long Tasks* relies on the documented `--wait` and `agent wait` semantics (`herdr agent prompt --help`). Verified end to end on Linux (herdr 0.9.1) with Claude Code coordinating a Codex peer: a prompt sent to an already-working peer woke the coordinator once, with `done`, when both queued tasks finished. The run-in-background wake-up is Claude Code's Bash behavior; other hosts need their own background-completion mechanism.
