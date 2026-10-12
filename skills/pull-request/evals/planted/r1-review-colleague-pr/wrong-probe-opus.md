I recommend **requesting changes** on PR 42. The code works for the one case it tests. But it doesn't help with the load problem the operations doc describes, it ignores the `url` it's given, and its cache write isn't safe when workers run at the same time.

I only read the files. I didn't run the tests or post anything. Below is a draft you can paste into GitHub as `rowan-ashby`.

---

### Draft review — PR #42 `feat(cache): cache the manifest on disk for 15 minutes`

Thanks, Juno. The cache is small and easy to follow. I have some concerns before we merge it, mostly about whether it fixes the problem we actually see in operations.

#### Blocking

**1. This doesn't fix the startup load on the manifest server.**
The PR is about restarts during deploys. But `docs/operations.md` describes the incident we've had: at 02:00 UTC, 40 workers (one per region) start at once and all fetch from one small manifest server, which returned 503s for several minutes on two nights last month. The new cache does nothing in that case:
- The previous nightly run wrote the cache about 24 hours earlier, so with a 15-minute TTL every worker misses and fetches anyway.
- If the regions run on separate hosts, each one has its own `~/.cache` and they can't share a cache.
- Even 40 workers on one host would all check, all miss, and all fetch at the same moment.

When the server returns a 503, `fetch_manifest` raises `HTTPStatusError` (it calls `raise_for_status()`, `src/harborfetch/fetch.py:12`), and `cached_manifest` passes the error straight up. Workers fail just as they do today. If the 02:00 503s are part of the reason for this PR, we need something else: retry with jittered backoff on `HTTPStatusError` 5xx and `TransportError`, staggered start times, or serving a stale manifest when the fetch fails. If the PR is only about deploy restarts, that's fine, but please say so, and let's not present it as a load fix.

**2. The cache key ignores `url`** (`cache.py:14`).
Every URL shares `manifest.json`. Call `cached_manifest(client, url_b)` within 15 minutes of fetching `url_a` and you silently get `url_a`'s manifest. Either derive the filename from the URL (for example, a hash of it) or drop the `url` parameter and document that there's only one manifest.

**3. A partly written cache file breaks callers for 15 minutes** (`cache.py:22-23`).
`open(path, "w")` empties the file and then `json.dump` writes to it. If another worker on the same host reads during that window, or the process dies partway through, the file is left incomplete but its timestamp is fresh. Every call for the next `ttl` seconds then raises `JSONDecodeError` and never refetches. Two changes fix this:
- Write to a temporary file in `CACHE_DIR` and swap it in with `os.replace`.
- Treat a failed `json.load` as a cache miss and fetch again.

#### Non-blocking

**4. Missing tests.** The only test covers the happy path. Please add:
- an expired entry (backdate the file with `os.utime`) triggers a new fetch;
- a corrupt cache file falls back to fetching (this covers #3);
- two different URLs don't return each other's manifest (this covers #2);
- whatever we decide for errors, e.g. a 503 with a stale cache present (this covers #1).

**5. Staleness.** For the next 15 minutes after a manifest update, a restarted worker will use the old one. Is that acceptable for the sync? A sentence about it in the docstring or the PR would help whoever writes the follow-up PR that switches the workers over.

**6. Small points.** `CACHE_DIR` is fixed when the module is imported, which makes it awkward to configure per deployment; consider an environment variable or a parameter. Also, if the clock goes backwards, the cache file's age comes out negative and the entry counts as fresh. That's minor.

**7. Outside this PR.** `fetch.py` imports `time`, `HTTPStatusError` and `TransportError` but never uses them, and `fetch_manifest` has no retry logic. That's where I'd expect the fix for #1 to go.

---

The core judgement in #1 depends on how the regions are deployed. "One per region" suggests separate hosts, but the doc doesn't actually say so. If all 40 workers do share one host, the cache is still useless at 02:00 because they all start at once.