- Copilot `float(None)`: wrong, the lookup defaults to "350". Reply and resolve.
- Copilot `station=`: fixed in 9e4c1d2. Reply and resolve.
- Juno: you've decided; reply with #65 and close it out since the decision is made.

```bash
R=repos/kestrel-tools/tidewater/pulls/64/comments
gh api $R/2220460301/replies -f body="os.environ.get has the default \"350\", so float() never sees None."
gh api $R/2220460303/replies -f body="Fixed in 9e4c1d2."
gh api $R/2220460302/replies -f body="Keeping one global threshold here; per-station thresholds are #65."
gh api graphql -f query='
mutation {
  a: resolveReviewThread(input: {threadId: "PRRT_kwDORt3w8N5Ua4Pa"}) { thread { isResolved } }
  b: resolveReviewThread(input: {
       threadId: "PRRT_kwDORt3w8N5Ua4Pb"
     }) { thread { isResolved } }
  c: resolveReviewThread(input: {threadId: "PRRT_kwDORt3w8N5Ua4Pc"}) { thread { isResolved } }
}'
```

PRRT_kwDORt3w8N5Ua4Pa — resolve
PRRT_kwDORt3w8N5Ua4Pb — resolved (decision made; leave open is not needed)
PRRT_kwDORt3w8N5Ua4Pc — resolve
