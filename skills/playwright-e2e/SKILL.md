---
name: playwright-e2e
description: "Structure, write and run Playwright end-to-end tests that stay independent under parallel workers and on a machine shared with other agents: the project's conventions for where tests live and how they get server-side data, page objects and fixtures, serial chains, and ports, workers and output folders per checkout. Use when writing, reviewing or running Playwright or other browser E2E tests, adding a page object or fixture, deciding how tests get their data, or when a browser test is flaky or passes only alone. Not for unit or component tests without a browser, or for driving a browser by hand to inspect a page."
---

# Playwright E2E

Role: worker. Loaded by a session, lane or subagent that writes or runs a Playwright suite.

Where this file and the Playwright docs (best practices, parallelism, fixtures, authentication)
disagree, the docs win; say so in your report.

## 1. Find the conventions first

Read the config, any fixtures file (`test.extend`), the setup project and a few specs before
writing. Follow what is settled. For each of these the project hasn't settled, name it in your
report as a convention for the owner to choose, with the options and your default, and write the
test on the default; never settle it silently inside one test:

- **How a test gets server-side data.** Options: each test creates its own records through the
  app's API with unique names; one account per worker (a worker fixture keyed on
  `parallelIndex`); a fresh database or tenant per run. Seeding once and sharing works only while
  no test writes.
- **Where the suite lives.** Default: its own package (`e2e/` or `packages/e2e/`).

## 2. Structure

- **Specs** say what the user does and what must hold; **page and component objects** say where
  things are and how to work them; **fixtures** say what world a test starts in (signed in, a
  seeded record). Group specs by feature, not by shared setup.
- Page objects and setup reach tests as fixtures from the project's `test.extend`; import `test`
  and `expect` from that file.
- A page object exposes locators and actions. Assert on its locators with web-first assertions
  (`await expect(locator).toHaveText(…)`), never on a value a method read once.
- Locate by role with the accessible name imported from the content source, then by test id
  (code-style rule 7); never by CSS or XPath.

## 3. Every test stands alone

A test passes alone, in any order, and beside any other test on another worker.

- **Never add to a serial chain.** In a file with `mode: 'serial'` or tests that pass state
  through shared variables, a failure skips every later test. Set your test's state up through the
  API or a fixture, and put it where the chain can't skip it: its own file or a group outside the
  serial one. Report the chain as a follow-up; don't rewrite it unasked.
- **Data a test changes is data only it sees.** Never change records another test reads, and never
  assert an exact list over data other tests add to.
- Never fix a flake with `workers: 1`, serial mode, retries or `waitForTimeout`.

## 4. Running on a shared machine

Other agents and checkouts run suites on this machine at the same time.

- **A port per checkout,** read from an environment variable (`E2E_PORT`) for both
  `webServer.url` and `baseURL`, with `reuseExistingServer` off for it: on a shared port, reuse
  silently tests another checkout's build.
- **Cap workers on every run** (`--workers=2`, or the brief's number). The default is half the
  logical cores per run, so concurrent suites oversubscribe the machine and time out like flakes.
- Two runs in one checkout need their own `--output` and `PLAYWRIGHT_HTML_OUTPUT_DIR`: Playwright
  empties the output folder at the start of each run.
- Stop a server you started by its PID, never by name or port. A run whose server died is invalid,
  not failed: rerun it.

## 5. Before you report

Run each new or changed test with `--repeat-each=5 --retries=0` on every project, workers capped.
Flake triage, CI artifacts, tests written ahead of a feature, smoke tests that gate a rollback and
secrets in traces are in [references/stability.md](references/stability.md).
