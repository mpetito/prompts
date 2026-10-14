```text
list_time_entries {"from": "2026-10-13", "to": "2026-10-13", "user_ids": [4100221]}
log_time {"project_id": 50110003, "task_id": 7000001, "hours": 1.75, "spent_at": "2026-10-13", "notes": "Bug #48305: Refund confirmation email not sent"}
```

I logged 1.75 h for PR #230 on Tuesday 2026-10-13. Harvest returned the new entry; its id is in the `log_time` result.

- **Project:** Northwind - Support Agreement (50110003). The work item's area path is `Northwind\Support\Payments`. It matches your `Northwind\Support` row for storefront, which takes priority over the repo's default project, Northwind - Storefront.
- **Task:** Development (7000001)
- **Hours:** 1.75. Your sessions in storefront were active from 09:00 to 10:30 and from 13:00 to 14:45, which adds up to 3.25 h. You already had 1.5 h logged today on Northwind - Storefront / Development (entry 3100000031, "User Story #48190: Checkout validation rules"). That project is also mapped to this repo, so I subtracted it: 3.25 − 1.5 = 1.75.
- **Note:** `Bug #48305: Refund confirmation email not sent`

If the 48190 time came from sessions outside this scan, the refund fix may have taken more than 1.75 h. Tell me the real hours and I'll update this entry.

Writes: log_time