# Stability, Flakes and CI Evidence

Load this from [playwright-e2e](../SKILL.md) when a suite must stay trustworthy as it grows:
CI artifacts, the stability gate for new tests, flake triage, tests written ahead of features,
smoke tests that gate a rollback, secrets in artifacts, and several agents sharing one host.

- The reviewer's probes (mutants, reproduce-and-ablate, secret-sink scans) are in
  [review](../../review/SKILL.md).
- CI waits, re-runs and merge refs are in [autonomous-loops](../../autonomous-loops/SKILL.md).
- Option names and behaviour below come from the Playwright 1.63 docs unless marked
  "observed". Check them against the installed version.

## CI Artifacts and Duration

Set these up with the first CI e2e job. A flake with no record of the failing attempt costs
rounds of guessing.

- **Keep a trace of every failed attempt.** The SKILL.md config uses `retain-on-failure`. The
  modes that matter here:

  | Mode                      | Records            | Keeps                      |
  | ------------------------- | ------------------ | -------------------------- |
  | `retain-on-failure`       | every run          | each run that failed       |
  | `retain-on-first-failure` | the first run only | that run, if it failed     |
  | `on-first-retry`          | the first retry    | that retry, pass or fail   |

- **Upload `test-results/` on failure, and the HTML report unless cancelled.** `outputDir`
  (default `test-results`) holds traces, screenshots and error context.
