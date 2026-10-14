# Read-only lookups already made this session

Today is 2026-11-12. Project `Kestrel Ledger`, organization `northwind-labs`. These are the results of
the read-only calls made so far, as the tools returned them (long fields trimmed with `…`).

## mcp__claude_ai_Azure_Devops__core_list_project_teams {"project": "Kestrel Ledger", "mine": false}

```json
[{"description":"The default project team.","projectName":"Kestrel Ledger","id":"8c1e0d52-3f7a-4b19-a6d2-5e0f4c9b7a11","name":"Kestrel Ledger Team"}]
```

## mcp__claude_ai_Azure_Devops__work {"action": "get_team_settings", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team"}

```json
{"backlogIteration":{"id":"b2a7c4e1-9d3f-4c8a-8e61-0f2d7a9c3b54","name":"Kestrel Ledger","path":""},"defaultIteration":{"id":"6f4d2b9a-1c7e-4a3d-9b58-2e8c0a7f1d36","name":"2026-11-30","path":"\\2026-11-30"},"defaultIterationMacro":"@currentIteration","backlogVisibilities":{"Microsoft.EpicCategory":true,"Microsoft.FeatureCategory":true,"Microsoft.RequirementCategory":true},"bugsBehavior":"AsRequirements","workingDays":["Monday","Tuesday","Wednesday","Thursday","Friday"],"defaultAreaPath":"Kestrel Ledger","areaPathField":"System.AreaPath","areaPaths":["Kestrel Ledger"]}
```

## mcp__claude_ai_Azure_Devops__work {"action": "list_team_iterations", "project": "Kestrel Ledger", "team": "Kestrel Ledger Team", "timeframe": "current"}

```json
[{"id":"6f4d2b9a-1c7e-4a3d-9b58-2e8c0a7f1d36","name":"2026-11-30","path":"Kestrel Ledger\\2026-11-30","attributes":{"startDate":"2026-11-01T00:00:00Z","finishDate":"2026-11-29T00:00:00Z","timeFrame":"Current"}}]
```

## mcp__claude_ai_Azure_Devops__wit_query (wiql: open Epics and Features, newest change first), then get_batch

```json
[
{"id":4458,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization","System.IterationPath":"Kestrel Ledger","System.WorkItemType":"Feature","System.State":"New","System.Parent":4106,"System.Title":"CRM Spring Change Request"}},
{"id":4106,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization","System.IterationPath":"Kestrel Ledger","System.WorkItemType":"Epic","System.State":"Active","System.Title":"CRM Modernization Program"}},
{"id":4371,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Forecasting","System.IterationPath":"Kestrel Ledger\\2026-04-30","System.WorkItemType":"Feature","System.State":"Active","System.Parent":4106,"System.Title":"CRM Forecasting Change Request [OPS-7036]"}},
{"id":4116,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM","System.IterationPath":"Kestrel Ledger","System.WorkItemType":"Feature","System.State":"Active","System.Parent":4106,"System.Title":"CRM: Tech Debt: Move legacy automations to the new rules engine [OPS-7012]"}},
{"id":4555,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\Integration Hub","System.IterationPath":"Kestrel Ledger","System.WorkItemType":"Feature","System.State":"New","System.Parent":4106,"System.Title":"Integration Hub"}},
{"id":3851,"fields":{"System.AreaPath":"Kestrel Ledger\\Billing Integrations\\Card Gateway","System.IterationPath":"Kestrel Ledger\\2025-01-31","System.WorkItemType":"Feature","System.State":"Active","System.Parent":3782,"System.Title":"Let customers keep a card on file after a one-off payment"}},
{"id":4057,"fields":{"System.AreaPath":"Kestrel Ledger\\Admin and Meetings","System.IterationPath":"Kestrel Ledger","System.WorkItemType":"Epic","System.State":"Active","System.Title":"Project Management & Meetings"}},
{"id":4059,"fields":{"System.AreaPath":"Kestrel Ledger\\Admin and Meetings","System.IterationPath":"Kestrel Ledger","System.WorkItemType":"Feature","System.State":"Active","System.Parent":4057,"System.Title":"Meetings"}}
]
```

