# autonomous-loops

Verdict: **needs-work** · SKILL.md body 258 lines · description 911 chars

The skill has a sharp, trigger-rich description, a five-element Loop Anatomy with a copyable template and iteration log, and a clear continue/pivot/stop decision order, so it works as a feedback-loop workflow. The biggest gap is that the fragile GitHub wait sequences (Copilot re-review polling, merge-then-deploy watching) are left as hand-rolled jq and prose even though the collection already ships watch-gates.sh and land.sh for them. Around it, the GitHub Actions troubleshooting facts, the opening paragraphs that repeat the description, and three restatements of the polling rule bulk up a body that should be an overview.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names CI/checks, PR, Lighthouse/PSI, vulnerability scan, Copilot review, deploys, MCP evaluators; ends with the collection's Not-for clause. |
| Description includes both what the Skill does and when to use it | pass | 'Run iterative agent loops against an external evaluation signal...' plus 'Use whenever a request repeats work until an outside system says done'. |
| SKILL.md body is under 500 lines | pass | 258 body lines; description 911 chars (under 1,024). |
| Additional details are in separate files (if needed) | partial | No references/ folder; a 14-row Common Issues table full of GitHub Actions specifics and four worked examples all sit inline. |
| No time-sensitive information (or in an 'old patterns' section) | partial | Observed Copilot latency 'about 8–13 minutes' and an undocumented verdict string are labelled as observations, but they will drift and are not dated. |
| Consistent terminology throughout | partial | The loop record is called 'session memory', 'session log', 'iteration log' and 'loop-<name>.md'; the async primitive is 'mode=async terminal', 'async-terminal notifications', 'the host's background task'. See Also says '/pr-feedback, /pr-resolve prompts' although the README says the collection has no prompts concept. |
| Examples are concrete, not abstract | pass | Examples A–D give concrete objectives, budgets, commands and escalation rules. |
| File references are one level deep | pass | All links go directly from SKILL.md to sibling skills or their reference files; the linked flake-triage anchor and Test-PrThreadsResolved.ps1 exist. |
| Progressive disclosure used appropriately | partial | Everything is inline. The GitHub run, merge-ref and timeout troubleshooting is only needed on some loops. |
| Workflows have clear steps | pass | Procedure steps 1–6 with an ordered stop-condition check; each example has numbered steps. |
| Scripts solve problems rather than defer to Claude | fail | No bundled scripts. The Copilot re-review wait and the merge/deploy/live-verify sequence are given as jq and prose for the model to rebuild each time, although ../orchestration-ops/scripts/watch-gates.sh and land.sh already implement them. |
| No 'voodoo constants' (all values justified) | pass | Budgets carry reasons ('PSI is noisy', 'Copilot rarely adds new comments after that'); the 15-minute deadline is tied to observed latency; the job cap cites the default of 360. |
| Required packages listed in instructions and verified as available | partial | Depends on gh and jq (via --jq) and on PowerShell pr-scripts without saying so; acceptable given the collection README lists gh/PowerShell. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | Merge is pinned with --match-head-commit, the deploy SHA is verified live, and the merge ref is checked with merge-base --is-ancestor. |
| Feedback loops included for quality-critical tasks | pass | The whole skill is an evaluate-log-decide loop with a regression rule. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 negative) but no behaviour cases with assertions. The with-skill vs without-skill delta can measure only triggering, not whether loops are run correctly. |

## Findings

