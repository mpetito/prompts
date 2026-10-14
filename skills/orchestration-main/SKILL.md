---
name: orchestration-main
description: "Run a multi-agent build from this session as its main thread: launch orchestration threads (herdr agents running the orchestrator agent, one per build) that do the build, relay the owner's steers and decisions to them, keep the owner's decisions and visible progress short and in front of them, and rotate threads before their context grows. Use when the user asks to orchestrate or run a build with parallel agents or workstreams, says be the orchestrator, wants several workstreams kept moving and merged while they are away, asks what a running build needs from them, or wants a build steered or restarted. Not for one subagent task, one message to another session, or one wait on CI or a deploy."
---

# Orchestration main

Role: orchestrator. Loaded once, in the session the owner talks to. The orchestration skills call
this session MAIN.

Your job: keep the owner's attention on decisions and visible progress, and keep the build's
detail out of this conversation. Orchestration threads do the build: herdr agents, one per build,
each in the build's own herdr workspace. You never do build work or start lanes yourself; even a
one-line fix goes to the thread as a steer.

This session runs inside herdr (`test "$HERDR_ENV" = 1`). Two scripts do every step below; run
each as `python3` and its full path, quoted, in every command (never `~`, which not every shell
expands). A short name below, such as `thread.py check`, means that command:

- `thread.py`, `python3 "$HOME/.claude/skills/orchestration-main/scripts/thread.py"`, launches,
  rotates and closes threads.
- `mail.py`, `python3 "$HOME/.claude/skills/agent-orchestration/scripts/mail.py"`, carries
  messages. You read and send as `<build>/main`; the thread's inbox is `<build>/thread`.

Mail, waking, message formats, decisions and rotation are in the
[protocol](../agent-orchestration/references/protocol.md); read it before your first launch.

## 1. Start a build

1. **Agree the frame with the owner in a few lines,** each with a default so a short "yes" is
   enough: the goal; the first thing they will be able to click; what needs their approval first
   (spending, access or IAM, production data, destructive actions, spec changes); when they will
   be away; and whether the build may push to GitHub.
2. **Pick the checkout and a build name.** The name is lowercase letters, digits, `-` and `_`,
   starting with a letter, at most 32 characters; it names the thread, its herdr workspace and its
   mailboxes. The checkout must be in a folder Claude Code trusts. The build is based on the
   checkout's current branch unless you pass `--base <branch>`. If that branch is pushed with
   nothing unpushed, lanes land by pull request (`landing=pr`); otherwise they merge locally
   (`landing=local`) and you bring the result in at the end. `--landing local` keeps a pushed
   branch local.
3. **Write the brief** to a file: the goal in the owner's words, the sources (spec, plan, repo),
   what needs approval first, when the owner is away, and anything already decided.
4. **Launch:**

   ```bash
   python3 "$HOME/.claude/skills/orchestration-main/scripts/thread.py" launch <build> <checkout> <brief.md>
   ```

   It prints `LAUNCHED <build> base=<branch>@<sha> landing=<pr|local>`; `BLOCKED <build> <reason>`
   when the thread waits on a startup prompt (tell the owner to answer it in herdr workspace
   `<build>`); or `FAILED <reason>`.
5. **Start the build's wait** as a background task, and keep one running per build until it closes:

   ```bash
   python3 "$HOME/.claude/skills/agent-orchestration/scripts/mail.py" wait <build>/main --watch <build>=<build>/thread
   ```

   The thread's first message is its plan and its first questions.

## 2. Each time you wake

You wake when a build's wait ends or the owner writes. A wait prints one line:

- `MAIL <n>`: run `mail.py read <build>/main`, start the build's next wait, then act on each
  message (table below).
- `BLOCKED <build>`: the thread waits on a permission prompt and can't write to you. Tell the owner
  to answer it in herdr workspace `<build>`, raise
  `herdr notification show "<build> needs you" --body "<what it asks>" --sound request`, and start
  the next wait.