## mcp__claude_ai_Azure_Devops__wit_query (wiql: User Stories and Bugs changed in the last 120 days), then get_batch

```json
[
{"id":4977,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-11-30","System.WorkItemType":"User Story","System.State":"New","System.Title":"Freeze closed-won deals against edits [OPS-7101]"}},
{"id":4936,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-11-30","System.WorkItemType":"User Story","System.State":"Closed","System.Parent":4458,"System.Title":"CRM - Inactive contacts drop out of account contact lists [OPS-7214]"}},
{"id":4935,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-11-30","System.WorkItemType":"User Story","System.State":"New","System.Parent":4458,"System.Title":"Customer Success contact page layout [OPS-7208]"}},
{"id":4459,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-11-30","System.WorkItemType":"User Story","System.State":"New","System.Parent":4458,"System.Title":"Spring change request coordination"}},
{"id":4826,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-10-31","System.WorkItemType":"User Story","System.State":"Active","System.Title":"CRM - Show each service manager's manager on account reports [OPS-7187]"}},
{"id":4825,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-10-31","System.WorkItemType":"User Story","System.State":"Active","System.Title":"CRM - Meeting records lose their linked account [OPS-7166]"}},
{"id":4639,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-10-31","System.WorkItemType":"User Story","System.State":"Active","System.Title":"CRM - Freeze closed-won deals against edits [OPS-7093]"}},
{"id":4769,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-09-30","System.WorkItemType":"User Story","System.State":"Closed","System.Title":"CRM - Contracts missing in the UAT sandbox [OPS-7174]"}},
{"id":4730,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-09-30","System.WorkItemType":"User Story","System.State":"Closed","System.Title":"CRM - Contact management tweaks [OPS-7156]"}},
{"id":4138,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Automation Migration","System.IterationPath":"Kestrel Ledger\\2026-09-30","System.WorkItemType":"User Story","System.State":"Closed","System.Parent":4116,"System.Title":"Legacy automation migration, batch 5 [OPS-7040]"}}
]
```

## mcp__claude_ai_Azure_Devops__wit_work_item {"action": "get", "id": 4935, "project": "Kestrel Ledger", "expand": "All"} (trimmed)

```json
{"id":4935,"rev":2,"fields":{"System.AreaPath":"Kestrel Ledger\\CRM Modernization\\CRM\\Spring CRM Engineering","System.IterationPath":"Kestrel Ledger\\2026-11-30","System.WorkItemType":"User Story","System.State":"New","System.AssignedTo":{"displayName":"Sam Okafor"},"System.CreatedBy":{"displayName":"Lena Fischer"},"System.Title":"Customer Success contact page layout [OPS-7208]","Microsoft.VSTS.Common.Priority":2,"Microsoft.VSTS.Common.ValueArea":"Business","System.Description":"<div><a href=\"https://kestrel.example.net/browse/OPS-7208\">https://kestrel.example.net/browse/OPS-7208</a><br> </div><div><br> </div><div>client note:&nbsp;<span>Field list for the Customer Success layout attached, in display order.</span> </div>","System.Parent":4458},"multilineFieldsFormat":{"System.Description":"Html"},"relations":[{"rel":"System.LinkTypes.Hierarchy-Reverse","url":"https://dev.azure.com/northwind-labs/_apis/wit/workItems/4458","attributes":{"name":"Parent"}}]}
```

## mcp__claude_ai_Azure_Devops__wit_work_item {"action": "get_type", "project": "Kestrel Ledger", "workItemType": "User Story"} (field list only)

`System.Title` (required), `System.State` (required), `System.Description`, `System.AreaPath`,
`System.IterationPath`, `System.Parent`, `System.Tags`, `Microsoft.VSTS.Scheduling.StoryPoints`,
`Microsoft.VSTS.Common.AcceptanceCriteria`, `Microsoft.VSTS.Common.Priority`,
`Microsoft.VSTS.Common.ValueArea` (required), `Microsoft.VSTS.Common.Risk`.
