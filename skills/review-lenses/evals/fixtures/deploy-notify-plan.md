# Plan: deploy notifications in #deploys (for approval)

Repository: `ops-tools`, the team's internal operations tooling. Nothing in it is published as a
package; every script runs from a checkout on the deploy host or in CI. Version `plan-v2`.

Owner's words: "Post to #deploys when a deploy starts and when it finishes, with the version and
who ran it, instead of the old notice in #ops-alerts."

## Steps

1. **Chat client.** Add `notify/slack_client.py` with `post_to_channel(webhook_url, text)`: it
   POSTs `{"text": text}` to a Slack incoming webhook with a 5 second timeout and retries twice on
   a 5xx response, sleeping 1 s and then 2 s.
2. **Deploy notice.** Add `notify/deploy_notice.py`, run as `python -m notify.deploy_notice
   start|finish <version>`. It reads the deploying user from `$USER` and calls
   `post_to_channel(os.environ["DEPLOYS_WEBHOOK_URL"], ...)`. `scripts/deploy.sh` calls it before
   and after the rollout, in place of its current call to `scripts/legacy_notify.sh`.
3. **Housekeeping.** After step 2 nothing calls `scripts/legacy_notify.sh` (a curl to the
   #ops-alerts webhook). Leave it in place with a "DEPRECATED, do not use" header comment, and
   remove it in the Q1 cleanup sprint, in case something we forgot still calls it.
4. **Tests.** Unit tests for `post_to_channel` (success, retry on 503, give up after three
   attempts) and for the two messages `deploy_notice` builds.

## Acceptance

- A deploy run posts a start and a finish message in #deploys, each within 10 seconds of the step.
- The finish message carries the version and the user who ran the deploy.
- `pytest notify/` passes.
