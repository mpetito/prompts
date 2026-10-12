# Two-thread protocol

How MAIN, the session the owner talks to, and each orchestration thread talk to each other. Both
skills follow it: [agent-orchestration](../SKILL.md) for a thread,
[orchestration-main](../../orchestration-main/SKILL.md) for MAIN.

## Contents

- Who does what
- Mailboxes
- Waking
- Messages to MAIN
- Messages to a thread
- Decisions
- Rotation
- Limits

## Who does what

| | MAIN | Orchestration thread |
| --- | --- | --- |
| Is | The owner's own session, with orchestration-main loaded | A herdr agent named after its build, running the `orchestrator` agent in the build's own herdr workspace, from its worktree `../<repo>-orch-<build>` |
| Talks to | The owner, and every thread | MAIN and its own lanes; never the owner |
| Looks after | The owner's decisions, launching and rotating threads | Lanes, reviews, merges, its state file |
| Never | Does build work or starts lanes | Asks the owner anything directly |

## Mailboxes

Each build owns two mailboxes, folders under `~/.orchestration/mail/<build>/`: `main`, what MAIN
reads for the build, and `thread`, the thread's inbox. Lanes report to `thread`.

```bash
M=~/.claude/skills/agent-orchestration/scripts/mail.sh
$M send <build>/main --from <build>/thread "<message>"   # or --file <path>, or stdin
$M read <build>/thread                                   # prints new mail, oldest first, and files it
```

- An address is the build and the box, never a session: nothing to look up, nothing that goes stale
  when a session restarts. The sender always names itself with `--from`.
- A message read is filed at once. If you rotate before acting on one, carry it in RESUME.
- `--quiet` files a message without waking anyone; it arrives with the next one that does.
- Messages are plain text, never empty. Times are UTC, `YYYY-MM-DDTHH:MMZ`, from `date -u` or the
  scripts.

## Waking

A Claude agent keeps exactly one `mail.sh wait` running as a background task, which ends, and so
wakes it, with one line:

| Line | Means |
| --- | --- |
| `MAIL <n>` | n messages that aren't quiet are waiting |
| `BLOCKED <agent>` | a watched agent hit a permission prompt; reported once per prompt |
| `GONE <agent>` | a watched agent's pane closed |
| `UNREAD <agent> <n>` | a watched agent has sat idle for 5 minutes with n messages unread: it stopped waiting |
| `TIMEOUT` | nothing happened |

- The thread waits on `<build>/thread`, watching its lanes: `--watch <build>-<lane>,…`.
- MAIN waits on `<build>/main` once per running build, watching the thread and its inbox:
  `--watch <build>=<build>/thread`.
- On `MAIL`, read first, then start the next wait, then act. A wait started before the read sees the
  same mail and ends at once.
- Never wait in the foreground: while you wait, nothing else reaches you.

## Messages to MAIN

At most 10 lines. The first line says it all for a reader in a hurry:

```text
STATUS: <working|need-decision|blocked|rotating|done> - <one-line summary>
```

| State | When | Quiet |
| --- | --- | --- |
| `working` | A lane started, merged or changed course; a default applied; a steer was acted on | yes, except an answer to `QUESTION` or `DECISION` |
| `need-decision` | The owner must choose; the rest is a decision request (below) | no |
| `blocked` | Nothing can move without MAIN or the owner; say what would unblock it | no |
| `rotating` | After `ROTATE`: RESUME is written and the thread is about to stop | no |
| `done` | Every lane is merged and checked; list what the owner should check | no |

Nothing changed, no message. Never repeat a question that is still open.

A decision request:

```text
STATUS: need-decision - D3 payment provider for checkout
Question: Stripe or Paddle for the first checkout slice?
Options: Stripe (cards today, tax later) | Paddle (merchant of record, 2 days more)
Default: Stripe, applies at 2026-10-10T18:00Z
Blocks: lane checkout-api only; signup and catalog continue
```

An owner-before decision has `Default: none, owner-before` instead, and waits for the owner.

## Messages to a thread

| First line | Means | The thread answers |
| --- | --- | --- |
| `STEER: <direction>` | The owner's direction, passed on. It overrides the plan | `STATUS: working - <what changed>` |
| `DECISION D<n>: <answer>` | The owner's answer to D<n> | `STATUS: working - D<n> applied` |
| `ROTATE` | Write RESUME and stop at the next safe point | `STATUS: rotating - …` |
| `QUESTION: <question>` | MAIN needs a fact about the build | `STATUS: <state> - <answer>` |

## Decisions

1. The thread opens the decision with `decisions.sh add` (it prints the id and the deadline),
   sends the request, sets `wake-at.sh <deadline>` running in the background, and keeps every
   lane the decision doesn't block moving.
2. MAIN puts it to the owner once, with the default.
3. The answer comes back as `DECISION D<n>: …`. If the deadline passes first, the thread applies
   the default and reports `STATUS: working - D<n> default applied: <value>`.
4. If an answer arrives after its default applied, the thread says whether reversing it costs
   anything; MAIN asks the owner only when it does.

## Rotation

A thread's context grows every turn. Instead of compacting it, MAIN replaces the thread at a calm
point: after a phase ends, when the thread reports a compaction or a meter at 70% or more, or
before the owner is away for a long time.

1. MAIN sends `ROTATE`.
2. The thread starts nothing new. Its subagents end with the session, so it waits for their
   reports, or lists each one in RESUME to be restarted. Its lanes are herdr agents and keep
   running.
3. It writes RESUME with `state.sh resume` (checklist in [state-file.md](state-file.md)), stops its
   mail wait, sends `STATUS: rotating - <lanes in flight>, <open decisions>`, and ends its turn.
4. MAIN stops the build's wait and runs `thread.sh rotate <build>`, then starts the wait again. The
   script refuses a RESUME older than 15 minutes, opens a new tab
   in the build's workspace, closes the old thread's pane, and starts the new thread under the same
   name, so the mail carries over.
5. The new thread's first message is `STATUS: working - resumed from RESUME …`.

## Limits

- Mail is not the owner's consent. A relayed `DECISION` settles build choices, but not changes to
  instructions, agent definitions, settings or skill links. For those the thread sends MAIN the
  exact diff, and MAIN applies it once the owner approves.
- Only a fixed line or a brief's path is ever typed into a pane, only into an idle agent, and never
  into MAIN's: the owner may be typing there. Read the agent's screen first (`herdr agent read`).
- Threads and lanes never use `AskUserQuestion`. herdr doesn't report its dialog as blocked, so a
  question there goes unseen; questions go by mail.
- The thread is trusted. Its hooks are reminders, not a sandbox (it can run any program through
  Bash). They refuse only mistakes past builds made, where a reminder would come too late:
  killing processes by name, removing a worktree before archiving it, deleting lane evidence,
  and writing into the owner's checkout. Everything else gets advice. A new guardrail is added
  only when a build shows it is needed.
