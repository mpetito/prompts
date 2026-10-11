- **Aa:** real bug; fix it.
- **Bb:** wrong: `_models.py` raises for `400 <= status_code < 600`.
- **Cc:** a tradeoff the ops notes don't settle (the 503s cleared in minutes, but on-call wants the page early). I won't decide it alone: I'd take it to model-council and bring both views to you. No reply yet; the thread stays open.
- **Dd:** typo; fix it.

```diff
-        if attempt == max_retries:
+        if attempt == max_retries - 1:
```

```bash
git commit -am "fix(fetch): raise the last error once retries run out"
git push
sha=$(git rev-parse --short HEAD)
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDOQx7a1M5Tq0Aa -Body "Fixed in $sha: the check is now attempt == max_retries - 1."
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDOQx7a1M5Tq0Bb -Body "minihttp raises HTTPStatusError for 5xx too: 400 <= status_code < 600 in _models.py."
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDOQx7a1M5Tq0Dd -Body "Fixed in $sha."
```

I stop here until Cc is decided.

PRRT_kwDOQx7a1M5Tq0Aa: resolve
PRRT_kwDOQx7a1M5Tq0Bb: resolve
PRRT_kwDOQx7a1M5Tq0Cc: leave open
PRRT_kwDOQx7a1M5Tq0Dd: resolve
