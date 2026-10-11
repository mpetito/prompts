Two issues should be fixed before workers adopt this cache:

- **[P2] Publish cache writes atomically** — [cache.py:22](src/harborfetch/cache.py:22). Opening the shared file with `"w"` immediately truncates it and refreshes its modification time. Another worker can treat that empty or partially written file as fresh and fail with `JSONDecodeError`. An interrupted write also leaves a broken cache. Write to a temporary file and atomically replace the destination; treat invalid cached JSON as a miss.

- **[P2] Coordinate refreshes across workers** — [cache.py:15](src/harborfetch/cache.py:15). Operations documents 40 simultaneous nightly starts and prior manifest-server overload. With a 15-minute TTL, the previous night’s cache is expired, so all workers can miss and fetch concurrently, preserving the burst that caused 503s. `fetch_manifest` propagates those errors. Use an interprocess refresh lock and recheck freshness after acquiring it.

The new function is unused until the follow-up PR, so these failures do not affect current workers yet. Reviewed the supplied diff, implementation, tests, operations notes, and vendored client. No files changed or tests run.