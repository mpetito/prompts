I split the request into two Issues and haven't created anything. Nothing was checked against a live board, so the parent Feature and the area path are placeholders to fill in. Sprint 24 is also unconfirmed: the input file only names Sprints 22 and 23.

Decisions that differ from the request:
- **Issue rather than User Story.** This upgrade changes nothing users can see. The team's Stories backlog holds Issue next to User Story, and Issue carries Story Points. Issue has no Acceptance Criteria field, so the criteria go under `### Acceptance Criteria` in the Description.
- **Two items rather than one story.** About 20 points is above the 13-point ceiling. The API and the worker have separate release pipelines, are deployed separately and can be rolled back separately, so each one ships on its own. Using the tech lead's figures:
  - API plus Core: 8 points, plus a few for the pipeline and image, comes to about 11, which rounds to 13.
  - Worker: 5 points, plus a few for the pipeline and image, comes to 8.
  - Together that's 21, close to the original estimate of 20.
- **The worker comes second.** It uses Dispatch.Core through a project reference, so it waits on the first item. It gets a predecessor link and a later sprint.
- **"Faster afterwards" isn't a criterion.** Nobody has committed to an improvement. What the facts do support is "no worse than 340 ms p95", so that's the criterion. "Everything should still work" is written as specific, checkable behaviour instead.

---

Type: Issue

## Title
Upgrade Dispatch API and Dispatch.Core from .NET 6 to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform (confirm against sibling items)

## Iteration Path
Dispatchboard\Sprint 23

## Parent
Open Feature for Dispatch platform maintenance (to be confirmed on the board)

## Story Points
13

## Links
Successor: Upgrade Dispatch route worker from .NET 6 to .NET 8

## Description
We need the Dispatch API and its shared Dispatch.Core library running on .NET 8 to clear the high-severity security findings caused by the out-of-support .NET 6 runtime.

#### Additional Context

The Dispatchboard Platform tech lead asked for this. .NET 6 went out of support in November 2024, and the security scan now flags every build. The scan currently reports 7 high-severity findings, all tied to the 6.0 runtime images. The target after the upgrade is 0 high findings. The platform team has confirmed that the 8.0 base images are approved. The tech lead originally asked for one story of about 20 points in the next sprint, because Sprint 22 is full. It was split into this item and a successor for the route worker because the API and the worker are released and deployed independently.

Components in this item:

| Component         | Project                             | Notes                                       |
| ----------------- | ----------------------------------- | ------------------------------------------- |
| Dispatch API      | src/Dispatch.Api                    | minimal APIs, 14 endpoints                  |
| Shared library    | src/Dispatch.Core                   | used by API and worker; EF Core 6.0.25      |
| Unit tests        | tests/Dispatch.Core.Tests           | 412 tests, all passing today                |
| Integration tests | tests/Dispatch.Api.IntegrationTests | 38 tests, need Docker                       |
| CI pipeline       | pipelines/build.yml                 | pins SDK 6.0.4xx                            |
| Container image   | Dockerfile.api                      | base image aspnet:6.0                       |

Performance baseline: staging p95 latency for GET /routes is 340 ms today. The upgrade must not make it worse. Nobody has committed to a specific improvement.

Rollback: the API can be redeployed on its previous image tag.

#### Out of Scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Rewriting EF queries other than the two in Dispatch.Core that EF Core 8 rejects.
- The route worker (src/Dispatch.RouteWorker, Dockerfile.worker), which is covered by the successor item.

#### Technical Notes

- Retarget Dispatch.Api and Dispatch.Core to net8.0 and move EF Core from 6.0.25 to 8.0.x.
- Dispatch.Core is a project reference, not a package, and the worker still builds against it on net6.0. Multi-target Dispatch.Core (`net6.0;net8.0`, with EF Core version conditioned per target) until the worker item ships, then drop net6.0 in that item. The alternative is to agree to hold worker releases until it does.
- Rewrite the two Dispatch.Core queries that rely on client-side evaluation, which EF Core 8 rejects at runtime, so they evaluate server-side.
- Update the SDK pin in pipelines/build.yml from 6.0.4xx to 8.0.x, and change the Dockerfile.api base from aspnet:6.0 to aspnet:8.0. Check that the worker's build still passes after the pipeline change.
- All 412 unit tests and 38 integration tests (Docker) pass on .NET 8.
- Deploy through the API's own release pipeline. To roll back, redeploy the previous image tag.

