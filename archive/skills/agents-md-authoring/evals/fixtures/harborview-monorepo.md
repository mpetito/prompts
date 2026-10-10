# Repository context: harborview (pnpm monorepo + one Python service)

The team uses both Claude Code and GitHub Copilot in this repo. The current agent
instructions are one big root file that nobody trusts. The lead wants it fixed.

## Tree (depth 3, abridged)

    harborview/
    ├── AGENTS.md                 (430 lines, see outline below)
    ├── README.md                 (architecture, product overview, deploy guide)
    ├── package.json              (pnpm workspaces: packages/*)
    ├── pnpm-lock.yaml
    ├── packages/
    │   ├── web/                  (Next.js app; same TS/lint/test setup as root)
    │   ├── api/                  (Fastify API; same TS/lint/test setup as root)
    │   │   └── AGENTS.md         (6 lines, see below)
    │   └── sdk/
    │       ├── src/
    │       └── generated/        (OpenAPI client, rewritten by `pnpm --filter sdk gen`)
    └── services/
        └── scoring/              (Python 3.12 risk-scoring service)
            ├── pyproject.toml    (uv, pytest, ruff, mypy --strict)
            └── uv.lock

## Root commands (verified this morning by the lead)

    pnpm install --frozen-lockfile
    pnpm -r test            # vitest in every TS package
    pnpm -r typecheck       # tsc --noEmit
    pnpm lint               # eslint . --max-warnings 0
    pnpm --filter sdk gen   # regenerates packages/sdk/generated from openapi.yaml

## services/scoring commands (verified)

    uv sync
    uv run pytest -q
    uv run ruff check . && uv run ruff format --check .
    uv run mypy --strict src

Python conventions differ from the TS packages: snake_case modules, dataclasses not
pydantic for internal types, no network calls in tests (use `tests/fakes/`).

## Outline of the current root AGENTS.md (430 lines)

1. "Project Overview" (60 lines copied from README: product pitch, customers, history)
2. "Architecture" (90 lines copied from README, with diagrams)
3. "Coding Philosophy": "Write clean code. Follow SOLID and best practices. Be thoughtful."
4. TypeScript rules (40 lines): strict mode, no `any`, zod at API edges, named exports
5. Python rules for services/scoring (70 lines, including how to install Python)
6. "Explaining React hooks for new contributors" (50 lines)
7. Commands (still lists `npm test` and `npm run build`; the repo moved to pnpm)
8. Deploy guide (80 lines copied from README)
9. One line at the very end: "don't touch generated code"

## Current packages/api/AGENTS.md (all 6 lines)

    # API agent notes
    - Run tests with `npm test`.
    - Install with `npm install`.
    - Use named exports.
    - Validate request bodies with zod.
    - Use strict mode; never use `any`.

## Facts the lead wants agents to respect

- Never edit `packages/sdk/generated/`; change `openapi.yaml` and regenerate.
- Never add a dependency without asking; the lockfile is reviewed by security.
- Do not commit `.env*` files; local secrets live in `.env.local` (gitignored).
- Python tests must never reach the network.
