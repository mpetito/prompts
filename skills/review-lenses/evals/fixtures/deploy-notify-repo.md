# Repository excerpt: ops-tools at main (a1c07e2)

## Tree

```text
ops-tools/
  jobs/backup_check.py
  jobs/cert_expiry.py
  lib/__init__.py
  lib/hostinfo.py
  lib/paths.py
  lib/teamfeed.py
  lib/timing.py
  scripts/deploy.sh
  scripts/legacy_notify.sh
  scripts/nightly_report.py
  scripts/rotate_logs.sh
  tests/test_paths.py
  tests/test_teamfeed.py
  tests/test_timing.py
  requirements.txt
```

## lib/hostinfo.py

```python
"""Facts about the host a script runs on."""
import os
import socket


def host_label() -> str:
    return os.environ.get("HOST_LABEL") or socket.gethostname()
```

## lib/paths.py

```python
"""Well-known paths on the deploy host."""
from pathlib import Path

RELEASES = Path("/srv/app/releases")
CURRENT = Path("/srv/app/current")


def release_dir(version: str) -> Path:
    return RELEASES / version
```

## lib/teamfeed.py

```python
"""Team feed: short status lines for people on the team."""
import os
import time

import requests


def broadcast_note(text: str) -> None:
    url = os.environ["CHAT_WEBHOOK_URL"]
    for attempt in range(3):
        r = requests.post(url, json={"text": text}, timeout=5)
        if r.status_code < 500:
            r.raise_for_status()
            return
        time.sleep(2 ** attempt)
    r.raise_for_status()
```

`broadcast_note` is called from `scripts/nightly_report.py`, `jobs/backup_check.py` and
`jobs/cert_expiry.py`.

## lib/timing.py

```python
"""Timing helpers for scripts."""
import time
from contextlib import contextmanager


@contextmanager
def stopwatch():
    start = time.monotonic()
    yield lambda: time.monotonic() - start
```

## scripts/deploy.sh

```sh
#!/bin/sh
set -eu
VERSION="$1"
. /etc/ops-tools/deploy.env

cd /srv/app
mkdir -p "releases/$VERSION"
tar -xzf "/tmp/app-$VERSION.tgz" -C "releases/$VERSION"
ln -sfn "releases/$VERSION" current.new
mv -T current.new current
systemctl restart app

./scripts/legacy_notify.sh "Deploying $VERSION"
```

## scripts/legacy_notify.sh

```sh
#!/bin/sh
# Announce a deploy in #ops-alerts.
curl -fsS -X POST -H 'Content-Type: application/json' \
  -d "{\"text\": \"$1\"}" "$OPS_ALERTS_WEBHOOK_URL"
```

## Environment variables

```text
$ grep -rn "WEBHOOK_URL" --include=*.py --include=*.sh --include=*.env . /etc/ops-tools
./lib/teamfeed.py:9:    url = os.environ["CHAT_WEBHOOK_URL"]
./scripts/legacy_notify.sh:5:  -d "{\"text\": \"$1\"}" "$OPS_ALERTS_WEBHOOK_URL"
/etc/ops-tools/deploy.env:3:OPS_ALERTS_WEBHOOK_URL=https://hooks.slack.com/services/T0/B0/x
/etc/ops-tools/deploy.env:4:CHAT_WEBHOOK_URL=https://hooks.slack.com/services/T0/B1/y
```

## requirements.txt

```text
requests==2.32.3
pytest==8.3.3
responses==0.25.3
```
