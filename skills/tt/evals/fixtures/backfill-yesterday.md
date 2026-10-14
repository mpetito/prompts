# Session state: back-filling yesterday

You are Dana Reyes's main Claude Code session (dana.reyes@example.com). Today is Tuesday 2026-10-13.
Dana is a Harvest administrator, so she can read everyone's time.

## Output of `python3 skills/tt/scripts/scan_sessions.py --from 2026-10-12`, already run

```text
2026-10-12 github.com/northwind/storefront 1.25 1 claude 10:05-11:20
2026-10-12 github.com/northwind/ticketing 3.00 3 claude,codex 13:00-16:00
```

## Harvest results, for the calls you make

`list_users` with `search: "dana.reyes"`:

```json
{"users": [{"id": 4100221, "full_name": "Dana Reyes", "email": "dana.reyes@example.com", "is_active": true, "access_role": "Administrator"}], "truncated": false}
```

`list_tasks` with `search: "Development"`:

```json
{"tasks": [{"id": 7000001, "name": "Development", "is_active": true}], "total_count": 1, "truncated": false}
```

`list_time_entries` with `from`/`to` 2026-10-12 returns these entries, narrowed to the `user_ids` and
`project_ids` you pass, if any:

```json
{"time_entries": [
  {"id": 3099990014, "spent_at": "2026-10-12", "hours": 2.0, "notes": "User Story #48213: Order history API", "user_id": 4100587, "user_name": "Sam Ortiz", "project_id": 50110001, "project_name": "Northwind - Ticketing Platform", "task_id": 7000001, "task_name": "Development"},
  {"id": 3099990011, "spent_at": "2026-10-12", "hours": 0.5, "notes": "User Story #48213: Order history filter, sort and tabs", "user_id": 4100221, "user_name": "Dana Reyes", "project_id": 50110001, "project_name": "Northwind - Ticketing Platform", "task_id": 7000001, "task_name": "Development"},
  {"id": 3099990012, "spent_at": "2026-10-12", "hours": 1.25, "notes": "Storefront - Checkout Validation", "user_id": 4100221, "user_name": "Dana Reyes", "project_id": 50110002, "project_name": "Northwind - Storefront", "task_id": 7000001, "task_name": "Development"}
], "truncated": false, "scope_limited": false}
```

Any write call succeeds and returns the entry it wrote.
