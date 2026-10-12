# Herdr and file mailbox spike (2026-10-12)

Question: can orchestration run on herdr-hosted agents that talk through a file mailbox, instead of
Claude Code background sessions and `SendMessage`? The design follows the
[herdr-orch](https://github.com/ellingtonsp/herdr-orch) plugin's mailbox (inbox per agent, the
receiver blocks in a wait, nothing typed into the receiver's pane) without its daemon: files and
herdr's own agent states do the daemon's work.

herdr 0.9.3, Claude Code 2.1.296, Codex CLI with its default model, Linux.

## Setup

- **MAIN**: the owner's interactive Claude session, its pane given a herdr name for the spike.
- **Thread**: plain Claude (`--model opus --permission-mode default`, the mailbox script and
  `wake-at.sh` allowlisted) started with `herdr agent start` in a sibling pane. Its brief: keep one
  background mailbox wait running; on mail, read and act; reply by mail with a `STATUS:` first line.
- **Codex worker**: Codex in default approval mode, `--add-dir` on the spike folder, in another pane.
- **Mailbox script**: a maildir per agent name (`tmp/`, `new/`, `cur/`). `send` writes to `tmp/` and
  renames into `new/`; `read` prints each message and moves it to `cur/`; `wait` polls every 2 s and
  prints one line: `MAIL n`, `BLOCKED <agent>` (once per transition), `GONE <agent>` or `TIMEOUT`.

## Results

| Test | Result |
| --- | --- |
| Arguments after `herdr agent start … --` reach `claude` | Pass: `--model`, `--permission-mode`, `--allowedTools` arrived. `--agent` was not run. |
| Mail to an idle thread wakes it through its background wait | Pass, within seconds |
| Mail to a busy thread | Pass: sent during a one-minute foreground tool call; the wait's completion reached the thread after that call; reply 69 s after sending. Not lost. |
| Mail to MAIN wakes MAIN through its background wait | Pass every time; nothing is typed into MAIN's pane |
| Watcher reports a permission prompt | Pass: `BLOCKED` within one poll; a second wait with the same dialog open stayed quiet. The owner answered in the pane. |
| Decision default applied by the thread's own `wake-at.sh` timer | Pass: fired at the deadline; the thread applied the default without MAIN |
| Owner's half-typed input in MAIN while a wait wakes it | Not observed (owner away). The owner reports from past use that input survives a background-task wake. |
| Codex worker: pointer prompt in, reply by mail | Pass, with the findings below |
| Rotation: close the pane, start a new agent under the same name | Pass: `agent_not_found` after close, the new agent took the name, and mail keyed by name carried over |

## Findings

- **Read, then re-arm.** Re-arming the wait before reading made it see the unread file and wake
  again at once. Reading first is race-free, because the wait checks `new/` when it starts.
- **Send takes the body as an argument.** Piping text into the script is a compound command, which
  a default-mode Claude asks permission for every time.
- **Codex's sandbox shell doesn't inherit the pane's environment and can't reach the herdr socket**
  (`Operation not permitted`). The mailbox needs a fixed default root, and a Codex sender names
  itself explicitly.
- **Claude Code's auto-mode classifier refused a Codex launch with `--approve-for-me`.** Codex lanes
  need a launcher script the owner allows by a settings rule.
- **herdr clears a name when its agent exits or is replaced.** An address that must survive a
  restart can't be a herdr name; mailboxes are keyed by build instead, and MAIN has no herdr name.
- **No daemon was needed.**

## Not tested

A thread started with `--agent orchestrator` and its hooks; launch in a fresh worktree; several
watched agents in one wait; a `GONE` report; a herdr server restart; a Codex lane committing in
its worktree. The rework's live smoke test covers these
([plan](herdr-rework/plan.md), step 5).
