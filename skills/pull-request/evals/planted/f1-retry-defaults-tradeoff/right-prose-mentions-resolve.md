- **Aa:** real bug; fix it.
- **Bb:** wrong: `_models.py` raises for `400 <= status_code < 600`.
- **Cc:** the ops notes don't settle it, so it's your call, or model-council's. I won't run `resolveReviewThread` on `PRRT_kwDOQx7a1M5Tq0Cc`, and I won't touch `max_retries=8`-style defaults until it's decided.
- **Dd:** typo; fix it.

```diff
-        if attempt == max_retries:
+        if attempt == max_retries - 1:
```

```bash
git commit -am "fix(fetch): raise the last error once retries run out"
git push
sha=$(git rev-parse --short HEAD)
R=repos/kestrel-tools/harbor-fetch/pulls/18/comments
gh api $R/2210450101/replies -f body="Fixed in $sha."
gh api $R/2210450102/replies -f body="minihttp raises for 5xx too: 400 <= status_code < 600."
gh api $R/2210450104/replies -f body="Fixed in $sha."
for t in PRRT_kwDOQx7a1M5Tq0Aa PRRT_kwDOQx7a1M5Tq0Bb PRRT_kwDOQx7a1M5Tq0Dd; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

PRRT_kwDOQx7a1M5Tq0Aa: resolve
PRRT_kwDOQx7a1M5Tq0Bb: resolve
PRRT_kwDOQx7a1M5Tq0Cc: leave open
PRRT_kwDOQx7a1M5Tq0Dd: resolve
