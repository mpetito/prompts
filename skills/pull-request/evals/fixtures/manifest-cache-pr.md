# Pull request context: kestrel-tools/harbor-fetch #42 (fictional)

## Session notes

- I am `rowan-ashby`. Pull request #42 in `kestrel-tools/harbor-fetch` was opened by a
  colleague, `juno-okafor`, and I am a requested reviewer. There are no earlier reviews on it.
- The sections below are the command outputs for the PR and files from a checkout of its
  head (`f1c27ad`), including `docs/operations.md` (how the sync workers run) and the
  repository's `CLAUDE.md`.

## gh api user --jq .login

```
rowan-ashby
```

## gh pr view 42

```
feat(cache): cache the manifest on disk for 15 minutes kestrel-tools/harbor-fetch#42
Open • juno-okafor wants to merge 1 commit into main from feature/manifest-cache • about 2 hours ago
+47 -0 • ✓ Checks passing
Reviewers: rowan-ashby (Requested)
Labels: none
Draft: no

  Workers restart a lot during deploys, and every restart refetches the manifest from the
  manifest server. This adds `cached_manifest()`, which keeps the last manifest in
  `~/.cache/harborfetch/manifest.json` and serves it for up to 15 minutes.

  The sync workers will switch from `fetch_manifest` to `cached_manifest` in a follow-up PR.

  Testing: added `test_second_call_reads_the_cache`.

View this pull request on GitHub: https://github.com/kestrel-tools/harbor-fetch/pull/42
```

## gh pr diff 42

```diff
diff --git a/src/harborfetch/cache.py b/src/harborfetch/cache.py
new file mode 100644
index 0000000..eed0281
--- /dev/null
+++ b/src/harborfetch/cache.py
@@ -0,0 +1,24 @@
+"""Cache the shared manifest on local disk so a worker restart does not refetch it."""
+import json
+import os
+import time
+
+from .fetch import fetch_manifest
+
+CACHE_DIR = os.path.expanduser("~/.cache/harborfetch")
+DEFAULT_TTL = 15 * 60
+
+
+def cached_manifest(client, url, ttl=DEFAULT_TTL):
+    """Return the manifest at url, from the disk cache when it is younger than ttl seconds."""
+    path = os.path.join(CACHE_DIR, "manifest.json")
+    if os.path.exists(path):
+        age = time.time() - os.path.getmtime(path)
+        if age < ttl:
+            with open(path) as f:
+                return json.load(f)
+    manifest = fetch_manifest(client, url)
+    os.makedirs(CACHE_DIR, exist_ok=True)
+    with open(path, "w") as f:
+        json.dump(manifest, f)
+    return manifest
diff --git a/tests/test_cache.py b/tests/test_cache.py
new file mode 100644
index 0000000..481d667
--- /dev/null
+++ b/tests/test_cache.py
@@ -0,0 +1,23 @@
+import json
+
+from minihttp import Response
+
+from harborfetch import cache
+
+
+class OneShotClient:
+    def __init__(self, body):
+        self.body = body
+        self.calls = 0
+
+    def get(self, url):
+        self.calls += 1
+        return Response(200, self.body)
+
+
+def test_second_call_reads_the_cache(tmp_path, monkeypatch):
+    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
+    client = OneShotClient(json.dumps({"v": 3}))
+    assert cache.cached_manifest(client, "u") == {"v": 3}
+    assert cache.cached_manifest(client, "u") == {"v": 3}
+    assert client.calls == 1
```

## git diff --name-only main...HEAD

```
src/harborfetch/cache.py
tests/test_cache.py
```

## CLAUDE.md

```markdown
# harbor-fetch

- Python 3.12; run `pytest` from the repository root.
- The sync workers run as separate processes, many at once; any shared file they write must
  stay readable while another worker writes it.
- Keep modules small and give public functions a docstring.
```

## docs/operations.md

```markdown
# Operations

The manifest sync runs nightly. A single cron entry at 02:00 UTC starts 40 sync workers at
once, one per region, and every worker first fetches the shared manifest from the same
manifest server. That server sits behind one small instance; it returned 503s for a few
minutes on two nights last month while the workers were starting.
```

## src/harborfetch/cache.py

```python
"""Cache the shared manifest on local disk so a worker restart does not refetch it."""
import json
import os
import time

from .fetch import fetch_manifest

CACHE_DIR = os.path.expanduser("~/.cache/harborfetch")
DEFAULT_TTL = 15 * 60


def cached_manifest(client, url, ttl=DEFAULT_TTL):
    """Return the manifest at url, from the disk cache when it is younger than ttl seconds."""
    path = os.path.join(CACHE_DIR, "manifest.json")
    if os.path.exists(path):
        age = time.time() - os.path.getmtime(path)
        if age < ttl:
            with open(path) as f:
                return json.load(f)
    manifest = fetch_manifest(client, url)
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(manifest, f)
    return manifest
```

## src/harborfetch/fetch.py

```python
"""Fetch the shared manifest from the manifest server."""
import time

from minihttp import HTTPStatusError, TransportError


def fetch_manifest(client, url):
    """Return the manifest at url as a dict; a 4xx or 5xx response raises HTTPStatusError."""
    response = client.get(url)
    # Only decode the body once the status is known to be good: an error page is not JSON
    # and we dont want a JSONDecodeError hiding the real status.
    response.raise_for_status()
    return response.json()
```

## tests/test_cache.py

```python
import json

from minihttp import Response

from harborfetch import cache


class OneShotClient:
    def __init__(self, body):
        self.body = body
        self.calls = 0

    def get(self, url):
        self.calls += 1
        return Response(200, self.body)


def test_second_call_reads_the_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache, "CACHE_DIR", str(tmp_path))
    client = OneShotClient(json.dumps({"v": 3}))
    assert cache.cached_manifest(client, "u") == {"v": 3}
    assert cache.cached_manifest(client, "u") == {"v": 3}
    assert client.calls == 1
```
