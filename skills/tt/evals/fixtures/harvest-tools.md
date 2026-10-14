# What a live session sees from the Harvest MCP server

Copied from a live session on 2026-10-14: the server's instructions and each tool's description verbatim,
for the tools the time-tracking procedure can reach. Parameter lists are shortened to the parameters the
procedure uses (deprecated aliases and filters it never passes are left out); each listed parameter's text
is verbatim, as `name`: description.

## Server instructions

When the user asks for an action none of the available tools can perform, call `submit_feedback` and frame the feedback as a feature request. Also use it when the user reports a bug, expresses friction, or asks to send feedback.

## list_time_entries

List time entries, most recent first. Defaults to the last 30 days when `from`/`to` are omitted. Each entry includes `started_time`/`ended_time` (24h "HH:MM" clock-in/out, null for duration entries). `hours` is the raw tracked duration. Each entry also carries two independent status fields: `billable` (whether the work *can* be billed) and `is_invoiced` (whether it *has* been invoiced — true once the entry is on an invoice). Neither is the same as `is_closed`, which is timesheet-approval status and says nothing about invoicing. To answer invoiced vs. uninvoiced hours, read each entry's `is_invoiced` or pass the `is_invoiced` filter — never infer invoicing from `is_closed` or `billable`. When the account configures hour rounding, each entry also includes `rounded_hours` — the same duration under the account's rounding rule, matching what shows on their Harvest reports and invoices; prefer it when the user asks "how many hours" for a rounding-configured account (accounts with no rounding configured omit `rounded_hours`, since it would equal `hours`). Returns `limit` entries per page (default 100, max 500); when `truncated` is true, paginate by passing `next_cursor` from the prior response back via `cursor` — keep all other parameters identical and treat the cursor as opaque (do not construct one yourself). Authorization is enforced server-side: a role with no cross-user read access gets `forbidden` for any `user_ids` other than its own. A manager who can read only their managed scope receives just the entries they can see for `user_ids` outside that scope (often none), rather than `forbidden`. In that case `scope_limited` is true: the page may be empty or only partial because of your permissions, not because the user logged nothing — do not treat absent or zero hours as authoritative.

- `from`: Inclusive start date (YYYY-MM-DD, e.g. 2026-06-01).
- `to`: Inclusive end date (YYYY-MM-DD, e.g. 2026-06-01).
- `project_ids`: Positive integer project ids to filter to. Omit to include all projects.
- `user_ids`: Positive integer user ids to filter to. Omit to include everyone you're allowed to see.
- `is_invoiced`: Filter by invoiced status. true returns only invoiced entries (on an invoice), false only uninvoiced entries. Omit to include both.
- `limit`: Page size, whole number 1–500. Omit to use the default of 100.
- `cursor`: Opaque pagination token. Omit on the first request; on later pages pass back the exact `next_cursor` string from the prior response. Never construct or send an empty cursor.

## log_time

Log a completed time entry for the authenticated user, or — for managers/admins — another team member via `user_id`. Use this for past time you already know the duration of. To track time as it elapses, use `start_timer` instead. Provide EITHER `hours` (use at least 0.01, the smallest stored increment; positive values that would be stored as 0 are rejected) OR a `started_time` and `ended_time` pair (e.g. "9:00am" to "11:00am"), from which the duration is derived. Accounts that track timestamped timers also record the interval on the entry; accounts that track decimal hours keep only the derived duration.

- `project_id` (required): Project id.
- `task_id` (required): Task id (must be assigned to the project).
- `hours`: Hours worked as a decimal. Use at least 0.01 (e.g. 1.5), the smallest stored increment; positive values that would be stored as 0 are rejected. Provide this OR started_time + ended_time, not both.
- `notes`: Notes describing the work. Required when `get_account_settings` reports `notes_required` — the entry will not save without them.
- `spent_at`: Date the work was performed (YYYY-MM-DD). Defaults to today in the user's timezone.
- `started_time`: Clock-in time, e.g. "9:00am" or "14:30". Provide together with ended_time instead of hours. On a decimal-hours account the duration is derived from the interval but no start or end time is stored.
- `ended_time`: Clock-out time in the same format as started_time (e.g. "11:00am"). Required alongside started_time.
- `user_id`: Log on behalf of another user. Requires manager/admin permission for that user; defaults to the authenticated user.

