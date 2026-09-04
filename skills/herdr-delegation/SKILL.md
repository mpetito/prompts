---
name: herdr-delegation
description: "Coordinate work across coding agents running in separate Herdr panes, including cross-harness delegation between Claude Code, Codex, and Copilot, result handoff, isolated worktree branches, and recovery from stalled or blocked peers. Use when delegating a task to another agent in a Herdr pane, when a peer agent stalls or sits on an approval dialog, when running agents in parallel on separate git worktrees, or when deciding between a Herdr peer and an in-process subagent. For Herdr CLI syntax, IDs, layout rules, and lifecycle definitions, run `herdr --skill` — this skill covers only the coordination layer on top of it."
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

---

## Delegating to a Peer

1. **Split a pane.** The new pane inherits the caller's working directory.

   ```bash
   split=$(herdr pane split --current --direction right --no-focus)
   peer_pane=$(printf '%s\n' "$split" | jq -r '.result.pane.pane_id')
   ```

2. **Start the agent.** Use `--no-focus` layout and a unique name matching `[a-z][a-z0-9_-]{0,31}`.

   ```bash
   herdr agent start reviewer --kind codex --pane "$peer_pane" --timeout 120000
   ```

   Startup ran ~5s for both `claude` and `codex` even with a large MCP config. A 120s timeout is ample; 30s (the default) is usually fine.

3. **Write the prompt for the target harness.** See *Cross-Harness Prompt Contract* below.

4. **Prompt and wait**, then **check the status, not the exit code**:

   ```bash
   herdr agent prompt reviewer "<task>" --wait --timeout 120000 > out.json
   status=$(jq -r '.result.agent.agent_status // .error.code' out.json)
   ```

5. **Collect the result from a file, not the screen.** See *Result Handoff*.

---

## Cross-Harness Prompt Contract

A prompt crossing harnesses must carry what the target cannot infer.

- **Shell dialect.** The peer runs its own shell, not yours. On Windows, Codex has no working bash — every bash call fails once with `Bash/Service/CreateInstance/E_ACCESSDENIED` before it retries in PowerShell, wasting a turn. State the shell explicitly, or give shell-neutral instructions.
- **Absolute paths.** Peers may start in a different cwd, and worktree peers always do.
- **An exact reply contract.** Ask for a single token or a file path. Free-form prose is expensive to parse off a terminal snapshot.
- **Whether to do the work or delegate it.** An agent told to "get X" may do X itself. If it must delegate, say so.

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

---

## Verification Status

Behavior confirmed on Windows 11 with Herdr panes running Claude Code v2.1.x and Codex (`gpt-5.6-sol`). **Copilot, Gemini, and the other supported kinds were not exercised** — treat the harness-specific notes (shell dialect, dialog shapes, ghost text) as verified only for Claude Code and Codex, and re-check them before relying on them for another kind.
