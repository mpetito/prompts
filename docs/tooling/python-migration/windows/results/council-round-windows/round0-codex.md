The defect is real at the cache boundary. `cache.py:7` ignores `tenant_id`, while user IDs restart within each tenant (`users.py:1,4–6`). The operations notes explicitly confirm that all tenants share one process (`D:/council-round-95d0007e/packet/ops-notes.md:3`).

Evidence pins: REVIEW_PIN = "acf1390e05ba" (`cache.py:2`); PACKET_PIN = 5610b17d0fda (`D:/council-round-95d0007e/packet/ops-notes.md:2`).

For tenants A and B, user 1 requesting the same resource produces the same key. Once A populates it, B receives A’s value and B’s loader never runs (`cache.py:11–14`). A read-only, in-memory probe confirmed: “tenant B received tenant A value; tenant B loader calls = 0.” The real harm is incorrect data returned across tenants, including disclosure if the cached value is private.

Adding the tenant prefix is a one-line change that follows the existing string-key convention (`cache.py:7`). Both reads and writes already use this helper, and its callers already supply `tenant_id`, so no additional plumbing is needed (`cache.py:6,10–14`). The in-memory candidate probe returned each tenant’s own value.

The strongest evidence against changing it is the “per-request” description (`cache.py:1`), which might suggest isolation through lifecycle management. However, the implementation provides a module-level dictionary and no clearing mechanism (`cache.py:3–14`), while the operations notes affirm process sharing. No caller code exists in the supplied repository to establish additional isolation or tenant-independent values.

I verified the pinned commit and clean tree. I could not verify production callers, actual disclosure, cache lifecycle outside these files, or identifier restrictions needed to rule out delimiter collisions. The probes used synthetic values; no repository files were changed.

stance: initial
disposition: defect
action: Change cache.py:7 to return f"{tenant_id}:{user_id}:{resource}".
decisive: cache.py:7
crux: Different tenants can reach the same cache dictionary with matching user_id and resource values.