```
list_time_entries {"from": "2026-10-13", "to": "2026-10-13", "user_ids": [4100221]}
log_time {"project_id": 50110004, "task_id": 7000001, "hours": 1.5, "spent_at": "2026-10-13", "notes": "User Story #48410: Onboarding checklist page"}
```

I logged 1.5 h for PR #240 under **Northwind - Internal / Development** on Tue 2026-10-13. Harvest returned the entry ID in the write result; the input files don't include it, so I can't quote it here.

- **Project:** Northwind - Internal (50110004)
- **Task:** Development (7000001)
- **Hours:** 1.50
- **Date:** 2026-10-13
- **Note:** `User Story #48410: Onboarding checklist page`

How I got there:
- **Project:** Your mapping file sends `github.com/northwind/handbook` to Northwind - Internal. It's the only row for that repo.
- **Hours:** The session scan shows 1.50 h of handbook work today (09:00–10:30). You had no Harvest entries for the day yet, so nothing was subtracted. Your day total is 1.5 h, well under the 16 h limit.
- **Work item:** The PR says `Closes AB#48410`, which is User Story "Onboarding checklist page". The note uses `#48410`, not the PR number and not `AB#`, so the billing sync can match it.

Two other repos from today are still unlogged, because this entry covers only the handbook repo:
- **`github.com/northwind/tools`, 2.00 h (10:00–12:00):** your mapping marks this repo as a conflict between Northwind - Internal (50110004) and Northwind - Training (50110005). Which project should it go to? I'll update the mapping once you choose. I didn't add these hours to the handbook entry.
- **`github.com/northwind/wiki`, 1.00 h (13:00–14:00):** this maps to Northwind - Training. It'll be logged on its next PR event or `/tt` run in that repo, or by a back-fill.

Writes: log_time