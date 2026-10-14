# Request

From Sam Okafor (CRM developer, Kestrel Ledger), in chat, 2026-11-12, ticket OPS-5911:

> Need a story for the case auto-assignment. Plan: record-triggered flow on Case (after insert),
> look up `Account.Service_Manager__c`, set `Case.OwnerId` to it; if the field is null or the user is
> inactive, assign to queue `CS_Triage`. Skip cases where `Origin = 'Partner Portal'` (partners
> route their own). Write `CaseRoutingFlowTest` with 90%+ coverage, deploy through the
> UATSTAGE sandbox then prod via change set. The client's Customer Success lead signs off in
> UAT, so make sure she can tell from the ticket when it's done. Put it on the board for this month.

Context Sam left out but is on the client ticket: today every new case lands in one shared queue
and a coordinator hand-assigns it, usually within half a day; customers with a named service
manager complain that someone else answers them. Partner Portal cases are handled by the partner
team and must keep landing in their queue as today.
