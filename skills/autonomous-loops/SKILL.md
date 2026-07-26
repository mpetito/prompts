---
name: autonomous-loops
description: "Procedural knowledge for running autonomous, iterative agent loops against an external evaluation signal. Use when the task is not single-shot — e.g. optimizing Page Speed Insights scores, working through Copilot PR review feedback, watching CI until it goes green, or any workflow that requires waiting on asynchronous external processes (CI, deploys, third-party scans, MCP evaluators) between iterations."
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
| GitHub CI checks          | `gh pr checks <pr> --watch --fail-fast` (sync terminal — blocks until done)                                       |
| GitHub Actions run        | `gh run watch <run-id> --exit-status`                                                                             |
| Long-running build/deploy | `mode=async` terminal, then act on the completion notification — prefer this over polling                         |
| Copilot PR review         | Poll `gh pr view --json reviewRequests,reviews,commits` (see [example B](#b-working-through-copilot-pr-feedback)) |
| Deployment of `main`      | Watch the deploy workflow run, then verify URL responds with the new build SHA                                    |
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

See also: [pr-feedback](../pr-feedback/SKILL.md) and [pr-resolve](../pr-resolve/SKILL.md) for the underlying thread tooling.

- **Objective**: All Copilot review threads resolved and PR checks green
- **Evaluation**: `../pr-scripts/Test-PrThreadsResolved.ps1` (unresolved threads) **and** `gh pr checks` (status); on failures, `../pr-scripts/Get-PrCheckFailures.ps1` returns the failing checks with log excerpts
- **Success**: 0 unresolved threads **and** all checks green on the latest commit
- **Budget**: 4 iterations (Copilot rarely adds new comments after that)
- **Steps**:
  1. Fetch current unresolved review threads.
  2. Group by file; address each with the smallest correct change.
  3. `/commit` and push.
  4. **Wait**: `gh pr checks <pr> --watch --fail-fast`.
  5. **Wait** for Copilot's re-review (if one is going to run) by polling the PR state — see [Polling Copilot re-review](#polling-copilot-re-review) below.
  6. Reply to addressed threads (cite the commit SHA), resolve them.
  7. Re-fetch threads; if new ones appeared, goto 2.
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

### C. Watching CI Until Green

- **Objective**: Latest commit on `<branch>` passes all required checks
- **Evaluation**: `gh pr checks <pr>` exit status
- **Success**: All required checks pass; non-required failures noted but not blocking.
- **Budget**: 3 fix iterations (flakes excluded)
- **Steps**:
  1. **Wait**: `gh pr checks <pr> --watch --fail-fast` (sync — blocks until terminal state).
  2. If green, stop.
  3. If failed, fetch logs for the failing job: `gh run view <run-id> --log-failed`.
  4. Diagnose: real failure vs. flake. **Do not** blindly re-run flakes more than once.
  5. Apply fix, `/commit`, push, goto 1.
- **Escalate when**: same job fails twice with different errors (environment issue), or fix requires touching code outside the PR's scope.

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
| Merging the PR breaks the deploy                              | Ask the user before merging. Treat merge + deploy as one atomic step in the loop, not two independent ones.                                                             |
| Budget exhausted with partial progress                        | Stop. Report metric delta, what was tried, and the recommended next direction. Do not silently keep iterating.                                                          |

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
- `/pr-feedback`, `/pr-resolve` prompts — single-pass building blocks used inside loops
- [skill-authoring](../skill-authoring/SKILL.md) — how this skill is structured
