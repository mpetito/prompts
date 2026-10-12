# checkout-totals: show tax and shipping separately in the order summary

Worktree: ../storefront-wt-checkout-totals, branch `lane/checkout-totals`.
This build runs three lanes at once on this machine: checkout-totals (you), search-filters and
account-settings, each in its own worktree of the same repository.

Changes:
1. `src/checkout/OrderSummary.tsx`: separate tax and shipping lines.
2. `tests/checkout-totals.spec.ts`: E2E test for the new lines.

Must hold before the first push: `npm test` and the E2E suite pass on the committed tree.
Report: first line `STATUS: done|blocked|partial - <summary>`.
