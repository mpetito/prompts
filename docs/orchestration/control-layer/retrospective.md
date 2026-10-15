# Retrospective: the control layer build

Built 2026-10-15 from [spec.md](spec.md) and [plan.md](plan.md): steps 1-6 and 8 landed first;
steps 7 and 9-11 followed the owner's answers (see "The second pass" below). One orchestration thread, five Claude lanes on Opus (probes, core, hooks,
controller, live), and five review subagents on Opus with the review or plan-review skill. The owner's
instruction for the whole build was "keep it simple", with a reviewer asking of everything "Is this
really necessary?".

## What the lens cut

Each cut is recorded beside its step in plan.md.

- **No new mail.** The session's wait and read are mail.py's own `wait` and `read`. `ctl.py` has no
  subcommand for them, and the controller's `read` and `wait` print only mail.py's lines.
- **No settings.** The default authority is a constant. `attach` takes no `--authority`, so `authority`
  is the one way to change a level, and there is no `--home`.
- **One ring line per kind.** `/control-attach <name>` both attaches a session and answers `UNREAD`,
  in place of a separate "unread mail" line. A Codex session is rung the way lanes are, with
  `Read <file> and follow it.`.
- **Files that were never written**: a test file for the protocol (the doc-and-code lint lives in
  test_ctl.py), a new test support module (the tests reuse agent-orchestration's `FakeHerdr`), a
  fixtures file for hook inputs, and an evals README or checker.
- **One hook script.** It picks its handler by `hook_event_name` and calls `ctl` in-process. The
  owner-activity filter has one home, `typed`.
- **No link** from the orchestration protocol to the control protocol, and no `allowed-tools` (left to
  the owner as D2).
- **A thread played by hand.** Step 8's MAIN got its thread's decisions by hand-sent mail, not from a
  real thread with lanes. Escalation at `relay` stayed a unit test, not a live case.

The lens added one thing back on evidence: the session record's session id. The plan review had cut
it, then the probes showed that a `/clear` keeps the pane and the name and changes only the id.

## What the reviews caught

- **Plan review.** A resumed session shows as `GONE`, not `UNREAD`, because herdr clears a name when
  its agent exits. The skill can't be live-linked without the owner. The hooks lane and the controller
  lane needed a fixed contract before they could run in parallel.
- **Probes.** A `/clear` and a resume drop a skill's frontmatter hooks; a compaction keeps them.
  Prompts that aren't the owner typing are told apart only by their first tag.
- **Core (2 rounds).** `ring` could type into an orchestration thread or lane and rename it, which
  would break MAIN's watch. One test missed a report sent under the wrong name. herdr failures failed
  open.
- **Controller (3 rounds).** A reused name let a ring into a build's thread. `start` could lift an
  owner's `observe` and mail what the level forbids. A ring could raise a session's level by
  attaching it under another name. Whose an agent is came back twice, so the third round asked for
  the whole class: one function on every ring path, with a table-driven test.
- **Hooks (2 rounds).** A stop the hook blocked lost the turn's `need-decision` or `done`, which the
  plan review's own "no report on a blocked stop" rule had caused. Any hook fault would have shown an
  error on every prompt. The `~/.claude/skills` fallback was wrong for a project skill.
- **Live acceptance.** A MAIN passed decisions up as "D1 (probe build)" because SKILL.md never named
  the `<build>/D<n>` ref. Only protocol.md did, and a session doesn't read it unprompted.

## Cost

About two hours of wall time (01:51Z to 03:45Z). Five lanes and eight review passes (plan, core ×2,
controller ×3, hooks ×2), plus one eval run of 3 cases × 2 arms × 3 runs on Opus. No Codex lanes.
The live acceptance ran about ten probe sessions, all on Opus. One check ran twice, after the
`<build>/D<n>` fix.

## Weak spots to know about

- **Weak evals** (fixed in step 10). Only one of the three cases failed without the skill on
  behaviour; now each fails 3 of 3 without it on the action taken and passes 3 of 3 with it.
- **An undocumented variable.** The hook finds its folder through `CLAUDE_PLUGIN_ROOT`, which the docs
  don't promise for a non-plugin skill. It was shown on Claude Code 2.1.300, both in a project skill
  and live.
- **Watching by name.** mail.py's `--watch` goes by herdr name, so after a `GONE`, an agent that later
  takes the name can draw an `UNREAD`. The ring that would follow is refused.

## Follow-ups outside this build

- Hoist the herdr JSON helper, now in lane.py, thread.py and ctl.py, into lib.py.
- `state.py` can't add a lane row. The thread added rows by hand.
- `land_local.py --subject` is prefixed with "Merge <lane>:", so a subject that starts with "Merge"
  repeats it.
- Spec "Sessions" still says a compaction may lose the wait and the instructions. "Shown 2026-10-15"
  shows it keeps both.
- Closing a herdr tab or workspace leaves its sessions' background waits running. The live lane
  stopped them by hand. Anything that closes attached sessions, a future `ctl.py` clean-up included,
  has to stop their waits too.

## What to reuse

- Fix the interface first, and have the next lanes' reviewer review it. The core lane's protocol.md
  let hooks and controller run in parallel without touching each other's files.
- Run the probes before writing hooks. Their results reversed two plan choices before any code
  depended on them.
- Brief reviewers with the owner's question and with mutants to plant. Every blocking finding came
  with a probe or a surviving mutant as evidence.

## The second pass

After the owner accepted the readmission gap (D3), set the supervisor build aside (D4), reversed D1
(the owner's newest words win, typed or relayed by `OWNER:`) and asked for one more "Is this really
necessary?" pass on session identity, three lanes ran: `owner` (Opus: D1 in SKILL.md, the evals, the
readmission entry), `simplify` (Opus: ctl.py and protocol.md) and `retire` (Sonnet: one record and a
health check). Three review rounds and one verifier, all Opus subagents.

- **The cut that went too far.** Dropping the Claude session id for a pane-only tie looked like a
  simpler rule. Review round 1 showed a session resumed in another pane could then be rung past
  `observe` and under a new name. The id came back, used only where a ring matches an unnamed agent.
- **The protocol was wrong about `/clear` from the start.** The live check, not review, found it:
  herdr drops an agent's name on `/clear`, so a cleared session is `gone` and its wait reports `GONE`,
  not `UNREAD`. "Shown" had recorded the name surviving only for an agent herdr had never named.
- **Review kept finding the same class one layer deeper**: a resumed session's ring (round 1), a
  re-attach keeping a stale id and a ring under another record's pane (round 2), one session holding
  two attached records (round 3). Two of the three were there before the pass. The class now has one
  rule in protocol.md: one session holds one attached record, and a ring attaches an agent only under
  its own record. Round 3 went to the owner as D5, per the three-round limit.
- **Known gap, by design since step 3.** An agent with no attached record falls back to every record
  in its pane, so a session in a recorded pane can be rung under that pane's record at its level. The
  verifier reached it through a four-pane sequence of exits and continues. Closing it means deciding
  what a pane's record is worth once its session has gone; that is the owner's call, not a fix.
- **Two changes for the OpenClaw adapter**, by its request: `--` ends ctl.py's options (a `--owner`
  answer text no longer marks a controller decision as the owner's), and `wait --timeout 0` is
  documented as one look.

What to reuse: a live check of every recovery path the protocol claims, before review; and when a
reviewer's third round finds the same class, state the invariant in one sentence and test that, not
the next example.
