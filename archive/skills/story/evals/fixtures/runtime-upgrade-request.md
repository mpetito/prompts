# Backlog request: move the Dispatch services off the old runtime

Project: Dispatchboard. Team: Dispatchboard Platform.
Current sprint: Dispatchboard\Sprint 22 (full). Next sprint: Dispatchboard\Sprint 23.

## Message from the tech lead

> Can you write this up as a story for the backlog? .NET 6 went out of support
> in November 2024 and the security scan now flags every build. The Dispatch
> services have to move to .NET 8. It should be faster afterwards and
> everything should still work. Put it in next sprint, this one is full.
> All-in I'd guess about 20 points.

## Inventory (from the repo)

| Component         | Project                               | Notes                                        |
| ----------------- | ------------------------------------- | -------------------------------------------- |
| Dispatch API      | src/Dispatch.Api                      | minimal APIs, 14 endpoints                   |
| Route worker      | src/Dispatch.RouteWorker              | background service, reads `route-requests`   |
| Shared library    | src/Dispatch.Core                     | used by API and worker; EF Core 6.0.25       |
| Unit tests        | tests/Dispatch.Core.Tests             | 412 tests, all passing today                 |
| Integration tests | tests/Dispatch.Api.IntegrationTests   | 38 tests, need Docker                        |
| CI pipeline       | pipelines/build.yml                   | pins SDK 6.0.4xx                             |
| Container images  | Dockerfile.api, Dockerfile.worker     | base image aspnet:6.0 / runtime:6.0          |

## Facts gathered so far

- The API and the worker have separate release pipelines and are deployed
  independently. Dispatch.Core is a project reference, not a package.
- The security scan currently reports 7 high-severity findings, all tied to the
  6.0 runtime images. Target after the upgrade: 0 high findings.
- Two queries in Dispatch.Core rely on client-side evaluation that EF Core 8
  rejects at runtime; both need rewriting. No other query changes are planned.
- The worker uses `IHostingEnvironment`, which is removed in 8.0.
- Staging p95 latency for GET /routes is 340 ms today. The upgrade must not
  make it worse than 340 ms; nobody has committed to a specific improvement.
- Rough split from the tech lead: "API plus Core is the bulk, maybe 8. The
  worker is smaller, maybe 5. Pipeline and image changes ride along with each
  service, call it a few points each."
- Rollback: each service can be redeployed on its previous image tag.

## Out of scope

- Moving to .NET 9.
- Replacing the queue or changing message formats.
- Rewriting EF queries other than the two above.

## Open questions

- None blocking. The platform team confirmed the 8.0 base images are approved.
