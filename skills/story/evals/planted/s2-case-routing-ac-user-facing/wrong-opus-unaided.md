I'd create one User Story under Feature 4458, add it to the current sprint, then link it to that Feature as its parent. I'm using the claude.ai connector because the earlier lookups used it.

Values taken from the lookups:
- **Sprint:** "this month" is November, and the team's current iteration is `Kestrel Ledger\2026-11-30` (Nov 1–29).
- **Area path and parent:** I copied them from the newest open CRM stories that carry OPS ticket numbers (4935, 4936). Those sit in `Spring CRM Engineering` under Feature 4458, "CRM Spring Change Request".
- **Required fields:** I set Value Area and State, the story type's other required fields besides Title.

The story is worded around what the customer gets. The acceptance criteria are things the Customer Success lead can check for herself in UAT. Sam's technical plan is kept as implementation notes, with the steps for deploying to production.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "CRM - Route new Cases to the Account's Service Manager automatically [OPS-5911]"},
    {"name": "System.AreaPath", "value": "Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering"},
    {"name": "System.IterationPath", "value": "Kestrel Ledger\\2026-11-30"},
    {"name": "System.State", "value": "New"},
    {"name": "Microsoft.VSTS.Common.ValueArea", "value": "Business"},
    {"name": "Microsoft.VSTS.Common.Priority", "value": 2},
    {"name": "System.Tags", "value": "OPS-5911; Case Routing; UAT"},
    {"name": "System.Description", "format": "Markdown", "value": "https://kestrel.example.net/browse/OPS-5911\n\n**As** a customer with a named Service Manager, **I want** my new case to go straight to that Service Manager **so that** the person who knows my account answers me, without waiting for someone to hand-assign it.\n\n**Today:** every new case lands in one shared queue, and a coordinator assigns it by hand, usually within half a day. Customers who have a named Service Manager complain that someone else answers them.\n\n**Out of scope:** Partner Portal cases. The partner team handles these, and they must keep landing in the partner queue exactly as they do today.\n\n**How to tell when it's done:** this story moves to **Closed** only after the Customer Success lead has signed off in UAT (UATSTAGE) and the change is live in production. Each step is recorded as a comment on this story.\n\n---\n\n**Implementation notes (Sam Okafor):**\n- Record-triggered flow on Case, after insert. Look up `Account.Service_Manager__c` and set `Case.OwnerId` to that user.\n- If the field is blank, the user is inactive, or the case has no Account, assign it to queue `CS_Triage`.\n- Skip cases where `Origin = 'Partner Portal'`.\n- Test class `CaseRoutingFlowTest`, 90%+ coverage. Include a bulk insert (200 cases) and the Partner Portal path.\n- Deploy to UATSTAGE for UAT, then to production by change set.\n\n**Open questions:**\n1. Is `CS_Triage` the shared queue cases land in today, or a new queue that has to be created and staffed?\n2. Do active Case assignment rules currently send Partner Portal cases to the partner queue? This needs confirming so the skip leaves that routing as it is."},
    {"name": "Microsoft.VSTS.Common.AcceptanceCriteria", "format": "Markdown", "value": "Verified in UATSTAGE by the client's Customer Success lead:\n\n1. A new case on an Account whose Service Manager is an active user is owned by that Service Manager as soon as it is saved, with no coordinator step.\n2. A new case on an Account with no Service Manager goes to the **CS_Triage** queue.\n3. A new case on an Account whose Service Manager is inactive goes to the **CS_Triage** queue.\n4. A new case with no Account goes to the **CS_Triage** queue.\n5. A new case with Origin **Partner Portal** lands in the partner team's queue exactly as it does today, and its owner is not changed.\n6. Existing cases, and edits to a case after it is created, are not reassigned.\n7. Cases created in bulk (for example, email-to-case or an import) are routed by the same rules, without errors.\n\nRelease:\n\n8. The Customer Success lead's UAT sign-off is recorded as a comment on this story.\n9. The change is deployed to production by change set, and one case per rule above is confirmed in production."}
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
  "linkType": "parent",
  "comment": "OPS-5911 case auto-assignment, part of the CRM Spring Change Request"
}
```

---

**Note to Sam:** I've created the OPS-5911 story in the 2026-11-30 sprint under "CRM Spring Change Request" (4458). Your flow plan, test class and deployment steps are in the description as implementation notes. The acceptance criteria are written so the Customer Success lead can check each one herself in UATSTAGE. Leave the story open until her UAT sign-off and the production deployment are both recorded as comments, then close it. Closed means it's live.

Three things for you:
- **Queue:** Is `CS_Triage` the shared queue cases land in today, or does it still need to be created and staffed?
- **Partner Portal routing:** Please confirm what sends Partner Portal cases to the partner queue today, so that skipping them really leaves them where they land.
- **Not set by me:** I didn't assign the story or set story points. Over to you.