```
list_time_entries {"from": "2026-10-13", "to": "2026-10-13", "user_ids": [4100221]}
```

I haven't logged time for PR #215 yet, because I need a work item id first.

This is a code change (`fix(export): stream large ticket exports instead of buffering them`), and I found no Azure DevOps work item for it. Searches for "export timeout", "stream ticket export" and the branch name `fix/export-timeout` all came back empty. I won't make up an id or log without one, and I won't use the PR number, since the billing sync reads the work item id from the note.

**Which work item id should I use for #215?** If you don't have one, tell me and I'll decide how to log it without one.

Once I have it, this is what I'd log:
- **Date:** today, 2026-10-13.
- **Project and task:** Northwind - Ticketing Platform (50110001), task Development (7000001). That is the default row for `github.com/northwind/ticketing`.
- **Hours:** 1.25. The scanner shows 12:50–14:00 on one Claude session, and you have no entries in Harvest today, so nothing needs subtracting.
- **Note:** `<work item type> #<id>: <title>`, using the title from Azure DevOps.

Writes: none