Change the flagged line in `parse_reading` and import `timezone`:

```diff
-from datetime import datetime
+from datetime import datetime, timezone
@@
-        taken_at=datetime.utcfromtimestamp(raw["ts"]),
+        taken_at=datetime.fromtimestamp(raw["ts"], tz=timezone.utc),
```

```bash
git commit -am "fix(feed): parse reading timestamps as aware UTC"
git push
gh api repos/kestrel-tools/tidewater/pulls/73/comments/2226730501/replies -f body="Fixed in $(git rev-parse --short HEAD)."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Uc7Ta"}){thread{isResolved}}}'
```

PRRT_kwDORt3w8N5Uc7Ta: resolve
