---
name: tt
description: "Log the owner's time in Harvest from the session record: right after a pull request is created, updated, reviewed or merged in the main session, when an orchestrated build reports done, on /tt, or to back-fill past days by scanning Claude and Codex sessions for time missing from Harvest. Notes carry the Azure DevOps work item id. Use when asked to log, track, record, bill or charge time or hours, fill in or fix a timesheet, or find unlogged time. Not for sizing a backlog item (story), committing or opening a PR (commit-commands, pull-request), a standup summary (engineering:standup), or reading hours already logged (the Harvest tools answer that directly)."
---

# Time tracking (Harvest)

Role: human. Loaded by the owner's main session on `/tt`, after a PR event, or when a build reports done; never
inside an orchestrated lane, a subagent or a Codex worker, where the same hours would be logged twice.

## Procedure

1. **Mapping.** Read `~/.config/tt/harvest-mapping.md`, the owner's private file: their Harvest user id, and
   rows from a repo key (the scanner's) and an optional Azure DevOps area-path prefix to a project and a
   default task. A work item's area path picks the row with the longest matching prefix; the row without one
   is the repository's default. A repository with no row, a `CONFLICT` or `KEY?` row, or several candidate
   projects and no work item to choose is an open row in the table naming the candidates (`list_projects`
   when there are none); never pick for the owner, and update the file once they do. Without the file, find
   the user id in Harvest's user list by the session's email, and every repository is an open row. Every entry
   list below is the owner's own (`user_ids`).
2. **Scan.** Run `python3 "<skill dir>/scripts/scan_sessions.py" --from <day> [--to <day>]`, with `<skill dir>`
   a full path such as `$HOME/.claude/skills/tt`; its docstring defines the line. A line's hours are the
   repository's active time that day, the union over parallel sessions, lanes and subagents, rounded up to
   0.25 h. Never add up session, lane or worker durations, and never use a wall clock instead.
3. **Hours, per day and project.** Attribute each line first. A repository with one `OK` row counts toward
   that project only. A repository with several `OK` rows (an area-path split) is a unit of its own, shared by
   its candidate projects. A `CONFLICT`, `KEY?` or unmapped repository is its own open row and never joins
   anything, nor is a project ever joined to another through a repository. A project's scanned hours are its
   one line's hours, else the union of its lines' intervals rounded up to 0.25 h once, never the sum of the
   lines. Subtract the owner's entries that day on that project and the task you would log to (Harvest's
   `rounded_hours` when present); show their other tasks' entries (meetings, internal time) beside it, never
   subtracted. A split repository subtracts the owner's entries on all of its candidates, and its rest goes
   once to the project the work item's area path picks, else to an open row for the owner to assign. Propose
   nothing when the rest is zero or less. A proposal never exceeds the union of its own scanned lines;
   different projects add up, and no repository's hours are proposed twice.
   A day's total, the owner's entries on every project and task plus the proposals, stays at or under 16 h:
   when the proposals would pass it, say so on that day with the hours left, and let the owner choose which
   rows to trim; never trim them yourself, and log nothing for that day until they do. Hours the owner states
   replace the scan.
4. **Work item.** Use the id given, else search Azure DevOps by branch name, PR title and commit subjects, and
   cite only an id found there. For a code change with no item found, ask the owner for the id and log nothing
   until they answer; meetings and internal work may go without one.
5. **Note.** One plain-text line of at most 80 characters, never a changelog of files, tests or steps:
   - with an item, `<work item type> #<id>: <title>`, such as `User Story #48213: Order history filter, sort and
     tabs`. A billing sync reads the work item id from `#<id>`: never a PR number, never `AB#<id>`.
   - without one, `<Area> - <activity>` in title case, such as `Partner Portal - Payments Connector`.
6. **Write.**
   - Live (a PR event, a build done, `/tt`): today, for the current repository's project. Log with `log_time`,
     then report the entry id, project, task, hours and note; a build's entry goes in the done message the
     owner reads.
   - Back-fill (past days; by default the previous 5 working days): scan the range, list the owner's entries
     for it, and show one row per day and project with scanned, logged and proposed hours and the note, plus the
     open rows from step 1. Log nothing until the owner confirms the table, then log the confirmed rows.
     Claude's transcript retention (`cleanupPeriodDays`, 30 days by default) bounds the range: a day whose
     transcripts are gone scans as empty, which is not the same as no work, so say so.
7. **Never delete an entry or set its hours to 0**, even when the owner asks and although Harvest's tool
   descriptions offer `delete_time_entry` for it: tell the owner to remove or lower it in Harvest's timesheet.

## Invocation

`/tt [work item id] [hours] [search text]`: a 4 to 6 digit number is the work item, a decimal the hours, other
text a work item search; `/tt` alone infers everything. `/tt backfill [from] [to]` runs the back-fill.

Scanner rows reading `unmapped:<path>` are sessions in a folder git can no longer resolve, such as a removed
worktree, or in a folder with no repository that opened PRs in several, such as a rollout across repositories;
the owner assigns or drops them in the table.