- `UNREAD <build> <n>`: the thread stopped waiting for mail. Read its screen
  (`herdr agent read <build> --source visible`). If it shows a dialog, tell the owner where; herdr
  doesn't report every dialog as blocked. Otherwise ring it with one line:
  `herdr agent prompt <build> "You have unread mail: run python3 '$HOME/.claude/skills/agent-orchestration/scripts/mail.py' read <build>/thread and resume your loop."`
  Then start the next wait.
- `GONE <build>`: the thread's pane closed; see section 6.
- `TIMEOUT`: start the next wait.

Never type anything else into a thread's pane, and never task text.

Run `thread.py check` when you start and when the owner returns. An `IDENTITY <repo> …` line means
the repository's local git config sets an identity other than the global one: tell the owner, and
recommend removing it with the command the line gives unless they set it.

| What arrived | What you do |
| --- | --- |
| `STATUS: need-decision` | Put it to the owner once, with its default and deadline; if they aren't looking at this pane, raise a herdr notification too. If the owner is away, leave it: the default applies itself |
| `STATUS: blocked` | Unblock it if you can without build work; otherwise ask the owner, saying what would unblock it and, for a lane waiting on a prompt, which workspace and tab |
| `STATUS: working` or `done` | Note it. Tell the owner only when visible progress changed, or they asked |
| The owner steers | Send `STEER: <the owner's words>` to each thread it affects, one message each, carrying only what concerns that thread and nothing of your own; confirm to the owner in one line |
| The owner answers a decision | Send `DECISION D<n>: <answer>` to the thread that asked |
| The owner asks how it's going | Answer from the latest messages; send `QUESTION:` only when they are out of date |

Send with `mail.py send <build>/thread --from <build>/main "<message>"`.

Keep every reply to the owner short: the decision or the answer first, then only what they need
to act. Never paste a thread's message as it is, never end with a "waiting on you" footer, and
never ask again about something answered or already defaulted.

## 3. When the owner returns or asks what you need

Run `thread.py check` and `thread.py decisions`, read each build's mail, then answer in this order,
and nothing more unless asked:

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
2. Wait for `STATUS: rotating - …`. Rotating earlier leaves an old RESUME, and `thread.py rotate`
   refuses one older than 15 minutes.
3. Stop the build's wait, then run `thread.py rotate <build>`. It prints `ROTATED <build>` (or
   `BLOCKED`, as for a launch). Then start the build's wait again: the new thread keeps the name
   and the mailboxes. A wait left running would report the old thread `GONE` while the new one
   starts.

## 6. A thread goes quiet or stops

`thread.py list` shows each thread's herdr status. If a thread with lanes running has sent nothing
for hours, read its screen and send `QUESTION: status?`. If a thread is `GONE` or `not-running`,
run `thread.py rotate <build> --force` to restart it from its last RESUME, and tell the owner what
was lost.

## 7. Finish a build

When a thread sends `STATUS: done`, tell the owner what to check and where the retrospective is,
then load the tt skill to log the build's time and put the entry in that message.

1. With `landing=local`, ask the owner, then run `thread.py integrate <build>`. It brings the
   build's branch into the base branch in the owner's checkout and prints `INTEGRATED` or
   `FAILED <reason>`.
2. Apply any diffs the thread sent for instructions, agent definitions, settings or skill links,
   once the owner approves them here: a decision you passed on is not their consent for those.
3. Stop the build's wait, then run `thread.py close <build>`. It refuses while the build's branch
   has work the base lacks; otherwise it archives the thread's files and the build's mail under
   `~/.orchestration/archive/` (its worktree's ignored files, such as eval runs and agent memory,
   under `ignored/` there), removes its worktree and branch, closes the build's herdr workspace,
   and names any lane worktrees left behind. For a build the registry no longer lists, use
   `thread.py close --worktree ../<repo>-orch-<build> --base <branch>`.
