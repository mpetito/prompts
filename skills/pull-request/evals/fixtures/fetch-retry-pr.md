# Pull request context: kestrel-tools/harbor-fetch #18 (fictional)

## Session notes

- Repository `kestrel-tools/harbor-fetch`. Pull request #18, branch `feature/fetch-retry`,
  opened by me (`rowan-ashby`). Copilot reviewed it and left 4 threads.
- The sections below were captured from the PR head (`a6bfd88`): the review threads from
  `gh api graphql` (thread ids `PRRT_...`, comment ids `PRRC_...` and REST `databaseId`s
  included), the diff, the source, the tests, the operations notes and the vendored HTTP client.
- CI on the PR head: `pytest` passed, 3 tests.

## gh api graphql (pullRequest 18 reviewThreads)

```json
{
  "data": {
    "repository": {
      "pullRequest": {
        "number": 18,
        "title": "feat(fetch): retry transport errors and 5xx with exponential backoff",
        "headRefName": "feature/fetch-retry",
        "headRefOid": "a6bfd88",
        "author": {
          "login": "rowan-ashby"
        },
        "reviewThreads": {
          "nodes": [
            {
              "id": "PRRT_kwDOQx7a1M5Tq0Aa",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/harborfetch/fetch.py",
              "line": 32,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOQx7a1M6Hc1Aa",
                    "databaseId": 2210450101,
                    "fullDatabaseId": "2210450101",
                    "author": {
                      "login": "copilot-pull-request-reviewer"
                    },
                    "body": "`attempt` takes the values `0 .. max_retries - 1`, so `attempt == max_retries` is never true. When every attempt fails, the loop sleeps once more after the final attempt and then falls off the end of the function, returning `None` instead of raising `last_error`. Callers will get `None` and fail later with a confusing `TypeError`.\n\n```suggestion\n        if attempt == max_retries - 1:\n            raise last_error\n```",
                    "createdAt": "2026-10-08T14:02:11Z"
                  }
                ]
              }
            },
            {
              "id": "PRRT_kwDOQx7a1M5Tq0Bb",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/harborfetch/fetch.py",
              "line": 27,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOQx7a1M6Hc1Bb",
                    "databaseId": 2210450102,
                    "fullDatabaseId": "2210450102",
                    "author": {
                      "login": "copilot-pull-request-reviewer"
                    },
                    "body": "In minihttp, `raise_for_status()` only raises `HTTPStatusError` for 4xx client errors; 5xx responses are returned normally. That makes this `status_code >= 500` path unreachable, so server errors such as 503 are never retried and the 5xx body is passed to `response.json()`. Check the status explicitly instead:\n\n```python\nresponse = client.get(url)\nif response.status_code >= 500:\n    last_error = ...\n```",
                    "createdAt": "2026-10-08T14:02:11Z"
                  }
                ]
              }
            },
            {
              "id": "PRRT_kwDOQx7a1M5Tq0Cc",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/harborfetch/fetch.py",
              "line": 16,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOQx7a1M6Hc1Cc",
                    "databaseId": 2210450103,
                    "fullDatabaseId": "2210450103",
                    "author": {
                      "login": "copilot-pull-request-reviewer"
                    },
                    "body": "With the defaults (`max_retries=3`, `base_delay=0.5`) the whole retry window is about 1.5 seconds, which is too short to ride out a typical server overload. Consider raising the defaults, for example `max_retries=8` and `base_delay=1.0` (roughly two minutes of total backoff), so that transient 503s don't fail the job.",
                    "createdAt": "2026-10-08T14:02:11Z"
                  }
                ]
              }
            },
            {
              "id": "PRRT_kwDOQx7a1M5Tq0Dd",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/harborfetch/fetch.py",
              "line": 11,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOQx7a1M6Hc1Dd",
                    "databaseId": 2210450104,
                    "fullDatabaseId": "2210450104",
                    "author": {
                      "login": "copilot-pull-request-reviewer"
                    },
                    "body": "Typo in comment: \"dont\" should be \"don't\".",
                    "createdAt": "2026-10-08T14:02:11Z"
                  }
                ]
              }
            }
          ]
        }
      }
    }
  }
}
```

## git log main..HEAD --oneline

```
a6bfd88 feat(fetch): retry transport errors and 5xx with exponential backoff
```

## git status

```
On branch feature/fetch-retry
Your branch is up to date with 'origin/feature/fetch-retry'.

nothing to commit, working tree clean
```

## git diff main...HEAD

