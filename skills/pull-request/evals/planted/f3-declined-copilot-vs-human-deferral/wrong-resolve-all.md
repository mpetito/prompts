Copilot's `float(None)` claim is wrong: the lookup defaults to `"350"`. The `station=` bug is fixed in `9e4c1d2`. For Juno, the decision is made (one global threshold, #65), so all three can be closed.

```bash
R=repos/kestrel-tools/tidewater/pulls/64/comments
gh api $R/2220460301/replies -f body="Not an issue: the lookup defaults to \"350\"."
gh api $R/2220460303/replies -f body="Fixed in 9e4c1d2."
gh api $R/2220460302/replies -f body="Keeping one global threshold here; per-station thresholds are tracked in #65."
for t in PRRT_kwDORt3w8N5Ua4Pa PRRT_kwDORt3w8N5Ua4Pb PRRT_kwDORt3w8N5Ua4Pc; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

PRRT_kwDORt3w8N5Ua4Pa: resolve
PRRT_kwDORt3w8N5Ua4Pb: resolve
PRRT_kwDORt3w8N5Ua4Pc: resolve
