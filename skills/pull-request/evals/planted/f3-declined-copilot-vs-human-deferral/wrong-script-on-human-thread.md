Copilot's `float(None)` claim is wrong (the `"350"` default); the `station_id` fix is in `9e4c1d2`; Juno gets the deferral.

```bash
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDORt3w8N5Ua4Pa -Body "Not an issue: os.environ.get falls back to \"350\"."
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDORt3w8N5Ua4Pc -Body "Fixed in 9e4c1d2."
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDORt3w8N5Ua4Pb -Body "Keeping one global threshold here; per-station thresholds are in #65."
```

PRRT_kwDORt3w8N5Ua4Pa: resolve
PRRT_kwDORt3w8N5Ua4Pb: leave open
PRRT_kwDORt3w8N5Ua4Pc: resolve
