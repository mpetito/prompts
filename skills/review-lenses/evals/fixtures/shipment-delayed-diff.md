# Change to review: publish shipment.delayed to partners

Repository: `fulfilment-api` (Python 3.12). Branch `feature/shipment-delayed`, head `8b14f2a`, base
`main`. Pull request open; CI green on this head.

## Author's description

> Partners asked to be told when a shipment will miss its promised date. This publishes a new
> `shipment.delayed` event to the partner event feed from the existing nightly delay check, and
> documents its schema for partners. The bus is sometimes briefly unavailable at night, so the
> publish now retries.

## Facts for the reviewers

- The partner event feed is public: partner carriers and marketplaces build integrations against
  the documented schemas, and we can't change a published event without coordinating with each of
  them.
- `check_delays()` runs from our own nightly job and reads only rows already in our database. No
  code in this change reads a request, a file, a message or any other input from outside the
  service.
- `docs/events/shipment.delayed.json` documents the event for partners; nothing validates
  events against it.
- The change adds no module, function, helper or script; it edits one existing function,
  `check_delays`, and adds one schema document.

## Diff

```diff
--- a/fulfilment/delays.py
+++ b/fulfilment/delays.py
@@ -1,6 +1,8 @@
+import time
 from datetime import datetime, timezone
 
 from .db import late_shipments
+from .bus import BusUnavailable, publish
 
 
 def check_delays(now: datetime | None = None) -> int:
@@ -8,6 +10,21 @@ def check_delays(now: datetime | None = None) -> int:
     now = now or datetime.now(timezone.utc)
     count = 0
     for s in late_shipments(now):
         s.mark_delayed()
+        event = {
+            "type": "shipment.delayed",
+            "shipment": s.id,
+            "promised": s.promised_at.strftime("%d/%m/%Y"),
+            "late_by": (now - s.promised_at).days,
+            "carrier_code": s.carrier_cd,
+        }
+        for attempt in range(6):
+            try:
+                publish("partners", event)
+                break
+            except BusUnavailable:
+                if attempt == 5:
+                    raise
+                time.sleep(0.5 * 2 ** attempt)
         count += 1
     return count
--- /dev/null
+++ b/docs/events/shipment.delayed.json
@@ -0,0 +1,13 @@
+{
+  "$schema": "https://json-schema.org/draft/2020-12/schema",
+  "title": "shipment.delayed",
+  "type": "object",
+  "required": ["type", "shipment", "promised", "late_by", "carrier_code"],
+  "properties": {
+    "type": { "const": "shipment.delayed" },
+    "shipment": { "type": "integer" },
+    "promised": { "type": "string" },
+    "late_by": { "type": "integer" },
+    "carrier_code": { "type": "string" }
+  }
+}
```

## pyproject.toml dependencies (unchanged)

```toml
[project]
dependencies = [
  "psycopg[binary]==3.2.3",
  "pydantic==2.9.2",
  "tenacity==9.0.0",
]
```
