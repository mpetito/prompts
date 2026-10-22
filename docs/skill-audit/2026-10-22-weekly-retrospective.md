# Retrospective: one week of sessions (2026-10-15 to 2026-10-22)

A review of every Claude session that was active in the window, run as a workflow: 13 Opus readers, one per
transcript bundle; an Opus synthesis; and an Opus verifier for each proposed ledger entry. The method is the
archived session-retro procedure. Project names, session ids and the readers' findings are in the private evidence
store (`retro/2026-10-22-weekly/`).

## In numbers

- 41 sessions had activity in the window (19 to 22 October). There were no Codex sessions; the last was 13 October.
  The sessions were three orchestrated investigation builds in one project (MAIN, 3 threads, about 8 lanes), one
  plain session rolling a configuration change out to about 25 client repositories, and five smaller plain sessions.
- 21 of the 49 condensed files were security-plugin commit reviews (`"entrypoint": "sdk-py"`), not lanes, and one
  plain session had been resumed into three files. The logical count is lower than the file count (see the
  session-selection entry below).
- Skill loads in the window: review 7 (subagents), tt 4, plan-review 3, pull-request 2, code-style 2, spec 1,
  orchestration-main 1. Every ad hoc agent launch set `opus`.
- Readers raised 22 gaps and 62 improvements. Synthesis kept 4 ledger candidates, and verification confirmed 3 and
  refuted 1. A fourth confirmed entry, the cp1252 fact, was added from this session.

## Ledger entries added

| Kind | Covering skill | Verdict |
| --- | --- | --- |
| canary before fan-out | new | confirmed, quote corrected |
| re-derived procedure (live capture through the Playwright MCP) | new (a brief or a project AGENTS.md) | confirmed |
| session selection | session-retro (archived) | confirmed, count corrected |
| re-derived fact (cp1252 under `python -I`) | new (a global CLAUDE.md line) | checked in the raw transcripts |
| owner-path check (preview called tested on a 200 response) | owner-acceptance (archived) | **refuted**: the 200 response came from a worker's report, and agent-orchestration §5 is its home |

## Readmission signal

No archived skill clears the bar this week. session-retro is the closest: weekly retrospectives are a repeated owner
request, and this run re-derived its procedure in four scratch scripts on top of its `condense.py`. Before it could
return, it needs an `sdk-py` filter, de-duplication of resumed sessions, a date window and UTF-8 file handling, and
then three evals built from this run. owner-acceptance has one refuted case and agent-briefs has none: this week's
brief gaps all belong to agent-orchestration's `references/briefs.md`.

## Improvements, ranked

P1 items cost real time or money this week and have a small, mechanical fix.

| P | Where | Change | Observed cost |
| --- | --- | --- | --- |
| P1 | settings, `land.py` | Turn commit and PR attribution off with the Claude Code setting (confirm the key in the settings docs); `land.py` stops on a `Co-Authored-By: Claude` trailer | lane subagents added the trailer despite the global rule; one PR had to be squashed |
| P1 | `mail.py wait`, orchestration-main §2–3 | Back off after consecutive timeouts and reset on mail; a thread with no work pending waits with no timeout; a timeout produces no owner-facing line | about 170 empty turns, including 59 after MAIN agreed to stop |
| P1 | `lane.py` | Enable the project's MCP servers in the lane worktree's local settings before the start prompt, then confirm the prompt arrived | the 20 October entry recurred twice after it was recorded, 25–30 min each |
| P1 | tt `scan_sessions.py` | Split attended from unattended time; flag rows resolved through a PR link; one session never feeds two rows | 2–4.5 h a week of overstated or doubled proposals, caught by hand |
| P1 | agent-orchestration §1, §4 | A findings report's recommended design goes through plan-review (least mechanism, Reuse) before MAIN, and its estimate lists line items | an estimate of 31–34 h fell to about 10 h only after the owner asked why it was so large |
| P1 | global CLAUDE.md | One line: Python here writes cp1252, and `-I` ignores `PYTHON*` variables, so use `-X utf8` | about 10 failed calls a week |
| P2 | `mail.py steer`, orchestration-main §2 | Relay the owner's words verbatim as a script argument; a separate note may carry only operational constraints | MAIN added a design to a steer; one rework round |
| P2 | global CLAUDE.md, agent-model-selection.md | Give the configuration repository's root directly (the link resolves to `instructions/`); say that a pinned named agent launches without an override | failed ledger writes; pr-watch and researcher ran over their sonnet pins |
| P2 | pull-request SKILL.md | Step 1 names the keys `get_pr_feedback.py` actually emits; the description fires on PRs opened in bulk by a script | 18 off-convention PR bodies |
| P2 | tt live mode | Wait until a batch of PRs ends before logging; split one repository window across parallel work items | an owner interruption and six repeated asks |
| P2 | `state.py`, state-file.md | `set` creates a missing lane row; the doc names the skeleton's real headers; every script accepts `--help` | 6–9 calls and a hand edit per thread |
| P2 | `finish_lane.py` | Unlink a junctioned dependency folder before `git worktree remove` (probe the Windows behaviour first) | a data-loss hazard to the main checkout |
| P2 | agent-orchestration §3, §5 | A spending decision defaults to its safe minimum; `land --check` runs only what CI runs; "try what the owner will try" applies to local previews too | 17.5 h idle on a decision with no default; a corrupted landing; two UI issues the owner found |
| P2 | global CLAUDE.md, Delegation | Before offering a deletion or saying that a change "won't" break something, check it or label it as inference; a change to many targets goes to one first | three owner corrections and a gate failure in plain sessions |
| P3 | briefs.md, verifier, analyst, pr-watch, herdr.md | Use `date -u` for times in deliverables; treat memory writes as outside the worktree; keep verifier and analyst briefs small; let pr-watch take several PRs; note that herdr only sees new environment variables after a restart | small losses each |

