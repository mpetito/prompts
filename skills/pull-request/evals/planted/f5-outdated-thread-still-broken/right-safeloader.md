`isOutdated` only means the lines moved in `7d3e0aa`. At the head, the handle is closed by the `with` block, but `_read_stations` still uses the full `yaml.Loader`, so that thread still applies.

```diff
-        return yaml.load(f, Loader=yaml.Loader)["stations"]
+        return yaml.load(f, Loader=yaml.SafeLoader)["stations"]
```

```bash
git commit -am "fix(stations): parse stations.yaml with SafeLoader"
git push
sha=$(git rev-parse --short HEAD)
gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' -f t=PRRT_kwDORt3w8N5Ub6Sa -f b="The refactor moved this but kept yaml.Loader; fixed in $sha with SafeLoader."
gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' -f t=PRRT_kwDORt3w8N5Ub6Sb -f b="Addressed in 7d3e0aa: the file is read in a with block."
for t in PRRT_kwDORt3w8N5Ub6Sa PRRT_kwDORt3w8N5Ub6Sb; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

PRRT_kwDORt3w8N5Ub6Sa: resolve
PRRT_kwDORt3w8N5Ub6Sb: resolve
