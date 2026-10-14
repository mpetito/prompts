Nothing was run. These are the two calls I would make, in order.

The connector is the connection whose read-only lookups already ran, so I use it for the writes. The skill names `wit_create_work_item`, but this session only has `wit_work_item_write` with `action: create`.

Call: mcp__claude_ai_Azure_Devops__wit_work_item_write
```json
{
  "action": "create",
  "project": "Kestrel Ledger",
  "workItemType": "User Story",
  "fields": [
    {"name": "System.Title", "value": "Auto-assign new Cases to the Account's Service Manager [OPS-5911]"},
    {"name": "System.AreaPath", "value": "Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering"},
    {"name": "System.IterationPath", "value": "Kestrel Ledger\\2026-11-30"},
    {"name": "Microsoft.VSTS.Scheduling.StoryPoints", "value": 5},
    {"name": "Microsoft.VSTS.Common.Priority", "value": 2},
    {"name": "Microsoft.VSTS.Common.ValueArea", "value": "Business"},
    {
      "name": "System.Description",
      "format": "Markdown",
      "value": "https://kestrel.example.net/browse/OPS-5911\n\nAs a service manager, I want new cases for my accounts to be assigned to me automatically so that my customers hear from me directly instead of waiting for a coordinator to hand-assign the case.\n\n#### Additional Context\n\n- Today every new case lands in one shared queue and a coordinator hand-assigns it, usually within half a day. Customers with a named service manager complain that someone else answers them.\n- Partner Portal cases are handled by the partner team and must keep landing in their queue as today.\n- Sign-off: the Customer Success lead confirms in UAT, using the acceptance criteria below.\n\n#### Technical Notes\n\n- Record-triggered flow on Case (after insert). It looks up Account.Service_Manager__c and sets Case.OwnerId to that user.\n- If Service_Manager__c is null or the user is inactive, set the owner to queue CS_Triage.\n- Skip cases where Origin = 'Partner Portal'.\n- Apex test class CaseRoutingFlowTest with at least 90% coverage.\n- Deploy to the UATSTAGE sandbox first, then to production by change set."
    },
    {
      "name": "Microsoft.VSTS.Common.AcceptanceCriteria",
      "format": "Markdown",
      "value": "### 1. Assignment to the Service Manager\n\n- [ ] When a new case is created for an account that has an active Service Manager, the case owner is that Service Manager immediately after the case is saved, with no coordinator action.\n- [ ] The case appears in that Service Manager's own case list and is not left in the shared queue.\n\n### 2. Fallback to Triage\n\n- [ ] When a new case is created for an account with no Service Manager, the case owner is the CS_Triage queue.\n- [ ] When a new case is created for an account whose Service Manager is an inactive user, the case owner is the CS_Triage queue.\n\n### 3. Partner Portal Cases\n\n- [ ] A new case with Origin 'Partner Portal' is not changed by this automation and lands in the partner team's queue exactly as it does today, including when the account has a Service Manager.\n\n### 4. Verification and Release\n\n- [ ] Each scenario above is demonstrated by the team in the UATSTAGE sandbox, and the Customer Success lead confirms them in UAT.\n- [ ] CaseRoutingFlowTest passes with at least 90% code coverage.\n- [ ] The change is deployed to production by change set, and a case created in production for an account with an active Service Manager is owned by that Service Manager.\n- [ ] Cases created before the release keep their current owner."
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
  "linkType": "parent",
  "comment": "Spring CRM change request, same parent as OPS-7208 and OPS-7214"
}
```

Note to Sam:

I've drafted one User Story for OPS-5911. Nothing has been created yet.

- **Placement:** The story goes in sprint 2026-11-30, the current iteration. Its area is Spring CRM Engineering, and its parent is Feature 4458, "CRM Spring Change Request". That is the same parent as OPS-7208.
- **Points:** I sized it at 5 because it covers the flow, the test class, UATSTAGE, the production change set and UAT. Change it if you see it as smaller.
- **Sign-off:** The acceptance criteria are written in business terms, so the Customer Success lead can check each scenario herself. The flow and Apex details are in a Technical Notes section of the description. This session has no tool for adding comments to a work item, so they could not go in a comment.
- **Assignee:** I left it blank because I don't have your ADO identity. Please assign yourself.

Questions I could not answer from the request:

1. **Cases with no Account:** What should happen to a case with no Account at all? I have not added a rule for it. My guess is that it goes to CS_Triage like a null Service Manager.
2. **Partner Portal queue:** Is the partner team's queue separate from CS_Triage? I assumed it is, since the story only says Partner Portal cases stay where they land today.