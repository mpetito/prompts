Reply to all three; resolve only the thread that was actually fixed. The other two stay open until their explanations are accepted.

```bash
R=repos/kestrel-tools/tidewater/pulls/64/comments
gh api $R/2220460301/replies -f body="I propose keeping this as is: the lookup defaults to \"350\", so float() never receives None."
gh api $R/2220460303/replies -f body="Fixed in 9e4c1d2."
gh api $R/2220460302/replies -f body="I propose keeping one global threshold in this PR; per-station thresholds are in #65."
gh api graphql -f query='mutation{resolveReviewThread(input:{threadId:"PRRT_kwDORt3w8N5Ua4Pc"}){thread{isResolved}}}'
```

PRRT_kwDORt3w8N5Ua4Pa: leave open
PRRT_kwDORt3w8N5Ua4Pb: leave open
PRRT_kwDORt3w8N5Ua4Pc: resolve
