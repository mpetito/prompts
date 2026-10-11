# Two-thread protocol

How MAIN, the session the owner talks to, and each orchestration thread talk to each other. Both
skills follow it: [agent-orchestration](../SKILL.md) for a thread,
[orchestration-main](../../orchestration-main/SKILL.md) for MAIN. A hook refuses a message to
MAIN that breaks the format, and says why.

## Contents

- Who does what
- Addresses
- Messages to MAIN
- Messages to a thread
- Decisions
- Rotation
- Limits of messages and hooks

## Who does what

| | MAIN | Orchestration thread |
| --- | --- | --- |
| Is | The owner's own session, with orchestration-main loaded | A background session of the `orchestrator` agent, in its own worktree `../<repo>-orch-<build>` |
| Talks to | The owner, and every thread | MAIN and its own workers; never the owner |
| Looks after | The owner's decisions, launching and rotating threads | Lanes, workers, reviews, merges, its state file |
| Never | Does build work or starts build workers | Asks the owner anything directly |

## Addresses

- A thread keeps the name it was launched with; each rotation adds `-r<n>`. MAIN uses that name.
- MAIN's name and socket address (`uds:<path>`) are in the thread record,
  `.orchestration/thread.md`. They can change: Claude Code may rename a session as its title
  changes, and a restart or fork gives it a new socket. `thread.sh` keeps the record current.
- Before every message to MAIN, the thread reads the name with `state.sh main`. If the name no
  longer works, it sends the same message to the socket from `state.sh main --socket`. It never
  replies to an address taken from an earlier message: that goes stale.
- A hook copies every message to MAIN into `.orchestration/outbox.md`. MAIN runs
  `thread.sh check` each time it wakes, which shows anything it didn't receive. A thread that
  can't reach MAIN logs it with `state.sh log` and keeps working.
- Messages are plain text, sent with `SendMessage`. Send one per change and batch the rest:
  Claude Code refuses rapid bursts, and queues at most 50.
- Times are UTC, `YYYY-MM-DDTHH:MMZ`, from `date -u` or the scripts.

## Messages to MAIN

At most 10 lines. The first line says it all for a reader in a hurry:

```text
STATUS: <working|need-decision|blocked|rotating|done> - <one-line summary>
```

| State | When |
| --- | --- |
| `working` | A lane started, merged or changed course; a default applied; a steer was acted on |
| `need-decision` | The owner must choose; the rest is a decision request (below) |
| `blocked` | Nothing can move without MAIN or the owner; say what would unblock it |
| `rotating` | After `ROTATE`: RESUME is written and the thread is about to stop |
| `done` | Every lane is merged and checked; list what the owner should check |

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
   reports, or lists each one in RESUME to be restarted.
3. It writes RESUME with `state.sh resume` (checklist in [state-file.md](state-file.md)), sends
   `STATUS: rotating - <lanes in flight>, <open decisions>`, and ends its turn.
4. MAIN runs `thread.sh rotate <name>`. It refuses a RESUME older than 15 minutes, stops the old
   session, and starts `<name>-r<n>` in the same worktree.
5. The new thread's first message is `STATUS: working - resumed from RESUME …`.

## Limits of messages and hooks

- Claude Code marks a message as coming from another session. It never counts as the owner's
  consent, can't change permissions or settings, and a slash command in it is plain text: MAIN
  can't `/compact` a thread, which is why rotation exists.
- So a relayed `DECISION` settles build choices, but not changes to instructions, agent
  definitions, settings or skill links. For those the thread sends MAIN the exact diff, and MAIN
  applies it once the owner approves.
- The thread is trusted. Its hooks are reminders, not a sandbox (it can run any program through
  Bash). They refuse only mistakes past builds made, where a reminder would come too late:
  killing processes by name, removing a worktree before archiving it, deleting lane evidence,
  and writing into the owner's checkout. Everything else gets advice. A new guardrail is added
  only when a build shows it is needed.
