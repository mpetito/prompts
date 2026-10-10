# Review request: customer endpoints for the partner apps

Repository: `<crm-api>` (TypeScript, Express, Prisma, date-fns). Branch `feature/partner-customer`,
head `a4e91f0`, base `main`. The PR is open; CI is green on this head.

## Author's description

> Adds two read-only endpoints so the partner's mobile apps can show a customer's profile and
> order history. Done properly this time: versioned under `/v1`, public `cus_`/`ord_` IDs instead
> of database keys, the shared error envelope, integer cents instead of float dollars, and paging.
> The OpenAPI document below is what we've sent the partner. No writes, no auth changes: both
> routes sit behind the existing partner API key middleware and only see the partner's own
> customers. 18 tests pass, 100% line coverage on the new routes.

## Context from the ticket

> The partner (an external company) ships their iOS and Android apps next week. Their team
> generates Swift and Kotlin clients from our OpenAPI document. Changing a response after their
> release means coordinating app-store updates on their side, and old app versions stay installed
> for months.

## Teammate comment already on the PR

> Nice: versioned, public IDs, error envelope, cents. Much better than the internal API. LGTM.

## Diff

```diff
--- /dev/null
+++ b/src/routes/partner/customers.ts
@@ -0,0 +1,44 @@
+import { Router } from "express";
+import { format } from "date-fns";
+import { prisma } from "../../db";
+import { apiError } from "../../errors";
+
+export const partnerCustomers = Router();
+
+const PAGE_SIZE = 50;
+const STATUS = { A: "active", S: "suspended", X: "closed" } as const;
+const timestamp = (d: Date) => format(d, "yyyy-MM-dd'T'HH:mm:ss");
+
+async function findCustomer(publicId: string, partnerId: bigint) {
+  return prisma.customer.findFirst({ where: { publicId, partnerId } });
+}
+
+partnerCustomers.get("/v1/customers/:id", async (req, res) => {
+  const c = await findCustomer(req.params.id, req.partner.id);
+  if (!c) return apiError(res, 404, "not_found", "No such customer");
+  res.json({
+    id: c.publicId,
+    status: STATUS[c.statusCd as keyof typeof STATUS],
+    name: c.name,
+    createdAt: timestamp(c.createdAt),
+  });
+});
+
+partnerCustomers.get("/v1/customers/:id/orders", async (req, res) => {
+  const c = await findCustomer(req.params.id, req.partner.id);
+  if (!c) return apiError(res, 404, "not_found", "No such customer");
+  const page = Math.max(1, Number(req.query.page) || 1);
+  const orders = await prisma.order.findMany({
+    where: { customerId: c.id },
+    orderBy: { createdAt: "desc" },
+    skip: (page - 1) * PAGE_SIZE,
+    take: PAGE_SIZE,
+  });
+  res.json(
+    orders.map((o) => ({
+      id: o.publicId,
+      totalCents: o.totalCents,
+      createdAt: timestamp(o.createdAt),
+    })),
+  );
+});
```

## OpenAPI document sent to the partner (excerpt)

```yaml
paths:
  /v1/customers/{id}:
    get:
      responses:
        "200": { content: { application/json: { schema: { $ref: "#/components/schemas/Customer" } } } }
        "404": { content: { application/json: { schema: { $ref: "#/components/schemas/Error" } } } }
  /v1/customers/{id}/orders:
    get:
      parameters:
        - { name: page, in: query, schema: { type: integer, minimum: 1, default: 1 } }
      responses:
        "200":
          content:
            application/json:
              schema: { type: array, items: { $ref: "#/components/schemas/Order" } }
        "404": { content: { application/json: { schema: { $ref: "#/components/schemas/Error" } } } }
components:
  schemas:
    Customer:
      type: object
      required: [id, status, name, createdAt]
      properties:
        id: { type: string, example: cus_8f3k2m }
        status: { type: string, enum: [active, suspended, closed] }
        name: { type: string }
        createdAt: { type: string, format: date-time }
    Order:
      type: object
      required: [id, totalCents, createdAt]
      properties:
        id: { type: string, example: ord_19xk2a }
        totalCents: { type: integer }
        createdAt: { type: string, format: date-time }
    Error:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
          properties:
            code: { type: string }
            message: { type: string }
```

## Prisma models the routes read (unchanged by this PR)

```prisma
model Customer {
  id        BigInt   @id @default(autoincrement())
  publicId  String   @unique
  partnerId BigInt
  statusCd  String   @db.Char(1)
  name      String
  createdAt DateTime @default(now()) @db.Timestamptz
  orders    Order[]
}

model Order {
  id         BigInt   @id @default(autoincrement())
  publicId   String   @unique
  customerId BigInt
  totalCents Int
  currency   String   @db.Char(3)
  createdAt  DateTime @default(now()) @db.Timestamptz
  customer   Customer @relation(fields: [customerId], references: [id])
}
```

## Other notes from the team channel

- Billing is adding `trial` and `past_due` customer statuses next quarter (new `statusCd` values).
- Customers with long histories have several thousand orders; new orders arrive all day.

## Validation output the author attached

```text
$ npx vitest run src/routes/partner
 ✓ src/routes/partner/customers.test.ts (18 tests) 0.74s
 Test Files  1 passed (1)
      Tests  18 passed (18)
 % Lines: 100 (src/routes/partner/customers.ts)
```
