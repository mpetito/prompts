# Plan: orchestration on herdr and a file mailbox

Spec: [spec.md](spec.md). Paths are from the repository root; `skills/agent-orchestration` and
`agents/orchestrator.md` are linked into `~/.claude`, so every edit is live at once: run no build
while steps 3-9 are open. Offline tests run with `bash skills/agent-orchestration/tests/run.sh`;
every new assertion is shown to fail against a planted mutant before its step is ticked.

- [x] 1. `docs/orchestration/2026-10-12-herdr-mailbox-spike.md`: the spike's results, made
  project-agnostic (no session ids, no private paths). Check: `grep -niEf
  ~/dev/prompts-evidence/names.txt` and `grep -nEf ~/dev/prompts-evidence/names-cs.txt` over the
  new files print nothing (verify.sh only scans committed history; it runs in step 11).
- [x] 2. `skills/agent-orchestration/scripts/mail.sh`, `skills/agent-orchestration/tests/run.sh`:
  the mailbox, under `$ORCHESTRATION_HOME/mail` (default `~/.orchestration/mail`), addressed
  `<build>/<box>` (`main` or `thread`).
  - `send <build>/<box> --from <sender> [--quiet] [<text> | --file <path>]`, stdin when neither;
    an empty message is refused; a quiet one wakes no wait and doesn't count as unread.
  - `read <build>/<box>`: print and file every new message, oldest first.
  - `wait <build>/<box> [--watch <agent>[=<its box>],...] [--timeout S]` prints one line: `MAIL
    <n>`, `BLOCKED <agent>` (once per transition), `GONE <agent>`, `UNREAD <agent> <n>` (idle or
    done while its box holds mail older than 5 minutes, once per stretch) or `TIMEOUT`. One wait
    per box: MAIN runs one per build.
  - A mocked `herdr` on PATH; the suite unsets every `HERDR_*` variable so it can't reach a real
    session.
  Check: run.sh passes send, read and wait cases with two watched agents, and fails against each
  of ten planted mutants (once per prompt, unread age, unread once, herdr down, gone unseen,
  atomic rename, read order, quiet wakes, quiet counted unread, empty allowed).
- [x] 3. `skills/orchestration-main/scripts/thread.sh`, `skills/agent-orchestration/scripts/state.sh`,
  `skills/agent-orchestration/tests/run.sh`: threads on herdr.
  - Launch: the thread's name is the build, `[a-z][a-z0-9_-]{0,31}`, refused while it is registered
    or a live agent holds it; `herdr workspace create --cwd <worktree> --label <build> --no-focus`
    (plus `--env ORCHESTRATION_HOME` when set); `herdr agent start <build> --kind claude --pane
    <root_pane> -- --agent orchestrator "<brief text>"`, the brief headed by its build, its mailboxes
    and its state file; `agent_not_ready` prints `BLOCKED <build> waiting on a startup prompt:
    answer it in workspace <build>`; any other start failure closes the workspace and drops the row.
    The record holds the build, no MAIN name or socket.
  - Stop resolves the pane from the agent name. Rotate keeps the name, opens the new thread in a new
    tab of the build's workspace (a new workspace when that is gone), then closes the old pane.
  - Close closes the thread's pane and the build's workspace, and archives `<build>/` from the mail
    root.
  - Deleted: `claude_env`, `start_session`, `live_sessions`, `session_of`, `inbox`, `main_socket`,
    `set_main`, `adopt`, `--main`, `--build`, and check's `INBOX`, `MOVED` and `BLOCKED` lines (check
    keeps `IDENTITY`); `state.sh main`; the mocked `claude`. lib.sh's `main_name` stays until step 6,
    because guard-message.sh still uses it.
  - The mock `herdr` keeps its agents in a file and rejects argv that 0.9.3 rejects (no `--pane`, a
    name off the pattern, a workspace without `--cwd` and `--no-focus`).
  Check: run.sh passes, and fails with a named check against each of eleven planted mutants (focus,
  held name, name pattern, startup prompt, failed-start cleanup, rotate's tab, rotate closing the
  old pane, close's mail, close's workspace, the home passed on, a missing agent read as an error).