## update_time_entry

Update an existing time entry's hours, notes, project, task, date, or clock-in/clock-out times — your own, or a teammate's whose time you can edit in Harvest (an admin, or a manager of them or of an active project they're assigned to). The server enforces the same permissions as the web timesheet — you'll get a `not_found` error for an entry you're not allowed to edit. Set the duration with EITHER `hours` (use at least 0.01, the smallest stored increment; positive values that would be stored as 0 are rejected) OR a `started_time` and `ended_time` pair (e.g. "9:00am" to "11:00am"), which is derived into hours. Accounts that track timestamped timers also record the interval on the entry; accounts that track decimal hours keep only the derived duration. To remove an entry use `delete_time_entry`, which enforces the same permissions.

- `id` (required): Positive integer id of the time entry to update (from list_time_entries).
- `hours`: New hours value. Use at least 0.01, the smallest stored increment; the server rejects 0, negative, or positive values that would be stored as 0. Use delete_time_entry to remove an entry. Provide this OR started_time + ended_time, not both.
- `notes`: Replacement notes.
- `project_id`: Move to a different project.
- `task_id`: Move to a different task.
- `spent_at`: Move to a different date (YYYY-MM-DD).
- `started_time`: New clock-in time, e.g. "9:00am" or "14:30". Provide together with ended_time instead of hours. On a decimal-hours account the duration is derived from the interval but no start or end time is stored.
- `ended_time`: New clock-out time in the same format as started_time (e.g. "11:00am"). Required alongside started_time.

## delete_time_entry

Permanently delete a time entry — your own, or a teammate's whose time you can edit in Harvest (an admin, or a manager of them or of an active project they're assigned to). The server enforces the same permissions as the web timesheet — you'll get a `not_found` error for an entry you're not allowed to delete. Entries on an invoiced or approval-locked period cannot be deleted and return a `validation_failed` error — unless you hold company-wide timer-write permission (an Administrator), which bypasses those locks here exactly as it does on the web timesheet. To zero out hours, delete the entry rather than updating it to 0.

- `id` (required): Positive integer id of the time entry to delete (from list_time_entries).

## start_timer

Start a new running timer on the given project + task, for the authenticated user or — for managers/admins — another team member via `user_id`. If that user already has a running timer for the same day, it is stopped first (cross-day timers are not auto-stopped — use stop_timer + start_timer in that case). Returns the running time entry.

## get_account_settings

Return the authenticated account's capabilities and tracking conventions so a caller can pre-validate before attempting an action instead of probing blind. Includes: `approval_required` (does logged time need approval), `notes_required` (every time entry must carry notes), `time_rounding` (whether hours are rounded and how), `wants_timestamp_timers` (timers track clock-in/out times vs raw durations), `week_start_day`, `time_format`, and whether the `invoice` and `expense` features are enabled. Account-level read — every authenticated user sees the same values; no per-row authorization applies.

## list_users

List team members in the user's Harvest account, ordered by id. Returns up to 100 users per page; `total_count` is how many users match the filter in full on every page, not how many are left. Fetch the rest by calling again with the returned `next_cursor` and the same filters, until `truncated` is false. Field availability follows the caller's role — populated values reflect what's visible to you.

- `search`: Case-insensitive prefix match on user name or email.
- `is_active`: Filter to active (true) or deactivated (false) users. Omit for all.

## list_projects

List projects in the user's Harvest account, ordered by client name then project name. Returns up to 100 projects per page; `total_count` is how many projects match the filter in full, so when `truncated` is true you can tell how many are missing — refine `search`, `client_ids`, or `is_active` to narrow the result.

- `search`: Case-insensitive substring match on project name, code, or client name; ignores punctuation and spacing.
- `is_active`: Filter to active (true) or archived (false) projects. Omit for all.

## list_tasks

List tasks in the user's Harvest account, ordered by name. Returns up to 100 tasks per page; `total_count` is how many tasks match the filter in full, so when `truncated` is true you can tell how many are missing — refine `search` or `is_active` to narrow the result.

- `search`: Case-insensitive substring match on task name; ignores punctuation and spacing.
- `is_active`: Filter to active (true) or deactivated (false) tasks. Omit for active tasks only — pass false explicitly to see deactivated ones.
