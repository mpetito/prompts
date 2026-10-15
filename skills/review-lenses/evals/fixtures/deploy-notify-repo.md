# Repository excerpt: ops-tools at main (a1c07e2)

Collected for the plan reviewer.

## Tree (abridged)

```text
ops-tools/
  jobs/backup_check.py
  lib/__init__.py
  lib/messaging.py
  lib/paths.py
  scripts/deploy.sh
  scripts/legacy_notify.sh
  scripts/nightly_report.py
  tests/test_messaging.py
  requirements.txt
```

## lib/messaging.py

```python
"""Post a message to the team chat."""
import os
import time

import requests


def send_chat_message(text: str) -> None:
    url = os.environ["CHAT_WEBHOOK_URL"]
    for attempt in range(3):
        r = requests.post(url, json={"text": text}, timeout=5)
        if r.status_code < 500:
            r.raise_for_status()
            return
        time.sleep(2 ** attempt)
    r.raise_for_status()
```

## Callers of send_chat_message

```text
$ grep -rn "send_chat_message" --include=*.py .
./scripts/nightly_report.py:41:    send_chat_message(summary)
./jobs/backup_check.py:27:        send_chat_message(f"Backup check failed: {reason}")
./tests/test_messaging.py:12:def test_send_chat_message_retries_on_503(responses):
```

## scripts/legacy_notify.sh

```sh
#!/bin/sh
# Announce a deploy in #ops-alerts.
curl -fsS -X POST -H 'Content-Type: application/json' \
  -d "{\"text\": \"$1\"}" "$OPS_ALERTS_WEBHOOK_URL"
```

## Callers of legacy_notify.sh

```text
$ grep -rn "legacy_notify" .
./scripts/deploy.sh:14:./scripts/legacy_notify.sh "Deploying $VERSION"
```

`$OPS_ALERTS_WEBHOOK_URL` is set only in the deploy host's environment file, for this script.

## requirements.txt

```text
requests==2.32.3
pytest==8.3.3
responses==0.25.3
```
