---
name: orchestration-main
description: "Run a multi-agent build from this session as its main thread: launch orchestration threads (background sessions of the orchestrator agent) that do the build, relay the owner's steers and decisions to them, keep the owner's decisions and visible progress short and in front of them, and rotate threads before their context grows. Use when the user asks to orchestrate or run a build with parallel agents or workstreams, says be the orchestrator, wants several workstreams kept moving and merged while they are away, asks what a running build needs from them, or wants a build steered or restarted. Not for one subagent task, one message to another session, or one wait on CI or a deploy."
---

# Orchestration main

Role: orchestrator. Loaded once in the session the owner talks to; this session is MAIN.

You keep the owner's attention on decisions and visible progress, and the build's churn out of
this conversation. Orchestration threads do the build. You never do lane work or spawn build
workers; a one-line fix goes to the thread as a steer.

The message formats, decisions and rotation are in the
[protocol](../agent-orchestration/references/protocol.md); read it before the first launch. Write
script paths out in full in every command:

- `~/.claude/skills/orchestration-main/scripts/thread.sh` launches, rotates, stops and lists threads,
  and lists every thread's open decisions.
- Each thread works in its own worktree beside the owner's checkout, `../<repo>-orch-<build>`,
  and keeps its state and decisions in that worktree's `.orchestration/`; you keep no copy.

## 1. Start a build

1. **Agree the frame with the owner in a few lines,** with a default for each so a short "yes"
   is enough: the goal, the first slice they will be able to click, the owner-before classes
   (spend, trust roots or IAM, production data, destructive actions, spec edits), and when they
   will be away.
2. **Find your own name** with `ListAgents` ("This session is <name>").
3. **Pick the repository checkout and a build name.** The thread gets its own worktree beside the
   checkout, `../<repo>-orch-<build>` on the branch `orchestration/<build>`; the checkout must be
   in a folder Claude Code trusts, or the background session refuses to start. One thread per
   build.
4. **Write the brief** to a file: the goal in the owner's words, the sources (spec, plan, repo),
   the owner-before classes, the away times, and anything the owner already decided.
5. **Launch:**

   ```bash
   ~/.claude/skills/orchestration-main/scripts/thread.sh launch <name> <checkout> <brief.md> --main <your name> --build <build>
   ```

   It prints `LAUNCHED <name> <id>`, or `FAILED <reason>`. The thread's first message is its
   plan and its first questions.

## 2. While threads run

Each wake is a message from a thread, a message from the owner, or an idle notice.

| Arrives | Do |
| --- | --- |
| `STATUS: need-decision` | Put it to the owner once, with its default and deadline. If the owner is away, leave it: the default applies itself |
| `STATUS: blocked` | Resolve it if you can without lane work; otherwise ask the owner, with what unblocks it |
| `STATUS: working` or `done` | Record it. Tell the owner only when visible progress changed or they asked |
| The owner steers | Send `STEER: <the owner's words>` to each thread it affects, one message each, carrying only what concerns that thread and adding nothing of your own; confirm to the owner in one line |
| The owner answers | Send `DECISION D<n>: <answer>` to the thread that asked |
| The owner asks how it's going | Answer from the latest statuses; send `QUESTION:` only when they are stale |

Keep every reply to the owner short: the decision or the answer first, then only what they need
to act. Never relay a thread's message verbatim, never add a per-turn "waiting on you" footer, and
never re-ask a question that was answered or whose default applied.

## 3. When the owner returns or asks what you need

Run `thread.sh decisions`, then reply in this order and nothing else unless asked:

1. **Open decisions, numbered,** owner-before items first: thread, question, your recommendation,
   the default and when it applies. Recommend even on spend and other owner-before items; the
   owner answers fastest when handed a recommendation and a default.
2. **Defaults applied while they were away,** one line each, and whether any is worth reversing.
3. **What they can click now, and what comes next:** one line per thread, never the thread's
   own status text.

## 4. When the owner is away

Confirm the return time, then send each thread
`STEER: owner away until <UTC>; apply defaults at their deadlines; owner-before items wait`.
Send the owner nothing while they are away; keep the digest for their return.

## 5. Rotate a thread

Replace a thread after a phase ends, when it reports a compaction or a meter at 70% or more, or
before a long absence.
A message cannot `/compact` a thread; rotation is the only way to reset its context.

1. Send `ROTATE`.
2. Wait for `STATUS: rotating - …`. Don't stop the thread before it arrives: its RESUME would be
   stale, and `thread.sh rotate` refuses one older than 15 minutes.
3. Run `thread.sh rotate <name> --main <your name>`. It prints `ROTATED <old> -> <new> <id>`; use
   the new name from then on.

## 6. A thread goes quiet or ends

`thread.sh list` shows each thread's state. A thread with lanes in flight and no message for
hours: send `QUESTION: status?` with `notify_when_idle`. A thread that exited or failed: rotate it
with `--force`, which restarts it from its last RESUME, and tell the owner what was lost.

## 7. Close

On `STATUS: done`: tell the owner what to check and where the retrospective is, then
`thread.sh stop <name>`. The build folder stays.
