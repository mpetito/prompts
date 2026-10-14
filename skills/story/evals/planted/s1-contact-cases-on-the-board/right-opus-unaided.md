Lena's request is written up as one User Story under Feature 4458, "CRM Spring Change Request". It goes in the same area path and the current sprint (2026-11-30) as the related contact-view story 4935.

I used the claude.ai connector for every write. Its `add_child` action is the only one here that sets the parent link at creation time. Its link tool doesn't confirm that `parent` is a valid link type, so I didn't rely on it for that.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "add_child",
  "project": "Kestrel Ledger",
  "parentId": 4458,
  "workItemType": "User Story",
  "items": [
    {
      "title": "Show a contact's open support cases on the Contact page for Customer Success [OPS-5902]",
      "description": "https://kestrel.example.net/browse/OPS-5902\n\n**Requested by:** Client Customer Success lead (via Lena Fischer, 2026-11-12)\n\n**As a** Customer Success rep or CS manager, **I want** the contact page in the CRM to show that contact's open support cases **so that** I can see them during a call without going to the Cases tab and filtering by contact name.\n\n**Problem today:** Reps open the Cases tab and filter by contact name. This takes a couple of minutes per call, and they pick the wrong cases when two contacts share a name.\n\n**Scope**\n- Add an \"Open Cases\" list to the Contact page.\n- Columns: Case Number (links to the case), Subject, Status, Priority, Last Updated.\n- Only open cases appear. Closed cases are excluded.\n- Newest first.\n- Show at most 10 rows, with a \"View all\" link to that contact's full case list.\n- Only Customer Success reps and Customer Success managers see it. Sales users do not.\n\n**Open questions (confirm before build)**\n1. Which case statuses count as \"open\"? For example, are Resolved and Pending Customer open?\n2. Does \"newest first\" mean the date the case was created, or Last Updated?\n3. Should \"View all\" list all of the contact's cases, including closed ones, or only the open ones?\n\n**Related:** #4935 Customer Success contact page layout [OPS-7208], which changes the same CS contact layout.",
      "format": "Markdown",
      "areaPath": "Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering",
      "iterationPath": "Kestrel Ledger\\2026-11-30"
    }
  ]
}
```

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "update",
  "project": "Kestrel Ledger",
  "id": "<id of new item 1>",
  "updates": [
    {
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "value": "- A CS rep or CS manager opening a Contact sees an **Open Cases** list with Case Number, Subject, Status, Priority and Last Updated.\n- The list contains only cases linked to **this contact record** (matched by record ID, not by name). Two contacts with the same name each see only their own cases.\n- Closed cases never appear in the list.\n- Cases are sorted newest first, using the date field agreed in the open questions.\n- At most 10 cases are shown. When the contact has more than 10 open cases, a **View all** link opens that contact's full case list.\n- Each Case Number links to that case's record.\n- When the contact has no open cases, the list shows an empty state instead of an error.\n- Sales users (and any role other than CS rep or CS manager) do not see the list on the Contact page.",
      "format": "Markdown"
    },
    {
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.ValueArea",
      "value": "Business"
    }
  ]
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
  "comment": "Both stories change the Customer Success contact view (OPS-7208 layout)"
}
```

---

**Note to Lena:**

Hi Lena, OPS-5902 is now on the board as a User Story:
- **Where it sits:** under *CRM Spring Change Request* (4458), in the November sprint (2026-11-30) and the Spring CRM Engineering area.
- **What's in it:** the user story and acceptance criteria.
- **Related link:** it's linked to 4935 (OPS-7208, the CS contact layout story), because both change the same contact page and Sam should do them together.

I haven't assigned it to Sam or set a priority yet. Tell me which you want and I'll add them.

Before Sam starts, could the client's CS lead answer three questions?
1. Which case statuses count as "open"? For example, are Resolved and Pending Customer open?
2. Does "newest first" mean the date the case was created, or the date it was last updated?
3. Should "View all" show every case for the contact, or only the open ones?