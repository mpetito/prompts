- **Aa:** real bug; fix with Copilot's suggestion.
- **Bb:** wrong: `_models.py` raises `HTTPStatusError` for `400 <= status_code < 600`.
- **Cc:** the ops notes argue both ways (the 503s cleared within four minutes; on-call wants the page early). I won't decide that alone: I'd put it to model-council and come back to you with both views. Meanwhile a short holding reply, and the thread stays open.
- **Dd:** typo; fix.

```diff
-        if attempt == max_retries:
+        if attempt == max_retries - 1:
```

```bash
git commit -am "fix(fetch): raise the last error once retries run out"
git push
sha=$(git rev-parse --short HEAD)
gh api repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450101/replies -f body="Fixed in $sha."
gh api repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450102/replies -f body="minihttp raises for 5xx too: 400 <= status_code < 600 in _models.py."
gh api repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450104/replies -f body="Fixed in $sha."
gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' \
  -f t=PRRT_kwDOQx7a1M5Tq0Cc -f b="Fair point; this trades an early page against riding out the outage, so I'm getting a second opinion before touching the defaults."
for t in PRRT_kwDOQx7a1M5Tq0Aa PRRT_kwDOQx7a1M5Tq0Bb PRRT_kwDOQx7a1M5Tq0Dd; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

I stop here until the council and you have weighed in on Cc.

PRRT_kwDOQx7a1M5Tq0Aa: resolve
PRRT_kwDOQx7a1M5Tq0Bb: resolve
PRRT_kwDOQx7a1M5Tq0Cc: leave open
PRRT_kwDOQx7a1M5Tq0Dd: resolve
