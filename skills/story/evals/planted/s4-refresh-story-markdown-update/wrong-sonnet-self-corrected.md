Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "update",
  "id": 4935,
  "updates": [
    {
      "op": "Test",
      "path": "/rev",
      "value": 2
    },
    {
      "op": "Replace",
      "path": "/fields/System.Description",
      "value": "As a Customer Success user, I want the Contact page to show the fields I need in a set order so that I can find a contact's details and service owner quickly.\n\n#### Additional Context\n\nThe client asked for a Contact page layout specific to Customer Success (CS) profiles. Ticket: https://kestrel.example.net/browse/OPS-7208. The client's note on the ticket: \"Field list for the Customer Success layout attached, in display order.\" What the client attached:\n\n- The layout applies to Customer Success profiles only.\n- Field order on the CS Contact page, top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.\n- Sales profiles keep today's layout.\n- \"Fax\" and \"Assistant phone\" are removed from the CS layout.\n- Customer Success users cannot edit Account or Service manager.\n\n#### Out of Scope\n\n- Any change to the Contact page for Sales profiles.\n- Any change to the Contact page for any other profile.\n\n#### Technical Notes\n\nThe ticket gives no technical approach; the implementer chooses one. The client's request covers the CS layout only, so Fax and Assistant phone are removed from that layout and nothing in the ticket asks for their data to be deleted.\n\n#### Dependencies\n\nNone"
    },
    {
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "value": "### 1. Customer Success layout\n\n- [ ] A Customer Success user opening a Contact sees exactly these fields, top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.\n- [ ] A Customer Success user does not see \"Fax\" on the Contact page.\n- [ ] A Customer Success user does not see \"Assistant phone\" on the Contact page.\n\n### 2. Editing rules for Customer Success\n\n- [ ] A Customer Success user cannot edit Account on a Contact.\n- [ ] A Customer Success user cannot edit Service manager on a Contact.\n\n### 3. Sales layout unchanged\n\n- [ ] A Sales user opening a Contact sees the same layout, with the same fields in the same order, as before this change.\n- [ ] A Sales user still sees \"Fax\" and \"Assistant phone\" on the Contact page, as before this change."
    }
  ]
}
```

I left Format off the updates above and need to correct that. The schema takes `format` per update entry, so this is the exact call to make:

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "update",
  "id": 4935,
  "updates": [
    {
      "op": "Test",
      "path": "/rev",
      "value": 2
    },
    {
      "op": "Replace",
      "path": "/fields/System.Description",
      "format": "Markdown",
      "value": "As a Customer Success user, I want the Contact page to show the fields I need in a set order so that I can find a contact's details and service owner quickly.\n\n#### Additional Context\n\nThe client asked for a Contact page layout specific to Customer Success (CS) profiles. Ticket: https://kestrel.example.net/browse/OPS-7208. The client's note on the ticket: \"Field list for the Customer Success layout attached, in display order.\" What the client attached:\n\n- The layout applies to Customer Success profiles only.\n- Field order on the CS Contact page, top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.\n- Sales profiles keep today's layout.\n- \"Fax\" and \"Assistant phone\" are removed from the CS layout.\n- Customer Success users cannot edit Account or Service manager.\n\n#### Out of Scope\n\n- Any change to the Contact page for Sales profiles.\n- Any change to the Contact page for any other profile.\n\n#### Technical Notes\n\nThe ticket gives no technical approach; the implementer chooses one. The client's request covers the CS layout only, so Fax and Assistant phone are removed from that layout and nothing in the ticket asks for their data to be deleted.\n\n#### Dependencies\n\nNone"
    },
    {
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "format": "Markdown",
      "value": "### 1. Customer Success layout\n\n- [ ] A Customer Success user opening a Contact sees exactly these fields, top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.\n- [ ] A Customer Success user does not see \"Fax\" on the Contact page.\n- [ ] A Customer Success user does not see \"Assistant phone\" on the Contact page.\n\n### 2. Editing rules for Customer Success\n\n- [ ] A Customer Success user cannot edit Account on a Contact.\n- [ ] A Customer Success user cannot edit Service manager on a Contact.\n\n### 3. Sales layout unchanged\n\n- [ ] A Sales user opening a Contact sees the same layout, with the same fields in the same order, as before this change.\n- [ ] A Sales user still sees \"Fax\" and \"Assistant phone\" on the Contact page, as before this change."
    }
  ]
}
```

Make only this second call. The first one is superseded because it has no Markdown flag.

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{
  "action": "get",
  "id": 4935,
  "project": "Kestrel Ledger",
  "expand": "All"
}
```

I'd check the read-back for four things:
- Both rich-text fields show as Markdown.
- Area path is `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering`.
- Iteration is `Kestrel Ledger\2026-11-30`.
- Parent is still 4458.

Note to Lena:

I rewrote story 4935 so Sam can start it cold. The new description has the user-story sentence, every fact from the client's OPS-7208 attachment, the Jira link, and Out of Scope, Technical Notes and Dependencies sections. The acceptance criteria are in three groups: the CS layout and field order, the two fields CS can't edit, and Sales staying unchanged. Each is something the client can check on screen.

- **No other changes:** I left the title, area, iteration (2026-11-30, the current one), parent (Feature 4458) and state alone. The parent link already exists, so I'm not adding another. I also didn't set story points, since you didn't ask for them. Tell me if you want an estimate.
- **Please confirm with the client:** I read "can't edit" as the Account and Service manager fields being read-only for CS users. I read "Customer Success profiles" as user profiles, not a type of contact. I wrote "Sales keeps today's layout" to include Fax and Assistant phone still showing. The ticket doesn't say whether Fax and Assistant phone data should be deleted, so I wrote it as a layout-only removal.
- **Not run yet:** nothing has been written. These calls will run once you confirm, and I'll read the item back afterwards to check it.