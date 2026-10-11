# Repository context: parcelpost (TypeScript shipping-label API, Claude Code only so far)

Request from the lead: "Everyone here uses Claude Code and the repo has a good CLAUDE.md.
We're adding Codex for background tasks, and we're turning on GitHub Copilot code review
for every PR. Make this repo work for Codex and Copilot too."

## Tree (depth 2, abridged)

    parcelpost/
    ├── CLAUDE.md              (180 lines, outline below)
    ├── README.md              (product overview, local setup)
    ├── package.json
    ├── pnpm-lock.yaml
    ├── .claude/
    │   ├── settings.json      (hook: runs `pnpm prettier --write` on every edited file)
    │   └── commands/
    │       └── release-notes.md
    ├── src/
    │   ├── carriers/          (one adapter per carrier: ups, fedex, dhl)
    │   ├── labels/            (label rendering, PDF and ZPL)
    │   ├── tenancy/           (tenant scoping)
    │   └── generated/         (carrier API clients, written by `pnpm codegen`)
    └── test/

There is no AGENTS.md and no `.github/copilot-instructions.md`.

## Outline of the current CLAUDE.md (180 lines)

1. "Commands" (12 lines):

        pnpm install --frozen-lockfile
        pnpm test               # vitest, unit only
        pnpm test:contract      # carrier sandbox contract tests; needs CARRIER_SANDBOX=1
        pnpm typecheck
        pnpm lint               # eslint . --max-warnings 0
        pnpm codegen            # regenerates src/generated/ from carriers/*.openapi.yaml

2. "Where things live" (20 lines): the folder notes in the tree above, in more detail.
3. "Rules" (60 lines), the ones that matter:
   - Every database query goes through `withTenantScope(tenantId, fn)`; a query without it
     leaks another tenant's labels.
   - Weights are integer grams and dimensions integer millimetres; never floats.
   - A carrier adapter never throws a carrier's raw error; map it to `CarrierError` with a code.
   - Never edit `src/generated/`; change the OpenAPI file and run `pnpm codegen`.
   - Never add a dependency without asking.
4. "Claude Code notes" (14 lines):
   - The edit hook in `.claude/settings.json` formats files; do not run prettier yourself.
   - Use `/release-notes` (in `.claude/commands/`) to draft release notes from merged PRs.
   - Use plan mode before touching `src/tenancy/`.
5. "Testing" (30 lines): fixtures in `test/fixtures/`, how to record a carrier sandbox
   cassette, never hit a live carrier API in tests.
6. "Do Not" (12 lines): the never-rules from section 3 again, as a list.
7. "PR checklist" (32 lines): what a reviewer should check on a PR — tenant scoping on new
   queries, unit handling, error mapping in adapters, a contract test for any new carrier
   endpoint, no edits under `src/generated/`.

## Things the team has noticed on another repo with Copilot review on

- Copilot left 30 comments on one PR; the author said most of them were noise.
- Someone suggested turning Copilot review off again.