- [x] 4. `skills/agent-orchestration/scripts/lane.sh`, `skills/agent-orchestration/scripts/codex-exec.sh`,
  `skills/agent-orchestration/tests/run.sh`: one lane launcher for both kinds replaces the headless
  Codex one. `lane.sh <build> <lane> <worktree> <brief> --kind claude|codex --model <id>
  [--network]`: a new tab labelled with the lane in the thread's workspace at the lane worktree,
  then `herdr agent start <build>-<lane>` with, for Codex, `--approve-for-me --add-dir <build mail
  folder>` (plus the sandbox network setting with `--network`), and for Claude, `--agent lane`;
  then the pointer prompt `Read <brief> and follow it.` A lane held at a startup prompt prints
  `BLOCKED` and gets no prompt; a lane that fails to start has its tab closed. codex-exec.sh, its
  tests and the mocked `codex` are deleted; its `--strip` of named secret variables has no
  equivalent, because a herdr agent inherits its pane's environment. Ask the owner for the
  settings rule `Bash(~/.claude/skills/agent-orchestration/scripts/lane.sh:*)` with step 6's diff.
  Check: run.sh passes, and fails with a named check against each of nine planted mutants
  (approve-for-me, add-dir, focus, the pointer prompt, network, the lane agent, the startup prompt,
  closing a failed lane's tab, the required model).
- [ ] 5. Live smoke test from a herdr pane, before any document is rewritten: `thread.sh launch` a
  probe build of this repository with the real `orchestrator` agent and hooks; mail both ways; a
  permission prompt reported to MAIN; a decision default applied; two builds, one wait each;
  a thread killed (`GONE`) and one left idle without a wait (`UNREAD`, then rung); a fresh MAIN
  session picking up the running build's mail; `ROTATE` and `thread.sh rotate`; a Codex lane that
  commits in its worktree, and whether the owner's one-time approval covered that worktree; a
  Claude lane that commits in its worktree, with a guard hook refusing a planted mistake;
  `thread.sh close`. Append the results to the spike document; findings that change steps 6-10
  update this plan first. Check: every probe's result is recorded, and there is no agent, workspace,
  `../prompts-orch-<probe>` worktree or `mail/<probe>` folder left for the probe.
- [x] 6. `agents/orchestrator.md`, `agents/lane.md`, `skills/agent-orchestration/hooks/guard-message.sh`,
  `skills/agent-orchestration/scripts/check-message.sh`, `skills/agent-orchestration/scripts/lib.sh`,
  `skills/agent-orchestration/tests/run.sh` (owner approval): the orchestrator's description says it
  is a herdr agent and its `SendMessage` hook goes; guard-message.sh, check-message.sh, lib.sh's
  `main_name` and their tests are deleted; `agents/lane.md` is the Claude lane agent, running
  guard-bash and guard-writes with `--lane` (no model pin; `lane.sh` passes it). The settings rule
  `Bash(~/.claude/skills/agent-orchestration/scripts/lane.sh:*)` is the owner's to add: Claude
  Code's classifier refuses an agent editing its own settings. Check: run.sh passes; `grep -rn
  'check-message\|guard-message\|SendMessage\|main_name' skills/*/scripts skills/*/hooks
  skills/*/tests agents` prints nothing (the docs and evals follow in steps 8 and 10); the commit
  body quotes the approval.
- [ ] 7. `skills/agent-orchestration/references/herdr.md`, `skills/agent-orchestration/scripts/finish-lane.sh`,
  `skills/agent-orchestration/hooks/guard-bash.sh`, `skills/agent-orchestration/tests/run.sh`: a
  short herdr reference for threads: the lanes' wake contract (the thread's wait watches its
  lanes; a blocked lane goes to MAIN as `STATUS: blocked - lane <x> waits in workspace <build>`;
  each lane has a `wake-at.sh` backstop), `codex-lane.sh`, replying with `mail.sh send --from`,
  escalating a first-time project to the owner, a lane agent living for one lane with its tab
  closed before `finish-lane.sh`, and the archived traps that still apply (`--wait` settles on
  blocked, the two-step wait, never re-prompt after a stall, read a dialog before sending keys).
  guard-bash and guard-writes treat a lane session (started with `--agent lane`; confirm from the
  hook docs which input field names the agent) as they treat a subagent worker today.
  finish-lane.sh resolves the worktree with `realpath` before comparing it with herdr's cwd.
  guard-bash advises on a foreground `mail.sh wait`. Check: run.sh fails without the realpath fix
  without the new guard-bash advice, and without the lane-session rule in either hook; every command in herdr.md matches `herdr <group>` help on
  0.9.3.
- [ ] 8. `skills/agent-orchestration/references/protocol.md`, `skills/agent-orchestration/references/state-file.md`,
  `skills/agent-orchestration/references/briefs.md`, `skills/agent-orchestration/SKILL.md`,
  `skills/README.md`: lanes are herdr agents of either kind; the build's mailboxes replace Addresses (`mail.sh`, read then re-arm), the
  wake and UNREAD rules, blocked handling, the consent rule restated for mail, no `-r<n>`, no
  SendMessage limits; threads send `working` with `--quiet`; only a fixed line or a brief pointer
  is ever typed into a pane, only into an idle agent, never MAIN; the RESUME checklist gains mail
  read but not yet acted on; the wake table gains the mail wait and herdr lanes and loses
  `codex-exec.sh`; briefs are written for a lane of either kind and tell it to report by
  `mail.sh send --from`; subagents stay for jobs that aren't lanes. Check: `grep -rn
  'SendMessage\|socket\|outbox\|background session\|-r<n>\|codex-exec'
  skills/agent-orchestration skills/README.md` prints nothing; a run.sh case asserts that every
  wait output named in protocol.md is one mail.sh documents and prints, and fails when one is
  renamed in either; step 10's new case passes.
- [ ] 9. `skills/orchestration-main/SKILL.md`: launch without `ListAgents` or `--main`; one
  background `mail.sh wait <build>/main --watch <build>=<build>/thread` per running build, and each
  wake starts from `mail.sh read`; `BLOCKED` names the workspace for the owner; a decision or a blocked pane also raises
  `herdr notification show … --sound request`;
  `UNREAD` rings the thread; rotation and a quiet thread use herdr state. Check: `grep -n
  'ListAgents\|adopt\|MOVED\|claude attach\|notify_when_idle\|background session\|--main'
  skills/orchestration-main/SKILL.md` prints nothing.
- [ ] 10. `skills/orchestration-main/evals/`, `skills/agent-orchestration/evals/`: replace
  `wake-after-fork` with a wake on `BLOCKED`; move every `SendMessage to …` assertion and the
  `cross-session-message`, `MAIN-SOCKET` and `codex-exec.sh` fixture text to mail; add a thread
  case "woken by `MAIL`: read, re-arm the wait in the background, reply with `mail.sh send`".
  Run both suites once on Opus with `scripts/run-skill-eval.ps1`. Check: each suite passes with
  the skill, and each new case fails without it.
- [ ] 11. Commit and push hygiene. Check: after each `git commit`, `verify.sh . names.txt
  names-cs.txt` from `~/dev/prompts-evidence` reports `total=0`, and `git log -1
  --format='%an <%ae>%n%b'` shows the owner's global identity and no attribution trailer.
