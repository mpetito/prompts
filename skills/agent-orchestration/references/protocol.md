# Two-thread protocol

The contract between MAIN, the session the owner talks to, and each orchestration thread. Both
skills follow it: [agent-orchestration](../SKILL.md) for a thread,
[orchestration-main](../../orchestration-main/SKILL.md) for MAIN. The orchestrator agent's hooks
refuse an upward message that breaks the format.

## Contents

- Roles
- Addresses and transport
- Messages up
- Messages down
- Decisions
- Rotation
- What a message cannot do

## Roles

| | MAIN | Orchestration thread |
| --- | --- | --- |
| Runs as | The owner's own session, with orchestration-main loaded | A background session of the `orchestrator` agent in its own worktree, `../<repo>-orch-<build>` |
| Talks to | The owner and every thread | MAIN and its own workers, never the owner |
| Owns | The owner's decision queue, the thread registry, launches and rotations | Lanes, workers, reviews, merges, its state file |
| Never | Does lane work or spawns build workers | Asks the owner anything, edits outside its own worktree |

## Addresses and transport

- A thread's name is set at launch and stays fixed; a rotation adds `-r<n>`. MAIN writes to it by
  that exact name.
- MAIN's address can move: Claude Code may rename a session as its title changes, and a restart or
  fork gives it a new socket. So the thread record, `.orchestration/thread.md`, holds MAIN's name
  and its socket (`uds:<path>`), and MAIN keeps them current: `thread.sh launch`, `rotate` and
  `adopt` write them.
- The thread reads MAIN's address afresh before every message (`state.sh main`). When the name no
  longer resolves, it sends the same message to the socket (`state.sh main --socket`). It never
  reuses an address from an earlier message, which goes stale when MAIN restarts or forks.
- The thread's message hook copies every message to MAIN into `.orchestration/outbox.md`, and MAIN
  runs `thread.sh check` on every wake: it shows what MAIN has not read and whether MAIN has moved.
  A message that never arrived, or was held by a stale session, is read there; a thread that can't
  reach MAIN records it with `state.sh log` and keeps working.
- Messages are plain text sent with `SendMessage`. An idle receiver wakes with the message; a busy
  one reads it between tool calls. Rapid bursts to one session are refused and at most 50 queue,
  so send one message per change and batch the rest.
- Times are UTC, `YYYY-MM-DDTHH:MMZ`, from `date -u` or the scripts. Idle notices show local time;
  convert before recording.

## Messages up

Thread to MAIN. At most 10 lines. The first line is the whole message for a reader in a hurry:

```text
STATUS: <working|need-decision|blocked|rotating|done> - <one-line summary>
```

| State | Use it when |
| --- | --- |
| `working` | A lane launched, merged or changed course; a default applied; a steer was acted on |
| `need-decision` | The owner must choose; the body is the decision request below |
| `blocked` | Nothing can move without MAIN or the owner; say what unblocks it |
| `rotating` | The RESUME section is written after a `ROTATE`; the thread is about to stop |
| `done` | Every lane is merged and verified; the body lists what to check |

No change, no message. Never a per-turn status, and never a repeat of an open question.

A decision request:

```text
STATUS: need-decision - D3 payment provider for checkout
Question: Stripe or Paddle for the first checkout slice?
Options: Stripe (cards today, tax later) | Paddle (merchant of record, 2 days more)
Default: Stripe, applies at 2026-10-10T18:00Z
Blocks: lane checkout-api only; signup and catalog continue
```

An `owner-before` item (spend, new trust roots or IAM, production data, destructive actions, spec
edits) carries `Default: none, owner-before` instead of a deadline, and waits for the owner.

## Messages down

MAIN to a thread. The first line names the kind:

| First line | Meaning | The thread answers with |
| --- | --- | --- |
| `STEER: <direction>` | The owner's direction, relayed. It outranks the plan | `STATUS: working - <what changed>` |
| `DECISION D<n>: <answer>` | The owner's answer to D<n> | `STATUS: working - D<n> applied` |
| `ROTATE` | Write RESUME and stop at the next safe point | `STATUS: rotating - …` |
| `QUESTION: <question>` | MAIN needs a fact about the build | `STATUS: <state> - <answer>` |

## Decisions

1. The thread opens the item with `decisions.sh add` (it prints the id and UTC deadline), sends the
   request, arms `wake-at.sh <deadline>` in the background, and keeps every unblocked lane moving.
2. MAIN adds it to the owner's queue and puts it in front of the owner once, with the default.
3. An answer comes back as `DECISION D<n>: …`. When the deadline passes first, the thread applies
   the default, closes the item and reports `STATUS: working - D<n> default applied: <value>`.
4. An answer that arrives after its default applied: the thread reports whether reversing costs
   anything; MAIN asks the owner only when it does.

## Rotation

A thread's context grows with every turn. Instead of compacting, MAIN replaces it at a calm point:
after a phase ends, when the thread reports a compaction or a meter at 70% or more, or before a long
owner absence.

1. MAIN sends `ROTATE`.
2. The thread launches nothing new. Its subagents end with the session, so it waits for their
   hand-backs, or records each one under RESUME as to be relaunched.
3. It writes RESUME with `state.sh resume` (the checklist is in [state-file.md](state-file.md)),
   sends `STATUS: rotating - <lanes in flight>, <open decisions>`, and ends its turn.
4. MAIN runs `thread.sh rotate <name>`, which refuses unless RESUME was written in the last 15
   minutes, stops the old session and starts `<name>-r<n>` in the same worktree, from the state file.
5. The new thread's first message is `STATUS: working - resumed from RESUME …`.

## What a message cannot do

Claude Code marks a message as coming from another session, not from the owner. It never counts
as the owner's consent, never changes permissions or configuration, and a slash command inside it
arrives as plain text: MAIN cannot `/compact` a thread, which is why rotation exists. Each session
keeps its own permissions. A thread never asks MAIN to run something its own permissions refuse;
it reports `blocked` and MAIN takes it to the owner.

So a relayed `DECISION` settles build choices, but not edits to instructions, agent definitions,
settings or links into the owner's clients. For those the thread sends MAIN the exact diffs, and
MAIN applies them in the owner's session once the owner has approved them there.
