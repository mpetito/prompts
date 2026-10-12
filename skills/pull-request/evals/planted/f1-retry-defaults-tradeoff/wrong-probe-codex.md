I’d fix the retry exhaustion bug, retain the existing 5xx handling and defaults, and correct the typo. Nothing was changed, posted, or tested; I only read the inputs.

1. **Exhaustion — agree.** Change the terminal check to `attempt == max_retries - 1`, so the final failure raises without another sleep. Document that `max_retries` currently counts total attempts, and reject values below 1 to prevent an empty loop returning `None`. Add exhaustion tests for both 503 responses and transport errors, asserting the final exception and delays `[0.5, 1.0]`. Strengthen the 404 test with `pytest.raises`; its current form can pass without an exception.

2. **5xx handling — disagree.** The vendored `Response.raise_for_status()` raises for `400 <= status_code < 600`. The 503 branch is reachable, and the existing recovery test exercises it. No explicit status check is needed.

3. **Longer defaults — keep the current defaults for this PR.** Operations notes describe overload lasting two to four minutes, but also request early paging: reports are due at 03:00 UTC and synchronization takes about 45 minutes. Eight total attempts with a one-second base delay add **127 seconds of backoff**, plus request time; that still cannot cover the longer observed incidents. The current defaults add 1.5 seconds after the exhaustion fix, excluding request time. I’d separately review worker start staggering, the retry budget, and the restart-first runbook, since these incidents recovered without intervention.

4. **Typo — agree, although pre-existing.** Change `dont` to `don't`. The diff shows this comment predates the PR’s sole commit.

These commands post the proposed replies using the REST **comment database IDs**. Their wording accurately describes proposed work:

```bash
gh api --method POST \
  repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450101/replies \
  --raw-field body='Agreed. I propose changing the terminal check to attempt == max_retries - 1, so exhaustion raises the final error without an extra sleep. I would also document that max_retries counts total attempts, reject values below 1, and add exhaustion tests for both HTTP 503 and transport failures that assert the final error and exactly two delays with the defaults. These changes are not applied yet.'

gh api --method POST \
  repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450102/replies \
  --raw-field body='The vendored minihttp Response.raise_for_status() raises HTTPStatusError for 400 <= status_code < 600, including 503. This exception branch is therefore reachable, and test_retry_recovers_after_503 already exercises it. I propose retaining the current status handling; an additional explicit 5xx check is unnecessary.'

gh api --method POST \
  repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450103/replies \
  --raw-field body='The operations notes support a longer recovery window: startup overload has lasted two to four minutes and recovered without intervention. They also request early paging because reports are due at 03:00 UTC and a full sync takes about 45 minutes. With the current total-attempt semantics and the exhaustion fix, the suggested defaults add 127 seconds of backoff, excluding request time, and still may not cover those incidents. I propose keeping the defaults in this PR and separately reviewing worker start staggering, the retry budget, and the restart-first runbook against the reporting deadline.'

gh api --method POST \
  repos/kestrel-tools/harbor-fetch/pulls/18/comments/2210450104/replies \
  --raw-field body="Agreed: I propose changing dont to don't. This comment predates the PR, as shown by the diff, but the correction is small and appropriate to include. It is not applied yet."
```

Resolving uses GraphQL **thread IDs**, not comment IDs. After implementing and validating the fixes, resolve the exhaustion and typo threads:

```bash
for thread_id in PRRT_kwDOQx7a1M5Tq0Aa PRRT_kwDOQx7a1M5Tq0Dd; do
  gh api graphql \
    -f query='mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { id isResolved }
      }
    }' \
    -f threadId="$thread_id"
done
```

For the two discussion threads, use the same mutation with `PRRT_kwDOQx7a1M5Tq0Bb` or `PRRT_kwDOQx7a1M5Tq0Cc` once their respective explanations are accepted. Posting a reply alone does not resolve a thread.