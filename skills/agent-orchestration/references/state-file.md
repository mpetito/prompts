# Orchestrator state file

The state file is the orchestrator's resume point. After a compaction the conversation summary
loses IDs, SHAs and queue order; this file keeps them. Re-read it at the top of every wake.

## Where and When

- **Location:** the same order of preference as the loop log in
  [autonomous-loops](../../autonomous-loops/SKILL.md): the host's session memory directory (Claude
  Code names one), then a memory tool, then the scratchpad or a gitignored file. Never commit it.
- **Update** on each state change: a launch, a verdict, a push, a merge, a decision, an arrival or
  departure of the human. Batch the edits of one turn into one write. Use the state helper from
  [orchestration-ops](../../orchestration-ops/SKILL.md): `state.sh log` appends a stamped line and
  `state.sh set` edits one cell, so no time is ever typed by hand.
- **Back it up before overwriting it** with `state.sh backup`, which copies it to
  `state.<timestamp>.md` with the timestamp from `date -u +%Y%m%dT%H%MZ`.
- **The decision queue is its own file,** `decisions.md` beside this one, kept by `decisions.sh`.
  This file points at it; the open-decisions table below is the fallback when the helper is not
  installed.
- **Durable decisions** also go in the repository's decision log. This file points at them.
- **Name brief and result files predictably** (`<lane>-brief.md`, `<lane>-result.md`), so a
  resumed orchestrator can rebuild a lane from disk.

## Template

Copy it, then replace each `<placeholder>`. Delete rows and sections you don't need. The first
two sections repeat the skill's per-turn rules and carry the resume procedure on purpose: after a
compaction, this file may be the only orchestration guidance left in context.

````markdown
# Orchestrator state: <build name>

Updated <date -u> · Plan <path> · Decision log <path> · Handoff <issue URL or path>

## Every wake

1. Run `date -u`, `meter.sh` and `decisions.sh due`. Apply and log each due default. Sweep every
   lane below, not only the one that woke you.
2. Before ending the turn, every in-flight lane has a wake source (the Wait column). Arm any that
   is missing.
3. Never block on a question tool while other work can move. Ask in a message with a default.
4. Above 70% on either meter: smaller model for authors, no second reviewers, no fan-out within
   3 h of a limit warning. On a limit notice: rewrite this file, arm `wake-at.sh` for the reset.

## After a compaction

1. Read this file in full, then the handoff. Act on no ID, SHA or number from memory.
2. Run `date -u`.
3. If the host loads tool schemas on demand (Claude Code's deferred tools), re-load the ones you
   will use before the first delegated action.
4. Re-verify each lane against its source, and fix the table where it is stale:
   - PRs: `gh pr view <PR> --json headRefOid,state,reviewDecision,statusCheckRollup`;
   - branches: `git rev-parse <branch>`;
   - agents and background waits: the host's task list;
   - results: each result file.
5. Sweep every lane, and arm a wake source for any lane that lacks one.
6. Re-read the approvals and the away rules, then continue the loop.

## Lanes

| Lane | Agent or peer (ID, model) | Worktree | Branch | PR | Head SHA | Review | Wait (task ID) | Result file | Next action | Waiting on |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <lane> | <agent ID, model> | <path> | <branch> | <#N> | <sha> | <round N: verdict for sha> | <task ID> | <path> | <action> | <who or what> |

## Peer queues

### <peer name>

Safe point: <after the current run, or after the next push>

1. <review findings for #N first> · brief <path>
2. <next task> · brief <path>

## Budget

| Meter | Last read (UTC) | Used | Resets (UTC) | Mode |
| --- | --- | --- | --- | --- |
| Codex weekly | <from meter.sh> | <n>% | <time> | normal / economy / stopped |
| Claude weekly | <from the harness usage view> | <n>% | <time> | normal / economy / stopped |

## Open decisions

Kept in `<path to decisions.md>` by `decisions.sh`; one line per item with the default and its
deadline. Fallback table when the helper is absent:

| # | Question | Recommendation | Default, and when it applies | Blocks |
| --- | --- | --- | --- | --- |
| 1 | <question> | <option and reason> | <applies at checkpoint X unless the human objects> | <lanes> |

## Human queue

- **Needs human:** <item, with the exact reply that unblocks it>
- **Decided by orchestrator:** <decision, with its log entry>
- **Escalated and unmerged:** <PR, conflict, options, recommendation>
- **Merged:** <PR, merge SHA, time>

## Approvals

| Class | Rule | Granted (the human's words, time) |
| --- | --- | --- |
| Carry-over | A head that only merges the base onto the approved head inherits approval after the check | <quote, time> |
| <class> | <human before / notice after / default> | <quote, time> |

## Away rules

- **Decide and log:** <implementation details>
- **Park with a safe default:** <content, legal, money>
- **Never:** <destructive actions, approval bypasses, gated deploys>
- **Report in:** <handoff issue or file>

## Standing rulings

- <flake signature>: owner <lane>, issue <#N>, rerun policy <policy>
- Standing-rules file that agents re-read: <path>

## Helper scripts

`OPS=<orchestration-ops skill folder>/scripts`; each prints one line and is run in the background.

| Script | Run | Prints |
| --- | --- | --- |
| Gate wait | `$OPS/watch-gates.sh <PR> <SHA> --check <name> --bot <login>` | `GATES …` or `MOVED …` |
| Land | `$OPS/land.sh <PR> <worktree> --check <name> --subject … --body-file …` | `LANDED …` or `STOPPED <reason>` |
| Lane launch | `$OPS/codex-exec.sh <worktree> <brief> <result> --model … --strip <VAR>` | `CODEX done|timeout|failed …` |
| Lane teardown | `$OPS/finish-lane.sh <worktree> <archive dir>` | archived, removed |
| Timed wake | `$OPS/wake-at.sh <UTC time> <label>` | `WAKE <label> at …` |
| Inbox | `$OPS/watch-inbox.sh <file> "<own prefix>"` | `INBOX …` with the new lines |
| <project script, e.g. a dev deploy> | `<command> <sha>` | `<one line>` |

## Log

- <date -u> <event>
````

## Before a Planned Compaction

Do this at a calm moment, not at the context limit.

1. Start any long background jobs first, so they wake you afterwards.
2. Back up the file, then rewrite it in full as a clean resume point: drop finished lanes, keep
   only open decisions, and collapse the log to the last few events.
3. Move durable rulings into the repository's decision log.
