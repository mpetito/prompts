I haven't run anything. These are the calls I would make, in order. I'd use the self-hosted gateway connection throughout. Its `create` call takes a per-field `format`, which the Markdown rule needs. Calls 1–6 are read-only. Calls 7–9 write, and they go ahead because you asked for it on the board and I'm keeping this as one story (see the note at the end).

**Call 1: team settings (default area path, backlog levels, default iteration)**

Call: mcp__MCP_DOCKER__azure-devops__work
```json
{"action": "get_team_settings", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team"}
```

**Call 2: the team's current iteration**

Call: mcp__MCP_DOCKER__azure-devops__work
```json
{"action": "list_team_iterations", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "timeframe": "current"}
```

**Call 3: User Story type fields (to confirm Acceptance Criteria and Story Points exist)**

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item
```json
{"action": "get_type", "project": "Kestrel Ledger", "workItemType": "User Story"}
```

**Call 4: open Epics and Features, the candidate parents**

Call: mcp__MCP_DOCKER__azure-devops__wit_query
```json
{"action": "wiql", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "top": 200, "wiql": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] IN ('Epic','Feature') AND [System.State] NOT IN ('Closed','Removed') ORDER BY [System.ChangedDate] DESC"}
```

**Call 5: stories, issues and bugs changed in the last ~6 months, closed ones included, for duplicates and sibling conventions**

Call: mcp__MCP_DOCKER__azure-devops__wit_query
```json
{"action": "wiql", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "top": 200, "wiql": "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] IN ('User Story','Issue','Bug') AND [System.State] <> 'Removed' AND [System.ChangedDate] >= @Today - 180 ORDER BY [System.ChangedDate] DESC"}
```

**Call 6: details of the items from calls 4 and 5**

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item
```json
{"action": "get_batch", "project": "Kestrel Ledger", "ids": "<ids from results of call 4 and call 5>", "fields": ["System.Id", "System.WorkItemType", "System.Title", "System.State", "System.AreaPath", "System.IterationPath", "System.Parent", "Microsoft.VSTS.Scheduling.StoryPoints"]}
```

I read these results before writing anything.
- If an existing item already covers open cases on the contact page, I'd stop and refine or link it instead of creating a new one.
- The parent is the Feature that holds the CRM or contact or cases stories. If none fits, I create no new Feature. I'd ask you.
- The area path comes from those siblings, falling back to the call 1 default.
- The iteration is the current-iteration path from call 2, exactly as returned.
- Titles follow the sibling convention.

**Call 7: create the story**

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "<title in the sibling convention, e.g. Show a contact's open support cases on the contact page>"},
    {"name": "System.AreaPath", "value": "<area path from the siblings in result of call 6>"},
    {"name": "System.IterationPath", "value": "<current iteration path from result of call 2>"},
    {"name": "Microsoft.VSTS.Scheduling.StoryPoints", "value": "3"},
    {
      "name": "System.Description",
      "format": "Markdown",
      "value": "As a CS rep or CS manager, I want to see a contact's open support cases on the contact page so that I can tell during a call whether they have open cases without leaving the page or filtering the Cases tab by name.\n\n#### Additional Context\n\nRequested by the client's Customer Success lead, passed on by Lena Fischer (project manager) on 2026-11-12. Today a CS rep opening a contact in the CRM cannot see whether that person has open support cases. They go to the Cases tab and filter by contact name. That takes a couple of minutes per call, and it gives wrong results when two contacts share a name.\n\nWhat the client asked for:\n\n- The contact page shows that contact's open cases.\n- Each case shows case number, subject, status, priority and last updated.\n- Newest first.\n- Each case links to the case.\n- Closed cases are not shown.\n- At most 10 cases on the page, with a \"View all\" link to the full list.\n- Only CS reps and CS managers need it. Sales does not.\n\nTicket: OPS-5902\n\n#### Out of Scope\n\n- Showing closed cases on the contact page.\n- Showing the section to sales users.\n- Any change to the Cases tab itself.\n\n#### Technical Notes\n\nMatch cases to the contact by contact record id, never by name, since two contacts can share a name. Role check, query, tests and deployment path to be filled in by the implementer.\n\n#### Dependencies\n\nNone"
    },
    {
      "name": "Microsoft.VSTS.Common.AcceptanceCriteria",
      "format": "Markdown",
      "value": "### 1. Who sees the open cases\n\n- [ ] A CS rep sees the open cases section on a contact page.\n- [ ] A CS manager sees the open cases section on a contact page.\n- [ ] A sales user does not see the open cases section on a contact page.\n\n### 2. Which cases are listed\n\n- [ ] The section lists only cases of the contact whose page is open, including when another contact has the same name.\n- [ ] A closed case is not listed.\n- [ ] A case that is not closed is listed. <exact open statuses to be confirmed, see note to requester>\n\n### 3. What each case shows\n\n- [ ] Each case shows its case number, subject, status, priority and last updated.\n- [ ] Clicking a case opens that case.\n\n### 4. Order and limit\n\n- [ ] Cases are listed newest first by last updated.\n- [ ] At most 10 cases are listed, even when the contact has more open cases.\n- [ ] A \"View all\" link shows when the contact has more than 10 open cases and opens the full list. <what the full list contains, see note to requester>\n- [ ] When the contact has no open cases, the section says so. <exact wording to be confirmed>"
    }
  ]
}
```

**Call 8: link the new story to its parent Feature**

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item_link_write
```json
{
  "action": "link",
  "project": "Kestrel Ledger",
  "updates": [
    {"id": "<id from result of call 7>", "linkToId": "<parent Feature id from result of call 6>", "type": "parent"}
  ]
}
```

**Call 9: read back to check format, area, iteration and parent**

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item
```json
{"action": "get", "project": "Kestrel Ledger", "id": "<id from result of call 7>", "expand": "All"}
```

**Note to Lena**

I'm filing this as one User Story, not a split. Seeing open cases on the contact page is a single outcome. The role limit and the "View all" link are rules inside it, not separate things to ship. I estimate it at 3 points. After the write I'll report the id, title, parent, area, iteration and link.

Before I write, I need four answers. I'll put your answers in the criteria and drop the marked placeholders.
1. Which case statuses count as "open"? I need the exact names.
2. Does "View all" open all of the contact's cases or only the open ones? And should it show only when there are more than 10?
3. What should the section say when a contact has no open cases?
4. Is "CS rep" and "CS manager" an existing role in the CRM? If it isn't, what is it called there?

Two other things:
- Your request is dated 2026-11-12, but this session's date is 2026-10-14. I used relative dates in the queries, so that doesn't affect them. Check which date is right when Sam plans the month.
- OPS-5902 is a reference without a URL. If you have the link, I'll add it to the description.