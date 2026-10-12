Checked against `a6bfd88`, vendored minihttp and the ops notes.

- Aa: real bug, fixing with Copilot's suggestion.
- Bb: wrong; `_models.py` raises for 400 <= status < 600. Declining with the evidence.
- Cc: no need for a second opinion here; on-call wants early pages, so the defaults stay. Reply and leave it open for Copilot.
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
gh api $R/2210450103/replies -f body="The defaults stay at 3 and 0.5: on-call asked to be paged as early as possible."
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
