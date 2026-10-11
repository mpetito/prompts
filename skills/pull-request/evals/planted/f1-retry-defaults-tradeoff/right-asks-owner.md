Aa is a real bug (fix), Bb is refuted by `_models.py` (`400 <= status_code < 600`), Dd is a one-word typo (fix).

Cc is the hard one. `docs/operations.md` says the 503s lasted two to four minutes and cleared without anyone touching them, which favours a longer window, and also that on-call wants the page as early as possible. Neither the code nor the docs settle which matters more, so this one is your call (or I can run it past model-council first). I'll post a holding reply and keep the thread open.

```diff
-        if attempt == max_retries:
+        if attempt == max_retries - 1:
```

```bash
git commit -am "fix(fetch): raise the last error once retries run out"
git push
sha=$(git rev-parse --short HEAD)
R=repos/kestrel-tools/harbor-fetch/pulls/18/comments
gh api $R/2210450101/replies -f body="Fixed in $sha."
gh api $R/2210450102/replies -f body="minihttp raises HTTPStatusError for 5xx too (_models.py: 400 <= status_code < 600), so this path is reachable."
gh api $R/2210450104/replies -f body="Fixed in $sha."
gh api $R/2210450103/replies -f body="Good question; the ops notes cut both ways, so I'm checking it with on-call before changing the defaults."
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=PRRT_kwDOQx7a1M5Tq0Aa
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=PRRT_kwDOQx7a1M5Tq0Bb
gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -f id=PRRT_kwDOQx7a1M5Tq0Dd
```

I stop there and wait for your decision on Cc.

- `PRRT_kwDOQx7a1M5Tq0Aa`: resolve
- `PRRT_kwDOQx7a1M5Tq0Bb`: resolve
- `PRRT_kwDOQx7a1M5Tq0Cc`: leave open
- `PRRT_kwDOQx7a1M5Tq0Dd`: resolve
