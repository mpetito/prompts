---
name: autonomous-loops
description: "Run iterative agent loops against an external evaluation signal that arrives asynchronously. Use when a task is not single-shot: raising Page Speed Insights scores, triaging Copilot PR feedback, watching CI until green, merging and releasing when every merge deploys, or waiting on deploys, scans, or MCP evaluators."
---

# Autonomous Loops Skill

Procedural knowledge for designing and running agent loops where progress depends on an **external evaluation signal** that arrives **asynchronously** (CI checks, deployments, Copilot reviews, Lighthouse runs, security scans, etc.).

Single-shot edits do not need this skill. Use it when the path to "done" is iterative and the verdict on each iteration comes from a system the agent does not control.

---

## When to Use

- The objective is a **measurable target**, not a code change (e.g. "PSI Performance ≥ 90", "all PR checks green", "no unresolved Copilot review threads").
- Verifying the outcome **requires an external system** to run first (deploy, CI pipeline, MCP evaluator, security scan, reviewer bot).
- Each iteration may **invalidate previous results** — fixes can introduce regressions, Copilot may add new comments after a push, CI flakes.
- A single attempt is unlikely to succeed; **incremental improvement** is expected.

If the task is "edit file X" or "fix this error", do not wrap it in a loop — just do it.

When a loop delegates work or generates a dynamic workflow, apply
[agent model selection](../skill-authoring/references/agent-model-selection.md) before launch.
Record explicit models per worker/stage alongside the iteration budget, including evaluators
and retries. Waiting and collecting output do not need the coordinator's premium model.

---

## Loop Anatomy

Every autonomous loop has the same five elements. Define them **explicitly before starting** and record them in session memory so they survive context compaction.

| Element               | What to capture                                                        |
| --------------------- | ---------------------------------------------------------------------- |
| **Objective**         | The measurable goal in one sentence. Include the metric and target.    |
| **Evaluation method** | The exact tool / command / MCP call that produces the verdict.         |
| **Stop conditions**   | Success criteria **and** budget limits (max iterations, time, cost).   |
| **Iteration steps**   | The ordered sequence performed each loop, including async wait points. |
| **Escalation rule**   | When to break out and ask the user instead of iterating again.         |

### Template

```markdown
## Loop: <name>

- **Objective**: <metric> reaches <target> on <scope>
- **Evaluation**: <tool / command / MCP call>
- **Success**: <exact pass condition>
- **Budget**: max <N> iterations, stop after <M> consecutive no-progress runs
- **Steps**: <ordered list, mark async waits>
- **Escalate when**: <ambiguous failure, repeated same error, budget exhausted>
```

Persist this as `loop-<name>.md` at the start, and update the iteration log there after
every run. Write it to whichever location the host provides, in this order of preference:

1. The session's persistent memory directory, when the host names one (Claude Code).
2. `/memories/session/loop-<name>.md`, on hosts exposing a memory tool.
3. The session scratchpad or a `.gitignore`d working file, when neither exists.

The point is survival across context compaction — any location the agent can re-read at
the top of each iteration works. Never commit the loop log to the repository.

---

## Procedure

### 1. Define the loop before acting

Do not start fixing things and then "see how it goes". Fill out the template above first. If any element is unclear (especially **Evaluation** and **Success**), ask the user one question rather than guessing.

### 2. Run one iteration end-to-end

Execute the steps in order. Treat each iteration as atomic — finish it (including the async wait and the new evaluation) before deciding what to change next.

### 3. Wait for async work correctly

Async waits are the part most likely to go wrong. Pick the right primitive:

