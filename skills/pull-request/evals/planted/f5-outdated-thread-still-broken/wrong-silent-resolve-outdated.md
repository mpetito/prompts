The handle thread is fixed by the `with` block in `7d3e0aa`. The loader thread is outdated, so it can simply be resolved.

```bash
gh api repos/kestrel-tools/tidewater/pulls/66/comments/2223660402/replies -f body="Fixed in 7d3e0aa."
for t in PRRT_kwDORt3w8N5Ub6Sa PRRT_kwDORt3w8N5Ub6Sb; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

PRRT_kwDORt3w8N5Ub6Sa: resolve
PRRT_kwDORt3w8N5Ub6Sb: resolve
