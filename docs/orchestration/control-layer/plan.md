# Plan: a control layer over orchestration

Spec: [spec.md](spec.md). Written on the spec's defaults (open questions 1-6); steps 7 and 9 wait
for the owner where they depend on an answer. Paths are from the repository root. Skills are linked
into `~/.claude` one by one, and linking `control-attach` is the owner's change, so until then
every live step loads it as a project skill from a scratch folder's `.claude/skills/`. Tests replace `lib.run`, as the orchestration suites
do, so nothing reaches the owner's herdr. Every new assertion is shown to fail against a planted
mutant before its step is ticked.

One new skill, `skills/control-attach/` (worker role: loaded once by each attached session), holds
the script, the protocol and the session's hooks. Its hooks are declared in its frontmatter: Claude
Code registers a skill's hooks when it is invoked and keeps them for the rest of the session
(https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents), so the owner's settings don't
change and unattached sessions run no control hook at all.

The controller's contract is `ctl.py`'s controller subcommands and the lines they print, documented
in the protocol with a version line. A controller in another account (the OpenClaw adapter,
specified in its own repository) reaches exactly those subcommands through its relay and never
reads the files below. A Claude session can be a controller by running the same subcommands; a
controller skill waits until one is wanted.

Control files live under `<home>/control/`, where `<home>` is `$ORCHESTRATION_HOME` or
`~/.orchestration`, as for mail: `mail/<name>/in` for each attached session and `mail/owner/in` for
the controller (mail.py's maildir and address form; `owner` is a reserved name), and
`sessions/<name>.json` for each attachment (session id, pane, authority, hold minutes, the owner's
last typed time). These files are private to `ctl.py`.

## Lanes

Each lane is one agent in its own worktree, branched from `orchestration/control`, and lands
locally after review.

| Order | Lane | Steps | Starts after |
| --- | --- | --- | --- |
| 1 | `probes` | 1 | the plan review |
| 1 | `core` | 2, then 3 | the plan review; step 3 after the protocol review |
| 2 | `hooks` | 4 | `probes` and `core` landed |
| 2 | `controller` | 5 | `core` landed |
| 3 | `live` | 6, then 8 | 6 after `hooks` landed; 8 after `controller` landed |

`hooks` and `controller` own different files: `controller` owns `ctl.py`'s controller handlers and
their tests, and protocol.md once step 2 lands; `hooks` owns `SKILL.md`, `hooks/` and `evals/`.
Step 2 fixes everything the hook calls, so `hooks` never edits `ctl.py`.

- [x] 1. `docs/orchestration/control-layer/spec.md` "Shown": the probes the hook design depends on,
  run before any hook is written. A skill's frontmatter hooks after `/compact`, after
  `claude --resume` and after `/clear`; a wake while the owner is mid-keystroke; the prompt-submit
  hook's input for another session's message and for a subagent's report. Check: each result
  recorded with versions; a probe that fails changes steps 3-4 here before they start.
  - Review: needed first are hooks after `/compact` and after a resume, the prompt-submit input
    for a subagent's report, whether invoking the skill twice runs its hooks twice (re-attach
    depends on it), and whether the prompt-submit hook fires for a typed `/control-attach`. `/clear`
    is cheap beside them. The wake mid-keystroke and another session's message come last, as time
    allows.
- [ ] 2. `skills/control-attach/references/protocol.md`,
  `skills/control-attach/tests/test_protocol.py`: the control protocol: layers, addresses, the four
  down messages and the `STATUS:` up message, authority levels and what each permits, the consent
  limits, the hold window, rings, and the controller subcommands with every line they print, under
  `Protocol version: 1`. One line in `skills/agent-orchestration/references/protocol.md` "Limits"
  links it. Check: test_protocol.py fails when the doc names a printed line `ctl.py` never prints,
  or omits one it does (the test_mail.py lint, for this pair).
  - Lens: the doc-and-code lint lives in `test_ctl.py`, beside the tests of the lines it
    checks, not in its own `test_protocol.py`. The link from the orchestration protocol is cut: a
    thread never meets control mail, and MAIN reads the control protocol from the skill it loaded.
  - Review: the lint moves to step 5, when every line it checks exists. The protocol also fixes
    what the hook calls: the exact wait command and how the Stop hook finds it among the background
    tasks; `report` and `typed` finding their session by `HERDR_PANE_ID` (a `/clear` changes the
    session id) and exiting 0 silently when the pane isn't attached; no report on a stop the hook
    blocks; `typed` ignoring the fixed ring lines, so a ring never holds the controller; the
    `sessions` row format the adapter parses; one controller reads `owner/in` at a time.
    `DECISION` says who made it (`--owner` or not); the session, which raised the decision and knows
    it is owner-before, refuses a controller-made answer to one, so no script tracks owner-before.
