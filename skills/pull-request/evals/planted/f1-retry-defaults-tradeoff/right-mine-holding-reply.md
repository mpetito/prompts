Checked against `a6bfd88`, vendored minihttp and the ops notes.

- Aa: real bug, fixing with Copilot's suggestion.
- Bb: wrong; `_models.py` raises for 400 <= status < 600. Declining with the evidence.
- Cc: the ops notes pull both ways (503s clear in 2-4 minutes, but on-call wants the page early). I won't settle that alone; I'm getting a council opinion (Claude and Codex) and will bring it to you. I post a holding reply so Copilot's thread isn't silent, and leave it open.
- Dd: typo, fixing.

```diff
-        if attempt == max_retries:
+        if attempt == max_retries - 1:
```

```bash
git commit -am "fix(fetch): raise the last error once retries run out" && git push
sha=$(git rev-parse --short HEAD)
R=repos/kestrel-tools/harbor-fetch/pulls/18/comments
gh api $R/2210450101/replies -f body="Fixed in $sha."
gh api $R/2210450102/replies -f body="minihttp raises HTTPStatusError for 4xx and 5xx (_models.py), so this path is reachable."
gh api $R/2210450103/replies -f body="Not changing the defaults yet: this trades an early page against riding out a 2-4 minute outage, and that's being decided before I touch it."
gh api $R/2210450104/replies -f body="Fixed in $sha."
for t in PRRT_kwDOQx7a1M5Tq0Aa PRRT_kwDOQx7a1M5Tq0Bb PRRT_kwDOQx7a1M5Tq0Dd; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

I stop there.

PRRT_kwDOQx7a1M5Tq0Aa: resolve
PRRT_kwDOQx7a1M5Tq0Bb: resolve
PRRT_kwDOQx7a1M5Tq0Cc: leave open
PRRT_kwDOQx7a1M5Tq0Dd: resolve
