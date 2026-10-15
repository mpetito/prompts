Story 4935 already sits where its siblings do, so placement stays as it is. It has parent Feature 4458 (CRM Spring Change Request), area `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering` and the current iteration `Kestrel Ledger\2026-11-30`. The type and title stay the same: the request is a layout change users will see, so it remains a User Story, and it is one outcome, so it doesn't need splitting. The only change is a rewritten Description and new Acceptance Criteria.

I'd write the two fields with `update_batch` rather than the single-item `update`. On this server only the batch call has a format field, and Description holds HTML today, so it needs the Markdown flag. Before writing, I'd read closed story 4730 (CRM - Contact management tweaks [OPS-7156]) in case it already changed this page.

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item
```json
{"action": "get", "id": 4730, "project": "Kestrel Ledger", "fields": ["System.Title", "System.State", "System.Description", "Microsoft.VSTS.Common.AcceptanceCriteria"]}
```

The write below assumes 4730 doesn't change the Customer Success layout. If it does, I'd add a mention of it under Additional Context and a `related` link before writing.

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item_write
```json
{
  "action": "update_batch",
  "project": "Kestrel Ledger",
  "batchUpdates": [
    {
      "id": 4935,
      "op": "Add",
      "path": "/fields/System.Description",
      "format": "Markdown",
      "value": "As a Customer Success user, I want the contact page to show the fields I work with in the order I use them so that I can find and update a contact's details without scrolling past fields Sales uses.\n\n#### Additional Context\n\nRequested by the client in OPS-7208 and passed on by Lena Fischer (project manager). The client attached the layout below for Customer Success profiles only, and the client signs off on this story.\n\nContact page fields for Customer Success, top to bottom:\n\n1. Name\n2. Account\n3. Role\n4. Email\n5. Phone\n6. Preferred contact method\n7. Service manager\n8. Last contacted\n\nRules from the attachment:\n\n- \"Fax\" and \"Assistant phone\" are removed from the Customer Success layout.\n- Customer Success can't edit Account or Service manager.\n- Sales profiles keep today's layout.\n\nTicket: https://kestrel.example.net/browse/OPS-7208\n\n#### Out of Scope\n\n- Any change to the contact page for Sales profiles.\n- Adding new contact fields. All eight fields above already exist on the contact.\n\n#### Technical Notes\n\nAdd a contact page layout assigned to the Customer Success profile only, and leave the Sales layout assignment untouched. Account and Service manager are read-only on this layout. Removing Fax and Assistant phone from the layout must not delete their data. Open questions for the client (see the comment to Lena): which layout other profiles get, and whether fields on today's page that the list doesn't mention should be dropped.\n\n#### Dependencies\n\nNone"
    },
    {
      "id": 4935,
      "op": "Add",
      "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
      "format": "Markdown",
      "value": "### 1. Customer Success contact page\n\n- [ ] A Customer Success user who opens any contact sees these fields from top to bottom: Name, Account, Role, Email, Phone, Preferred contact method, Service manager, Last contacted.\n- [ ] A Customer Success user does not see \"Fax\" or \"Assistant phone\" on the contact page.\n\n### 2. Fields Customer Success can't edit\n\n- [ ] A Customer Success user who edits a contact sees Account and Service manager but cannot change them.\n- [ ] A Customer Success user can change Name, Role, Email, Phone, Preferred contact method and Last contacted and save the contact.\n\n### 3. Sales contact page\n\n- [ ] A Sales user who opens any contact sees the same fields, in the same order, as before this change, including \"Fax\" and \"Assistant phone\".\n- [ ] A Sales user can still edit every field they can edit today.\n\n### 4. Existing data\n\n- [ ] A contact whose Fax or Assistant phone was filled in still shows those values to a Sales user after the change."
    }
  ]
}
```

Call: mcp__MCP_DOCKER__azure-devops__wit_work_item
```json
{"action": "get", "id": 4935, "project": "Kestrel Ledger", "expand": "All"}
```

On the read-back I'd check four things:
- `multilineFieldsFormat` shows Markdown for both System.Description and Microsoft.VSTS.Common.AcceptanceCriteria.
- Area is still `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering`.
- Iteration is still `Kestrel Ledger\2026-11-30`.
- The parent relation to 4458 is still in place.

---

**Note to Lena:**

I've rewritten the description of story 4935 ("Customer Success contact page layout [OPS-7208]") so it stands on its own: it includes the client's full field list, the two fields being removed, the two that Customer Success can't edit, and the OPS-7208 link. I also added acceptance criteria the client can sign off against. Its parent (4458, CRM Spring Change Request), area, iteration (2026-11-30) and Sam's assignment are unchanged, and I didn't add a story point estimate.

Two things the attachment doesn't settle, which the client should answer before Sam starts on Monday:
1. **Other profiles:** which layout should profiles other than Customer Success and Sales (admins, for example) see?
2. **Unlisted fields:** today's contact page may have fields that are neither in the list nor among the two being removed. Should those disappear from the Customer Success layout too? The "top to bottom" list suggests yes, but it doesn't say so.