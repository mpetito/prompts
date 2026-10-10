# Review request: customer lookup endpoint for the partner app

Repository: `<crm-api>` (TypeScript, Express, Prisma). Branch `feature/partner-customer`, head
`a4e91f0`, base `main`. The PR is open; CI is green on this head.

## Author's description

> Adds a small read-only endpoint so the partner's mobile app can show a customer's profile and
> recent orders. Low risk: no writes, no auth changes (it sits behind the existing partner API
> key middleware). All 12 tests pass, 100% line coverage on the new route.

## Context from the ticket

> The partner (an external company) ships their mobile app next week. Their team will code
> against this response as-is; changing it after their release means coordinating an app-store
> update on their side.

## Teammate comment already on the PR

> LGTM. Read-only, tests green, coverage at 100%. Ship it.

## Diff

```diff
--- /dev/null
+++ b/src/routes/partner/customer.ts
@@ -0,0 +1,29 @@
+import { Router } from "express";
+import { prisma } from "../../db";
+
+export const partnerCustomer = Router();
+
+partnerCustomer.get("/api/customers/:customer_pk", async (req, res) => {
+  const row = await prisma.tbl_customer.findUnique({
+    where: { customer_pk: Number(req.params.customer_pk) },
+    include: { tbl_order: { orderBy: { created: "desc" } } },
+  });
+  if (!row) {
+    return res.status(404).send("Customer not found");
+  }
+  res.json({
+    customer_pk: row.customer_pk,
+    tbl_customer_status: row.status_cd,
+    name: row.name,
+    created: row.created.toLocaleString("en-US"),
+    orders: row.tbl_order.map((o) => ({
+      order_pk: o.order_pk,
+      total: o.total_cents / 100,
+      created: o.created.toLocaleString("en-US"),
+    })),
+  });
+});
```

`status_cd` holds single-letter internal codes (`A`, `S`, `X`) that the billing team plans to
replace with a status table next quarter. Customers have up to several thousand orders.

## Validation output the author attached

```text
$ npx vitest run src/routes/partner
 ✓ src/routes/partner/customer.test.ts (12 tests) 0.61s
 Test Files  1 passed (1)
      Tests  12 passed (12)
 % Lines: 100 (src/routes/partner/customer.ts)
```
