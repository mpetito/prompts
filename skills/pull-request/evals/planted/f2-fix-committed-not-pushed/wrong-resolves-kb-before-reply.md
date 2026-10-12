Push first, since `4be91c2` isn't on the PR yet.

```bash
git push
R=repos/kestrel-tools/harbor-fetch/pulls/23/comments
gh api $R/2214410201/replies -f body="Fixed in 4be91c2."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDOQx7a1M5Tr1Ka"}){thread{isResolved}}}'
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDOQx7a1M5Tr1Kb"}){thread{isResolved}}}'
gh api $R/2214410202/replies -f body="Fixed in 4be91c2."
```

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
