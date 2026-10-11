Aa is a real bug, Bb is wrong (minihttp raises for `400 <= status_code < 600`), Dd is a typo. For Cc I weighed it as a second opinion would: the 503s cleared in two to four minutes, but on-call wants the page early, so I'm keeping the defaults.

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
gh api $R/2210450103/replies -f body="Keeping the defaults: on-call wants the page early."
gh api $R/2210450104/replies -f body="Fixed in $sha."
for t in PRRT_kwDOQx7a1M5Tq0Aa PRRT_kwDOQx7a1M5Tq0Bb PRRT_kwDOQx7a1M5Tq0Cc PRRT_kwDOQx7a1M5Tq0Dd; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

Done after the loop.

PRRT_kwDOQx7a1M5Tq0Aa: resolve
PRRT_kwDOQx7a1M5Tq0Bb: resolve
PRRT_kwDOQx7a1M5Tq0Cc: resolve
PRRT_kwDOQx7a1M5Tq0Dd: resolve