## Fixes applied (2026-10-22)

The P1 items, each with a test that fails without it where there is code:

- **Attribution:** `"attribution": { "commit": "", "pr": "", "sessionUrl": false }` in this machine's
  user settings, documented in [setup.md](../setup.md). The running session's attribution reminder
  changed to "do not add attribution lines" as soon as the file was saved. The `land.py` trailer gate
  was left out: code-style's trust rule says to warn your own workers, never gate them, and the
  setting removes the cause.
- **Wait cadence:** without `--timeout`, a `mail.py wait` lasts as long as its box has been quiet
  since its newest message, read or not, at least an hour and at most 8. The backoff is derived from
  the maildir, so no counter is kept. protocol.md, orchestration-main and control-attach now say a
  `TIMEOUT` gets no reply.
- **Lane start:** `lane.py` starts a Claude lane with `--settings` on the main checkout's
  `.claude/settings.local.json`. On Windows, Claude Code keeps that file per worktree
  ([settings](https://code.claude.com/docs/en/settings)), so a new lane worktree has no record of
  the owner's MCP approvals. No prompt-arrival check was added: the cause is gone, and section 2
  of agent-orchestration already reads the screen of a lane that has made no progress.
- **tt scanner:** a session's PR links decide its repository only when they all name one. One
  rollout session had landed on three rows (its last link's repository, another repository and
  `unmapped:`); it is now one `unmapped:` row. The proposed split of attended and unattended time was
  not built: this week's overnight ticks were the hourly wait timeouts, which the backoff removes at
  the source. Look at it again if next week's scans still show them.
- **Findings get plan-review:** agent-orchestration section 4 sends any report that recommends a fix
  or gives an estimate through plan-review before MAIN. The report leads with the smallest design
  that meets the acceptance criteria, and its estimate lists line items.
- **cp1252:** instructions/CLAUDE.md has a "Python on Windows" section.

## Retention

These helped and stay: agent-orchestration, orchestration-main, tt (back-fill), pull-request (its scripts),
plan-review, review, and the verifier, researcher and pr-watch agents. story, project-setup, playwright-e2e, firecrawl,
control-attach and review-lenses had no loads this week. Their 30-day checks fall between 10 and 15 November.

## Meta-lessons

- **Every rule that broke this week was prose**, and several broke right after the model acknowledged them. The fixes
  that hold are a script default, a setting or a landing check.
- **The costliest mistakes happened in plain sessions.** There, only the global CLAUDE.md applies: premises were
  stated as fact, and changes were fanned out to client repositories without a canary. Rules for unaided work have to
  live in CLAUDE.md, a setting or a hook.
- **Count logical sessions, not files.** Before readers run, merge resumed copies, drop plugin sessions, and classify
  a session as a lane by its brief, not by its folder name.
