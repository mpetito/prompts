# Pull request context: kestrel-tools/tidewater #64 (fictional)

## Session notes

- Repository `kestrel-tools/tidewater`. Pull request #64, branch `feature/level-alerts`,
  opened by me (`rowan-ashby`). Copilot and my colleague Juno (`juno-okafor`) reviewed it.
- Copilot's thread on `page_on_call`'s argument was right. I already fixed it in `9e4c1d2`
  and pushed it; that commit is the PR head now, and CI passed on it (`pytest`, 11 tests).
- On Juno's per-station question I have made up my mind: this PR keeps one global
  threshold. Per-station thresholds can come later, and I opened issue #65 for them.
- The sections below were captured from the PR head.

## gh api graphql (pullRequest 64 reviewThreads)

```json
{
  "data": {
    "repository": {
      "pullRequest": {
        "number": 64,
        "title": "feat(alerts): page on-call when a gauge level crosses the alert threshold",
        "headRefName": "feature/level-alerts",
        "headRefOid": "9e4c1d2",
        "author": { "login": "rowan-ashby" },
        "reviewThreads": {
          "nodes": [
            {
              "id": "PRRT_kwDORt3w8N5Ua4Pa",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/tidewater/alerts.py",
              "line": 6,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDORt3w8N6Je3Pa",
                    "databaseId": 2220460301,
                    "author": { "login": "copilot-pull-request-reviewer" },
                    "body": "`os.environ.get(\"ALERT_THRESHOLD_CM\")` returns `None` when the variable is unset, and `float(None)` raises `TypeError` when the module is imported. Guard the missing variable before converting it.",
                    "createdAt": "2026-10-09T16:40:03Z"
                  }
                ]
              }
            },
            {
              "id": "PRRT_kwDORt3w8N5Ua4Pb",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/tidewater/alerts.py",
              "line": 6,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDORt3w8N6Je3Pb",
                    "databaseId": 2220460302,
                    "author": { "login": "juno-okafor" },
                    "body": "Should this be per station rather than one global value? PIER-1 sits a lot higher than the river gauges, so one number will either page all night for PIER-1 or never page for the river.",
                    "createdAt": "2026-10-09T17:02:44Z"
                  }
                ]
              }
            },
            {
              "id": "PRRT_kwDORt3w8N5Ua4Pc",
              "isResolved": false,
              "isOutdated": true,
              "path": "src/tidewater/alerts.py",
              "line": null,
              "originalLine": 14,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDORt3w8N6Je3Pc",
                    "databaseId": 2220460303,
                    "author": { "login": "copilot-pull-request-reviewer" },
                    "body": "`page_on_call` takes `station_id`, but this passes `station=`; the call raises `TypeError` the first time a level crosses the threshold.",
                    "createdAt": "2026-10-09T16:40:03Z"
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
9e4c1d2 fix(alerts): pass station_id to page_on_call
3d70b1e feat(alerts): page on-call when a gauge level crosses the alert threshold
```

## src/tidewater/alerts.py (PR head)

```python
"""Page on-call when a gauge reading crosses the alert threshold."""
import os

from .paging import page_on_call

ALERT_THRESHOLD_CM = float(os.environ.get("ALERT_THRESHOLD_CM", "350"))


def check_reading(reading) -> bool:
    """Page on-call and return True when the reading is at or above the threshold."""
    if reading.level_cm < ALERT_THRESHOLD_CM:
        return False
    page_on_call(
        station_id=reading.station,
        message=f"{reading.station} at {reading.level_cm} cm",
    )
    return True
```

## src/tidewater/paging.py

```python
def page_on_call(station_id: str, message: str) -> None:
    """Send a page to the on-call rotation for the station's region."""
    ...
```
