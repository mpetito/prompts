I propose splitting this into two Issues and creating nothing until you confirm the split. I could not look at the board, so the parent Feature and area path are placeholders to fill in from sibling items.

**Why Issue:** the Stories backlog lists Issue beside User Story, and this work has no user-facing change.

**Why two:** the lead's estimate of about 20 points is above 13, so it has to split along parts that ship separately. The API and the worker have separate release pipelines and deploy independently.

**Order:** the worker references Dispatch.Core, so it waits on the API and Core item. It gets a predecessor link and the following sprint.

**Estimates:** I used the lead's figures and mapped them to Fibonacci values.
- API item: 8 for the API plus Core, plus about 3 for pipeline and image, is 11. That maps to 13.
- Worker item: 5, plus about 3 for pipeline and image, is 8.

Together they come to 21 points, which is close to the lead's 20.

---

Type: Issue

## Title
Move Dispatch API and Dispatch.Core to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform (confirm against sibling items)

## Iteration Path
Dispatchboard\Sprint 23

## Story Points
13

## Parent
The Feature that holds the runtime or security work, taken from sibling items. No new Feature is created.

## Links
Related: "Move Dispatch Route worker to .NET 8". It is the successor of this item.

## Description
We need the Dispatch API and the shared Dispatch.Core library to run on .NET 8 to get off the unsupported .NET 6 runtime and clear the security scan findings.

#### Additional Context

The tech lead asked for this. .NET 6 went out of support in November 2024, and the security scan flags every build. The scan currently reports 7 high-severity findings, all tied to the 6.0 runtime images. The target after the upgrade is 0 high findings. Both the API and the worker are covered by that count, so this item clears the API's share and the worker item clears the rest.

Facts from the request:
- Dispatch API (`src/Dispatch.Api`) uses minimal APIs and has 14 endpoints.
- Dispatch.Core (`src/Dispatch.Core`) is shared by the API and the worker and uses EF Core 6.0.25. It is a project reference, not a package.
- Two queries in Dispatch.Core use client-side evaluation that EF Core 8 rejects at runtime. Both need rewriting.
- Staging p95 latency for GET /routes is 340 ms today.
- The 8.0 base images are approved by the platform team.
- The API and the worker have separate release pipelines and are deployed independently.
- Each service can be redeployed on its previous image tag.
- The tech lead's rough estimate for this part is about 8 for the API and Core, plus a few points for the pipeline and image.

Ticket: the tech lead's message in the Dispatchboard runtime upgrade request (no tracker link was provided).

#### Out of Scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Rewriting EF queries other than the two above.
- The Route worker, which has its own item.

#### Technical Notes

- Upgrade `Dispatch.Api` and `Dispatch.Core` to the net8.0 target and move EF Core from 6.0.25 to 8.x.
- Rewrite the two client-evaluated queries in Dispatch.Core.
- Change `pipelines/build.yml` to pin an SDK 8 version instead of 6.0.4xx.
- Change `Dockerfile.api` from the aspnet:6.0 base to aspnet:8.0.
- The existing checks are the 412 unit tests in `tests/Dispatch.Core.Tests` and the 38 integration tests in `tests/Dispatch.Api.IntegrationTests`, which need Docker. All must pass.
- Moving Dispatch.Core to net8.0 affects the worker build. Coordinate so the worker item can follow.
- Release through the API's own pipeline. Rollback is redeploying the previous image tag.

#### Dependencies

None.

### Acceptance Criteria

### 1. Security scan

- [ ] The security scan of the Dispatch API image reports 0 high-severity findings.
- [ ] The Dispatch API image is built on the .NET 8.0 base image, not 6.0.

### 2. Behaviour is unchanged

- [ ] All 14 Dispatch API endpoints return the same responses as before the upgrade for the same requests.
- [ ] Both queries in Dispatch.Core that relied on client-side evaluation return the same results as before the upgrade.

### 3. Performance

- [ ] On staging, p95 latency for GET /routes is 340 ms or lower.

### 4. Build and release

- [ ] The build pipeline completes on SDK 8 with no failed step.
- [ ] The Dispatch API is deployed to staging through its own release pipeline.
- [ ] The Dispatch API can be redeployed on its previous (.NET 6) image tag.

---

Type: Issue

## Title
Move Dispatch Route worker to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform (same as the item above)

## Iteration Path
Dispatchboard\Sprint 24 (the iteration after Sprint 23, as returned by the team's iteration list). It waits on the API and Core item.

## Story Points
8

## Parent
The same Feature as the item above.

## Links
Predecessor: "Move Dispatch API and Dispatch.Core to .NET 8".

## Description
We need the Dispatch Route worker to run on .NET 8 to get off the unsupported .NET 6 runtime and clear the remaining security scan findings.

#### Additional Context

The tech lead asked for this. .NET 6 went out of support in November 2024, and the security scan flags every build. The scan currently reports 7 high-severity findings, all tied to the 6.0 runtime images. The target after the upgrade is 0 high findings overall, so this item clears the worker's share.

Facts from the request:
- The Route worker (`src/Dispatch.RouteWorker`) is a background service that reads the `route-requests` queue.
- It uses `IHostingEnvironment`, which is removed in 8.0.
- It references Dispatch.Core by project reference, so it needs the Core upgrade from the API item first.
- It has its own release pipeline and is deployed independently of the API.
- The 8.0 base images are approved by the platform team.
- Each service can be redeployed on its previous image tag.
- The tech lead's rough estimate for this part is about 5 for the worker, plus a few points for the pipeline and image.

Ticket: the tech lead's message in the Dispatchboard runtime upgrade request (no tracker link was provided).

#### Out of Scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Rewriting EF queries other than the two in Dispatch.Core, which the API item covers.
- The Dispatch API, which has its own item.

#### Technical Notes

- Upgrade `Dispatch.RouteWorker` to the net8.0 target.
- Replace `IHostingEnvironment` with `IHostEnvironment`.
- Change `Dockerfile.worker` from the runtime:6.0 base to runtime:8.0.
- Update the worker's part of `pipelines/build.yml` for SDK 8, if that is not already done.
- Run the unit and integration tests as a regression check.
- Release through the worker's own pipeline. Rollback is redeploying the previous image tag.

#### Dependencies

Waits on "Move Dispatch API and Dispatch.Core to .NET 8", because Dispatch.Core is a project reference.

### Acceptance Criteria

### 1. Security scan

- [ ] The security scan of the Route worker image reports 0 high-severity findings.
- [ ] The Route worker image is built on the .NET 8.0 base image, not 6.0.
- [ ] After this item and the API item are both released, the security scan reports 0 high-severity findings in total, down from 7.

### 2. Behaviour is unchanged

- [ ] The Route worker starts on staging with no startup error.
- [ ] The Route worker reads requests from `route-requests` and processes them with the same results as before the upgrade.
- [ ] The message format on the queue is unchanged.

### 3. Build and release

- [ ] The build pipeline completes on SDK 8 with no failed step.
- [ ] The Route worker is deployed to staging through its own release pipeline.
- [ ] The Route worker can be redeployed on its previous (.NET 6) image tag.

---

**Placement decisions to confirm:**
- Please confirm the split, the Sprint 24 placement for the worker, and the parent Feature and area path. After that I will create the items and read them back with Markdown format on the Description.
- The API item at 13 points is a big commitment for a full team. If Sprint 23 has less room, the pipeline and image work could move into its own item per service.