# ~/.config/tt/harvest-mapping.md (the owner's private mapping file)

Harvest user id: `4100221` (Dana Reyes, dana.reyes@example.com).

Repo key is the session scanner's key. Area path, when set, is an Azure DevOps area-path prefix: the work
item's area path picks the row with the longest matching prefix, and the row with no area path is the
repository's default. A `CONFLICT` row lists the candidates the owner has not chosen between yet.

| Repo key | Area path | Project | project_id | Task | task_id | Status |
| --- | --- | --- | --- | --- | --- | --- |
| github.com/northwind/ticketing | | Northwind - Ticketing Platform | 50110001 | Development | 7000001 | OK |
| github.com/northwind/ticketing-api | | Northwind - Ticketing Platform | 50110001 | Development | 7000001 | OK |
| github.com/northwind/storefront | | Northwind - Storefront | 50110002 | Development | 7000001 | OK |
| github.com/northwind/storefront | Northwind\Support | Northwind - Support Agreement | 50110003 | Development | 7000001 | OK |
| github.com/northwind/handbook | | Northwind - Internal | 50110004 | Development | 7000001 | OK |
| github.com/northwind/wiki | | Northwind - Training | 50110005 | Development | 7000001 | OK |
| github.com/northwind/tools | | Northwind - Internal (50110004) or Northwind - Training (50110005) | | Development | 7000001 | CONFLICT |
