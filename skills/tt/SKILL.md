---
name: tt
description: "Log or update a Harvest time entry for work performed, with best-effort linkage to an Azure DevOps work item. Use when logging time, recording hours, tracking time, updating a timesheet, after authoring or updating a pull request, or when invoked via /tt. Triggers: log time, track time, harvest entry, timesheet, record hours, /tt."
---

# Time Tracking (Harvest + Azure DevOps)

Create or update an **estimated** Harvest time entry for work just performed, linking it to
an Azure DevOps (ADO) work item when one can be identified.

> **Absolute rule:** entries are **created or updated, never deleted or zeroed out.**
> The Harvest MCP server exposes no delete tool — respect this as an invariant, not a
> limitation to work around. Never use timers; always use `log_time` / `update_time_entry`.

## When to Use

- The user invokes `/tt` or asks to "log time", "track time", or "record hours".
- After a pull request is created or updated (invoked as a follow-up by `pr-authoring`).
- The user describes finished work and asks for it to be recorded on their timesheet.

## Inputs (all optional)

- **A work item** — an ADO id (e.g. `62196`) or descriptive text to search for.
- **An amount of time** — hours as a decimal (e.g. `1.5`).

Anything omitted is inferred (work item via ADO search; hours from the session/changeset
scope). Use the question tool only when the project is genuinely ambiguous or the time
truly cannot be estimated.

## Parsing the invocation

From the user's input, extract whatever is present (all optional):

- A standalone **4–6 digit number** -> the ADO work item id.
- A **trailing decimal** (e.g. `1.5`) -> hours worked.
- Any other **free text** -> search terms for the work item.

Examples: `/tt 62196 1.5`, `/tt 1.5`, `/tt mount compatibility`, `/tt` (infer everything).

## Procedure

### 1. Resolve the repo → Harvest project + task

Repo→project mappings live in **repository memory** (not a checked-in file), because
Harvest projects change over time and the mapping benefits other sessions and developers
in the same workspace.

1. Read `/memories/repo/harvest-time-tracking.md` (memory tool, `view`). It holds a table
   keyed by **git remote URL** (fallback: repo folder name) → `project_id`, project name,
   default `task_id`.
2. **On a hit**, use its `project_id` + default `task_id`.
3. **On a miss**, identify the project:
   - Derive search terms from the git remote / repo / client name.
   - Search Harvest with `list_projects` (`search` = prefix of those terms, `is_active: true`).
   - If exactly one strong match, propose it; otherwise ask with the question tool.
   - After the user confirms, **append** the mapping to
     `/memories/repo/harvest-time-tracking.md` (create the file with the table header if it
     does not exist). Never overwrite existing rows — add a new one.

### 2. Choose the task

Tasks are account-global; these ids are stable:

| Work kind                          | Task            | task_id    |
| ---------------------------------- | --------------- | ---------- |
| Build / dev work (default)         | `Development`   | `6127094`  |
| Meetings (standup, planning, etc.) | `Meetings`      | `12876566` |
| Out of office                      | `Internal Time` | `6127097`  |

Use **Development** unless the work is clearly a meeting or time off. If unsure whether a
task is assigned to the resolved project, confirm with `list_tasks`.

### 3. Resolve the work item (best effort)

- **If an id/text was given:** fetch it via ADO `wit_get_work_item` (or `search_workitem`
  for text). Capture `System.WorkItemType`, `System.Title`, and the item URL.
- **If none was given:** search ADO using the branch name, PR title, and recent commit
  subjects.
- **If the work is a code change, feature, bug fix, or tied to a pull request and ADO
  search finds nothing, ask the user for a work item id before logging** (question tool).
  Such work almost always has a backing item; logging without one produces an unlinked
  entry that has to be corrected later. Only skip the question for clearly internal or
  high-level work (e.g. general meetings, RFP exploration, ad-hoc bug fixes with no item).
- Finding nothing is acceptable **only** for that internal/high-level work — fall through
  to the canonical descriptive note in step 4.
