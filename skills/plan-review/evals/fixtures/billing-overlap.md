# Plan: annual billing (for approval)

Owner's words: "I want customers to be able to pay yearly with a discount. Show me something I
can click by Friday."

## Workstreams

- **A. billing-api:** add annual plans. Edits `src/billing/invoice.ts` and `src/billing/plans.ts`.
- **B. proration:** prorate upgrades from monthly to annual. Edits `src/billing/invoice.ts` and
  `src/billing/proration.ts`.
- **C. pricing-page:** the monthly/annual toggle on the public pricing page. Scheduled last, after
  A, B and D.
- **D. tax-report:** an annual revenue-recognition report for finance.

## Notes

- Stripe automatically prorates annual upgrades, so B is mostly configuration.
- The annual discount is 20% for now; the owner hasn't decided between 15% and 20%.

## Acceptance

- Billing works.
