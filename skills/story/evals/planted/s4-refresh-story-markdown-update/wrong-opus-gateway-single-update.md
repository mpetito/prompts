Lena wants two fields changed on story 4935: the description and the acceptance criteria. The lookups already give me everything else, so one update call is enough. The `update` action has no `format` parameter, and the story's description is already stored as HTML, so I've written both values as HTML. I'm using `add`, which sets the field whether or not it already has a value. `replace` would fail on Acceptance Criteria because that field is empty. I'm not changing the title, state, assignee, iteration or parent.

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item_write
```json
{
  "action": "update",
  "project": "Kestrel Ledger",
  "id": 4935,
  "updates": [
    {
      "op": "add",
      "path": "/fields/System.Description",
      "value": "<h3>Summary</h3><p>Give Customer Success profiles their own Contact page layout. It shows the fields the client asked for, in the order they asked for. Sales profiles keep the layout they have today.</p><h3>Customer Success Contact layout (top to bottom)</h3><ol><li>Name</li><li>Account (read-only for Customer Success)</li><li>Role</li><li>Email</li><li>Phone</li><li>Preferred contact method</li><li>Service manager (read-only for Customer Success)</li><li>Last contacted</li></ol><h3>Changes from the current layout</h3><ul><li>Remove <b>Fax</b> and <b>Assistant phone</b> from the Customer Success layout.</li><li>Make <b>Account</b> and <b>Service manager</b> read-only for Customer Success.</li></ul><h3>Out of scope</h3><ul><li>The Sales profile's Contact layout. It stays exactly as it is today.</li></ul><h3>Source</h3><p>Client request and attachment on Jira <a href=\"https://kestrel.example.net/browse/OPS-7208\">OPS-7208</a>: \"Field list for the Customer Success layout attached, in display order.\"</p>"
    },
    {
      "op": "add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "value": "<ol><li>A user with the Customer Success profile who opens a Contact sees these fields, top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.</li><li>The Customer Success layout does not show Fax or Assistant phone.</li><li>A Customer Success user can see Account and Service manager on a Contact but cannot edit them.</li><li>A Customer Success user can still edit Name, Role, Email, Phone, Preferred contact method and Last contacted, as they can today.</li><li>A user with the Sales profile sees the same Contact layout as today: same fields, same order, same edit rights, Fax and Assistant phone included.</li><li>Values entered before the change, including any Fax or Assistant phone data, are still on the Contact record. Only the Customer Success layout changes.</li></ol>"
    }
  ]
}
```

Note to Lena:

I've rewritten the description of story 4935 so it stands on its own. It keeps the OPS-7208 link and the client's note as the source. I've also added six acceptance criteria. I didn't change the title, state, assignee, sprint or parent. Please confirm or correct these points with the client before Sam starts on Monday:

1. **Fields not on the list:** I've treated the eight fields as the complete Customer Success layout. If the current layout has fields besides Fax and Assistant phone, those would also disappear for Customer Success. I need the client to confirm that's intended.
2. **Which profile counts:** I read "Customer Success profiles" as the profile of the person viewing the Contact. If it means a type of contact record instead, the description and criteria need rewording.
3. **Last contacted:** Criterion 4 assumes Customer Success can edit Last contacted by hand. If that field fills in automatically, I'll take it out of criterion 4.
4. **Fax and Assistant phone data:** Criterion 6 is my addition, not the client's. It says existing Fax and Assistant phone values stay on the record and are only hidden from the Customer Success layout. If the client wants those values deleted, the criterion needs changing.