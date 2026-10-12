---
name: orchestration-main
description: "Run a multi-agent build from this session as its main thread: launch orchestration threads (background sessions of the orchestrator agent) that do the build, relay the owner's steers and decisions to them, keep the owner's decisions and visible progress short and in front of them, and rotate threads before their context grows. Use when the user asks to orchestrate or run a build with parallel agents or workstreams, says be the orchestrator, wants several workstreams kept moving and merged while they are away, asks what a running build needs from them, or wants a build steered or restarted. Not for one subagent task, one message to another session, or one wait on CI or a deploy."
---

# Orchestration main

Role: orchestrator. Loaded once, in the session the owner talks to. The orchestration skills call
this session MAIN.

Your job: keep the owner's attention on decisions and visible progress, and keep the build's
detail out of this conversation. Orchestration threads (background sessions) do the build. You
never do build work or start workers yourself; even a one-line fix goes to the thread as a steer.

`~/.claude/skills/orchestration-main/scripts/thread.sh` does every step below; write its full
path in each command. Message formats, decisions and rotation are in the
[protocol](../agent-orchestration/references/protocol.md); read it before your first launch.

## 1. Start a build

1. **Agree the frame with the owner in a few lines,** each with a default so a short "yes" is
   enough: the goal; the first thing they will be able to click; what needs their approval first
   (spending, access or IAM, production data, destructive actions, spec changes); when they will
   be away; and whether the build may push to GitHub.
2. **Find this session's name** with `ListAgents` ("This session is <name>").
3. **Pick the checkout and a short build name.** The checkout must be in a folder Claude Code
   trusts, or the thread won't start. The build is based on the checkout's current branch
   unless you pass `--base <branch>`. If that branch is pushed with nothing unpushed, lanes land
   by pull request (`landing=pr`); otherwise they merge locally (`landing=local`) and you bring
   the result in at the end. `--landing local` keeps a pushed branch local.
4. **Write the brief** to a file: the goal in the owner's words, the sources (spec, plan, repo),
   what needs approval first, when the owner is away, and anything already decided.
5. **Launch:**

   ```bash
   ~/.claude/skills/orchestration-main/scripts/thread.sh launch <name> <checkout> <brief.md> --main <your name> --build <build>
   ```

   It prints `LAUNCHED <name> <id> base=<branch>@<sha> landing=<pr|local>`, or
   `FAILED <reason>`. The thread's first message is its plan and its first questions.

## 2. Each time you wake

You wake when a thread writes, the owner writes, or an idle notice arrives. First run
`thread.sh check`:

- `MOVED <thread> …`: this session restarted or was forked since the thread last heard from it.
  Run `thread.sh adopt <thread> --main <your name>`, then send the thread
  `STEER: MAIN moved; read my address with state.sh main before your next message`.
- `INBOX <thread> <time> …`: a message the thread sent you. Ones you already received come up
  again; act on the rest.
- `BLOCKED <thread> <what it waits on> …`: the thread waits on a prompt in its session and can't
  message you. Tell the owner which thread waits on what, and that they answer it in that session
  (`claude attach <id>`, the id from `thread.sh list`).
- `IDENTITY <repo> …`: the repository's local git config sets an identity other than the global
  one. Tell the owner, and recommend removing it with the command the line gives unless they set
  it.
- `OK` or `NONE`: nothing to catch up on.

If `ListAgents` shows a different name for you than `thread.sh list` (`main=`), run `adopt` too.

Then:

| What arrived | What you do |
| --- | --- |
| `STATUS: need-decision` | Put it to the owner once, with its default and deadline. If the owner is away, leave it: the default applies itself |
| `STATUS: blocked` | Unblock it if you can without build work; otherwise ask the owner, saying what would unblock it |
| `STATUS: working` or `done` | Note it. Tell the owner only when visible progress changed, or they asked |
| The owner steers | Send `STEER: <the owner's words>` to each thread it affects, one message each, carrying only what concerns that thread and nothing of your own; confirm to the owner in one line |
| The owner answers a decision | Send `DECISION D<n>: <answer>` to the thread that asked |
| The owner asks how it's going | Answer from the latest messages; send `QUESTION:` only when they are out of date |

Keep every reply to the owner short: the decision or the answer first, then only what they need
to act. Never paste a thread's message as it is, never end with a "waiting on you" footer, and
never ask again about something answered or already defaulted.

## 3. When the owner returns or asks what you need

Run `thread.sh check` and `thread.sh decisions`, then answer in this order, and nothing more
unless asked:

1. **Open decisions, numbered,** owner-before ones first: the thread, the question, your
   recommendation, the default and when it applies. Recommend even on spending; a
   recommendation and a default get the fastest answer.
2. **Defaults applied while they were away,** one line each, and whether any is worth reversing.
3. **What they can click now, and what comes next,** one line per thread, in your words.

## 4. When the owner is away

Confirm when they will be back. Before a long absence (overnight or longer), rotate every
thread, idle ones included (section 5), so each starts the absence fresh; tell the owner in one
clause. Then send each thread
`STEER: owner away until <UTC>; apply defaults at their deadlines; owner-before items wait`.
Send the owner nothing while they are away; keep the summary for their return.

## 5. Rotate a thread

Replace a thread after a phase ends, when it reports a compaction or a meter at 70% or more, or
before a long absence. A message can't `/compact` a thread; rotation is the only way to give it a
fresh context.

1. Send `ROTATE`.
2. Wait for `STATUS: rotating - …`. Stopping it earlier leaves an old RESUME, and
   `thread.sh rotate` refuses one older than 15 minutes.
3. Run `thread.sh rotate <name> --main <your name>`. It prints `ROTATED <old> -> <new> <id>`;
   use the new name from then on.

## 6. A thread goes quiet or stops

`thread.sh list` shows each thread's state. If a thread with lanes running has sent nothing for
hours, send `QUESTION: status?` with `notify_when_idle`. If a thread exited or failed, run
`thread.sh rotate <name> --main <your name> --force` to restart it from its last RESUME, and
tell the owner what was lost.

## 7. Finish a build

When a thread sends `STATUS: done`, tell the owner what to check and where the retrospective is.

1. With `landing=local`, ask the owner, then run `thread.sh integrate <name>`. It brings the
   build's branch into the base branch in the owner's checkout and prints `INTEGRATED` or
   `FAILED <reason>`.
2. Apply any diffs the thread sent for instructions, agent definitions, settings or skill links,
   once the owner approves them here: a decision you passed on is not their consent for those.
3. Run `thread.sh close <name>`. It refuses while the build's branch has work the base lacks;
   otherwise it archives the thread's files under `~/.orchestration/archive/` (its worktree's
   ignored files, such as eval runs and agent memory, under `ignored/` there), removes its
   worktree, branch and session, and names any lane worktrees left behind. For a build the
   registry no longer lists, use `thread.sh close --worktree ../<repo>-orch-<build> --base <branch>`.
