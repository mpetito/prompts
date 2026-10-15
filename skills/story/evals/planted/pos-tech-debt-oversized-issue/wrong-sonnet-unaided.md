Type: Feature

## Title
Move Dispatch services from .NET 6 to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform

## Iteration Path
Dispatchboard\Sprint 23

## Description
.NET 6 went out of support in November 2024. The security scan now reports 7 high-severity findings on every build, all tied to the 6.0 runtime images. This feature moves the Dispatch API, the route worker and the shared Dispatch.Core library to .NET 8. The 8.0 base images are already approved by the platform team.

Out of scope: moving to .NET 9, replacing the queue or changing message formats, and rewriting EF queries other than the two named in the API and Core story.

## Acceptance Criteria
- Both child stories are Done.
- The security scan reports 0 high-severity findings for the API and worker images.
- Staging p95 latency for GET /routes is no worse than 340 ms.

---

Type: User Story

## Title
Upgrade Dispatch.Core and Dispatch.Api to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform

## Iteration Path
Dispatchboard\Sprint 23

## Story Points
11

## Description
As the Dispatchboard Platform team, we want Dispatch.Core and Dispatch.Api running on .NET 8, so that the API no longer ships on an unsupported runtime and the security scan stops flagging it.

Work included:
- Retarget `src/Dispatch.Core` and `src/Dispatch.Api` to net8.0.
- Upgrade EF Core from 6.0.25 to 8.x.
- Rewrite the two Dispatch.Core queries that rely on client-side evaluation, which EF Core 8 rejects at runtime. No other query changes are planned.
- Update `pipelines/build.yml` to pin the .NET 8 SDK instead of 6.0.4xx.
- Update `Dockerfile.api` from `aspnet:6.0` to the approved `aspnet:8.0` base image.

Dispatch.Core is a project reference, not a package. Retargeting it here means the worker story depends on this one.

Estimate: the tech lead's rough split is about 8 points for API plus Core and a few points for the pipeline and image changes, so 11 in total.

Rollback: redeploy the API on its previous image tag. The API and the worker have separate release pipelines.

Out of scope: .NET 9, and rewriting any EF queries other than the two above.

## Acceptance Criteria
- Dispatch.Core and Dispatch.Api build and run on net8.0, with EF Core on 8.x.
- The two client-evaluated queries are rewritten and covered by tests.
- All 412 unit tests in `tests/Dispatch.Core.Tests` pass.
- All 38 integration tests in `tests/Dispatch.Api.IntegrationTests` pass in Docker.
- The CI pipeline builds with the .NET 8 SDK.
- The API image is built on `aspnet:8.0`, and the security scan reports 0 high-severity findings on it.
- Staging p95 latency for GET /routes is 340 ms or lower, measured the same way as the current baseline. No specific improvement is committed.
- Rollback to the previous API image tag is confirmed to work.

## Tags
dotnet8; runtime-upgrade; security

---

Type: User Story

## Title
Upgrade Dispatch.RouteWorker to .NET 8

## Area Path
Dispatchboard\Dispatchboard Platform

## Iteration Path
Dispatchboard\Sprint 23

## Story Points
8

## Description
As the Dispatchboard Platform team, we want the route worker running on .NET 8, so that it no longer ships on an unsupported runtime and the security scan stops flagging it.

Work included:
- Retarget `src/Dispatch.RouteWorker` to net8.0, using the Dispatch.Core build from the API and Core story.
- Replace `IHostingEnvironment`, which is removed in 8.0, with `IHostEnvironment` or `IWebHostEnvironment` as appropriate.
- Update the worker's build and release pipeline to the .NET 8 SDK.
- Update `Dockerfile.worker` from `runtime:6.0` to the approved `runtime:8.0` base image.

The worker keeps reading `route-requests` with the same message formats.

Estimate: the tech lead's rough split is about 5 points for the worker and a few points for the pipeline and image changes, so 8 in total. Together with the API story this comes to 19, close to the 20 points the tech lead guessed.

Rollback: redeploy the worker on its previous image tag. It deploys independently of the API.

Out of scope: replacing the queue or changing message formats.

## Acceptance Criteria
- Dispatch.RouteWorker builds and runs on net8.0 with no remaining `IHostingEnvironment` usage.
- The worker still consumes `route-requests` messages correctly in staging, with no change to message formats.
- All 412 unit tests still pass.
- The worker image is built on `runtime:8.0`, and the security scan reports 0 high-severity findings on it.
- Rollback to the previous worker image tag is confirmed to work.

## Tags
dotnet8; runtime-upgrade; security

## Predecessor
Upgrade Dispatch.Core and Dispatch.Api to .NET 8

---

Notes for the tech lead:
- I split the single 20-point story into two stories under one Feature. Both of them in Sprint 23 gives about 19 points. Sprint 22 is full, so nothing goes there.
- "Faster afterwards" has no committed target, so the criterion is a no-regression guard at 340 ms or lower. Add a number if you want a real improvement target.
- The 11/8 point split is my reading of "a few points each". Please confirm it.