Copilot's `float(None)` thread is wrong: the lookup has a default of "350". Juno gets the deferral and keeps her thread.

```bash
R=repos/kestrel-tools/tidewater/pulls/64/comments
gh api $R/2220460301/replies -f body="Not an issue, closing."
gh api $R/2220460303/replies -f body="Fixed in 9e4c1d2."
gh api $R/2220460302/replies -f body="One global threshold for now; per-station thresholds are in #65."
for t in PRRT_kwDORt3w8N5Ua4Pa PRRT_kwDORt3w8N5Ua4Pc; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

PRRT_kwDORt3w8N5Ua4Pa: resolve
PRRT_kwDORt3w8N5Ua4Pb: leave open
PRRT_kwDORt3w8N5Ua4Pc: resolve
