# Repository context: ledgerline (single-package TypeScript service)

Request from the tech lead: "Agents keep getting this repo wrong. Give us the root
instructions file. Use whatever below is useful."

## Tree (depth 2)

    ledgerline/
    ├── README.md            (212 lines, human onboarding)
    ├── CONTRIBUTING.md      (branch naming, PR template, review rules)
    ├── package.json
    ├── pnpm-lock.yaml
    ├── src/
    │   ├── settlement/      (settlement run orchestration)
    │   ├── ledger/          (posting rules, shadow ledger)
    │   ├── generated/       (Prisma client + OpenAPI types, written by codegen)
    │   └── theme/tokens.ts  (admin UI design tokens)
    └── tests/

## package.json (scripts and engines only)

    "packageManager": "pnpm@9.12.0",
    "scripts": {
      "dev": "tsx watch src/server.ts",
      "test:unit": "vitest run --project unit",
      "test:int": "vitest run --project integration",
      "typecheck": "tsc --noEmit",
      "lint": "eslint . --max-warnings 0",
      "codegen": "prisma generate && openapi-typescript openapi.yaml -o src/generated/api.ts",
      "db:migrate": "prisma migrate dev"
    }

`test:int` needs Postgres from `docker compose up -d db`; `test:unit` needs nothing.

## README.md excerpt

> Ledgerline began in 2021 as a hackathon project to replace spreadsheet-based
> month-end close. It now reconciles payouts for every merchant on the platform and
> is owned by the Payments Platform team.
>
> ### Getting started
> `yarn install && yarn dev` then open http://localhost:4100.
>
> ### Roadmap
> Multi-currency settlement (Q3), ledger snapshots (Q4), retiring the v1 export API.

Note from the lead: the README still says yarn; we moved to pnpm in 2025 and nobody
has updated it.

## Team wiki: "Engineering conventions" (copied verbatim)

- Write clean, maintainable code and follow best practices.
- All money is integer minor units (`amountMinor: bigint`); never use floats or `number`.
- Postings are immutable. Corrections are new reversing postings, never UPDATEs.
- Only a settlement run may write to the shadow ledger.
- A slip that fails validation goes to `slip_quarantine`, it is never dropped.
- Admin UI colours come from `src/theme/tokens.ts`.
- Be careful with the database.
- Files under `src/generated/` are overwritten by `pnpm codegen`.

## Slack thread excerpt (#ledgerline, last week)

> new hire: what's a slip vs a posting?
> lead: a slip is one provider-reported money movement before we post it.
> lead: the settlement run is the nightly job that nets a merchant's slips into one payout.
> new hire: and the shadow ledger?
> lead: a parallel ledger we dry-run the settlement run against before it commits.

## Things agents have done wrong recently

1. Used `parseFloat` on an amount and lost a cent on a large payout.
2. Hand-edited `src/generated/api.ts`; the next codegen wiped the change.
3. Ran `pnpm db:migrate` against the shared staging database from a laptop.
4. Added a new npm dependency for date formatting without asking.