```diff
diff --git a/src/harborfetch/fetch.py b/src/harborfetch/fetch.py
index ec522d0..ac85c10 100644
--- a/src/harborfetch/fetch.py
+++ b/src/harborfetch/fetch.py
@@ -11,3 +11,24 @@ def fetch_manifest(client, url):
     # and we dont want a JSONDecodeError hiding the real status.
     response.raise_for_status()
     return response.json()
+
+
+def fetch_manifest_with_retry(client, url, max_retries=3, base_delay=0.5, sleep=time.sleep):
+    """Like fetch_manifest, but retry transport errors and 5xx responses.
+
+    Waits base_delay, then 2 * base_delay, and so on between attempts. A 4xx response is
+    raised at once: retrying will not change it.
+    """
+    last_error = None
+    for attempt in range(max_retries):
+        try:
+            return fetch_manifest(client, url)
+        except HTTPStatusError as exc:
+            if exc.response.status_code < 500:
+                raise
+            last_error = exc
+        except TransportError as exc:
+            last_error = exc
+        if attempt == max_retries:
+            raise last_error
+        sleep(base_delay * 2 ** attempt)
diff --git a/tests/test_fetch.py b/tests/test_fetch.py
index b66c563..6ec1093 100644
--- a/tests/test_fetch.py
+++ b/tests/test_fetch.py
@@ -16,3 +16,25 @@ class FakeClient:
 
 def test_fetch_manifest_returns_json():
     assert fetch_manifest(FakeClient(Response(200, '{"v": 1}')), "u") == {"v": 1}
+
+
+from minihttp import HTTPStatusError
+
+from harborfetch.fetch import fetch_manifest_with_retry
+
+
+def test_retry_recovers_after_503():
+    delays = []
+    client = FakeClient(Response(503, ""), Response(200, '{"v": 2}'))
+    assert fetch_manifest_with_retry(client, "u", sleep=delays.append) == {"v": 2}
+    assert delays == [0.5]
+
+
+def test_404_is_not_retried():
+    delays = []
+    client = FakeClient(Response(404, ""))
+    try:
+        fetch_manifest_with_retry(client, "u", sleep=delays.append)
+    except HTTPStatusError:
+        pass
+    assert delays == []
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


def fetch_manifest_with_retry(client, url, max_retries=3, base_delay=0.5, sleep=time.sleep):
    """Like fetch_manifest, but retry transport errors and 5xx responses.

    Waits base_delay, then 2 * base_delay, and so on between attempts. A 4xx response is
    raised at once: retrying will not change it.
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return fetch_manifest(client, url)
        except HTTPStatusError as exc:
            if exc.response.status_code < 500:
                raise
            last_error = exc
        except TransportError as exc:
            last_error = exc
        if attempt == max_retries:
            raise last_error
        sleep(base_delay * 2 ** attempt)
```

## tests/test_fetch.py

```python
from minihttp import Response

from harborfetch.fetch import fetch_manifest


class FakeClient:
    def __init__(self, *responses):
        self.responses = list(responses)

    def get(self, url):
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def test_fetch_manifest_returns_json():
    assert fetch_manifest(FakeClient(Response(200, '{"v": 1}')), "u") == {"v": 1}


from minihttp import HTTPStatusError

from harborfetch.fetch import fetch_manifest_with_retry


def test_retry_recovers_after_503():
    delays = []
    client = FakeClient(Response(503, ""), Response(200, '{"v": 2}'))
    assert fetch_manifest_with_retry(client, "u", sleep=delays.append) == {"v": 2}
    assert delays == [0.5]


def test_404_is_not_retried():
    delays = []
    client = FakeClient(Response(404, ""))
    try:
        fetch_manifest_with_retry(client, "u", sleep=delays.append)
    except HTTPStatusError:
        pass
    assert delays == []
```

## docs/operations.md

```markdown
# Operations

The manifest sync runs nightly. A cron entry at 02:00 UTC starts the sync workers, and every
worker first fetches the shared manifest from the manifest server. That server sits behind
one small instance; on two nights last month it returned 503s for two to four minutes while
the workers were starting, and both times the 503s stopped without anyone touching it.

When a worker cannot get the manifest it exits non-zero and the scheduler pages on-call at
once. The runbook's first step for that page is to restart the manifest server, and on-call
has asked for the page to come as early as possible: downstream reports are due at 03:00 UTC
and a full sync takes about 45 minutes.
```

## vendor/minihttp/README.md

```markdown
# minihttp 2.3 (vendored)

A small synchronous HTTP client. Vendored at 2.3.1; see `_models.py` for `Response`.

## Errors

- `TransportError`: the request never got a response (DNS failure, refused connection, reset,
  timeout). Raised by `Client.get` and `Client.post`.
- `HTTPStatusError`: raised by `Response.raise_for_status()` when the response status is a
  client error (4xx) or a server error (5xx). The response is available as `exc.response`.

`Client.get` itself never raises for a status code; call `raise_for_status()` to turn 4xx and
5xx responses into `HTTPStatusError`.
```

## vendor/minihttp/_models.py

```python
class TransportError(Exception):
    """No response was received."""


class HTTPStatusError(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


class Response:
    def __init__(self, status_code, body, headers=None):
        self.status_code = status_code
        self._body = body
        self.headers = headers or {}

    def json(self):
        import json

        return json.loads(self._body)

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            kind = "Client error" if self.status_code < 500 else "Server error"
            raise HTTPStatusError(f"{kind} {self.status_code}", response=self)
        return self
```

## vendor/minihttp/_client.py

```python
from ._models import Response, TransportError


class Client:
    """Synchronous client. get/post raise TransportError when no response arrives;
    they never raise for a status code (see Response.raise_for_status)."""

    def get(self, url, timeout=None):
        raise NotImplementedError("network I/O elided in the vendored excerpt")
```
