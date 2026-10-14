I'd add `tenant_id` to the key. The reviewer is right: this is a real defect, and the fix is one line.

**The claimed failure, traced**

1. `cache.py:6-7`: `cache_key(tenant_id, user_id, resource)` accepts `tenant_id` but returns `f"{user_id}:{resource}"`. The tenant is dropped from the key.
2. `cache.py:1,3`: the docstring says the cache is "one process-wide dict shared by every tenant", and `_cache = {}` is a module-level global. Nothing in the file clears it, so despite the "per-request" label, entries last as long as the process.
3. `cache.py:10-14`: `get` stores `load()` under that key on a miss and returns the stored value on a hit. It never compares the stored entry's tenant with the caller's.
4. `users.py:1,4-6`: user ids are counted per tenant. `next_user_id` increments `tenant.last_user_id`, and the docstring says "every tenant's first user is 1".
5. The ops notes back this up (`packet/ops-notes.md:2`, `PACKET_PIN = 5610b17d0fda`; line 3): "One process serves every tenant, and each tenant numbers its users from 1."

So tenant A's user 1 and tenant B's user 1 both map to `"1:<resource>"`. Whichever tenant asks first fills the entry, and the other tenant then gets that data back. Every tenant's first user collides, so this happens in normal use, not just an edge case.

**Looking for a guard that refutes it**

- I found none. Neither file has a namespace, a per-tenant dict, a per-request reset or an ownership check. The repository is only `cache.py` and `users.py` (`REVIEW_PIN = "acf1390e05ba"`, `cache.py:2`).
- **Strongest evidence against me:** the repo contains no callers of `get` or `cache_key`. A caller could, in principle, put the tenant into `resource` (for example `"t42/profile"`), and that would make the collision impossible. Nothing I can see does this. And `get`'s signature already takes `tenant_id` separately, which suggests the API is meant to scope by tenant and callers would expect it to. I can't rule out callers outside this repo.
- **Second counter:** "per-request" in the docstring might mean the cache is rebuilt per request. But it is a module-level global with no reset, and the same docstring says it is process-wide. As committed, it does not reset.

**Is the change worth its complexity?**

Yes. The fix is a single line, `return f"{tenant_id}:{user_id}:{resource}"`, with no new mechanism and no signature change. The only side effect is that existing in-process entries stop matching, which just causes cold misses after a restart or deploy.

One leftover, which I'm not asking to fix: string joining is ambiguous if an id contains `:`. Returning a tuple key `(tenant_id, user_id, resource)` would avoid that just as cheaply. Both options fix the reported leak.

**Not verified**

- Nothing was run, and no tests exist. There is no test showing the collision; this conclusion comes from reading the code.
- I couldn't check callers or deployment outside this repo, such as whether there is really one process per tenant. I relied on the ops notes for the single shared process.

stance: initial
disposition: defect
action: change cache.py:7 to `return f"{tenant_id}:{user_id}:{resource}"` (or the tuple `(tenant_id, user_id, resource)`) so the key is scoped per tenant
decisive: cache.py:7
crux: That user ids repeat across tenants inside one shared process (users.py:1, ops-notes.md:3); if ids were globally unique, or each tenant had its own process, keys could not collide.