#### Dependencies

None.

### Acceptance Criteria

#### 1. Security

- [ ] The security scan of the new Dispatch API image reports 0 high-severity findings. Today it reports 7.

#### 2. Behaviour unchanged

- [ ] Each of the 14 Dispatch API endpoints returns the same results in staging after the upgrade as it did before, for the same requests.
- [ ] Results that depend on the two rewritten queries list the same records, in the same order, as before the upgrade.

#### 3. Performance

- [ ] Staging p95 latency for GET /routes is 340 ms or less after the upgrade.

#### 4. Rollback

- [ ] An operator can return staging to the previous Dispatch API version by redeploying its previous image tag, and the API then serves requests as before.

---

Type: Issue

## Title
Upgrade Dispatch route worker from .NET 6 to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform (confirm against sibling items)

## Iteration Path
Dispatchboard\Sprint 24 (the sprint after the predecessor; confirm it exists)

## Parent
Same Feature as "Upgrade Dispatch API and Dispatch.Core from .NET 6 to .NET 8"

## Story Points
8

## Links
Predecessor: Upgrade Dispatch API and Dispatch.Core from .NET 6 to .NET 8

## Description
We need the Dispatch route worker running on .NET 8 to clear the high-severity security findings caused by the out-of-support .NET 6 runtime.

#### Additional Context

The Dispatchboard Platform tech lead asked for this. .NET 6 went out of support in November 2024, and the security scan now flags every build. The scan currently reports 7 high-severity findings across the Dispatch services, all tied to the 6.0 runtime images. The target after the upgrade is 0 high findings. The platform team has confirmed that the 8.0 base images are approved. This item is split from a single request of about 20 points because the route worker has its own release pipeline and is deployed independently of the API.

Components in this item:

| Component       | Project                  | Notes                                      |
| --------------- | ------------------------ | ------------------------------------------ |
| Route worker    | src/Dispatch.RouteWorker | background service, reads `route-requests` |
| Container image | Dockerfile.worker        | base image runtime:6.0                     |
| CI pipeline     | pipelines/build.yml      | pins SDK 6.0.4xx (moved to 8.0 in the predecessor) |

The worker uses `IHostingEnvironment`, which is removed in .NET 8.0.

Rollback: the worker can be redeployed on its previous image tag.

#### Out of Scope

- Moving to .NET 9.
- Replacing the `route-requests` queue or changing message formats.
- Rewriting any EF queries (the two needed rewrites are in the predecessor).

#### Technical Notes

- Retarget Dispatch.RouteWorker to net8.0 and replace `IHostingEnvironment` with `IHostEnvironment`.
- Drop the net6.0 target from Dispatch.Core if the predecessor multi-targeted it.
- Change the Dockerfile.worker base from runtime:6.0 to runtime:8.0, and make any remaining worker-specific pipeline changes.
- All 412 unit tests still pass on .NET 8.
- Deploy through the worker's own release pipeline. To roll back, redeploy the previous image tag.

#### Dependencies

Waits on "Upgrade Dispatch API and Dispatch.Core from .NET 6 to .NET 8", because the worker references Dispatch.Core.

### Acceptance Criteria

#### 1. Security

- [ ] The security scan of the new route worker image reports 0 high-severity findings.
- [ ] After this item and its predecessor are deployed, the security scan reports 0 high-severity findings for the Dispatch services. Today it reports 7.

#### 2. Behaviour unchanged

- [ ] A route request placed on the `route-requests` queue in staging is picked up and processed by the worker, with the same result as before the upgrade.
- [ ] Route requests in the existing message format are processed without errors after the upgrade.

#### 3. Rollback

- [ ] An operator can return staging to the previous route worker version by redeploying its previous image tag, and the worker then processes route requests as before.