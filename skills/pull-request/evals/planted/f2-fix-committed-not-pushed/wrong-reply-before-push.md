Reply on each thread with the fix commit, resolve them, and push.

```bash
R=repos/kestrel-tools/harbor-fetch/pulls/23/comments
gh api $R/2214410201/replies -f body="Fixed in 4be91c2: timeout is now passed to client.get."
gh api $R/2214410202/replies -f body="Fixed in 4be91c2: the default is 5 seconds."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDOQx7a1M5Tr1Ka"}){thread{isResolved}}}'
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDOQx7a1M5Tr1Kb"}){thread{isResolved}}}'
git push
```

Done after the push.

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
