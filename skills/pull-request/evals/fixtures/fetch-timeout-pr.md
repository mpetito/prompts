# Pull request context: kestrel-tools/harbor-fetch #23 (fictional)

## Session notes

- Repository `kestrel-tools/harbor-fetch`. Pull request #23, branch `feature/fetch-timeout`,
  opened by me (`rowan-ashby`). Copilot reviewed it at `b52d0e7` and left 2 threads.
- I fixed both points in one commit, `4be91c2`, and ran `pytest` on it: 5 passed.
- The sections below were captured from my working copy just now.

## gh api graphql (pullRequest 23 reviewThreads)

```json
{
  "data": {
    "repository": {
      "pullRequest": {
        "number": 23,
        "title": "feat(fetch): give up on a manifest request after a timeout",
        "headRefName": "feature/fetch-timeout",
        "headRefOid": "b52d0e7",
        "author": { "login": "rowan-ashby" },
        "reviewThreads": {
          "nodes": [
            {
              "id": "PRRT_kwDOQx7a1M5Tr1Ka",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/harborfetch/fetch.py",
              "line": 8,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOQx7a1M6Hd2Ka",
                    "databaseId": 2214410201,
                    "fullDatabaseId": "2214410201",
                    "author": { "login": "copilot-pull-request-reviewer" },
                    "body": "`timeout` is accepted by `fetch_manifest` but never passed to `client.get`, so a hung manifest server still blocks the worker forever. Pass it through: `client.get(url, timeout=timeout)`.",
                    "createdAt": "2026-10-09T09:14:52Z"
                  }
                ]
              }
            },
            {
              "id": "PRRT_kwDOQx7a1M5Tr1Kb",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/harborfetch/fetch.py",
              "line": 7,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDOQx7a1M6Hd2Kb",
                    "databaseId": 2214410202,
                    "fullDatabaseId": "2214410202",
                    "author": { "login": "copilot-pull-request-reviewer" },
                    "body": "The docstring says the timeout is in seconds, but the default is `5000`, which reads like milliseconds. As written, the default waits over 80 minutes.",
                    "createdAt": "2026-10-09T09:14:52Z"
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

## git log --oneline -3

```
4be91c2 fix(fetch): pass the timeout to client.get and default it to 5 seconds
b52d0e7 feat(fetch): give up on a manifest request after a timeout
a6bfd88 feat(fetch): retry transport errors and 5xx with exponential backoff
```

## git status

```
On branch feature/fetch-timeout
Your branch is ahead of 'origin/feature/fetch-timeout' by 1 commit.
  (use "git push" to publish your local commits)

nothing to commit, working tree clean
```

## git show 4be91c2

```diff
commit 4be91c2
    fix(fetch): pass the timeout to client.get and default it to 5 seconds

diff --git a/src/harborfetch/fetch.py b/src/harborfetch/fetch.py
--- a/src/harborfetch/fetch.py
+++ b/src/harborfetch/fetch.py
@@ -4,9 +4,9 @@ from minihttp import HTTPStatusError, TransportError
 
 
-def fetch_manifest(client, url, timeout=5000):
+def fetch_manifest(client, url, timeout=5.0):
     """Return the manifest at url as a dict; give up after timeout seconds."""
-    response = client.get(url)
+    response = client.get(url, timeout=timeout)
     response.raise_for_status()
     return response.json()
diff --git a/tests/test_fetch.py b/tests/test_fetch.py
--- a/tests/test_fetch.py
+++ b/tests/test_fetch.py
@@ -20,3 +20,9 @@ def test_fetch_manifest_returns_json():
+
+
+def test_timeout_reaches_the_client():
+    client = RecordingClient(Response(200, '{"v": 1}'))
+    fetch_manifest(client, "u", timeout=2.5)
+    assert client.timeouts == [2.5]
```

## pytest (on 4be91c2)

```
5 passed in 0.21s
```
