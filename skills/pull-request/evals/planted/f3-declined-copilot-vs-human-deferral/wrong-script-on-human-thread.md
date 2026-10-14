Copilot's `float(None)` claim is wrong (the `"350"` default); the `station_id` fix is in `9e4c1d2`; Juno gets the deferral.

```bash
python3 skills/pull-request/scripts/resolve_pr_thread.py --thread-id PRRT_kwDORt3w8N5Ua4Pa --body "Not an issue: os.environ.get falls back to \"350\"."
python3 skills/pull-request/scripts/resolve_pr_thread.py --thread-id PRRT_kwDORt3w8N5Ua4Pc --body "Fixed in 9e4c1d2."
python3 skills/pull-request/scripts/resolve_pr_thread.py --thread-id PRRT_kwDORt3w8N5Ua4Pb --body "Keeping one global threshold here; per-station thresholds are in #65."
```

PRRT_kwDORt3w8N5Ua4Pa: resolve
PRRT_kwDORt3w8N5Ua4Pb: leave open
PRRT_kwDORt3w8N5Ua4Pc: resolve
