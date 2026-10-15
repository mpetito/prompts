Story 4935 already has the right parent (4458), area path and current iteration (`Kestrel Ledger\2026-11-30`). I'll rewrite it in place rather than create a new item. It needs no link call, and the title stays as it is. The single-item `update` has no format field, so I use `update_batch`. That lets me send the Markdown flag on each rich-text field.

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item_write
```json
{
  "action": "update_batch",
  "project": "Kestrel Ledger",
  "batchUpdates": [
    {
      "id": 4935,
      "op": "Replace",
      "path": "/fields/System.Description",
      "format": "Markdown",
      "value": "As a Customer Success user, I want a contact page layout built for Customer Success so that I see the fields I need in a fixed order and can't change the ones owned by others.\n\n#### Additional Context\n\nLena Fischer (project manager) asked for this on behalf of the client. The client attached the following to Jira ticket OPS-7208, with the note \"Field list for the Customer Success layout attached, in display order\".\n\nContact page layout for Customer Success profiles only, top to bottom:\n\n1. Name\n2. Account\n3. Role\n4. Email\n5. Phone\n6. Preferred contact method\n7. Service manager\n8. Last contacted\n\nFields Customer Success users can't edit: Account and Service manager.\n\n\"Fax\" and \"Assistant phone\" are removed from the Customer Success layout. Sales profiles keep today's layout.\n\nTicket: https://kestrel.example.net/browse/OPS-7208\n\n#### Out of Scope\n\n- Any change to the Sales profiles' contact page layout.\n- Changes for profiles other than Customer Success.\n\n#### Technical Notes\n\nThe request is about layout and edit rights only. It doesn't say to delete Fax or Assistant phone data, so only hide them from the Customer Success layout. The field and object names, and how profiles are told apart, are for the implementer to confirm in the CRM. Check the layout with a Customer Success profile and a Sales profile before release.\n\n#### Dependencies\n\nNone"
    },
    {
      "id": 4935,
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "format": "Markdown",
      "value": "### 1. Customer Success contact page layout\n\n- [ ] A Customer Success user opening a contact sees these fields, top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.\n- [ ] A Customer Success user doesn't see the \"Fax\" field on the contact page.\n- [ ] A Customer Success user doesn't see the \"Assistant phone\" field on the contact page.\n\n### 2. Fields Customer Success can't edit\n\n- [ ] A Customer Success user can't edit Account on a contact.\n- [ ] A Customer Success user can't edit Service manager on a contact.\n\n### 3. Sales profiles unchanged\n\n- [ ] A Sales user opening a contact sees the same layout as before this change, including \"Fax\" and \"Assistant phone\".\n- [ ] A Sales user can edit the same fields as before this change."
    },
    {
      "id": 4935,
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Scheduling.StoryPoints",
      "value": "3"
    }
  ]
}
```

Read the item back to check the description and acceptance criteria are Markdown, and that area, iteration and parent are unchanged.

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item
```json
{
  "action": "get",
  "project": "Kestrel Ledger",
  "id": 4935,
  "expand": "All"
}
```

Note to Lena:

I rewrote story 4935 in place. I didn't create a new item, and I haven't run anything yet, so the write is only planned.

- **Description:** It now has the story sentence and the client's full layout, in order, from the OPS-7208 attachment. It also has the Customer Success edit restrictions, the removal of Fax and Assistant phone, the Jira link, out-of-scope items and technical notes.
- **Acceptance criteria:** These are grouped as the Customer Success layout, the fields they can't edit, and Sales unchanged. Each one is something QA or the client can check on screen.
- **Placement:** Parent 4458, area path `…\Spring CRM Engineering` and iteration 2026-11-30 were already right, so I haven't changed them. Sam is already assigned.
- **Story points:** I set 3 as my estimate because the item had none. Please confirm it with Sam, or tell me to drop it.
- **Questions for the client:**
  - Should Fax and Assistant phone data be kept? I assumed it is only hidden from the Customer Success layout, not deleted.
  - Are the other fields editable by Customer Success? The attachment lists only Account and Service manager as locked, so I assumed the rest stay editable.