# Pull request context: kestrel-tools/tidewater #73 (fictional)

## Session notes

- Repository `kestrel-tools/tidewater`. Pull request #73, branch `feature/gauge-feed`,
  opened by me (`rowan-ashby`). Copilot reviewed the PR head, `5a81c3e`, and left 1 thread.
- CI passed on the head (`pytest`, 12 tests).
- The sections below were captured from the PR head. `feed.py` is new in this PR.

## gh api graphql (pullRequest 73 reviewThreads)

```json
{
  "data": {
    "repository": {
      "pullRequest": {
        "number": 73,
        "title": "feat(feed): parse readings, events and alarms from the gauge feed",
        "headRefName": "feature/gauge-feed",
        "headRefOid": "5a81c3e",
        "author": { "login": "rowan-ashby" },
        "reviewThreads": {
          "nodes": [
            {
              "id": "PRRT_kwDORt3w8N5Uc7Ta",
              "isResolved": false,
              "isOutdated": false,
              "path": "src/tidewater/feed.py",
              "line": 11,
              "comments": {
                "nodes": [
                  {
                    "id": "PRRC_kwDORt3w8N6Lg5Ta",
                    "databaseId": 2226730501,
                    "author": { "login": "copilot-pull-request-reviewer" },
                    "body": "`datetime.utcfromtimestamp` returns a naive datetime. `export_readings` compares `taken_at` with a timezone-aware `since`, so a parsed reading makes that comparison raise `TypeError: can't compare offset-naive and offset-aware datetimes`. `utcfromtimestamp` is also deprecated since Python 3.12. Build an aware value with `datetime.fromtimestamp(..., tz=timezone.utc)`.",
                    "createdAt": "2026-10-10T13:22:09Z"
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

## src/tidewater/store.py (excerpt)

```python
@dataclass(frozen=True)
class Reading:
    station: str
    taken_at: datetime  # timezone-aware UTC
    level_cm: int


@dataclass(frozen=True)
class Event:
    station: str
    at: datetime  # timezone-aware UTC
    kind: str


@dataclass(frozen=True)
class Alarm:
    station: str
    raised_at: datetime  # timezone-aware UTC
    level_cm: int
```

## src/tidewater/feed.py (PR head)

```python
"""Parse records from the gauge feed into Reading, Event and Alarm objects."""
from datetime import datetime

from .store import Alarm, Event, Reading


def parse_reading(raw: dict) -> Reading:
    """A reading record: station, ts (epoch seconds, UTC) and level_cm."""
    return Reading(
        station=raw["station"],
        taken_at=datetime.utcfromtimestamp(raw["ts"]),
        level_cm=int(raw["level_cm"]),
    )


def parse_event(raw: dict) -> Event:
    """An event record: station, at (epoch seconds, UTC) and kind."""
    return Event(
        station=raw["station"],
        at=datetime.utcfromtimestamp(raw["at"]),
        kind=raw["kind"],
    )


def parse_alarm(raw: dict) -> Alarm:
    """An alarm record: station, raised (epoch seconds, UTC) and level_cm."""
    return Alarm(
        station=raw["station"],
        raised_at=datetime.utcfromtimestamp(raw["raised"]),
        level_cm=int(raw["level_cm"]),
    )
```
