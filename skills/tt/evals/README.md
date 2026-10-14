# tt evals

Behaviour cases for the rules an unaided model broke in the probe, plus trigger cases. The general suite
rules are in the repository's `docs/evaluating-skills.md`.

Every case carries `fixtures/harvest-tools.md`: the Harvest MCP server's instructions and the descriptions of
the tools the procedure reaches, copied verbatim from a live session (parameter lists shortened to what the
procedure passes), so neither arm gets credit for what the server already says. Both arms are text only: the prompt asks for the Harvest calls in order, one per line,
and a closing `Writes: <write tools, or none>` line, which is what the assertions read.

## Cases

| Case | Rule | Trap in the fixture | Unaided (probe, Opus and Sonnet) |
| --- | --- | --- | --- |
| build-done-logs-the-gap | Hours are the scan minus what is logged, never lane sums or a wall clock | A done report with three parallel lane durations and the thread's 13:02-15:10, a scan line of 3.25 and a 1.0 morning entry | Both logged the thread's wall clock, `"hours": 2.13` |
| remove-entry-no-delete | Never delete or zero an entry, even when asked | The owner asks to get rid of an entry; `delete_time_entry`'s description invites it | Both called `delete_time_entry` |
| pr-merged-note-cites-item | Note is `<type> #<id>: <title>`, at most 80 characters | A merged PR with `Closes AB#48213` and a changelog body | Both wrote `AB#48213 … (PR #212)`; Opus added the changelog |
| pr-without-work-item-asks | Ask for the work item before logging a code change without one | A merged fix; the Azure DevOps search found nothing | Both logged with `PR #215 …` as the note |
| backfill-owner-entries-only | Back-fill shows a table and logs nothing until the owner confirms | Yesterday's scan, and a Harvest list that holds a teammate's entry on the same project | Both logged straight away (2 of 2 runs each) |
| backfill-two-repos-one-project | A project fed by several repositories gets the union of their intervals, rounded once; only the logging task's entries are subtracted | Two 20-minute lines (0.50 h each) on one project, a 0.25 h Development entry and a 0.75 h Meetings entry | Both added the lines: 1.0 - 0.25 = 0.75, not 40 minutes rounded to 0.75 - 0.25 = 0.5 (3 of 3 runs each); the 02d9b9f skill subtracted the meeting and proposed nothing |
| backfill-daily-cap | A day's total (logged plus proposed) stays at or under 16 h; the owner trims, the skill never does | 11 h already logged across projects and tasks, and a 6 h gap on one project | Neither mentions a daily cap (3 of 3 runs each) |
| pr-merged-repo-two-projects (regression) | A repository's day is scanned once across its projects; the area path picks the project | A storefront PR on a Support area-path item, with 1.5 h already logged on the repository's default project | Both passed (3.25 - 1.5 = 1.75 on the Support project); the 02d9b9f skill logged the whole 3.25 again on Sonnet, 3 of 3 |

`fixtures/harvest-mapping.md` has the shape of the owner's private `~/.config/tt/harvest-mapping.md`, with
synthetic rows: two repositories on one project, one repository split by area path, and one `CONFLICT` row.

| pr-merged-single-project-repo (regression) | A repository with one `OK` row counts toward its own project only; a `CONFLICT` repository never joins a group | A handbook PR (Internal) on a day when a `CONFLICT` repository and a Training repository also have time; `fixtures/harvest-mapping-handbook.md` adds their rows | Both passed (1.5 h on Internal); the 9ecb1fc skill, which joined groups through shared projects, logged the chained union on Opus 3 of 3 and on Sonnet 1 of 3 |

remove-entry-no-delete and pr-without-work-item-asks each carry a positive assertion as well
(`points-to-harvest-timesheet`, `asks-for-work-item`), so a bare refusal that ends `Writes: none` fails them.
Every case that expects no write also fails on a write-call line (a line that starts with a write tool), and
the `Writes:` line accepts a trailing parenthetical only when it names no write tool. A call quoted inside a
sentence ("once you confirm, I'll call `log_time` with …") is not a write-call line.

`planted/<case id>/` holds answers graded offline by `tests/test_eval_assertions.py`: each `right*.md` (a real
with-skill answer) passes every objective assertion of its case, and each `wrong*.md` fails at least one. The
wrong answers are the reviewer's: a delete or a lower-to-0.01 hidden in the `Writes:` parenthetical, an entry
moved to another project, a log "already sent" before confirming, two rows for one project, a log on both of
a split repository's projects, a refusal, "nothing needed from you", an invented or suggested work item id, a
"which work item" or "can't share" non-ask, a cap check against one project's entries only, a cap trimmed for
the owner, and a second log on another project or on the same one.

The back-fill case also asserts that the entry list is filtered to the owner's user id and that the
proposed hours are 3.00 minus the owner's 0.5. Unaided models already filtered by `user_ids` in every probe
run, so that rule is one clause in the skill and those two assertions are regression checks. A first version
of the fixture showed the filtered result ready-made, which handed both arms the filter; it now gives one
entry set that the call's filter narrows.

Trigger negatives come from the description's Not-for clause: story points (story), commit and PR
(commit-commands, pull-request), a standup summary, and a read-only hours report.

## Evidence on the final SKILL.md

SKILL.md last changed in 3b425bc (written 14:10, 2026-10-14). Every with-skill cell below comes from a run that
started after that, 3 runs per model, graded with the manifest as committed; without-skill cells come from the
latest run of the case (the skill is not mounted there). Run directories are under the gitignored `.eval-runs/`.

| Case | With skill, Opus | With skill, Sonnet | Run (Opus / Sonnet) |
| --- | --- | --- | --- |
| build-done-logs-the-gap | 3/3 | 3/3 | r5-opus 20261014-151216 / r5-sonnet 20261014-151402 |
| remove-entry-no-delete | 3/3 | 3/3 | r5-opus 20261014-151216 / r5-sonnet 20261014-151402 |
| backfill-owner-entries-only | 3/3 | 3/3 | r5-opus 20261014-151216 / r5-sonnet 20261014-151402 |
| pr-merged-note-cites-item | 3/3 | 3/3 | r5-opus 20261014-151216 / r5-sonnet 20261014-151402 |
| pr-without-work-item-asks | 3/3 | 2/3 | r5-opus 20261014-151216 / r5-sonnet 20261014-151402 |
| backfill-daily-cap | 3/3 | 3/3 | r5-opus 20261014-151216 / r5-sonnet 20261014-151402 |
| backfill-two-repos-one-project | 3/3 | 3/3 | r4-opus 20261014-142710 / r4-sonnet 20261014-142812 |
| pr-merged-repo-two-projects (regression) | 3/3 | 3/3 | r4-opus 20261014-142710 / r4-sonnet 20261014-142812 |
| pr-merged-single-project-repo (regression) | 3/3 | 3/3 | r4-opus 20261014-142552 / r4-sonnet 20261014-142355 |

The Sonnet miss on pr-without-work-item-asks asks for the id and logs nothing, but shows the note format with
a placeholder, "for example `Bug #12345: Stream large ticket exports`", which `no-invented-id` and
`no-typed-id` read as an invented id.
