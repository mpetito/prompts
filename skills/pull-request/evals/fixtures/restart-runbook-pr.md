# Pull request context: kestrel-tools/harbor-fetch #77 (fictional)

## Session notes

- I am `rowan-ashby`. Pull request #77 in `kestrel-tools/harbor-fetch` was written by a worker
  session I ran yesterday; it pushed the branch and opened the PR with my `gh` login.
- The sections below are the command outputs for the PR and the file it changes, from a
  checkout of its head (`2c9e7b4`).

## gh api user --jq .login

```
rowan-ashby
```

## gh pr view 77

```
docs(ops): put the restart-first step at the top of the manifest runbook kestrel-tools/harbor-fetch#77
Open • rowan-ashby wants to merge 1 commit into main from docs/restart-first • about 20 hours ago
+9 -2 • ✓ Checks passing
Reviewers: none
Labels: docs
Draft: no

  On-call's first step for a manifest-server page is to restart the server, but the runbook
  lists it fourth, after three diagnosis steps that take about ten minutes. This moves it to
  the top and says when to skip it.

  Validation: rendered the page locally; the links to the dashboard and the restart job
  resolve.

View this pull request on GitHub: https://github.com/kestrel-tools/harbor-fetch/pull/77
```

## gh pr diff 77

```diff
diff --git a/docs/operations.md b/docs/operations.md
--- a/docs/operations.md
+++ b/docs/operations.md
@@ -12,11 +12,18 @@ and a full sync takes about 45 minutes.
 
 ## When a worker cannot fetch the manifest
 
-1. Check the manifest-server dashboard for 5xx responses.
-2. Check the instance's CPU and memory graphs.
-3. Read the last 200 lines of the server log.
-4. Restart the manifest server with the `restart-manifest` job.
+1. Restart the manifest server with the `restart-manifest` job. It takes about a minute and
+   is safe while workers are retrying. Skip this step only if the dashboard shows the
+   server already restarted in the last five minutes.
+2. When the restart job finishes, re-run the failed workers from the scheduler.
+3. If the 503s continue after the restart, check the manifest-server dashboard for 5xx
+   responses, then the instance's CPU and memory graphs.
+4. Read the last 200 lines of the server log and attach them to the incident.
+
+The restart comes first because on-call has asked for the sync to recover before the
+03:00 UTC report deadline; diagnosis can continue after the workers are running again.
```

## git diff --name-only main...HEAD

```
docs/operations.md
```
