I'll file this as one User Story. The request describes a single outcome: a CS rep sees a contact's open cases on the contact page. The 10-case limit, the "View all" link, hiding closed cases and limiting it to CS roles are all rules within that outcome, so there's no split to confirm first. Because Lena asked to put it on the board, I'll go ahead and create it once the read-only checks find no existing item that covers it.

I'll use the **connector** tools throughout. Its create call takes the Markdown format flag on each field, and its link call takes a `parent` link directly.

---

### Step 1: Read-only checks

Call: mcp__claude_ai_Azure_Devops__work
```json
{"action": "get_team_settings", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team"}
```

Call: mcp__claude_ai_Azure_Devops__work
```json
{"action": "list_team_iterations", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "timeframe": "current"}
```

Call: mcp__claude_ai_Azure_Devops__wit_query
```json
{"action": "wiql", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "top": 200, "wiql": "SELECT [System.Id], [System.WorkItemType], [System.Title], [System.State], [System.AreaPath], [System.IterationPath] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] IN ('Epic', 'Feature') AND [System.State] NOT IN ('Closed', 'Removed', 'Done') ORDER BY [System.ChangedDate] DESC"}
```

Call: mcp__claude_ai_Azure_Devops__wit_query
```json
{"action": "wiql", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "top": 200, "wiql": "SELECT [System.Id], [System.WorkItemType], [System.Title], [System.State], [System.AreaPath], [System.IterationPath], [System.Parent] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] IN ('User Story', 'Issue', 'Bug') AND [System.ChangedDate] >= @today - 120 ORDER BY [System.ChangedDate] DESC"}
```

Call: mcp__claude_ai_Azure_Devops__wit_query
```json
{"action": "wiql", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "top": 200, "wiql": "SELECT [System.Id], [System.WorkItemType], [System.Title], [System.State], [System.Parent] FROM WorkItems WHERE [System.TeamProject] = @project AND ([System.Title] CONTAINS 'case' OR [System.Title] CONTAINS 'contact' OR [System.Description] CONTAINS 'OPS-5902' OR [System.Tags] CONTAINS 'OPS-5902') ORDER BY [System.ChangedDate] DESC"}
```
This duplicate search includes closed items on purpose.

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{"action": "get_batch", "project": "Kestrel Ledger", "ids": "<IDs from results of calls 3, 4 and 5>", "fields": ["System.Id", "System.WorkItemType", "System.Title", "System.State", "System.AreaPath", "System.IterationPath", "System.Parent", "System.Tags"]}
```

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{"action": "get_type", "project": "Kestrel Ledger", "workItemType": "User Story"}
```
This confirms that User Story has its own Acceptance Criteria field and a Story Points field.

---

### Step 2: Create the story

This step runs only if call 5 finds no existing item covering this request. If it finds one, I'd refine or link that item instead.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "Show a contact's open support cases on the contact page"},
    {"name": "System.AreaPath", "value": "<area path used by the sibling stories in call 4, else the default area path from call 1>"},
    {"name": "System.IterationPath", "value": "<current iteration path from call 2>"},
    {"name": "Microsoft.VSTS.Scheduling.StoryPoints", "value": "5"},
    {"name": "System.Tags", "value": "OPS-5902"},
    {"name": "System.Description", "format": "Markdown", "value": "As a Customer Success rep, I want to see a contact's open support cases on their contact page so that I can tell during a call whether they have open issues without searching the Cases tab.\n\n#### Additional Context\n\nRequested by the client's Customer Success lead in ticket OPS-5902, passed on by Lena Fischer (project manager) on 2026-11-12. Sam is expected to pick it up this month.\n\nToday, when a CS rep opens a contact in the CRM, they cannot see whether that person has any open support cases. They have to go to the Cases tab and filter by contact name. This:\n\n- takes a couple of minutes per call;\n- gives wrong results when two contacts share a name.\n\nWhat the client asked for:\n\n- The contact page shows that contact's open cases.\n- Each case shows: case number, subject, status, priority, last updated.\n- Cases are sorted newest first.\n- Each case links to the case.\n- Closed cases are not shown.\n- At most 10 cases are shown on the page, with a \"View all\" link to the full list.\n- Only CS reps and CS managers need to see it. Sales does not.\n\nTicket: OPS-5902 <link to OPS-5902>\n\n#### Out of Scope\n\n- Closed cases.\n- Visibility for Sales users or any role other than CS rep and CS manager.\n- Creating or editing cases from the contact page.\n\n#### Technical Notes\n\n- Match cases to the contact by the contact's record, not by name, so that two contacts with the same name each see only their own cases.\n- \"Newest first\" means by last updated, most recent at the top.\n- Make the section visible only to the CS rep and CS manager roles (or their equivalent permission sets or profiles).\n- Test with: a contact with 0, 1, 10 and 11+ open cases; a contact with closed cases only; two contacts with the same name; one user from each role.\n\n#### Dependencies\n\nNone"},
    {"name": "Microsoft.VSTS.Common.AcceptanceCriteria", "format": "Markdown", "value": "### 1. Open cases on the contact page\n\n- [ ] A CS rep who opens a contact sees a list of that contact's open support cases on the contact page.\n- [ ] Each case in the list shows its case number, subject, status, priority and last updated date.\n- [ ] The list is sorted by last updated, most recent first.\n- [ ] Clicking a case in the list opens that case.\n- [ ] Closed cases do not appear in the list.\n- [ ] When two contacts share a name, each contact's page shows only that contact's own cases.\n\n### 2. Limit and View all\n\n- [ ] When a contact has more than 10 open cases, the page shows the 10 most recently updated ones.\n- [ ] A \"View all\" link on the contact page opens the full list of that contact's open cases.\n\n### 3. Who sees it\n\n- [ ] A CS rep sees the open cases list on the contact page.\n- [ ] A CS manager sees the open cases list on the contact page.\n- [ ] A Sales user who opens the same contact does not see the open cases list."}
  ]
}
```

### Step 3: Link to the parent Feature

This step runs only if call 3 or call 4 points to a Feature these stories sit under, such as one covering the CRM contact page or Customer Success.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_link_write
```json
{"action": "link", "project": "Kestrel Ledger", "id": "<new work item ID from call 8>", "linkToId": "<parent Feature ID from calls 3/4>", "linkType": "parent"}
```

### Step 4: Read it back

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{"action": "get", "project": "Kestrel Ledger", "id": "<new work item ID from call 8>", "expand": "All"}
```
I'd check that Description and Acceptance Criteria are stored as Markdown, and that the area, iteration, parent link and story points are what I set.

---

**Note to Lena:**

Once the duplicate check comes back clean, this goes on the board as one User Story: "Show a contact's open support cases on the contact page" (OPS-5902, 5 points). It goes in the team's current iteration for Sam, under the Feature its sibling stories use, if there is one. I'll send you the ID, placement and link when it's created.

There are three things I'd like you to confirm with the client:

1. **What a contact with no open cases sees.** Should there be an empty message (and if so, the exact wording), or should the section be hidden?
2. **When "View all" shows.** Should the link always appear, or only when the contact has more than 10 open cases?
3. **Which iteration.** Your message is dated 2026-11-12, but today is 2026-10-14. I'll use whatever iteration the board reports as current, so tell me if "this month" means a later sprint.