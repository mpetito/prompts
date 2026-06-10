---
name: tt
description: Log or update a Harvest time entry for current work, linked to an Azure DevOps work item when possible
---

# Track Time

Log time for work just performed using the **time-tracking** skill. Entries are created or
updated, **never deleted**, and always logged as estimated hours via `log_time` (never timers).

## Parse the input

From `$ARGUMENTS`, extract whatever is present (all optional):

- A standalone **4–6 digit number** → the ADO work item id.
- A **trailing decimal** (e.g. `1.5`) → hours worked.
- Any other **free text** → search terms for the work item.

Examples: `/tt 62196 1.5`, `/tt 1.5`, `/tt mount compatibility`, `/tt` (infer everything).

## Then

Follow the time-tracking skill end-to-end:

1. Resolve the repo → Harvest project + task (from repo memory, else search and confirm).
2. Resolve the work item via ADO when an id/text is given, or by searching from the branch,
   PR title, and recent commit subjects. Finding nothing is acceptable.
3. Compose the note (work-item format or canonical descriptive), determine hours
   (round up to the nearest 0.25h), and **create or update** today's entry.

Use the question tool only when the project is ambiguous or the time truly can't be
estimated. Report the entry id, project, task, hours, and final note.

## User Input

```text
$ARGUMENTS
```
