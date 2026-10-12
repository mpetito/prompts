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

## Live smoke test of the rework (plan step 5)

Run at 2026-10-12T16:50Z–17:14Z from a herdr pane in this repository: `thread.sh launch` of a probe build
with the real `orchestrator` agent and hooks (auto permission mode), driven by mail from MAIN. herdr 0.9.3,
Claude Code 2.1.296.

| Probe | Result |
| --- | --- |
| Launch with the brief as a multi-line agent argument | **Failed**: herdr refuses agent arguments it can't encode for the shell (`invalid_agent_argument`). Fixed: the brief goes in a file and the thread starts on `Read <file> and follow it.` The failed launch left no registry row or workspace. |
| Launch, after the fix | Pass: no trust prompt for the new coordination worktree; `--agent orchestrator` started, its start-up `/agent-orchestration` command took the one-line prompt as arguments |
| Mail both ways | Pass |
| Lanes started by the thread through `lane.sh`, with no settings rule | Pass for a Claude lane and a Codex lane with `--approve-for-me`: the classifier allowed both |
| Each lane commits in its own worktree and reports by mail | Pass, within a minute of launch, under the owner's identity; Codex asked for no approval |
| guard-writes refuses a Claude lane writing into the owner's checkout | Pass: refused, nothing written |
| A quiet message doesn't wake MAIN; the next read prints it | Pass |
| Decision default applied by the thread's own `wake-at.sh` | Pass: armed for 17:01Z, applied at 17:01:08Z with no answer from MAIN |
| `GONE` when a lane's pane closes | Pass, 14 s after the close, reported by the thread |
| `UNREAD` when the thread stops waiting, then a ring in its pane | Pass: `UNREAD` at exactly 5 min; the ringed thread read and replied 11 s later |
| A thread showing an `AskUserQuestion` dialog | **herdr reported it `done`, not `blocked`** (`herdr agent explain`: the title rule `osc_title_idle` matched), so no watcher fired. The owner answered in the pane and the reply arrived by mail. The spike saw `blocked` for a permission prompt. |
| Rotation | Pass: the new thread opened in a new tab of the build's workspace, the old pane closed, the name stayed, and the new thread resumed from RESUME and answered mail |
| `finish-lane.sh` while the lane's agent runs | Pass: refused, with the lane named by a relative path |
| `thread.sh close` | Pass: pane and workspace closed, worktree and branch removed, the build's mail moved into the archive |

Not run as its own probe: a second build waited on alongside the first, and a fresh MAIN session reading the
build's mail. MAIN has no identity in the mailbox, so any session reading `<build>/main` picks up the mail; the
offline tests cover two watched agents.

Findings for the remaining steps:

- Threads and lanes must never use `AskUserQuestion`: herdr doesn't report it as blocked. Questions go by mail.
- MAIN reads a thread's screen (`herdr agent read`) before ringing it, so a ring never types into a dialog herdr
  didn't recognise.
- No settings rule is needed for `lane.sh`.
