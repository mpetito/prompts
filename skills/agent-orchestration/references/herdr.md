# Lanes in herdr

How the thread runs lanes. Every lane is a herdr agent, Claude or Codex, treated the same way: its own
tab in the build's workspace, its own worktree, its own brief file. `herdr --skill` documents the CLI.

## Contents

- Start a lane
- Hear from a lane
- Give a lane more work
- End a lane
- Traps

## Start a lane

1. Create the worktree: `git worktree add -b <branch> ../<repo>-wt-<lane> <LANE-BASE>`.
2. Write the brief ([briefs.md](briefs.md)) to `.orchestration/briefs/<lane>-<kind>.md`.
3. Run, from your own pane:

   ```bash
   ~/.claude/skills/agent-orchestration/scripts/lane.sh <build> <lane> ../<repo>-wt-<lane> <brief> --kind claude|codex --model <id> [--network]
   ```

   It prints `LANE <build>-<lane> pane=<pane> kind=<kind>`, `BLOCKED …` or `FAILED <reason>`.
   - A Claude lane runs the `lane` agent, with the guard hooks a subagent worker gets.
   - A Codex lane runs with `--approve-for-me`, so Codex's own reviewer grants its approvals, and can
     write the build's mail folder. Its sandbox sees neither the pane's environment nor herdr, which is
     why every lane names itself when it sends.
   - `BLOCKED` means the lane waits on a startup prompt. For a Codex lane in a project Codex hasn't
     been approved for, send MAIN `STATUS: blocked - Codex needs the owner to run it once in <worktree>`.
     Once the owner has answered and the lane is idle, send the pointer prompt yourself (below).
4. Restart your mail wait with the lane added to `--watch`, and arm a `wake-at.sh` timer for the
   lane's time box, so a lane that goes quiet still wakes you.

## Hear from a lane

- A lane reports by mail: `mail.sh send <build>/thread --from <build>/<lane> "STATUS: …"`, with the
  long version in a file in its worktree. Its brief says so.
- Your wait prints `BLOCKED <build>-<lane>` when a lane hits a permission prompt. Read its screen
  (`herdr agent read <build>-<lane> --source visible`). Send MAIN
  `STATUS: blocked - lane <lane> waits in workspace <build>, tab <lane>: <what it asks>`, so the owner
  can answer it in place. Never answer a lane's dialog yourself.
- `GONE <build>-<lane>` means its pane closed. Check its report and its branch before anything else.
- herdr doesn't report an `AskUserQuestion` dialog as blocked. Briefs forbid it; a lane that shows one
  anyway looks idle without reporting, so its timer is what catches it.

## Give a lane more work

Update its brief file, then, once the lane is idle, prompt it with one line:
`herdr agent prompt <build>-<lane> "Read <brief> and follow it."` Read its screen first.

- Never type task text into a pane: only a fixed line or a brief's path.
- Never prompt a lane that is working or blocked. herdr refuses a blocked one; a message queued into a
  busy Codex lane can be lost.

## End a lane

When its work is merged or dropped: close its pane with `herdr pane close <pane>`, then run
`finish-lane.sh`, which refuses while an agent still runs in the worktree. A lane agent lives for one
lane; never start a long-lived agent inside a lane worktree, because removing the worktree breaks it.

## Traps

- `herdr agent prompt --wait` exits 0 when the agent settles on `blocked`; branch on
  `.result.agent.agent_status`, never on the exit code.
- `herdr agent wait` returns at once when the agent is already in the state asked for. After a prompt,
  wait for `working` first, then for `idle` or `done`.
- `agent_prompt_stalled` usually means the text landed but Enter didn't. Read the screen, then
  `herdr agent send-keys <name> enter`. Never send the prompt again: it appends to the pending text.
- Read a dialog before sending any key; defaults differ, and Claude's folder trust dialog defaults to
  exit.
- herdr refuses agent arguments it can't encode for the shell, a multi-line text among them; pass a
  file's path instead.
- Never prompt, close or answer an agent you didn't start.
