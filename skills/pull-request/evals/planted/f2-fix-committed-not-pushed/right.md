`git status` says the branch is one commit ahead of `origin/feature/fetch-timeout`, so `4be91c2` isn't on the PR yet. Copilot would see replies pointing at a commit that isn't there. Push first, then reply on each thread with the SHA, then resolve each one. No code changes are needed; the fix and its test are already in `4be91c2` (pytest: 5 passed).

```bash
git push
R=repos/kestrel-tools/harbor-fetch/pulls/23/comments
gh api $R/2214410201/replies -f body="Fixed in 4be91c2: fetch_manifest now passes timeout to client.get, and test_timeout_reaches_the_client covers it."
gh api $R/2214410202/replies -f body="Fixed in 4be91c2: the default is now 5.0 seconds, matching the docstring."
for t in PRRT_kwDOQx7a1M5Tr1Ka PRRT_kwDOQx7a1M5Tr1Kb; do
  gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id="$t"
done
```

I stop after the resolve loop.

PRRT_kwDOQx7a1M5Tr1Ka: resolve
PRRT_kwDOQx7a1M5Tr1Kb: resolve