- A related-but-not-resolving item still counts: cite it in the note. The work item link
  records _what the time was spent near_, not only what a PR closes.
- **Never invent or guess a work item id.** Only cite one you verified in ADO.

### 4. Compose the note (plain text)

Notes are plain text only; the MCP server sets no structured link. Embed `#<id>` literally
so Harvest's own ADO integration renders the link.

**Notes must be short summaries — never exhaustive changelogs.** Do not list
implementation details, file names, test counts, or step-by-step changes. One line,
≤ 80 characters.

**Case A — with a work item:** `<WorkItemType> #<id>: <Title>`

- `Issue #62196: Updated Mount Compatibility Requirements`
- `User Story #63295: Investigate VPP Product File Population and Data Gap Analysis`
- Meeting variant — append the id to the meeting name:
  `Peerless-AV - Standup #60974`, `NYEH Sprint Planning Bi-Weekly #62616`

**Case B — no work item (canonical descriptive):** Title Case, `<Area> - <concise activity>`,
no trailing punctuation, ≤ 80 chars.

- `RFP Copilot Design`
- `NYEH Tixsense Backend Design`
- `RFP Copilot - SAM.gov connector & validation`
- `Bug fixes`

❌ **Bad** (verbose changelog — never do this):

> `RFP Agent - spec 015 dashboard lens display/filter/tabs: denormalized a per-lens lensScores map onto OpportunitySummary (seed-then-set per-lens path writes in putScore; conditional brief flag in recordBrief); list now shows scored-lens chips + a single-select lens segmented filter...`

✅ **Good** (work item note): `User Story #1234: Dashboard lens display, filter, and tabs`
✅ **Good** (descriptive note): `RFP Agent - Dashboard Lens Display`

### 5. Determine hours

- If given, use it.
- Otherwise estimate from the session / changeset scope (files touched, commit count, PR
  size).
- **Round up to the nearest 0.25h** (15 min): `0.25`, `0.5`, `2.25`, `3.0`.
- If you cannot estimate within a reasonable range, ask the user with the question tool.

### 6. Create or update (never delete)

1. List today's entries for the same project with
   `list_time_entries` (`from`/`to` = today, `project_id` = resolved project).
2. **If an entry already exists today for the same project + task and same work**
   (matching `#<id>` or descriptive area): prefer `update_time_entry` — increase `hours`
   (existing + new, re-rounded up) and/or refine `notes`.
3. **Otherwise:** `log_time` a new entry with `project_id`, `task_id`, `hours`, `spent_at`
   (default today), and `notes`.

### 7. Report

State the entry id, project, task, hours, and final note back to the user.

## Rules

- ❌ Never delete, zero-out, or replace an existing entry's hours with a smaller value.
- ❌ Never invent a work item id; cite only ids verified in ADO.
- ❌ Never use `start_timer` / `stop_timer` — this workflow logs estimated, rounded hours.
- ❌ Never write verbose changelogs in notes — one summary line, ≤ 80 chars.
- ✅ Keep estimates honest; prefer asking over guessing wildly.
- ✅ Keep the repo→project mapping in repo memory current; append, don't overwrite.

## Repo memory format

`/memories/repo/harvest-time-tracking.md`:

```markdown
# Harvest project mappings

| Git remote / repo           | Project name           | project_id | default task_id |
| --------------------------- | ---------------------- | ---------- | --------------- |
| <remote-url-or-repo-folder> | <Harvest project name> | <id>       | 6127094         |
```

## Common Issues

| Problem                            | Resolution                                                    |
| ---------------------------------- | ------------------------------------------------------------- |
| `not_found` on `update_time_entry` | The entry isn't yours — `log_time` a new one instead.         |
| `list_projects` `truncated: true`  | Refine `search` / pass `client_ids` to narrow.                |
| Task not assigned to project       | Confirm with `list_tasks`; pick an assigned task or ask user. |
| Two equally strong project matches | Ask with the question tool; record the choice in repo memory. |
