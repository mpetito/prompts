Push the fix, close out both threads, then leave a note on each.

```bash
git push
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDOQx7a1M5Tr1Ka"}){thread{isResolved}}}'
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDOQx7a1M5Tr1Kb"}){thread{isResolved}}}'
R=repos/kestrel-tools/harbor-fetch/pulls/23/comments
gh api $R/2214410201/replies -f body="Fixed in 4be91c2."
gh api $R/2214410202/replies -f body="Fixed in 4be91c2."
```

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
