The tech lead asked for one story, but this request covers two things that ship separately. The API and the worker have separate release pipelines, deploy independently and roll back independently. So I've split it into two items. The single item for tracking the whole upgrade is the parent Feature.

The two child items are Issues, not User Stories, because no user sees or does anything new; this is technical work. If the team's process has no Issue type, use User Story instead and keep the text as written.

The estimate of about 20 points is too big for one item (the limit is 13), so it's estimated per item:
- **API and shared library:** 8 points, plus about 3 for its pipeline and image changes, comes to 11. That rounds up to the nearest allowed value, 13.
- **Route worker:** 5 points, plus about 3 for its pipeline and image changes, comes to 8.
- **Total:** 21, close to the tech lead's guess.

The worker can't move until the shared library is on .NET 8, because it uses the library as a project reference. So the worker item waits on the API item and goes in Sprint 24.

"It should be faster afterwards" isn't a promise anyone can check. I've replaced it with the agreed limit: no slower than 340 ms.

I couldn't look at the board, so please check two things before filing: whether an upgrade item already exists, and whether the area path and title convention match the existing items.

---

Type: Feature

## Title
Dispatch services: upgrade from .NET 6 to .NET 8

## Area Path
Dispatchboard (use the Dispatchboard Platform team's area path)

## Iteration Path
Dispatchboard\Sprint 23

## Description
We need the Dispatch services (Dispatch API and Route worker) moved from .NET 6 to .NET 8 so that they run on a supported runtime and the security scan stops flagging every build.

#### Additional Context

Requested by the Dispatchboard Platform tech lead. .NET 6 went out of support in November 2024, and the security scan now flags every build. Today the scan reports 7 high-severity findings, all tied to the 6.0 runtime images. The target is 0 high findings. The platform team has confirmed that the 8.0 base images are approved. There are no blocking open questions.

The work is split into one child item per independently deployed service:
1. Dispatch API and the shared library Dispatch.Core (13 points, Sprint 23)
2. Route worker (8 points, Sprint 24; waits on item 1)

The tech lead's overall estimate was about 20 points.

#### Out of Scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Rewriting EF queries other than the two in Dispatch.Core that EF Core 8 rejects.

#### Dependencies

None

---

Type: Issue

## Title
Dispatch API: upgrade API and shared library to .NET 8

## Parent
Dispatch services: upgrade from .NET 6 to .NET 8 (Feature above)

## Area Path
Dispatchboard (same as the parent Feature)

## Iteration Path
Dispatchboard\Sprint 23

## Story Points
13

## Description
We need the Dispatch API and its shared library moved from .NET 6 to .NET 8 so that the API runs on a supported runtime and its image passes the security scan with no high-severity findings.

#### Additional Context

Requested by the Dispatchboard Platform tech lead. .NET 6 went out of support in November 2024, and the security scan flags every build. Today it reports 7 high-severity findings, all tied to the 6.0 runtime images. The target is 0. The platform team has approved the 8.0 base images.

- Dispatch API: src/Dispatch.Api, minimal APIs, 14 endpoints.
- Shared library: src/Dispatch.Core, used by both the API and the Route worker. It is a project reference, not a package. It uses EF Core 6.0.25.
- Unit tests: tests/Dispatch.Core.Tests, 412 tests, all passing today.
- Integration tests: tests/Dispatch.Api.IntegrationTests, 38 tests, need Docker.
- CI pipeline: pipelines/build.yml pins SDK 6.0.4xx.
- API container image: Dockerfile.api, base image aspnet:6.0.
- Staging p95 latency for GET /routes is 340 ms today. The upgrade must not make it worse. Nobody has committed to a specific improvement.
- The API has its own release pipeline and deploys independently of the worker.
- Rollback: redeploy the API on its previous image tag.
- Tech lead's estimate: API plus Core about 8 points, plus a few points for the pipeline and image changes.

#### Out of Scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Rewriting EF queries other than the two below.
- The Route worker (separate item).

#### Technical Notes

- Retarget Dispatch.Api and Dispatch.Core to net8.0, and upgrade EF Core from 6.0.25 to 8.0.x.
- Rewrite the two Dispatch.Core queries that rely on client-side evaluation, which EF Core 8 rejects at runtime. Make no other query changes.
- Change the SDK pin in pipelines/build.yml from 6.0.4xx to 8.0.x. Change Dockerfile.api to use aspnet:8.0.
- Moving Dispatch.Core to net8.0 stops the net6.0 worker from building against it. Retarget the worker in the same change (TFM only) if needed to keep it building. Its runtime changes, image and release stay in the worker item.
- Run all 412 unit tests and all 38 integration tests (Docker) green.
- Measure the p95 for GET /routes in staging before and after.
- Rollback path: redeploy the previous image tag.

#### Dependencies

None

## Acceptance Criteria
### 1. Security scan

- [ ] The security scan of the Dispatch API image reports 0 high-severity findings, down from the 7 tied to the 6.0 runtime images.
- [ ] The Dispatch API build is not flagged for an out-of-support runtime.

### 2. Behaviour unchanged

- [ ] Each of the 14 Dispatch API endpoints in staging returns the same results for the same requests as before the upgrade.
- [ ] Screens and reports that use the two rewritten route queries show the same records as before the upgrade.

### 3. Performance

- [ ] In staging, the p95 response time for GET /routes is 340 ms or less.

### 4. Rollback

- [ ] An operator can return the API to the previous version by redeploying the previous image tag, without redeploying the Route worker.

## Links
- Parent: the Feature above

---

Type: Issue

## Title
Route worker: upgrade to .NET 8

## Parent
Dispatch services: upgrade from .NET 6 to .NET 8 (Feature above)

## Area Path
Dispatchboard (same as the parent Feature)

## Iteration Path
Dispatchboard\Sprint 24

## Story Points
8

## Description
We need the Route worker moved from .NET 6 to .NET 8 so that it runs on a supported runtime and its image passes the security scan with no high-severity findings.

#### Additional Context

Requested by the Dispatchboard Platform tech lead. .NET 6 went out of support in November 2024, and the security scan flags every build. Today it reports 7 high-severity findings across the services, all tied to the 6.0 runtime images. The target is 0. The platform team has approved the 8.0 base images.

- Route worker: src/Dispatch.RouteWorker, a background service that reads the `route-requests` queue.
- It uses `IHostingEnvironment`, which is removed in .NET 8.0.
- It depends on src/Dispatch.Core through a project reference. Core is upgraded in the Dispatch API item.
- Worker container image: Dockerfile.worker, base image runtime:6.0.
- The worker has its own release pipeline and deploys independently of the API.
- Rollback: redeploy the worker on its previous image tag.
- Tech lead's estimate: about 5 points, plus a few for the pipeline and image changes.

#### Out of Scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Any EF query changes.

#### Technical Notes

- Retarget Dispatch.RouteWorker to net8.0, if the API item hasn't already done so.
- Replace `IHostingEnvironment` with `IHostEnvironment`.
- Change Dockerfile.worker to use runtime:8.0, and update the worker's release pipeline.
- Run the unit tests green.
- In staging, process a sample of `route-requests` messages and compare the output with the 6.0 worker.
- Rollback path: redeploy the previous image tag.

#### Dependencies

Waits on "Dispatch API: upgrade API and shared library to .NET 8", because Dispatch.Core must be on .NET 8 first.

## Acceptance Criteria
### 1. Security scan

- [ ] The security scan of the Route worker image reports 0 high-severity findings.
- [ ] The Route worker build is not flagged for an out-of-support runtime.

### 2. Route processing unchanged

- [ ] In staging, route requests placed on the route-requests queue are picked up and produce the same routes as before the upgrade.
- [ ] Messages on the route-requests queue keep the same format as before; nothing that sends or reads them needs to change.

### 3. Rollback

- [ ] An operator can return the worker to the previous version by redeploying the previous image tag, without redeploying the Dispatch API.

## Links
- Parent: the Feature above
- Predecessor: Dispatch API: upgrade API and shared library to .NET 8