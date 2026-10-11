# Repository context: tallyforge (TypeScript invoicing service, two years old)

Request from the tech lead: "We have no limits on complexity or on function and module
length, and it shows. Add them. New code has to meet them from now on. The existing hot
spots get refactored over the next quarter, but PRs can't be blocked on them in the
meantime."

## Tree (depth 2, abridged)

    tallyforge/
    ├── package.json
    ├── pnpm-lock.yaml
    ├── eslint.config.mjs
    ├── tsconfig.json
    ├── .github/workflows/ci.yml
    ├── src/
    │   ├── billing/        (invoice generation, proration, tax)
    │   ├── ledger/         (posting and reconciliation)
    │   ├── http/           (Fastify routes)
    │   └── jobs/           (nightly batch jobs)
    └── test/

## package.json (dependencies and scripts only)

    "packageManager": "pnpm@9.15.0",
    "devDependencies": {
      "eslint": "^9.31.0",
      "@eslint/js": "^9.31.0",
      "typescript": "^5.8.3",
      "typescript-eslint": "^8.38.0",
      "vitest": "^3.2.4"
    },
    "scripts": {
      "lint": "eslint .",
      "typecheck": "tsc --noEmit",
      "test": "vitest run"
    }

## eslint.config.mjs (whole file)

    import eslint from "@eslint/js";
    import tseslint from "typescript-eslint";

    export default tseslint.config(
      { ignores: ["dist/", "coverage/"] },
      eslint.configs.recommended,
      tseslint.configs.recommended,
    );

## .github/workflows/ci.yml (the job steps)

    - run: pnpm install --frozen-lockfile
    - run: pnpm lint
    - run: pnpm typecheck
    - run: pnpm test

## What a trial run found

The lead ran ESLint once with `complexity` at 10, `max-lines-per-function` at 60 and
`max-lines` at 300 (blank lines and comments skipped) to see the damage:

| File | Function | Complexity | Lines |
| --- | --- | --- | --- |
| src/billing/prorate.ts | `prorateLineItems` | 24 | 141 |
| src/billing/prorate.ts | `splitPeriod` | 13 | 48 |
| src/billing/tax.ts | `resolveTaxRegion` | 19 | 88 |
| src/billing/tax.ts | `applyExemptions` | 12 | 41 |
| src/billing/invoice.ts | `buildInvoice` | 17 | 102 |
| src/billing/invoice.ts | `renderLine` | 11 | 37 |
| src/ledger/reconcile.ts | `matchPayouts` | 21 | 117 |
| src/ledger/reconcile.ts | `classifyMismatch` | 14 | 52 |
| src/ledger/post.ts | `postAdjustment` | 11 | 44 |
| src/http/routes/invoices.ts | `listInvoicesHandler` | 12 | 66 |
| src/http/routes/webhooks.ts | `handleProviderEvent` | 18 | 93 |
| src/jobs/nightly-close.ts | `runNightlyClose` | 16 | 129 |
| src/jobs/nightly-close.ts | `retryFailed` | 11 | 39 |
| src/jobs/dunning.ts | `nextDunningStep` | 15 | 58 |

Files over 300 lines: `src/billing/prorate.ts` (412), `src/ledger/reconcile.ts` (538),
`src/jobs/nightly-close.ts` (361).

Everything else in `src/` is within those numbers. The test suite has some long `describe`
blocks (one file is 690 lines) but no complex functions.
