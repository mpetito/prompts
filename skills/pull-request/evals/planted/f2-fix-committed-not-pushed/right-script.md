`4be91c2` is local only (`git status`: ahead of origin by 1), so push it first. Then the skill's script replies on each thread and resolves it.

```bash
git push
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDOQx7a1M5Tr1Ka -Body "Fixed in 4be91c2: fetch_manifest passes timeout to client.get."
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDOQx7a1M5Tr1Kb -Body "Fixed in 4be91c2: the default is 5.0 seconds now."
```

I stop after the second thread.

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
