The fix commit `4be91c2` is local only (`git status`: ahead of origin by 1), so I push it before saying "fixed" anywhere.

```bash
git push
sha=$(git rev-parse --short HEAD)   # 4be91c2
gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' \
  -f t=PRRT_kwDOQx7a1M5Tr1Ka -f b="Fixed in $sha: the timeout now reaches client.get."
gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t=PRRT_kwDOQx7a1M5Tr1Ka
gh api graphql -f query='mutation($t:ID!,$b:String!){addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$t,body:$b}){comment{id}}}' \
  -f t=PRRT_kwDOQx7a1M5Tr1Kb -f b="Fixed in $sha: the default is 5.0 seconds now."
gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t=PRRT_kwDOQx7a1M5Tr1Kb
```

Stop after the second resolve.

- `PRRT_kwDOQx7a1M5Tr1Ka`: resolve
- `PRRT_kwDOQx7a1M5Tr1Kb`: resolve
