Both threads are outdated only because `7d3e0aa` moved the code. At the head the handle is closed by a `with` block, but `_read_stations` still uses the full `yaml.Loader`.

```diff
-        return yaml.load(f, Loader=yaml.Loader)["stations"]
+        return yaml.safe_load(f)["stations"]
```

```bash
git commit -am "fix(stations): load stations.yaml with the safe loader"
git push
sha=$(git rev-parse --short HEAD)
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDORt3w8N5Ub6Sa -Body "The refactor moved this but kept yaml.Loader; fixed in $sha with yaml.safe_load."
pwsh -NoProfile -File skills/pull-request/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_kwDORt3w8N5Ub6Sb -Body "Addressed in 7d3e0aa: the file is read in a with block."
```

PRRT_kwDORt3w8N5Ub6Sa: resolve
PRRT_kwDORt3w8N5Ub6Sb: resolve
