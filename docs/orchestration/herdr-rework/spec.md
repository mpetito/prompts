# Orchestration on herdr and a file mailbox

## Why

Orchestration threads run as Claude Code background sessions and talk to MAIN with `SendMessage`.
Real builds broke where those sessions are weakest: MAIN's address goes stale when MAIN is forked
or restarted, a thread waiting on a permission prompt is invisible, and Codex lanes need a separate
mechanism. Each break got a home-grown patch (address records, an outbox, `MOVED` and `adopt`, a
`BLOCKED` check, a message-format hook, an unlanded watcher). The owner always works in herdr,
which already hosts agents in visible panes under names and knows when each one is idle, working
or blocked.

A spike on 2026-10-12 (`../2026-10-12-herdr-mailbox-spike.md`) showed, with a plain Claude thread
and a Codex worker: mail both ways, waking an idle and a busy thread, a blocked thread reported
once, a decision default applied by the thread's own timer, and a rotated agent taking over a name
and its mail. No daemon was needed.

## What changes

- **Hosting.** Every build gets its own herdr workspace, opened without taking focus and labelled
  with the build. The thread is a herdr agent named after the build, running the `orchestrator`
  agent from the coordination worktree in that workspace's first tab; each lane gets its own tab
  there. MAIN's workspace is never touched. The owner can switch to a build's workspace to
  watch it or answer a prompt in place. Rotation starts a fresh agent under the same name.
- **Messages.** Each build owns two mailboxes: `main` (what MAIN reads for that build) and
  `thread`. Lanes report to `thread`; the thread gives a lane work by prompting the lane's own pane.
  A message can be quiet: it wakes no one and is read with the next batch. Threads send routine
  `working` updates quietly, so MAIN wakes only for what needs it (a decision, a blocked pane,
  `done`, `rotating`). A message is never empty. A mailbox is a folder, written by atomic rename and read in order; mail is
  addressed `<build>/<box>`. Anyone sends with one command: MAIN, a thread, a Codex worker or the
  owner. Nothing is ever typed into MAIN's pane, so the owner's half-typed input is never touched.
- **MAIN has no herdr name.** Nothing watches or prompts MAIN, so its address is a mailbox, not a
  name: herdr clears a name when its agent exits, and a restarted, forked or fresh MAIN session
  needs nothing renamed or adopted. MAIN keeps one background wait per running build, on that
  build's `main` box, and sends from it. Thread names follow herdr's rule (lowercase, at most 32
  characters, unique among live agents); launch refuses a name a live agent holds.
- **Waking.** A Claude agent (MAIN or a thread) keeps one background wait running. It returns on
  new mail, on a watched agent turning blocked (once per prompt), on a watched agent disappearing,
  on a watched agent sitting idle with mail unread for 5 minutes (it stopped waiting), or on a
  timeout. The agent reads its mail, then starts the next wait. An idle agent with unread mail is
  rung with a short prompt in its own pane, never MAIN's.
- **Blocked.** When a thread, or a lane it watches, is stuck on a permission or question prompt,
  the watcher reports it; the thread tells MAIN, and MAIN tells the owner which pane to answer.
- **Getting the owner's attention.** When MAIN has a decision for the owner or a blocked pane, it
  also raises a herdr notification with a sound, so the owner hears it from any workspace.
- **What may be typed into a pane.** Only a fixed line or a pointer to a brief file, never task
  text, and only into an idle agent: a lane's pointer prompt, or the ring for a thread with unread
  mail. Never into MAIN.
- **Mail in hand.** Reading files a message at once, so a thread that rotates between reading a
  message and acting on it would lose it. The RESUME checklist carries mail read but not yet acted
  on.
- **Lanes.** A lane is a herdr agent, Claude or Codex, treated the same either way: started by
  one launcher script in its own tab and lane worktree, given work by a short prompt pointing at
  its brief, watched by the thread's wait, backed by a `wake-at.sh` timer, and reporting by mail
  under its own name (a Codex sandbox can't see the pane's environment or reach herdr, so the
  sender is always explicit). A Claude lane runs a lane agent definition that carries the same
  guard hooks a subagent worker inherits today. A Codex lane runs with `--approve-for-me`, so
  Codex's automatic reviewer grants its approvals (commits in the worktree's protected git
  directory among them). The owner allows the launcher in their settings, since Claude Code's
  auto-mode classifier refuses such launches otherwise. The first time a project needs Codex, the
  owner is asked to run Codex there once by hand to record approval. Subagents stay for short jobs
  that aren't lanes, such as a test run or a plan review.

## What stays

Decisions with defaults that apply at a deadline (the thread's own timer), rotation from the state
file's RESUME, lanes and the landing scripts, worker briefs, the eval suites and offline tests,
the message format (`STATUS:` first line; `STEER`, `DECISION`, `ROTATE`, `QUESTION` down), and the
hooks that refuse proven mistakes.

## What goes

MAIN's name and socket in the thread record; the outbox; the `INBOX`, `MOVED`, `adopt` and `BLOCKED` paths
of the thread check; the message-format hook; reading session state from `claude agents`.

## Not yet shown

The spike didn't run these; the live smoke test must before the skills depend on them: a thread
started with `--agent orchestrator` and its hooks; launch in a fresh coordination worktree (trust
prompt); a fresh MAIN session picking up a running build's mail; several watched agents in one
wait; a `GONE` report; a Claude lane (its hooks firing) and a Codex lane with `--approve-for-me`, each
committing in its worktree;
whether the owner's one-time Codex approval covers new lane worktrees; the owner's half-typed input while a wait wakes MAIN (the
owner reports it survives, from past use).

## Out of scope

Independent peers. Letterbox-style coordination between peers that each own their work (task
acknowledgements, ownership records, leases) belongs to a layer above this one: a peer agent in the
owner's place, driving MAIN and talking to other peers. Nothing here should block that layer.

## Rules carried over

- Mail is not the owner's consent. A relayed `DECISION` settles build choices, never changes to
  instructions, agent definitions, settings or skill links; those go to MAIN as an exact diff.
- The thread is trusted; hooks are reminders, not a sandbox.
- The repository stays public and project-agnostic.

## Decided

1. **Lanes:** herdr agents of either kind through one launcher the owner allows in settings;
   Codex with `--approve-for-me`; Claude with a lane agent definition; the headless Codex launcher
   goes.
2. **MAIN's address:** a mailbox per build, `<build>/main`; MAIN has no herdr name.
3. **Placement:** one herdr workspace per build, the thread in its first tab, one tab per lane;
   MAIN's workspace untouched.
4. **Rotation:** the same name, replacing the thread in its workspace's first tab.
5. **After a build:** close archives the build's mail folder, then closes its workspace.
6. **MAIN's waits:** one per running build, on its `main` box, watching its thread.
7. **The orchestration home:** launch passes `ORCHESTRATION_HOME` to the build's workspace when it
   is set.