- **Make the failure message carry the state the test waited on.** Poll the state itself, so
  the error prints the last value seen (observed in 1.63; the docs don't say):

  ```ts
  await expect.poll(() => readDrawerState(page)).toEqual({ open: true, animating: false });
  ```

- **Track e2e job duration as the suite grows.** Shard (`--shard=1/4`) or raise
  `timeout-minutes` before the suite reaches it; a job cancelled at the cap reads like a test
  failure.
- **Scope the browser tier by changed paths** so docs-only PRs don't wait on it. For a required
  check, skip inside the job (a change-detection step), not with workflow-level `paths`: a
  workflow skipped by a path filter leaves its checks pending and blocks the merge.
- **Run proof suites in CI.** Suites that test the harness itself (helpers, guards, negative
  controls) rot when only a reviewer runs them. Wire them in, path-filtered to their support
  code, when the first one is created.

## Stability Gate for New or Changed Tests

One green run proves little. Before opening a PR that adds or changes a browser test:

```bash
taskset -c 0,1 npx playwright test tests/cart.spec.ts --repeat-each=5 --retries=0
```

- **Every project,** WebKit and phone profiles included. Timing bugs show first on the slower
  engines.
- **Constrained CPU and a parallel load.** Pin to a few cores (`taskset` on Linux) and run
  another suite or a load generator alongside.
- **`--retries=0` and zero failures.** Report pass, fail and flaky counts per project.
- **Timing-bound tests on a slower CI engine:** local repeats are necessary, not sufficient.
  Approve only with CI evidence (several green CI runs on that project, or a `--repeat-each`
  run in CI), and record the local-to-CI timing ratio as the margin.
- **Interaction tests also run with motion on and real input,** not only under reduced motion
  with synthetic clicks. Keep one real `tap()` probe per primary control on phone profiles.

## Helpers That Bypass Actionability

`force: true` skips the check that the target actually receives the click, and dispatched
events skip it too. A cover that blocks real users then passes the test.

- **Treat a failed native click as a possible product defect.** Report it before working
  around it.
- **A bypass helper must still hit-test** the target's centre (`document.elementFromPoint`) and
  fail when another element is on top. Ship a negative control: a control under a transparent
  overlay must be rejected.
- **Choose the click mode from declared inputs** (the reduced-motion setting, a pause flag),
  never from a snapshot of transient state such as "an animation is running now".

## Flake Triage

Work in this order. Never loosen a test on an unconfirmed hypothesis.

1. **Confirm the artifacts exist** for the failing attempt: trace, error context, report. If
   they don't, fix the upload before anything else.
2. **Run an unrelated control PR on the same base** before blaming a diff. If the control fails
   the same way, the PR is not the cause.
3. **Check the upstream trackers** (Playwright and the browser engine) for the crash or error
   signature and the pinned browser build, before designing a test-side change. Report a match
   at once.
4. **Put the waited-on state in the failure message** (see `expect.poll` above), so the next
   failure explains itself.
5. **Reproduce under load with a no-feature control:** the same constrained run with the
   feature stubbed. If the control fails too, the fault is in the test or harness.
6. **Size N from the failure rate.** A test still failing at rate p passes about 3/p runs in a
   row only 5% of the time; three passes at p = 0.5 happen 1 time in 8 with no fix. Re-runs of
   one CI run reuse its commit and merge ref, so they are not independent and miss everything
   merged since. Count runs on a merge ref that includes the current base.
7. **Quarantine within one round** when no confirmed fix is in reach: `test.fixme` with an
   issue link, a note naming the guard that is now off, and a narrower deterministic interim
   test. Restore only after N green CI runs on the current merge ref with diagnostics on; if
   any fail, keep the quarantine.
8. **"Not reproduced, no fix claimed" is an acceptable outcome.** Report it with the evidence
   instead of shipping a guessed fix. Label an unreproduced diagnosis "inferred".

## Tests Written Ahead of Features

Tests can land before their feature as `test.fixme`, which Playwright does not run past the
`fixme` call.

- **One enable toggle per scenario ID,** so a feature PR switches on exactly its own tests.
  Decide this before the first test PR lands.
- **Ship an activation audit** with the tests: removing one toggle enables exactly one case
  per project.
- **Validate against the feature branch** in a throwaway merge (never committed) and against
  plain main. Report both results with their SHAs.
- **Run a forced-on pass** with every toggle lifted, and classify each failure as "feature
  missing" or "test wrong". Repeat it against the feature PR before it merges.
- **An un-fixme PR reports passed and skipped counts before and after.** The run count must
  rise by the expected number.
- **Parked tests protect nothing.** Before merging a shared CSS or behaviour change, un-park
  the in-flight PRs' dependent scenarios in a scratch run. When removing skips, run against
  current main, not the author's old base.

## Smoke Tests That Gate a Rollback

When a post-deploy smoke failure triggers a rollback, every false failure rolls back a good
release.

- **Tell the author that any failure triggers a rollback.**
- **Assert invariants only.** Handle every legitimate state: sold out, maintenance, a
  redirected host. Derive expectations from live responses, and allowlist a host only after a
  real run has shown it.
- **Separate "smoke infrastructure failed" from "release failed".** A stalled browser install,
  runner network loss or harness crash must not roll back. Install timeouts and retries are in
  [autonomous-loops](../../autonomous-loops/SKILL.md).
- **Pair every "absent" assertion with an existence check** (SKILL.md Common Pitfalls).
- Ordering a check change against the behaviour change it checks is release policy:
  [agent-orchestration](../../agent-orchestration/SKILL.md).

## Secrets in Artifacts

Error messages, call logs, error-context files, traces (DOM snapshots and network),
screenshots, videos and every report can carry a secret. In 1.63 a failed locator assertion's
call log quotes the resolved element's markup, attribute values included (observed; the docs
don't say).

- **Redact the message, the stack and reporter output,** not only the final thrown error. Step
  records keep the original text.
- **Prove the redaction with a planted marker:** put a unique fake secret where the real one
  would be, force a failure, and grep every artifact (`test-results/`, the report, unzipped
  traces) for it. First confirm the scan catches a deliberate leak.
- **Keep real secrets out of the test build's DOM and URLs** where possible. Redaction is the
  second line of defence.

## Parallel Agents on One Host

Several agents or checkouts running suites on one machine interfere in ways that look like
flakes.

- **A port per agent, from an environment variable** (the SKILL.md config reads `E2E_PORT`).
  With a shared port, `reuseExistingServer` silently tests another checkout's build.
- **An output directory per run:** `--output <dir>`, plus `PLAYWRIGHT_HTML_OUTPUT_DIR` for the
  report. Playwright cleans `outputDir` at the start of a run, so two runs sharing it delete
  each other's artifacts.
- **Keep test output outside lint, typecheck and format globs,** or add it to their ignore
  files once.
- **Cap workers per run** (`--workers=2`). The default is half the logical cores per run, so
  concurrent suites oversubscribe the host. Cap concurrent browser suites by CPU count.
- **A run whose server died or was killed is invalid, not failed.** Rerun it and report it
  apart from real failures.
- `TMPDIR` on disk, stopping servers by PID and the other shared-machine rules are in the
  standing block of [agent-briefs](../../agent-briefs/SKILL.md).
