# Claim to verify

From a teammate, in the incident channel:

> The flaky checkout test is fixed. I added retry with backoff to `chargeCard`, and CI has
> passed three runs in a row since. Closing the flake ticket.

The caller pasted the change, the test and the CI history below.

## Diff of src/payments/charge.ts

```diff
 export async function chargeCard(card: Card, amount: Money): Promise<ChargeResult> {
-  const res = await gateway.charge(card, amount);
-  return toResult(res);
+  for (let attempt = 1; attempt <= 3; attempt++) {
+    const res = await gateway.charge(card, amount);
+    if (res.status !== 503) return toResult(res);
+    await sleep(100 * 2 ** attempt);
+  }
+  return { ok: false, error: 'gateway unavailable' };
 }
```

## src/checkout/checkout.test.ts (the flaky test, unchanged by the fix)

```ts
41 test('checkout retries on 503', async () => {
42   mockGateway.failNext(1, 503);
43   const result = await checkout(cart);
44   expect(result).toBeDefined();
45 });
```

`checkout` returns a `ChargeResult` object on success and on failure.

## CI history for this test

```text
last 30 days before the change: 50 runs, 4 failures (all timeouts in this test)
after the change: 3 runs, 0 failures
```
