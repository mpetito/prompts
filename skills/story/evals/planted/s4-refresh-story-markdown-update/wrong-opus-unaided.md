I'd make one write: a single update to story 4935 through the claude.ai connector, the only tool that supports a revision check. The snapshot already shows everything needed (the story is at rev 2, the Description is stored as HTML, and Acceptance Criteria is empty), so no further reads are required. Nothing else changes: the title, state, assignee, iteration, parent link (4458) and Jira link all stay as they are.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "update",
  "id": 4935,
  "project": "Kestrel Ledger",
  "updates": [
    {
      "op": "Test",
      "path": "/rev",
      "value": 2
    },
    {
      "op": "Replace",
      "path": "/fields/System.Description",
      "format": "Html",
      "value": "<p>Give Customer Success users their own Contact page layout, with only the fields they need, in the order the client specified. Sales users keep today's Contact layout unchanged.</p><h3>Customer Success Contact layout</h3><p>Fields, top to bottom:</p><ol><li>Name</li><li>Account</li><li>Role</li><li>Email</li><li>Phone</li><li>Preferred contact method</li><li>Service manager</li><li>Last contacted</li></ol><ul><li><b>Removed from the CS layout:</b> Fax, Assistant phone.</li><li><b>Read-only for Customer Success:</b> Account, Service manager.</li></ul><h3>Out of scope</h3><ul><li>Any change to the Sales Contact layout.</li></ul><h3>Source</h3><p>Client request in Jira <a href=\"https://kestrel.example.net/browse/OPS-7208\">OPS-7208</a> (field list and order attached to the ticket).</p>"
    },
    {
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "format": "Html",
      "value": "<ol><li>A user with the Customer Success profile who opens a Contact sees these fields, top to bottom, in this order: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.</li><li>The Customer Success Contact layout does not show Fax or Assistant phone.</li><li>A Customer Success user cannot edit Account or Service manager on a Contact. Both fields are visible but read-only.</li><li>A Customer Success user can still edit the other fields on the layout that they can edit today.</li><li>A user with the Sales profile who opens a Contact sees exactly today's layout: the same fields, in the same order, with the same editability, including Fax and Assistant phone.</li></ol>"
    }
  ]
}
```

---

**Note to Lena:**

I've rewritten the description of 4935 so it stands on its own and added five acceptance criteria. The Jira link to OPS-7208 is still in the description. I left the title, state, iteration and parent alone. If someone else edits the story first, the update fails instead of overwriting their change, and I'll redo it against the new version.

Before Sam starts on Monday, could you check three things with the client? I didn't want to guess any of them into the sign-off criteria:

1. **Fax and Assistant phone:** I've read "remove" as hiding them on the Customer Success layout only. Any data already in those fields would be kept. Is that right?
2. **Last contacted:** the client didn't say whether Customer Success users can edit it. Should it be read-only like Account and Service manager?
3. **Phone:** does this mean the existing single Phone field, or does it include any mobile or other phone fields Customer Success uses today?

Whatever they answer, I'll add it to the story's acceptance criteria.