- [ ] 3. `skills/control-attach/scripts/ctl.py`, `skills/control-attach/tests/test_ctl.py`,
  `skills/control-attach/tests/support.py`: the session-side subcommands, importing
  `agent-orchestration/scripts/mail.py` and `lib.py` as thread.py imports lib.
  - `attach <name> [--authority observe|relay|delegate] [--hold <minutes>]`: resolve this session's
    id and pane from `HERDR_PANE_ID` and `herdr agent get`; refuse a name another live session
    holds; `herdr agent rename` the session to `<name>`, so mail.py's `--watch` sees it; write the
    record; print the wait command. Idempotent: re-attaching the same session keeps its mail and
    record, which is how a resumed or compacted session comes back.
  - `detach`, `authority <level>`, `typed`, and `report` (stdin to `owner/in` from `<name>`; quiet
    unless its first line is `STATUS: need-decision|blocked|done`).
  - Defaults: authority `delegate`, hold 10 minutes (spec questions 1, 3).
  Check: test_ctl.py passes, and fails against mutants: name collision allowed, rename skipped,
  mail lost on re-attach, default authority changed, quiet `need-decision`, report from the wrong
  name.
  - Lens: `attach` takes no `--authority`: every session starts at the default and `authority`
    is the one way to change it, so there are not two.
  - Review: the record keeps no session id (herdr's list gives it live and the pane identifies
    the session) and gains `attached` (detach clears it, authority unchanged) and `started`. `attach`
    refuses `owner` and names outside herdr's pattern. The tests reuse agent-orchestration's
    `FakeHerdr` by path instead of a new support.py.
  - Probe: a `/clear` and a resume drop the skill's hooks, and a compaction keeps them (spec "Shown
    2026-10-15"), so re-running `attach` is the only way back, after either. A `/clear` keeps
    herdr's pane and name and changes the session id, so the id is the only sign a cleared session
    lost its hooks: the record keeps the session id `attach` saw after all, and re-attaching
    replaces it. A live id that differs from the record's means the session needs attaching again,
    which the controller's `sessions` (step 5) can show and ring as it does for `GONE`.
