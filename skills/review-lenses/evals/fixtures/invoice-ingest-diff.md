# Review request: ingest invoice events from the billing provider

Repository: `invoice-sync` (TypeScript, Node 22, Express). Branch `feature/invoice-events`, head
`5d2b81e`, base `main`. Staged change, not yet pushed.

## Author's description

> Consumes `invoice.issued` events from the billing provider's queue, works out the due date from
> the payment terms, and forwards the invoice to the ledger service, retrying when the ledger is
> briefly down. Kept it dependency-free so it's easy to read. 9 tests pass.

## Diff

```diff
--- /dev/null
+++ b/src/ingest/envelope.ts
@@ -0,0 +1,21 @@
+export interface Envelope {
+  id: string;
+  type: string;
+  occurredAt: string;
+  data: { invoiceId: string; amountCents: number; currency: string; issuedAt: string; termsMonths: number };
+}
+
+export function isEnvelope(x: any): x is Envelope {
+  return (
+    x !== null &&
+    typeof x === "object" &&
+    typeof x.id === "string" &&
+    typeof x.type === "string" &&
+    typeof x.occurredAt === "string" &&
+    typeof x.data === "object" &&
+    typeof x.data.invoiceId === "string" &&
+    typeof x.data.amountCents === "number" &&
+    typeof x.data.currency === "string" &&
+    typeof x.data.issuedAt === "string"
+  );
+}
--- /dev/null
+++ b/src/ingest/dueDate.ts
@@ -0,0 +1,8 @@
+// Due date = issue date plus the payment terms, in calendar months.
+export function shiftMonths(d: Date, months: number): Date {
+  return new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + months, d.getUTCDate()));
+}
+
+export function daysUntil(due: Date, now: Date): number {
+  return Math.round((due.getTime() - now.getTime()) / 86_400_000);
+}
--- /dev/null
+++ b/src/ingest/backoff.ts
@@ -0,0 +1,14 @@
+const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
+
+export async function withBackoff<T>(fn: () => Promise<T>, attempts = 5): Promise<T> {
+  let lastError: unknown;
+  for (let i = 0; i < attempts; i++) {
+    try {
+      return await fn();
+    } catch (e) {
+      lastError = e;
+      await sleep(200 * 2 ** i);
+    }
+  }
+  throw lastError;
+}
--- /dev/null
+++ b/src/ingest/handleInvoiceIssued.ts
@@ -0,0 +1,17 @@
+import { isEnvelope } from "./envelope";
+import { shiftMonths } from "./dueDate";
+import { withBackoff } from "./backoff";
+import { ledger } from "../clients/ledger";
+import { log } from "../log";
+
+export async function handleInvoiceIssued(raw: unknown): Promise<void> {
+  if (!isEnvelope(raw) || raw.type !== "invoice.issued") {
+    log.warn({ raw }, "dropping malformed invoice event");
+    return;
+  }
+  const { invoiceId, amountCents, currency, issuedAt, termsMonths } = raw.data;
+  const due = shiftMonths(new Date(issuedAt), termsMonths);
+  await withBackoff(() =>
+    ledger.post("/invoices", { invoiceId, amountCents, currency, dueDate: due.toISOString() }),
+  );
+}
--- /dev/null
+++ b/test/ingest/dueDate.test.ts
@@ -0,0 +1,13 @@
+import { shiftMonths, daysUntil } from "../../src/ingest/dueDate";
+
+test("adds one month", () => {
+  expect(shiftMonths(new Date("2026-01-15T00:00:00Z"), 1).toISOString()).toBe("2026-02-15T00:00:00.000Z");
+});
+
+test("adds three months", () => {
+  expect(shiftMonths(new Date("2026-03-10T00:00:00Z"), 3).toISOString()).toBe("2026-06-10T00:00:00.000Z");
+});
+
+test("days until due", () => {
+  expect(daysUntil(new Date("2026-02-15T00:00:00Z"), new Date("2026-02-01T00:00:00Z"))).toBe(14);
+});
```

The other six tests cover `isEnvelope` on a valid event and on five events with one field missing.

## package.json (unchanged by this diff)

```json
{
  "name": "invoice-sync",
  "private": true,
  "type": "module",
  "engines": { "node": ">=22" },
  "dependencies": {
    "date-fns": "^3.6.0",
    "express": "^4.21.1",
    "pino": "^9.5.0",
    "zod": "^3.23.8"
  },
  "devDependencies": {
    "@types/express": "^5.0.0",
    "jest": "^29.7.0",
    "ts-jest": "^29.2.5",
    "typescript": "^5.6.3"
  }
}
```

## Test log

```text
PASS test/ingest/envelope.test.ts (6 tests)
PASS test/ingest/dueDate.test.ts (3 tests)
Tests: 9 passed, 9 total
```
