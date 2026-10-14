I read all three files. Four choices shaped the calls:

- **Item type and parent:** This is a User Story under Feature 4458, "CRM Spring Change Request". That is the open parent for the other Spring CRM Engineering stories, including the sibling contact-view story 4935.
- **Area path and iteration:** The story goes in the area path `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering`. Its iteration is `Kestrel Ledger\2026-11-30`, the current one, so Sam can pick it up this month.
- **Title:** The title ends with `[OPS-5902]`, like the sibling stories.
- **Required fields:** I set Priority 2 and ValueArea Business to match 4935, which is the sibling story. ValueArea is required.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "Show open support cases on the Contact page for Customer Success [OPS-5902]"},
    {"name": "System.AreaPath", "value": "Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering"},
    {"name": "System.IterationPath", "value": "Kestrel Ledger\\2026-11-30"},
    {"name": "Microsoft.VSTS.Common.Priority", "value": 2},
    {"name": "Microsoft.VSTS.Common.ValueArea", "value": "Business"},
    {"name": "System.Description", "value": "Source ticket: OPS-5902 (requested by the client's Customer Success lead via Lena Fischer, 2026-11-12).\n\n**Problem**\nWhen a CS rep opens a contact in the CRM they cannot see whether that person has open support cases. They have to go to the Cases tab and filter by contact name. This takes a couple of minutes per call and gives wrong results when two contacts share a name.\n\n**Request**\nShow the contact's open support cases on the Contact page, so reps no longer have to search the Cases tab by name.\n\n**Scope**\n- A related list on the Contact page showing only that contact's cases (matched on the contact record, not on name), so contacts with the same name are never mixed up.\n- Columns: case number, subject, status, priority, last updated.\n- Each case links to the case record.\n- Open cases only; closed cases are not shown.\n- Newest first (by last updated).\n- At most 10 rows on the page, with a \"View all\" link to the full list of that contact's cases.\n- Visible to CS reps and CS managers only; not shown to sales.\n\n**Out of scope**\n- Changes to the Cases tab itself.\n- Changing the Contact layout fields requested in OPS-7208 (separate story).\n\n**Open questions for Lena / the client**\n1. Which case statuses count as \"open\" (everything except Closed, or also exclude Resolved/Cancelled)?\n2. Should \"View all\" show open cases only or all cases for the contact? The request says \"the full list\", which reads as all open cases; please confirm.\n3. Exact profiles/roles for \"CS rep\" and \"CS manager\"; do admins also need to see it?\n4. \"Newest first\": last updated, as the column implies, or created date?"},
    {"name": "Microsoft.VSTS.Common.AcceptanceCriteria", "format": "Markdown", "value": "1. Given a CS rep or CS manager opens a contact, the Contact page shows a list of that contact's open cases.\n2. Cases are matched by the contact record; two contacts with the same name each show only their own cases.\n3. Each row shows case number, subject, status, priority and last updated, and the case number (or subject) links to the case.\n4. Closed cases are not listed.\n5. Rows are ordered newest first.\n6. A maximum of 10 rows is shown; when the contact has more than 10 open cases, a \"View all\" link opens the full list for that contact.\n7. A contact with no open cases shows an empty state (e.g. \"No open cases\") rather than an error.\n8. Users outside CS rep / CS manager (e.g. sales) do not see the list.\n9. Tested with a contact that has 0, 1, 10 and 11+ open cases, and with two same-name contacts."}
  ]
}
```

Call: mcp__claude_ai_Azure_Devops__wit_work_item_link_write
```json
{
  "action": "link",
  "project": "Kestrel Ledger",
  "id": "<id of new item 1>",
  "linkToId": 4458,
  "linkType": "parent"
}
```

Call: mcp__claude_ai_Azure_Devops__wit_work_item_link_write
```json
{
  "action": "link",
  "project": "Kestrel Ledger",
  "id": "<id of new item 1>",
  "linkToId": 4935,
  "linkType": "related",
  "comment": "Related contact-view work for Customer Success (OPS-7208 layout fields); OPS-5902 adds the open-cases list."
}
```

**Note to Lena:**
I've written up OPS-5902 as a User Story, "Show open support cases on the Contact page for Customer Success [OPS-5902]". It sits under "CRM Spring CRM Change Request" in the Spring CRM Engineering area, in the 2026-11-30 iteration, so it is on the board for this month. It is related to the existing story OPS-7208, which covers the CS contact layout fields. That one is separate, and I haven't touched it.

I left it unassigned, so please assign it to Sam. The story covers everything you listed. I added one detail: cases are matched on the contact record, not on name, which is what fixes the same-name mix-ups.

I need answers to four questions, which are also listed in the story:
1. Which statuses count as "open"? Is it everything except Closed, or are Resolved and Cancelled excluded too?
2. Should "View all" show only open cases, or every case for the contact?
3. Which exact roles count as CS rep and CS manager, and do admins need to see it?
4. Should "newest first" sort by last updated or by created date?

Sam can start on the layout while these are answered. Questions 1 and 2 affect the query, so they need answers before it is built.