- [ ] 4. `skills/control-attach/SKILL.md` (frontmatter hooks), `skills/control-attach/hooks/control_hook.py`,
  `skills/control-attach/tests/test_hook.py`: the attached session.
  - Body, under 120 lines: the wait loop (read, re-arm, act), each down message and how to treat it,
    the owner's typed words winning, the consent limits, the up message, `authority` only on the
    owner's own words.
  - Stop hook: `report` the `last_assistant_message`; when the wait command isn't in
    `background_tasks` and `stop_hook_active` is false, block the stop with a reason naming the
    command.
  - UserPromptSubmit hook: `typed`, unless the prompt is a task notification (starts
    `<task-notification>`) or a non-owner form step 1 found.
  - Probe: the non-owner forms are a prompt starting `<task-notification>`, `<agent-message ` or
    `<cross-session-message ` (spec "Shown 2026-10-15"); a typed `/control-attach` also reaches the
    hook on a re-attach, and `typed` ignores it with the ring lines. Invoking the skill again doesn't
    double the hooks. A wait started before a `/clear` keeps running and is in `background_tasks`
    after the re-attach, so attaching must not start a second one: the session starts the wait only
    when the Stop hook finds it missing. test_hook.py also feeds the recorded subagent report and
    cross-session message.
  Check: test_hook.py feeds the 2026-10-14 probe's recorded inputs and passes, and fails against
  mutants: blocks while the wait runs, blocks on `stop_hook_active`, counts a task notification as
  typing. Three behaviour evals in `skills/control-attach/evals/` pass with the skill and fail
  without (an `OWNER:` steer acted on; a `CONTROL:` settings change refused and taken to the owner;
  a `CONTROL:` that conflicts with the owner's typed words yielding to them).
- [ ] 5. `skills/control-attach/scripts/ctl.py`, `tests/test_ctl.py`: the controller subcommands,
  with the spec's rules in the script rather than in prose.
  - `sessions`: herdr's agent list joined with the records: name or pane, kind, state, authority,
    held until, unread both ways. Codex sessions listed as observed.
  - `send <name> OWNER|CONTROL|DECISION|QUESTION <text>`: refuse what the session's authority
    doesn't permit (`CONTROL` and a controller-made `DECISION` below `delegate`, anything at
    `observe`); `HELD <until>` for anything but `QUESTION` inside the hold window.
  - `read`, `wait [--timeout]`: the controller's box, watching attached sessions through mail.py's
    `--watch`, so `BLOCKED`, `GONE` and `UNREAD` arrive as they do for MAIN.
  - `ring <name|pane> <attach-name>`: types `/control-attach <attach-name>` only when herdr reports
    the agent idle and its visible input line is empty, printing `RUNG` or `REFUSED <reason>`. The
    same line answers `UNREAD`. Ringing an unattached session needs default `delegate` (spec
    question 2).
  - `start <name> <folder> <objective-file>`: only in a listed folder, at most 3 started sessions
    running (spec question 4); a new workspace without focus; the agent starts on the attach command
    and the objective file.
  Check: test_ctl.py passes, and fails against mutants: `CONTROL` at `relay`, sending inside the
  hold window, ringing a non-empty input line, ringing a working agent, starting outside the list,
  a fourth started session.
  - Lens: a Codex session is rung the way lanes are, with `Read <file> and follow it.`, the only
    fixed line it can act on; the owner's "observe-and-ring" needs nothing more. The folders `start`
    may use are one owner-written file, `<home>/control/folders`, a path per line; without it,
    `start` refuses.
  - Review: herdr clears a name when its agent exits, so a resumed session shows as `GONE`, not
    `UNREAD`; the controller rings the pane in its record, once that pane holds an idle agent again.
    `sessions` shows unread down only. A Codex ring is `ring <target> --brief <file>`, allowed while
    the default authority is `delegate`. `start` counts records flagged `started` whose agent is
    live, matches a folder that is a listed path or inside one, mails the objective to `<name>/in`
    and types only `/control-attach <name>`.
- [ ] 6. Live check the owner can watch: from this repository, attach one plain session, then from
  a second pane `ctl.py send` an `OWNER:` steer, see it acted on, see its report arrive with
  `ctl.py read`, type in the session and see the next send `HELD`. Check: each step's printed line
  recorded in spec.md "Shown"; the sessions and mail cleaned up.
  - Review: runs once `hooks` lands, with `mail.py send/read` against `<home>/control` if `ctl.py`'s
    controller side hasn't landed yet; the `HELD` check moves to step 8.
- [ ] 7. `docs/skill-audit/candidates.md`, `~/dev/prompts-evidence`: the readmission entry for
  `control-attach` (the gap: the owner is the only path into MAIN and plain sessions), project names
  kept to the evidence store. Waits on the owner accepting the gap, per the readmission bar. Check:
  the names greps over the changed files print nothing.
- [ ] 8. Live acceptance, recorded in spec.md: a controller driving `ctl.py` by hand, two attached
  sessions (a MAIN with a running probe build, and a plain one), one unattached Claude session and
  one Codex session. A steer relayed; a MAIN decision settled at `delegate` and escalated at
  `relay`; an owner-before decision escalated at both; the controller held while the owner types; a
  ring attaching the unattached session; `start` opening a new attached session; a `/compact` and a
  resume followed by `UNREAD` and a ring that brings the wait back; the owner's draft surviving
  every wake. Check: each line passes, and the probe's sessions, workspaces and mail are cleaned up.
  - Lens: the MAIN runs orchestration-main on a probe build whose thread is played by mail sent
    by hand to `<probe build>/main`: the decisions are what is under test, not a thread's work.
  - Review: escalation at `relay` stays a step 5 test, not a live case. A detached session plays
    the unattached one. The Codex session checks that `sessions` lists it observed and that a
    `--brief` ring reaches it, if Codex starts in the scratch folder without a prompt.
- [ ] 9. Retire the earlier supervisor build (spec question 6): its worktree set aside unmerged and
  recorded as evidence where the setup records keep it. Waits on the owner's answer. Check: the
  installed bridge still reports healthy, and the worktree is listed as set aside.
