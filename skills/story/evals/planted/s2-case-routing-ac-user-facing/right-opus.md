I'm filing one User Story for this. It's a new capability, not a bug, and it's one outcome the Customer Success lead can accept on her own. I checked the board first: no open or closed item covers case routing. The closest match, #4826 (service managers' managers on account reports), is a different outcome.

The story is placed like its newest siblings, #4935 and #4936:
- **Parent:** Feature #4458 "CRM Spring Change Request".
- **Area:** `Kestrel Ledger\CRM Modernization\CRM\Spring CRM Engineering`.
- **Iteration:** the team's current one, `Kestrel Ledger\2026-11-30` (1–29 Nov), which is "this month".
- **Title:** ends with the ticket number, the same convention as the siblings.

I write through the connector, the same connection the earlier lookups used. It's the one that accepts the Markdown format flag on updates and links by parent.

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
    {"name": "Microsoft.VSTS.Scheduling.StoryPoints", "value": 3},
    {"name": "Microsoft.VSTS.Common.Priority", "value": 2},
    {"name": "Microsoft.VSTS.Common.ValueArea", "value": "Business"},
    {"name": "System.Description", "format": "Markdown", "value": "As a service manager, I want new cases from my accounts assigned to me automatically so that my customers hear back from me rather than from someone else.\n\n#### Additional Context\n\nRequested by Sam Okafor (CRM developer, Kestrel Ledger) on 2026-11-12. The client's Customer Success lead signs this off in UAT.\n\nToday every new case lands in one shared queue and a coordinator assigns it by hand, usually within half a day. Customers who have a named service manager complain that someone else answers them.\n\nRules from the ticket:\n\n- A new case on an account whose Service Manager is an active user is owned by that service manager.\n- If the account has no Service Manager, or the Service Manager is an inactive user, the case goes to the CS_Triage queue.\n- Cases with Origin = Partner Portal are skipped. The partner team handles these, and they must keep landing in the partner team's queue as they do today.\n\nTicket: https://kestrel.example.net/browse/OPS-5911\n\n#### Out of Scope\n\n- Changing the owner of cases that already exist, or of a case when it is edited later (this runs only when a case is created).\n- Re-routing open cases when an account's Service Manager changes.\n- Any change to how Partner Portal cases are routed.\n\n#### Technical Notes\n\n- Record-triggered flow on Case, after insert (after save). Entry condition: `Origin != 'Partner Portal'`.\n- Look up `Account.Service_Manager__c`. If it is populated and that User is active, set `Case.OwnerId` to it. Otherwise set `Case.OwnerId` to the queue `CS_Triage`.\n- A case with no Account is treated as \"no Service Manager\" (CS_Triage). Confirm this with Sam.\n- Check how the flow and the existing case assignment rule (the shared queue) interact, so the flow's owner wins for non-partner cases and Partner Portal cases still reach the partner queue unchanged.\n- Test class `CaseRoutingFlowTest`, 90%+ coverage. It covers active manager, empty manager, inactive manager, no account, and Partner Portal origin.\n- Deployment: UATSTAGE sandbox, then Customer Success UAT sign-off in UATSTAGE, then production by change set.\n\n#### Dependencies\n\nNone"},
    {"name": "Microsoft.VSTS.Common.AcceptanceCriteria", "format": "Markdown", "value": "### 1. Cases on accounts with a service manager\n\n- [ ] When a case is created on an account whose Service Manager is an active user, the case owner shown on the saved case is that service manager.\n- [ ] The service manager sees the new case among the cases they own, without a coordinator assigning it.\n\n### 2. Fallback to the CS_Triage queue\n\n- [ ] When a case is created on an account with no Service Manager, the case owner is the CS_Triage queue.\n- [ ] When a case is created on an account whose Service Manager is an inactive user, the case owner is the CS_Triage queue.\n\n### 3. Partner Portal cases\n\n- [ ] When a case is created with Case Origin \"Partner Portal\", it lands in the partner team's queue exactly as it does today, even when the account has an active Service Manager.\n- [ ] A Partner Portal case is never assigned to the account's service manager or to the CS_Triage queue.\n\n### 4. Existing cases\n\n- [ ] Cases created before go-live keep their current owner.\n- [ ] Editing an existing case does not change its owner."}
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

Call: mcp__claude_ai_Azure_Devops__wit_work_item
```json
{
  "action": "get",
  "project": "Kestrel Ledger",
  "id": "<id of new item 1>",
  "expand": "All"
}
```

After the read-back I check four things: `multilineFieldsFormat` shows Markdown for both Description and Acceptance Criteria, the area path is right, the iteration is `Kestrel Ledger\2026-11-30`, and there's a Parent relation to #4458.

---

**Note to Sam:**

The case auto-assignment story is on the board as **#<id of new item 1>**, "Auto-assign new Cases to the Account's Service Manager [OPS-5911]".
- **Placement:** under Feature #4458 "CRM Spring Change Request", in Spring CRM Engineering, iteration 2026-11-30.
- **Estimate:** 3 points, Priority 2.

**Where your plan went:**
- **Description:** I added the ticket context you left out: today's shared queue, coordinators taking about half a day, and the complaints from customers who have a named service manager.
- **Technical Notes:** the flow design, `CaseRoutingFlowTest` with 90% coverage, and the UATSTAGE → change set deployment are all here.
- **Acceptance criteria:** written only as what the Customer Success lead will see on a case in UAT. There are four sections: service manager owns the case, empty or inactive manager goes to CS_Triage, Partner Portal unchanged, existing cases untouched. When every box is ticked, she can sign off.

**Three things to confirm:**
1. **Cases with no Account:** I assumed they go to CS_Triage.
2. **Partner team's queue name:** what is it, so UAT can check against it?
3. **Ticket link:** I built it from the pattern on #4935 (`https://kestrel.example.net/browse/OPS-5911`). Fix it if your ticket URL is different.