I'll add one User Story under the open Feature #4458 "CRM Spring Change Request". That's where the related contact stories (#4935, #4936) already sit. I'm using the connector tools because the earlier lookups were made with them. There are two things Lena should know first:

- **Item 2 looks like it's already done.** #4936 "CRM - Inactive contacts drop out of account contact lists [OPS-7214]" is Closed. I've kept item 2 in the story only as a check that inactive contacts are still searchable, and linked it to #4936.
- **Item 5 can't finish this sprint.** It needs the Integration Hub nightly sync, which that team ships next month. The current sprint (2026-11-30) ends 2026-11-29. So I'm putting the story on the backlog rather than in the sprint, and tagging the dependency.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "Contact Hub [OPS-5930]"},
    {"name": "System.AreaPath", "value": "Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering"},
    {"name": "System.IterationPath", "value": "Kestrel Ledger"},
    {"name": "Microsoft.VSTS.Common.ValueArea", "value": "Business"},
    {"name": "Microsoft.VSTS.Common.Priority", "value": 2},
    {"name": "Microsoft.VSTS.Scheduling.StoryPoints", "value": 21},
    {"name": "System.Tags", "value": "Contact Hub; Dependency: Integration Hub"},
    {"name": "System.Description", "format": "Markdown", "value": "Client ticket: https://kestrel.example.net/browse/OPS-5930\n\nThe client's \"contact hub\" wish list, kept as one story for reporting.\n\n1. Customer Success reps see a contact's open support cases on the contact page (newest first, 10 max, link to all).\n2. Contacts marked inactive disappear from the Contacts related list on accounts, but stay searchable. *Hiding was delivered in #4936 (OPS-7214, Closed); only searchability still needs checking.*\n3. A \"Last contacted\" date on each contact, filled in automatically from logged calls and meetings.\n4. CS managers can export the contacts of an account to CSV (name, email, phone, role, last contacted).\n5. Duplicate contacts (same email on the same account) are flagged nightly for a CS manager to merge; nothing merges automatically. **Blocked:** needs the Integration Hub nightly sync (#4555), which that team ships next month.\n\nEstimate: about 21 points for the whole list (Sam Okafor)."},
    {"name": "Microsoft.VSTS.Common.AcceptanceCriteria", "format": "Markdown", "value": "- [ ] Contact page shows the contact's open support cases, newest first, at most 10, with a link to all of them.\n- [ ] Inactive contacts stay hidden from the account Contacts related list (#4936) and still show up in search.\n- [ ] Each contact has a \"Last contacted\" date that updates automatically from logged calls and meetings.\n- [ ] CS managers can export an account's contacts to CSV with name, email, phone, role and last contacted.\n- [ ] A nightly job flags contacts with the same email on the same account for a CS manager to merge; no automatic merging. (Depends on the Integration Hub nightly sync.)"}
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
  "comment": "Item 5 (nightly duplicate flagging) depends on the Integration Hub nightly sync, which ships next month."
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
  "comment": "Item 2: hiding inactive contacts was already delivered here (OPS-7214)."
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
  "comment": "Item 1 changes the same Customer Success contact page (OPS-7208)."
}
```

**Note to Lena:**

Hi Lena, the contact hub list (OPS-5930) is now one User Story, "Contact Hub [OPS-5930]", under the CRM Spring Change Request feature (#4458). It has Sam's 21 points and the five wish-list items as acceptance criteria. Three things to check:

1. **Item 2 is mostly done already.** #4936 (OPS-7214, Closed) already hides inactive contacts from the related list. The only open part is confirming they're still searchable. You may want to ask Sam whether the 21 points should drop.
2. **Item 5 is blocked until the Integration Hub ships next month.** Because of that, the story is on the backlog rather than in the 2026-11-30 sprint, which ends 29 November. It's tagged and linked to the Integration Hub feature (#4555). Move it into a sprint when you're ready, or tell me if you'd rather split item 5 out so items 1–4 can start now.
3. **Item 1 touches the same Customer Success contact page as #4935 (OPS-7208),** so I've linked the two.