| Wait target               | Correct mechanism                                                                                                 |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| GitHub CI checks          | `gh pr checks <pr> --watch --fail-fast` (sync terminal — blocks until done). Without `--watch` it exits 8 while checks are pending (`gh pr checks --help`); that is not a failure |
| Merge-when-green watcher  | Key on the head SHA and the newest run per workflow: `gh run list --commit <sha> --workflow <file> --limit 1` (newest first). Poll until that run exists, then `gh run watch`. Re-arm after a close and reopen |
| GitHub Actions run        | `gh run watch <run-id> --exit-status`                                                                             |
| Long build, deploy or local suite | One background command writing a log (`mode=async` terminal or the host's background task), then act on the completion notification once. No interval polling or progress narration |
| Copilot PR review         | Poll `gh pr view --json reviewRequests,reviews,commits` (see [example B](#b-working-through-copilot-pr-feedback)) |
| Deployment of `main`      | Find the run for the merge commit (`gh run list --commit <merge-sha> --workflow <deploy-file>`), watch it, then verify the URL serves the new build SHA. No run after about 2 minutes: see [Common Issues](#common-issues) |
| Third-party scan / MCP    | Call the evaluation tool directly; if it queues, poll with backoff (≥ 30s)                                        |

**Prefer push-style waits** (blocking watch commands, async-terminal notifications) over polling. Use polling only when the evaluator exposes no completion signal — and when you do, use **backoff** (≥ 30s between checks) and a **hard cap** on attempts. Avoid `Start-Sleep` / `sleep` for fixed delays except as the spacer inside an explicit poll loop with a cap.

### 4. Evaluate and log

After each iteration, run the evaluation tool exactly as defined and append to the session log:

```markdown
### Iteration <N> — <timestamp>

- **Change**: <one-line summary of what was modified>
- **Result**: <metric value> (delta: <±X>)
- **Status**: improved | regressed | no-change | failed
- **Next**: <hypothesis for next iteration, or "stop">
```

Compare against the previous iteration, not just the target. A regression is a signal to revert or reconsider, not push harder.

### 5. Decide: continue, pivot, or stop

After logging, check stop conditions in order:

1. **Success met?** → stop, report outcome.
2. **Budget exhausted?** → stop, summarize progress and remaining gap.
3. **No progress for N consecutive iterations?** → pivot strategy or escalate.
4. **Same failure repeating?** → stop and escalate. Do not retry the same approach.
5. Otherwise → next iteration with a **new** hypothesis.

### 6. Report on exit

Always produce a final summary: objective, final metric vs. target, iterations used, what worked, what was tried and abandoned, and any follow-ups for the user.

---

## Example Loops

### A. Page Speed Insights Optimization

- **Objective**: PSI mobile Performance score ≥ 90 on `<url>`
- **Evaluation**: PSI MCP tool against the deployed dev URL
- **Success**: Performance ≥ 90 on two consecutive runs (PSI is noisy)
- **Budget**: 6 iterations
- **Steps**:
  1. Run PSI evaluation; record LCP, CLS, INP, TBT, opportunities.
  2. Pick the **single highest-impact** opportunity; implement the fix.
  3. `/commit` and push to the PR branch.
  4. **Wait**: `gh pr checks <pr> --watch --fail-fast` (sync).
  5. Address any CI failures; goto 3 if changes were needed.
  6. Merge the PR (ask the user before merging).
  7. **Wait**: `gh run watch <deploy-run-id> --exit-status`.
  8. Verify the dev URL serves the new build (check a known asset hash or `/version` endpoint).
  9. Re-run PSI; goto 2 if not yet at target.
- **Escalate when**: two consecutive iterations show no improvement, or PSI flags an issue requiring infra changes (CDN, hosting tier).

### B. Working Through Copilot PR Feedback

Load [pr-feedback](../pr-feedback/SKILL.md) for collection and evidence-based triage, and
[pr-resolve](../pr-resolve/SKILL.md) for authorized thread actions.

- **Objective**: All Copilot findings triaged, accepted fixes verified, and PR checks green
- **Evaluation**: `../pr-scripts/Test-PrThreadsResolved.ps1` (unresolved threads) **and** `gh pr checks` (status); on failures, `../pr-scripts/Get-PrCheckFailures.ps1` returns the failing checks with log excerpts
- **Success**: All visible and suppressed findings have evidence-backed dispositions, accepted
  fixes pass checks on the latest commit, and threads are resolved where authorized. Report
  intentionally open disagreements/deferred work; do not claim all threads are resolved
- **Budget**: 4 iterations (Copilot rarely adds new comments after that)
- **Steps**:
  1. Fetch unresolved threads and full review bodies, including suppressed sections.
  2. Verify each claim with `pr-feedback`; change only accepted findings, using the smallest
     correct fix. Retain evidence for false positives, unnecessary complexity, and deferrals.
  3. `/commit` and push.
  4. **Wait**: `gh pr checks <pr> --watch --fail-fast`.
  5. **Wait** for Copilot's re-review (if one is going to run) by polling the PR state — see [Polling Copilot re-review](#polling-copilot-re-review) below.
  6. Reply to addressed threads (cite the commit SHA), resolve them.
  7. Re-fetch threads and review bodies; if new claims appeared, goto 2.
- **Escalate when**: Copilot repeatedly flags the same line after two attempts (likely a disagreement, not a defect) — surface it to the user with both perspectives.

#### Polling Copilot re-review

Copilot does not always re-review on every push, and when it does the latency is variable. Compare the latest Copilot review timestamp against the head commit, and check whether Copilot is currently in `reviewRequests`:

```bash
gh pr view <PR#> --json reviewRequests,reviews,commits --jq '
  {
    rereview_pending: ([.reviewRequests[].login] | map(test("copilot"; "i")) | any),
    last_copilot_review: ([.reviews[] | select(.author.login | test("copilot"; "i"))] | sort_by(.submittedAt) | last),
    last_commit: (.commits | sort_by(.commit.committedDate) | last.commit.committedDate)
  }'
```

Interpretation:

- `rereview_pending: true` → Copilot is queued or running. Wait and re-poll.
- `last_copilot_review.submittedAt >= last_commit` and not pending → re-review complete; proceed.
- `last_copilot_review.submittedAt < last_commit` and not pending → no re-review was triggered for this push; proceed without waiting further.

Poll with backoff (e.g. 30s, 60s, 120s) and a hard cap (e.g. 5 attempts) before giving up and proceeding. Re-requesting Copilot review via API/CLI is not fully supported in all scenarios, but the read path above does reflect re-requested state once it has been triggered.

Reviews have arrived about 8–13 minutes after a push (observed; GitHub documents no latency), so set the deadline at about 15 minutes after the push. A summary verdict such as "Needs a closer look" with no inline comments is informational (observed; undocumented): gate on unresolved threads, and report the verdict and the findings separately.

### C. Watching CI Until Green

- **Objective**: Latest commit on `<branch>` passes all required checks
- **Evaluation**: `gh pr checks <pr>` exit status (8 means still pending)
- **Success**: All required checks pass; non-required failures noted but not blocking.
- **Budget**: 3 fix iterations (flakes excluded)
- **Steps**:
  1. **Wait**: `gh pr checks <pr> --watch --fail-fast` (sync — blocks until terminal state).
  2. If green, stop.
  3. If failed, fetch logs for the failing job: `gh run view <run-id> --log-failed`.
  4. Diagnose: real failure, flake, or cancelled at the time cap. **Do not** blindly re-run flakes more than once; a re-run tests the same merge commit, so it cannot pick up a fix merged since. Browser-test flakes: [flake triage](../playwright-e2e/references/stability.md#flake-triage).
  5. Apply fix, `/commit`, push, goto 1.
- **Escalate when**: same job fails twice with different errors (environment issue), or fix requires touching code outside the PR's scope.

### D. Merge and Release When Every Merge Deploys

This is the loop. When to pause, what needs approval and the preflight before the first deploy are policy in [agent-orchestration](../agent-orchestration/SKILL.md).

- **Objective**: each approved PR is merged and verified live before the next one merges
- **Evaluation**: the deploy run for the merge commit, then a live check of the served build
- **Success**: the deploy run is green, and production serves the merge SHA with the change working
- **Budget**: one PR in flight; stop at the first failed or rolled-back release
- **Steps**:
  1. Read the head SHA (`gh pr view <pr> --json headRefOid`). Confirm `gh pr checks <pr> --required` passes and the approval is for that SHA.
  2. Merge pinned to that head: `gh pr merge <pr> --squash --match-head-commit <sha>`.
  3. Read the merge commit: `gh pr view <pr> --json mergeCommit --jq .mergeCommit.oid`.
  4. **Wait** for the deploy run: `gh run list --commit <merge-sha> --workflow <deploy-file> --limit 1 --json databaseId,status,conclusion`. No run after about 2 minutes: dispatch it (see [Common Issues](#common-issues)).
  5. **Wait**: `gh run watch <run-id> --exit-status`.
  6. Verify live: production serves the merge SHA and the change behaves as intended.
  7. If the next PR touches the same files or the deploy path, merge the base into it and wait for fresh checks; a re-run would test its old merge commit.
- **Escalate when**: a release fails or rolls back. Stop merging and follow the release policy in agent-orchestration.

---

## Common Issues

| Problem                                                       | Solution                                                                                                                                                                |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Agent polls in a tight loop ("is it done yet?")               | Prefer a blocking watch (`gh pr checks --watch`, `gh run watch`) or `mode=async` + notification. If polling is unavoidable, use backoff (≥ 30s) and a hard attempt cap. |
| Evaluation passes locally but fails in the deployed env       | Always evaluate against the **deployed** artifact, not the local build. Verify the deploy SHA before re-evaluating.                                                     |
| Same fix tried repeatedly with the same failure               | Stop after the second identical failure. Re-read the error, change strategy, or escalate.                                                                               |
| Loop "succeeds" but on stale data (cached PSI, old PR view)   | Re-fetch evaluation inputs each iteration. For PSI, run twice and require both above target.                                                                            |
| Context compaction loses the loop definition                  | Persist objective, evaluation, and iteration log to `loop-<name>.md` in the host's memory location (see **Loop Anatomy**); re-read at the top of each loop.              |
| Copilot adds new threads after a push, agent thinks it's done | After resolving threads + push, **always** wait for the next review pass before declaring success.                                                                      |
| Merging the PR breaks the deploy                              | Merge only with the user's go-ahead or a standing approval rule. Treat merge, deploy and live check as one step ([example D](#d-merge-and-release-when-every-merge-deploys)). |
| Budget exhausted with partial progress                        | Stop. Report metric delta, what was tried, and the recommended next direction. Do not silently keep iterating.                                                          |
| Re-running a PR's failed job ignores a fix merged since       | A `pull_request` run uses the merge commit on `refs/pull/<N>/merge`, and a re-run reuses the original run's commit and ref (GitHub docs). Merge the base into the branch, or close and reopen the PR. Then confirm the merge ref contains the fix (`git fetch origin refs/pull/<N>/merge`, then `git merge-base --is-ancestor <fix-sha> FETCH_HEAD`). |
| Watcher acts on a stale run, or exits before the run exists   | Key on (head SHA, newest run per workflow) and poll until the expected run appears. Report why it did not merge: conflict, cancelled at the time cap, real failure, or watcher deadline. |
| No run appears for a PR                                       | GitHub skips `pull_request` workflows while the PR has a merge conflict. Resolve it, then re-arm the watcher.                                                           |
| No deploy run appears after a merge                           | Check `gh run list --commit <merge-sha>` after about 2 minutes. Events made with `GITHUB_TOKEN` start no runs (except `workflow_dispatch` and `repository_dispatch`). Dispatch it with `gh workflow run <deploy-file> --ref main`; give deploy workflows a `workflow_dispatch` trigger and make them idempotent. |
| A CI job "fails" near its time limit                          | GitHub cancels a job at `timeout-minutes` (default 360). Treat cancelled-at-cap as its own state, not a test failure, and track job duration against the cap.             |
| A stalled install fails a deploy or smoke job and rolls back  | Give dependency and browser installs in deploy and smoke jobs a step-level `timeout-minutes` and a retry loop. The job cap would otherwise trigger the rollback.          |

---

## Anti-Patterns

- ❌ Starting the loop without a written **Success** condition — you will not know when to stop.
- ❌ `Start-Sleep 30` between status checks **as a fixed wait** — prefer a watch command or async notification. If the evaluator only supports polling, wrap `Start-Sleep` in a capped backoff loop, not a bare delay.
- ❌ Running the evaluation against `localhost` when the objective requires the deployed environment.
- ❌ Bundling unrelated fixes into one iteration — you cannot attribute the metric change.
- ❌ Treating a regression as noise. Investigate before pushing through.
- ❌ Open-ended "keep going until it's good" loops with no iteration cap.
- ❌ Force-pushing or amending merged commits to "retry" — the loop iterates forward, not backward.

---

## See Also

- [pr-feedback](../pr-feedback/SKILL.md) and [pr-resolve](../pr-resolve/SKILL.md) — review thread tooling used by the Copilot-feedback loop
- [agent-orchestration](../agent-orchestration/SKILL.md) — release policy and the multi-lane loop that runs these waits
- [playwright-e2e stability](../playwright-e2e/references/stability.md) — flake triage and CI artifacts for browser tests
- `/pr-feedback`, `/pr-resolve` prompts — single-pass building blocks used inside loops
- [skill-authoring](../skill-authoring/SKILL.md) — how this skill is structured
