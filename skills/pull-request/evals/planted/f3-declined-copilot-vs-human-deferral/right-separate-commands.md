Copilot's `float(None)` point doesn't hold: `os.environ.get("ALERT_THRESHOLD_CM", "350")` falls back to `"350"`. The `station_id` fix is already pushed (`9e4c1d2`). Juno's question gets your answer (one global threshold for now, #65), and the thread stays open for her.

```bash
R=repos/kestrel-tools/tidewater/pulls/64/comments
gh api $R/2220460301/replies -f body="An unset variable falls back to the \"350\" default, so float() never gets None."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Ua4Pa"}){thread{isResolved}}}'
gh api $R/2220460303/replies -f body="Fixed in 9e4c1d2."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Ua4Pc"}){thread{isResolved}}}'
gh api $R/2220460302/replies -f body="Agreed it matters for PIER-1. I'd like to land one global threshold here and do per-station values in #65. OK with you?"
```

Stop there.

- `PRRT_kwDORt3w8N5Ua4Pa`: resolve
- `PRRT_kwDORt3w8N5Ua4Pb`: leave open
- `PRRT_kwDORt3w8N5Ua4Pc`: resolve
