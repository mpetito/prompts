Both threads are outdated after the refactor in 7d3e0aa, which moved the loading into `_read_stations`.

```bash
R=repos/kestrel-tools/tidewater/pulls/66/comments
gh api $R/2223660401/replies -f body="Outdated after 7d3e0aa; the loader moved into _read_stations. We can switch to yaml.safe_load() in a follow-up."
gh api $R/2223660402/replies -f body="Fixed by the refactor in 7d3e0aa: the file is read in a with block."
for t in PRRT_kwDORt3w8N5Ub6Sa PRRT_kwDORt3w8N5Ub6Sb; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

PRRT_kwDORt3w8N5Ub6Sa: resolve
PRRT_kwDORt3w8N5Ub6Sb: resolve
