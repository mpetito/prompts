The flagged line has two siblings in this PR with the same naive timestamp (`parse_event`, `parse_alarm`), and `store.py` documents all three fields as aware UTC, so one helper fixes all three.

## src/tidewater/feed.py

```python
"""Parse records from the gauge feed into Reading, Event and Alarm objects."""
from datetime import UTC, datetime

from .store import Alarm, Event, Reading


def _utc(seconds: float) -> datetime:
    """An epoch-seconds value from the feed as an aware UTC datetime."""
    return datetime.fromtimestamp(seconds, tz=UTC)


def parse_reading(raw: dict) -> Reading:
    """A reading record: station, ts (epoch seconds, UTC) and level_cm."""
    return Reading(station=raw["station"], taken_at=_utc(raw["ts"]), level_cm=int(raw["level_cm"]))


def parse_event(raw: dict) -> Event:
    """An event record: station, at (epoch seconds, UTC) and kind."""
    return Event(station=raw["station"], at=_utc(raw["at"]), kind=raw["kind"])


def parse_alarm(raw: dict) -> Alarm:
    """An alarm record: station, raised (epoch seconds, UTC) and level_cm."""
    return Alarm(station=raw["station"], raised_at=_utc(raw["raised"]), level_cm=int(raw["level_cm"]))
```

```bash
git commit -am "fix(feed): parse feed timestamps as aware UTC"
git push
gh api repos/kestrel-tools/tidewater/pulls/73/comments/2226730501/replies -f body="Fixed in $(git rev-parse --short HEAD) for all three record types."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Uc7Ta"}){thread{isResolved}}}'
```

PRRT_kwDORt3w8N5Uc7Ta: resolve
