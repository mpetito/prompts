Dana has 0.50 h of Ticketing Platform time still missing for 2026-10-12, but I haven't logged it. I need a work item id first, and the table needs your confirmation.

```
list_time_entries {"from": "2026-10-12", "to": "2026-10-12", "user_ids": [4100221]}
```

Proposed entry (note pending the work item id):

2026-10-12 | Northwind - Ticketing Platform | 0.50 | <work item type> #<id>: <title> (id needed)

How I got 0.50 h:
- **Scan:** both repositories (`ticketing` and `ticketing-api`) map to the same project, so they form one group. The scan shows 09:00-09:20 and 13:00-13:20, which is 40 minutes of active time. That rounds up to 0.75 h. I did not add the two lines, which would give 1.00 h.
- **Already logged:** 0.25 h on Development for the same project (User Story #48213). Subtracting it leaves 0.50 h.
- **Not subtracted:** 0.75 h of Meetings on the same project (Northwind - Sprint Planning). It is a different task, so I'm showing it only for context.
- **Day total:** 0.25 + 0.75 + 0.50 = 1.50 h, well under the 16 h cap.

| Day | Group | Scanned | Logged (Development) | Proposed |
| --- | --- | --- | --- | --- |
| 2026-10-12 | Northwind - Ticketing Platform (Development) | 0.75 | 0.25 | 0.50 |

Before I log anything, I need two things:
1. **Work item id.** This is a code change and I found no work item for it. I have no Azure DevOps search in this session, so I can't look one up. Please give me the id, or tell me if it is #48213, which is already on the 0.25 h entry. Without an id I'd have to guess the note, and the billing sync reads the id from it.
2. **Confirmation** of the row above.

No other days or unmapped rows are open.

Writes: none