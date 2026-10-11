## src/tidewater/feed.py

```python
"""Parse records from the gauge feed into Reading, Event and Alarm objects."""
from datetime import datetime, timezone

from .store import Alarm, Event, Reading


def parse_reading(raw: dict) -> Reading:
    """A reading record: station, ts (epoch seconds, UTC) and level_cm."""
    return Reading(station=raw["station"], taken_at=datetime.fromtimestamp(raw["ts"], tz=timezone.utc), level_cm=int(raw["level_cm"]))


def parse_event(raw: dict) -> Event:
    """An event record: station, at (epoch seconds, UTC) and kind."""
    return Event(station=raw["station"], at=datetime.fromtimestamp(raw["at"], tz=timezone.utc), kind=raw["kind"])


def parse_alarm(raw: dict) -> Alarm:
    """An alarm record: station, raised (epoch seconds, UTC) and level_cm."""
    return Alarm(station=raw["station"], raised_at=datetime.fromtimestamp(raw["raised"], tz=timezone.utc), level_cm=int(raw["level_cm"]))
```

```bash
git commit -am "fix(feed): parse every feed timestamp as aware UTC" && git push
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Uc7Ta"}){thread{isResolved}}}'
```

PRRT_kwDORt3w8N5Uc7Ta: resolve
