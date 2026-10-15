# Review request: localised amounts in the invoice email

Repository: `billing-service` (TypeScript, Node 22). Branch `feature/invoice-email-currency`, head
`e19c4a7`, base `main`. Staged change, not yet pushed. The repository is internal; nothing in it is
published as a package.

## Author's description

> Invoice emails showed every amount as US dollars ("$1234.50") even for EUR customers. This adds a
> small `formatCents` helper next to the email code and uses it for the line items and the total,
> in the customer's locale. 8 tests pass.

## Diff

```diff
--- /dev/null
+++ b/src/billing/formatCents.ts
@@ -0,0 +1,6 @@
+// Format an amount held in the currency's smallest unit, e.g. 123450 + "EUR" + "de-DE" -> "1.234,50 €".
+export function formatCents(cents: number, currency: string, locale: string): string {
+  const nf = new Intl.NumberFormat(locale, { style: "currency", currency });
+  const scale = 10 ** (nf.resolvedOptions().maximumFractionDigits ?? 2);
+  return nf.format(cents / scale);
+}
--- a/src/billing/invoiceEmail.ts
+++ b/src/billing/invoiceEmail.ts
@@ -1,6 +1,6 @@
 import { Invoice } from "./types";
 import { renderTemplate } from "../mail/templates";
-import { legacyPrice } from "./legacyPrice";
+import { formatCents } from "./formatCents";
 
 export function invoiceEmail(invoice: Invoice): string {
   const { customer, lines, totalCents, currency } = invoice;
@@ -8,9 +8,9 @@ export function invoiceEmail(invoice: Invoice): string {
     greeting: `Hello ${customer.name},`,
     lines: lines.map((l) => ({
       description: l.description,
-      amount: legacyPrice(l.amountCents / 100),
+      amount: formatCents(l.amountCents, currency, customer.locale),
     })),
-    total: legacyPrice(totalCents / 100),
+    total: formatCents(totalCents, currency, customer.locale),
     locale: customer.locale,
   });
 }
--- /dev/null
+++ b/test/billing/formatCents.test.ts
@@ -0,0 +1,17 @@
+import { formatCents } from "../../src/billing/formatCents";
+
+test("formats USD in en-US", () => {
+  expect(formatCents(123450, "USD", "en-US")).toBe("$1,234.50");
+});
+
+test("formats EUR in de-DE", () => {
+  expect(formatCents(123450, "EUR", "de-DE")).toBe("1.234,50 €");
+});
+
+test("formats JPY, which has no minor unit", () => {
+  expect(formatCents(123450, "JPY", "en-US")).toBe("¥123,450");
+});
+
+test("formats zero", () => {
+  expect(formatCents(0, "USD", "en-US")).toBe("$0.00");
+});
```

## Test log

```text
PASS test/billing/formatCents.test.ts (4 tests)
PASS test/billing/invoiceEmail.test.ts (2 tests)
PASS test/billing/legacyPrice.test.ts (2 tests)
Tests: 8 passed, 8 total
```

## Repository context (files this change does not touch)

### Tree

```text
billing-service/
  src/billing/invoiceEmail.ts
  src/billing/legacyPrice.ts
  src/billing/types.ts
  src/mail/templates.ts
  src/shared/http/retry.ts
  src/shared/ids.ts
  src/shared/text/labels.ts
  src/web/receiptPage.tsx
  src/web/statementPage.tsx
  test/billing/invoiceEmail.test.ts
  test/billing/legacyPrice.test.ts
  test/shared/text/labels.test.ts
```

### Imports on `main` (before this change)

| Module | Imported by |
| --- | --- |
| `src/billing/legacyPrice.ts` | `src/billing/invoiceEmail.ts`, `test/billing/legacyPrice.test.ts` |
| `src/billing/types.ts` | `src/billing/invoiceEmail.ts`, `src/web/receiptPage.tsx`, `src/web/statementPage.tsx` |
| `src/mail/templates.ts` | `src/billing/invoiceEmail.ts` |
| `src/shared/http/retry.ts` | `src/mail/templates.ts` |
| `src/shared/ids.ts` | `src/web/receiptPage.tsx`, `src/web/statementPage.tsx` |
| `src/shared/text/labels.ts` | `src/web/receiptPage.tsx`, `src/web/statementPage.tsx`, `test/shared/text/labels.test.ts` |

### src/billing/legacyPrice.ts

```ts
// Price label.
export function legacyPrice(dollars: number): string {
  return "$" + dollars.toFixed(2);
}
```

### src/shared/http/retry.ts

```ts
// Retry an idempotent request on network errors and 5xx, with jittered backoff.
export async function retryIdempotent<T>(fn: () => Promise<T>, attempts = 3): Promise<T> {
  /* 18 lines, unchanged */
}
```

### src/shared/ids.ts

```ts
// Public ids: a prefix and a random suffix, e.g. inv_8f2k1.
export function publicId(prefix: string): string {
  /* 6 lines, unchanged */
}
```

### src/shared/text/labels.ts

```ts
// Short display labels for the web pages.

export function dateLabel(d: Date, locale: string, timeZone: string): string {
  return new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeZone }).format(d);
}

export function moneyLabel(minor: number, currency: string, locale: string): string {
  const fmt = new Intl.NumberFormat(locale, { style: "currency", currency });
  const digits = fmt.resolvedOptions().maximumFractionDigits ?? 2;
  return fmt.format(minor / 10 ** digits);
}

export function countLabel(n: number, singular: string, plural: string): string {
  return `${n} ${n === 1 ? singular : plural}`;
}
```
