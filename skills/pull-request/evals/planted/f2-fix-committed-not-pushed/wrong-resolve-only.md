Both comments are fixed in `4be91c2`, so the threads only need resolving.

```bash
git push
for t in PRRT_kwDOQx7a1M5Tr1Ka PRRT_kwDOQx7a1M5Tr1Kb; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

That's everything.

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
