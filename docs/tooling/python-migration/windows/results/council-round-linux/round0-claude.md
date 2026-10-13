## Findings

**The problem is real.** Nothing in the repo prevents it.

1. **The key leaves out the tenant.** `cache_key` takes `tenant_id` but never uses it: it returns `f"{user_id}:{resource}"` (`cache.py:5-6`). `get` passes `tenant_id` in (`cache.py:10`), and that argument is the only tenant information `get` has. It is then thrown away.

2. **The store is shared across tenants.** The module docstring says so directly: "one process-wide dict shared by every tenant" (`cache.py:1`). `_cache` is a module global (`cache.py:2`). Nothing in either file clears it, partitions it, or expires entries. The word "per-request" in the docstring might suggest a reset per request, but no code does one.

3. **User ids repeat across tenants.** `users.py:1` says "every tenant's first user is 1". `next_user_id` increments a counter stored on each tenant object (`users.py:4-6`). So tenant A's user 1 and tenant B's user 1 both produce the key `"1:<resource>"`.

4. **The failure path.** Tenant A calls `get("A", 1, "profile", loadA)`. The entry is stored under `"1:profile"` (`cache.py:11-12`). Tenant B then calls `get("B", 1, "profile", loadB)`. The key is already present, so `loadB` never runs and B receives A's data (`cache.py:13`). This is a cross-tenant read, as the reviewer said.

**Is there a guard that refutes it?** I looked for one and found none: no tenant prefix in callers, no namespacing, no assertion, no test. The tracked files are only `cache.py` and `users.py`.

## Strongest evidence against my conclusion

- **No callers.** Nothing in the repo calls `get` or `cache_key`. I could not trace a real call site, so I can't show that callers pass a `user_id` from `next_user_id`, or that they don't add a tenant prefix to `resource` themselves.
  - That is the crux. If every caller already scoped `resource` by tenant, the cache would be safe today, though only by convention.
  - Even so, `get`'s signature accepts `tenant_id` explicitly. A caller would reasonably expect the cache to use it. Ignoring it breaks the function's evident contract, so the defect remains.
- **Unverified starting value.** The "first user is 1" claim depends on `last_user_id` starting at 0. That is set wherever tenants are created, which isn't in the repo. I rely on the docstring at `users.py:1` for it.
- **Nothing was run.** No tests exist and I executed nothing; this conclusion comes from reading the code only.

## Is the fix worth its complexity?

Yes. It is a one-line change that uses an argument the function already receives: `return f"{tenant_id}:{user_id}:{resource}"`.

A tuple key, `(tenant_id, user_id, resource)`, would also avoid ambiguity if an id or resource ever contains `:`. Either way, there is no new mechanism.

Leaving it as is means a cross-tenant data leak, and that cost far outweighs the change.

stance: initial
disposition: defect
action: change cache_key in cache.py:6 to include tenant_id, e.g. return f"{tenant_id}:{user_id}:{resource}"
decisive: cache.py:6
crux: That user_id values collide across tenants in the shared process-wide _cache (users.py:1 "every tenant's first user is 1"); if user ids were globally unique, the key would not leak across tenants.
