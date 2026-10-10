# Model council: state after round 1

Scratch directory: /tmp/council-7f3a (absolute paths; the packet and answers are below).
Requested by the main session: "Copilot flagged the catalogue cache key as a cross-tenant leak. I
traced it and still can't tell. Get Claude and Codex on it; I'm waiting, so give me a
recommendation as soon as you have one."

## Packet (both members received this, pinned at head 9c41e07)

Question: does `src/cache/catalog-cache.ts` leak one tenant's catalogue to another, and what should
change? Candidate actions: no change; add the tenant id to the cache key; something else.

- `src/cache/catalog-cache.ts:42`: `const key = \`catalog:${sku}\`;`
- `src/app.ts:17`: `app.use(withTenant(cacheClient));`
- `src/middleware/with-tenant.ts:9-14`: `withTenant` returns a client whose `get` and `set` prefix
  every key with `t:${req.tenantId}:`, unless the request sets `req.skipTenant`.
- `src/jobs/warm-catalog.ts:21`: the nightly warm-up job calls `catalogCache.set(...)` with a raw
  `cacheClient`, not through a request.
- Tests: `catalog-cache.test.ts` passes (single tenant only).

## Members

- Claude: subagent, model opus, effort high; focus correctness and contract.
- Codex: `codex-member.sh`, model gpt-6-astra, effort high; focus simplicity and maintenance.
  Printed: `MEMBER done member=codex model=gpt-6-astra session=0199c2f1-6a40-7d11-9e2b-5d0b8e1f4c77 stance=initial disposition=false-positive out=/tmp/council-7f3a/round0-codex.md`

## /tmp/council-7f3a/round0-claude.md

The key at catalog-cache.ts:42 carries only the SKU. Request traffic is protected because
`withTenant` prefixes keys, but the warm-up job at warm-catalog.ts:21 writes through the raw
client, so warmed entries land at `catalog:<sku>` with no tenant prefix. Whether a request can
then read them depends on whether any request path sets `skipTenant`; I could not find one in the
packet, but I also could not rule it out. The cheapest defence is a key that names the tenant.

stance: initial
disposition: defect
action: add the tenant id to the key at src/cache/catalog-cache.ts:42
decisive: src/jobs/warm-catalog.ts:21
crux: whether any request path can read an unprefixed key

## /tmp/council-7f3a/round0-codex.md

Every request goes through `withTenant` (app.ts:17), which prefixes keys with the tenant id
(with-tenant.ts:9-14), so request reads are tenant-scoped. The warm-up job writes unprefixed keys,
but requests never read unprefixed keys, so those entries are dead weight, not a leak. Adding the
tenant id to the key would double-prefix every request key and break the warm-up job's purpose.

stance: initial
disposition: false-positive
action: no change
decisive: src/middleware/with-tenant.ts:9-14
crux: whether any request sets req.skipTenant
