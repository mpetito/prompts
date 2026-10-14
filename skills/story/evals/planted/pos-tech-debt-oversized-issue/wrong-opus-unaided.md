I've split the request into one Feature and two User Stories, all set for Sprint 23. There are two things to check before these go to the team.

**1. Check the target version with the tech lead before Sprint 23 starts.** .NET 8 support ends on 10 November 2026, less than a month from today (14 October 2026). .NET 9 also ends support that day, and it's out of scope anyway. If the services land on .NET 8 during Sprint 23, the scan will probably start flagging every build again within weeks. .NET 10 is the current long-term support release, supported until November 2028. I've kept .NET 8 as the target because that's what was asked for, and I've raised the risk in the Feature. The tech lead should decide this before the sprint starts.

**2. I split the work in two.** The tech lead asked for one story of about 20 points, but the API and the worker are released separately and roll back separately. The tech lead's own estimate also splits along those lines. The order matters because of the shared Dispatch.Core library: a .NET 8 app can use a .NET 6 library, but not the other way round. So the worker has to move first, then Core and the API. Doing it in the opposite order breaks the worker's build.

---

Type: Feature

## Title
Move Dispatch services from .NET 6 to .NET 8

## Description
.NET 6 went out of support in November 2024. The security scan now reports 7 high-severity findings, all tied to the 6.0 runtime images, and flags every build. This Feature moves the Dispatch API, the route worker and the shared Dispatch.Core library to .NET 8. That includes the CI pipeline and both container images.

The work is split into two stories because the API and the worker have separate release pipelines and deploy independently:
1. Route worker to .NET 8 (do first)
2. Dispatch.Core and Dispatch API to .NET 8 (do second)

Out of scope: moving to .NET 9, replacing the queue or changing message formats, and rewriting any EF queries other than the two client-side evaluation queries in Dispatch.Core.

**Risk to confirm before Sprint 23:** .NET 8 support ends on 10 November 2026. If we finish this upgrade around then, the services will soon be on an unsupported runtime again, and the scan findings will likely come back. .NET 10, the current long-term support release, is supported until November 2028. The tech lead needs to confirm .NET 8 as the target or change it before the stories are started.

## Acceptance Criteria
- Both child stories are done.
- The security scan reports 0 high-severity findings for the Dispatch API and route worker images.
- No Dispatch project, pipeline or image still targets or uses .NET 6.

## Iteration Path
Dispatchboard\Sprint 23

## Tags
dotnet-upgrade; security; tech-debt

---

Type: User Story

## Title
Upgrade the Dispatch route worker to .NET 8

## Description
As the Dispatchboard Platform team, we want the route worker running on .NET 8 so its builds and image no longer carry the .NET 6 security findings.

Scope:
- Change `src/Dispatch.RouteWorker` to target `net8.0`.
- Replace `IHostingEnvironment`, which is removed in 8.0, with `IHostEnvironment`.
- Change the `Dockerfile.worker` base image from `runtime:6.0` to `runtime:8.0`. The platform team has approved the 8.0 base images.
- Update the worker's part of `pipelines/build.yml` and its release pipeline to use the .NET 8 SDK.

Order: do this story **before** the Dispatch.Core / API story. Dispatch.Core is a project reference, not a package. A .NET 8 worker can keep using Dispatch.Core while it is still on .NET 6, but a .NET 6 worker can't build against a .NET 8 Dispatch.Core.

Rollback: redeploy the worker on its previous image tag.

Out of scope: changing the `route-requests` queue or its message formats; moving to .NET 9.

## Acceptance Criteria
- `Dispatch.RouteWorker` targets `net8.0` and builds in CI on the .NET 8 SDK.
- No code references `IHostingEnvironment`.
- `Dockerfile.worker` uses the `runtime:8.0` base image.
- All 412 tests in `tests/Dispatch.Core.Tests` pass.
- The worker in staging takes messages from `route-requests` and processes them. Message formats are unchanged.
- The security scan reports 0 high-severity findings for the worker image.
- The rollback to the previous worker image tag has been checked and is written down in the release notes.

## Story Points
8

## Iteration Path
Dispatchboard\Sprint 23

## Tags
dotnet-upgrade; security; route-worker

## Notes
Estimate: the tech lead put the worker at about 5 points and the pipeline/image work at "a few points" per service, so 8 in total. Before work starts, confirm the target version (see the Feature).

---

Type: User Story

## Title
Upgrade Dispatch.Core and the Dispatch API to .NET 8 and EF Core 8

## Description
As the Dispatchboard Platform team, we want the Dispatch API and the shared Dispatch.Core library on .NET 8 and EF Core 8, so the API image no longer carries the .NET 6 security findings and the shared code is on a supported runtime.

Scope:
- Change `src/Dispatch.Core` to target `net8.0` and upgrade EF Core from 6.0.25 to 8.x.
- Rewrite the two Dispatch.Core queries that rely on client-side evaluation, which EF Core 8 rejects at runtime. No other query changes.
- Change `src/Dispatch.Api` (minimal APIs, 14 endpoints) to target `net8.0`.
- Change the `Dockerfile.api` base image from `aspnet:6.0` to `aspnet:8.0`.
- Update `pipelines/build.yml` and the API release pipeline to use the .NET 8 SDK (it currently pins 6.0.4xx).

Order: depends on the route worker story. The worker must already be on .NET 8 before Dispatch.Core moves to `net8.0`. Changing Dispatch.Core also changes the worker, so rebuild, regression-test and redeploy the worker with this story too.

Rollback: redeploy the API (and the worker, if it was redeployed) on the previous image tag.

Out of scope: rewriting any other EF queries; moving to .NET 9.

## Acceptance Criteria
- `Dispatch.Core` and `Dispatch.Api` target `net8.0`, and Dispatch.Core uses EF Core 8.x.
- The two client-side evaluation queries are rewritten and run without EF Core 8 runtime errors. No other queries are changed.
- `pipelines/build.yml` no longer pins SDK 6.0.4xx, and CI builds on the .NET 8 SDK.
- `Dockerfile.api` uses the `aspnet:8.0` base image.
- All 412 tests in `tests/Dispatch.Core.Tests` pass.
- All 38 tests in `tests/Dispatch.Api.IntegrationTests` pass (they need Docker).
- All 14 API endpoints respond correctly in staging.
- Staging p95 latency for `GET /routes` is no higher than 340 ms (today's baseline). No speed improvement is required.
- The worker is rebuilt against the upgraded Dispatch.Core and still processes `route-requests` in staging.
- The security scan reports 0 high-severity findings for the API image.
- The rollback to the previous image tags has been checked and is written down in the release notes.

## Story Points
13

## Iteration Path
Dispatchboard\Sprint 23

## Tags
dotnet-upgrade; security; dispatch-api; ef-core

## Notes
Estimate: the tech lead put API plus Core at about 8 points and the pipeline/image work at "a few points", which gives about 12. I rounded up to 13. Both stories add up to 21 points, close to the tech lead's guess of about 20. If 21 points is too much for Sprint 23, this story can move to Sprint 24, because it has to come after the worker story anyway. Before work starts, confirm the target version (see the Feature).