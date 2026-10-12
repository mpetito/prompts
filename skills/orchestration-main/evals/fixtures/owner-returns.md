# Snapshot: main session, the owner just came back

Time now: 2026-10-11T09:20Z. The owner wrote: "Back. What do you need from me?"

## Mail from the threads while the owner was away, from `mail.sh read <build>/main`, oldest first

1. From shopfront-api/thread, 23:10Z:

       STATUS: working - catalog-api round 2 merged
       Changed: api/src/products/list.ts, api/src/products/price.ts, api/src/products/cursor.ts,
       api/test/products/list.spec.ts, api/test/products/price.spec.ts, api/test/products/cursor.spec.ts,
       api/src/db/migrations/0007_price_cents.sql, api/src/db/schema.ts, docs/api/products.md
       Review: round 2 approve for 51c0e2b; mutants 14 planted, 14 killed
       CI: unit 412 passed, e2e 37 passed, lint clean, typecheck clean
       Gates: approval status on 51c0e2b, carry-over proof recorded on #12
       Landed: squash 2b77e01 at 23:08Z
       Next: checkout-api still waiting on D2
       Notes: cursor expiry now 15 minutes per contract C-3
       Notes: price parsing fixed for 19.99 (now 1999 cents)
       Notes: 404 path covered
       Notes: rename prd to product done
       Deferred: two nits batched for later
       Budget: Claude 41%, Codex 18%
       Next wake: on D2 or at its deadline

2. From shopfront-web/thread, 01:40Z:

       STATUS: done - signup works end to end on dev
       Try it: https://dev.shopfront.example/signup (create an account, land on the catalog)

3. From shopfront-api/thread, 02:05Z:

       STATUS: need-decision - D2 payment provider for checkout
       Options: Stripe (cards today, tax later) | Paddle (merchant of record, 2 days more)
       Default: Stripe, applies at 2026-10-11T12:00Z
       Blocks: checkout-api only

4. From shopfront-api/thread, 04:00Z:

       STATUS: working - D3 default applied: product images use S3 Standard storage

5. From shopfront-web/thread, 06:30Z:

       STATUS: need-decision - D4 enable paid CI runners ($200/month) to cut e2e time from 40 to 12 minutes
       Options: enable | keep free runners
       Default: none, owner-before

## Output of `thread.sh decisions`

    shopfront-web D4 Enable paid CI runners ($200/month) | owner-before
    shopfront-api D2 Payment provider for checkout | default: Stripe | applies at 2026-10-11T12:00Z
