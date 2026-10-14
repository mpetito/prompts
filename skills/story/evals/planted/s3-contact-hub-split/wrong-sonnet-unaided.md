I've read all three files. The plan is one User Story that covers the wish list. It goes under the existing "CRM Spring Change Request" Feature, in the same area and iteration as the sibling CRM stories.

Findings that shaped the plan:
- **Wish-list item 2 is already done.** "CRM - Inactive contacts drop out of account contact lists [OPS-7214]" (4936) is Closed. The new story says so and doesn't re-scope it. I've only linked to it.
- **Item 1 overlaps 4935.** "Customer Success contact page layout [OPS-7208]" is still New and covers the Customer Success contact page. I've linked it as related and not merged them.
- **Item 5 depends on the Integration Hub.** The "Integration Hub" Feature (4555) is still New. I've linked it as related and recorded the dependency in the story text.

Every call below uses the connector (`mcp__claude_ai_Azure_Devops__`), the same connection as the lookups already made.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "CRM Contact Hub wish list [OPS-5930]"},
    {"name": "System.AreaPath", "value": "Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering"},
    {"name": "System.IterationPath", "value": "Kestrel Ledger\\2026-11-30"},
    {"name": "Microsoft.VSTS.Scheduling.StoryPoints", "value": 21},
    {"name": "Microsoft.VSTS.Common.Priority", "value": 2},
    {"name": "Microsoft.VSTS.Common.ValueArea", "value": "Business"},
    {
      "name": "System.Description",
      "value": "Ticket: https://kestrel.example.net/browse/OPS-5930\n\nClient \"contact hub\" wish list, tracked as one item for reporting. Estimate: about 21 points (Sam Okafor).\n\n**Already delivered (not part of this work):** item 2, hiding inactive contacts from the Contacts related list on accounts, was done under OPS-7214 (work item 4936, Closed).\n\n**Dependency:** item 5 needs the nightly sync from the Integration Hub team, which ships next month (see Integration Hub Feature 4555). Items 1, 3 and 4 do not depend on it.\n\n**Related:** item 1 touches the Customer Success contact view also covered by OPS-7208 (work item 4935).",
      "format": "Markdown"
    },
    {
      "name": "Microsoft.VSTS.Common.AcceptanceCriteria",
      "value": "1. Customer Success reps see a contact's open support cases on the contact page, newest first, 10 max, with a link to all cases.\n2. (Already delivered under OPS-7214 / 4936. Inactive contacts are hidden from the Contacts related list on accounts but stay searchable. Verify only.)\n3. Each contact has a \"Last contacted\" date, filled in automatically from logged calls and meetings.\n4. CS managers can export an account's contacts to CSV with name, email, phone, role and last contacted.\n5. Duplicate contacts (same email on the same account) are flagged nightly for a CS manager to merge. Nothing merges automatically. Blocked until the Integration Hub nightly sync ships.",
      "format": "Markdown"
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
  "linkToId": 4555,
  "linkType": "related",
  "comment": "Wish-list item 5 (nightly duplicate flagging) needs the Integration Hub nightly sync, shipping next month."
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
  "comment": "Wish-list item 1 overlaps the Customer Success contact view (OPS-7208)."
}
```

Call: mcp__claude_ai_Azure_Devops__wit_work_item_link_write
```json
{
  "action": "link",
  "project": "Kestrel Ledger",
  "id": "<id of new item 1>",
  "linkToId": 4936,
  "linkType": "related",
  "comment": "Wish-list item 2 (hide inactive contacts) was already delivered here (OPS-7214)."
}
```

**Note to Lena:**

Hi Lena, the contact hub wish list (OPS-5930) is now one User Story. It sits under "CRM Spring Change Request", in the current 2026-11-30 iteration, at 21 points as Sam estimated. The plan above is written out but not yet run, so the story has no ID yet. Four things to check:

1. **Item 2 is already done.** The inactive-contacts change shipped as OPS-7214 and is Closed. I listed it in the story as delivered and linked to it. If Sam's 21 points included it, the estimate may be a bit high.
2. **Item 5 is blocked.** It can't start until the Integration Hub's nightly sync ships next month. I linked the story to the Integration Hub Feature and noted this in the description. A single 21-point story in this iteration can't close until then, so you may want to move it or split item 5 out.
3. **Item 1 overlaps OPS-7208.** That story, "Customer Success contact page layout", is still New. I linked the two as related. Please tell me if you'd rather fold them together.
4. **Left blank:** I left the story unassigned, since you didn't say who owns it. Priority is 2 and Value Area is Business, matching the sibling stories.