1. **high** · Set appropriate degrees of freedom (low freedom for fragile sequences); Provide utility scripts; Solve, don't defer · SKILL.md, B. Working Through Copilot PR Feedback > Polling Copilot re-review (lines 166-187), and D. Merge and Release (lines 211-218)
   > gh pr view <PR#> --json reviewRequests,reviews,commits --jq '
  { rereview_pending: ([.reviewRequests[].login] | map(test("copilot"; "i")) | any), ...

   Fix: Replace the jq block, its three-case interpretation and the backoff prose with a one-line instruction to run ../orchestration-ops/scripts/watch-gates.sh <pr> <head-sha> --bot copilot --minutes 15. Replace D steps 1-6 with ../orchestration-ops/scripts/land.sh, keeping only the live-verify step. watch-gates.sh keys on review commit_id == head, which is more reliable than the timestamp comparison here, because committedDate can predate the push.

2. **medium** · Progressive disclosure patterns (Pattern 3, conditional details); Concise is key · SKILL.md, Common Issues table rows on merge refs, watcher, no run, no deploy run, time-limit cancel and stalled install (lines 235-240)
   > | Re-running a PR's failed job ignores a fix merged since | A `pull_request` run uses the merge commit on `refs/pull/<N>/merge`, and a re-run reuses the original run's commit and ref (GitHub docs)...

   Fix: Move the six GitHub Actions-specific rows, plus the merge-when-green and deployment rows of the wait table, into references/github-actions.md with a one-line pointer: 'CI or deploy run missing, stale or cancelled: see references/github-actions.md'. Keep only the generic loop failures (tight polling, stale data, repeated fix, budget exhausted) in SKILL.md.

3. **medium** · Concise is key (Claude is already very smart; the description already carries when-to-use) · SKILL.md, intro and When to Use (lines 8-21)
   > Single-shot edits do not need this skill. Use it when the path to "done" is iterative...
If the task is "edit file X" or "fix this error", do not wrap it in a loop — just do it.

   Fix: Delete the intro paragraphs and the four When to Use bullets. They restate the description, which is all the model sees when choosing a skill, and they say 'single-shot edits do not need this skill' twice. Keep the agent-model-selection paragraph as a short note under Procedure step 1.

4. **medium** · Concise is key; Use consistent terminology (one statement per rule) · SKILL.md, step 3 (line 91), Common Issues row 1 (line 227), Anti-Patterns (line 247); also lines 55-63 vs 231 and 115 vs 229
   > **Prefer push-style waits** (blocking watch commands, async-terminal notifications) over polling... use **backoff** (≥ 30s between checks) and a **hard cap**

   Fix: State the polling rule once, in step 3, and drop the Common Issues 'tight loop' row and the Start-Sleep anti-pattern. Likewise drop the compaction row (already in Loop Anatomy) and the 'same fix tried repeatedly' row (already stop condition 4).

5. **low** · Use consistent terminology · SKILL.md, Loop Anatomy (line 32), step 4 (line 95), step 3 table and line 91
   > record them in session memory ... append to the session log ... `mode=async` terminal or the host's background task ... async-terminal notifications

   Fix: Name the record once ('the loop file, loop-<name>.md') and use only that. Name the async primitive once ('a background command and its completion notification'), and give the VS Code `mode=async` spelling as a single parenthetical host example.

6. **low** · Use consistent terminology; Observe how Claude navigates Skills (ignored or misleading links) · SKILL.md, See Also (lines 256-262)
   > - `/pr-feedback`, `/pr-resolve` prompts — single-pass building blocks used inside loops
- [skill-authoring](../skill-authoring/SKILL.md) — how this skill is structured

   Fix: Delete both lines. The README says 'There is no separate prompts/ concept', and pr-feedback/pr-resolve are already linked two lines above. The skill-authoring link does not help someone running a loop. Also drop the agent-orchestration and playwright entries, which are already linked inline in Examples C and D.

7. **low** · Avoid time-sensitive information · SKILL.md, Polling Copilot re-review (lines 185-187)
   > Reviews have arrived about 8–13 minutes after a push (observed; GitHub documents no latency)... A summary verdict such as "Needs a closer look" ... (observed; undocumented)

   Fix: Add an observation date to these two observed-behaviour claims, or move them with the GitHub specifics into the reference file, so a future reader knows to re-measure. Also drop 'Re-requesting Copilot review via API/CLI is not fully supported in all scenarios', which is vague and gives no action.

8. **low** · Build evaluations first; Checklist: At least three evaluations created · evals/shared-benchmark.json
   > "kind": "trigger" (all 8 cases); "assertions": []

   Fix: Add at least three behaviour cases with assertions on observable conduct: the agent writes the loop template with Success and Budget before acting, it uses gh pr checks --watch or a background wait instead of a bare sleep, and it stops and escalates on a repeated identical failure. Then the CONTRIBUTING paired-delta check can show whether a shortened body keeps its value.

## Strengths

- A Loop Anatomy table plus a fill-in template and a per-iteration log format: a strict template other workflow skills can copy so state survives compaction.
- An explicit ordered stop-condition check (success, budget, no-progress, repeated failure, otherwise a new hypothesis) that turns a feedback loop into a decision procedure rather than 'keep trying'.
- A precise, trigger-tested description: plain-language paraphrases of each loop type, a 'load before the first command' timing cue, and negative cases in evals that mirror the Not-for clause.

## Cut candidates

- Intro paragraphs under '# Autonomous Loops Skill' (lines 8-10): restate the description
- 'When to Use' bullets and 'If the task is "edit file X"... just do it' (lines 14-21)
- Common Issues rows 'Agent polls in a tight loop', 'Context compaction loses the loop definition' and 'Same fix tried repeatedly' (duplicate step 3, Loop Anatomy and stop condition 4)
- Anti-Patterns bullet on `Start-Sleep 30` (third statement of the polling rule)
- Polling Copilot re-review jq block and interpretation (replace with orchestration-ops/scripts/watch-gates.sh)
- See Also lines for '/pr-feedback, /pr-resolve prompts' and 'skill-authoring — how this skill is structured'
