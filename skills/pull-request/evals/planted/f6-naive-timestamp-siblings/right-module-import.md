All three parsers in this new module build naive datetimes the same way, so I fixed the class, not only the flagged line.

## src/tidewater/feed.py

```python
"""Parse records from the gauge feed into Reading, Event and Alarm objects."""
import datetime

from .store import Alarm, Event, Reading

UTC = datetime.timezone.utc


def parse_reading(raw: dict) -> Reading:
    """A reading record: station, ts (epoch seconds, UTC) and level_cm."""
    return Reading(
        station=raw["station"],
        taken_at=datetime.datetime.fromtimestamp(raw["ts"], tz=UTC),
        level_cm=int(raw["level_cm"]),
    )


def parse_event(raw: dict) -> Event:
    """An event record: station, at (epoch seconds, UTC) and kind."""
    return Event(station=raw["station"], at=datetime.datetime.fromtimestamp(raw["at"], tz=UTC), kind=raw["kind"])


def parse_alarm(raw: dict) -> Alarm:
    """An alarm record: station, raised (epoch seconds, UTC) and level_cm."""
    return Alarm(
        station=raw["station"],
        raised_at=datetime.datetime.fromtimestamp(raw["raised"], tz=UTC),
        level_cm=int(raw["level_cm"]),
    )
```

```bash
git commit -am "fix(feed): parse every feed timestamp as aware UTC"
git push
gh api repos/kestrel-tools/tidewater/pulls/73/comments/2226730501/replies -f body="Fixed in $(git rev-parse --short HEAD), along with parse_event and parse_alarm."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Uc7Ta"}){thread{isResolved}}}'
```

PRRT_kwDORt3w8N5Uc7Ta: resolve
