# orchestration-ops

Verdict: **needs-work** · SKILL.md body 125 lines · description 1014 chars

The SKILL.md is a short, low-freedom procedure. Each step gives an exact command for a documented script that prints one line on exit, and the skill comes with hooks, a hook self-check and offline tests. The most important gap is that every command depends on a `$OPS` shell variable that is set "once per session". Shell state does not carry over between Bash calls on the host, so each `"$OPS/…"` call resolves to `/…` and fails until Claude works out the real path.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names every script's job and gives plain-words triggers (merge this approved PR when CI is green, check the Codex budget). |
| Description includes both what the Skill does and when to use it | pass | Has both, but it is 1014 of the 1024 allowed characters, and the what-list and the trigger-list repeat the same nine moves. |
| SKILL.md body is under 500 lines | pass | 125 body lines. |
| Additional details are in separate files (if needed) | pass | The hooks settings snippet and per-hook rationale are in references/hooks.md. Script usage is in each script's header. |
| No time-sensitive information | pass | The 173-PR anecdote is history, not a dated instruction. |
| Consistent terminology throughout | partial | The description says 'coordinator' and the body says 'orchestrator'. The economy rule in step 2 differs from the rule meter.sh prints. |
| Examples are concrete, not abstract | pass | Every step gives an exact command line with placeholders and its output format. |
| File references are one level deep | pass | SKILL.md links references/hooks.md directly. hooks.md links only to vendor docs. Cross-skill links follow the ../ convention. |
| Progressive disclosure used appropriately | pass | Hooks detail is loaded only at install time. Scripts are run, not read. |
| Workflows have clear steps | pass | Seven numbered steps keyed to orchestrator moments (once per project, every wake, landing, teardown). |
| Scripts solve problems rather than defer to Claude | partial | meter.sh exits with "date: invalid date '@'" when the newest log has no primary rate limit, instead of printing codex=unknown. Missing positional arguments fail with 'unbound variable' instead of a usage message. |
| Error handling is explicit and helpful | partial | land.sh and finish-lane.sh refuse with specific reasons. But if `gh pr merge` fails in land.sh's CLEAN branch, the script falls through to another round and ends with a generic 'after 4 rounds' stop. |
| No voodoo constants (all values justified) | partial | --max-rounds is justified. The 120x20 s check wait, the 12x10 s UNKNOWN wait, 25/240-minute watch caps, the 2 h codex cap, the 70% meter switch and the 70% inode warning are not. |
| Required packages listed in instructions and verified as available | pass | Prerequisites list bash 5, GNU date, jq, python3, gh, git, rsync and codex. |
| Scripts have clear documentation | pass | Every script header gives its usage line and its one-line output contract. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | land.sh proves the carry-over and merges with --match-head-commit. finish-lane.sh archives and refuses on a live agent or uncommitted changes. Step 1 checks that the hooks fire. |
| Feedback loops included for quality-critical tasks | pass | tests/run.sh plus the hook self-check. land.sh stops rather than retrying. |
| At least three evaluations created | fail | There is no evals/ folder. tests/run.sh covers script behaviour only, not skill triggering or use. |
| Runtime environment: make execution intent clear and test file access patterns with real requests | partial | Execution intent is clear (run, in the background). But `$OPS` relies on shell state that the host does not keep between calls. |

## Findings

1. **high** · Runtime environment (test file access patterns with real requests); Provide utility scripts (make execution intent clear) · SKILL.md, Prerequisites (lines 24-25), and every command block in Procedure
   > Call them by absolute
  path from this skill's folder. Set `OPS=<this skill folder>/scripts` once per session

   Fix: Shell variables do not survive between Bash tool calls, so `"$OPS/meter.sh"` runs as `/meter.sh`. Write the literal installed path, `~/.claude/skills/orchestration-ops/scripts/`, which references/hooks.md already assumes, in each command block. Or tell Claude to prefix each call with `OPS=… ;` in the same command.

2. **medium** · Solve, don't defer; Checklist: Error handling is explicit and helpful · scripts/meter.sh lines 12-15; positional args in land.sh, codex-exec.sh, finish-lane.sh, watch-gates.sh
   > read -r used resets < <(grep -h '"used_percent"' "$latest" | tail -1 \
  | jq -r '[.payload.rate_limits.primary.used_percent, .payload.rate_limits.primary.resets_at] | @tsv')

   Fix: When `used` or `resets` is empty or null, print the documented `codex=unknown … verdict=unknown` line. A probe with a log lacking `primary` exits 1 with "date: invalid date '@'", which contradicts the Common Issues row. Check the positional argument count before `shift` and print the usage line. In land.sh, call `stop "merge failed"` when `gh pr merge` fails instead of letting the loop fall through to a generic round-cap stop.

3. **medium** · Writing effective descriptions; Technical notes (description maximum 1,024 characters) · SKILL.md frontmatter description
   > Scripts and hooks that mechanise an orchestrator's recurring moves: stamp the state file with date -u, keep the decision queue … Use whenever a coordinator is about to do one of those by hand, even in plain words: log what just happened in the state file, note a decision…

   Fix: At 1014/1024 characters, any future edit breaks the limit. The nine-item 'what' list is restated as eight trigger phrases. Collapse the first list to one clause, such as 'Scripts and hooks for an orchestrator's recurring moves: state stamps, decision queue, Codex meter, landing, gate and inbox watchers, lane teardown, background codex exec.' Keep the plain-words triggers and the Not-for clause. Use 'orchestrator' throughout, as the body does. (about 60 tokens saved)

4. **medium** · Concise is key ("Does Claude really need this explanation?") · SKILL.md opening paragraph (lines 8-12) and When to Use (lines 14-18)
   > In one 173-PR build, every rule that became a script or a check held (the carry-over proof, the
head-match merge, the attribution grep), and every rule that stayed in a skill paragraph decayed

   Fix: Cut the anecdote. It is motivation for the author, not instruction for Claude. Keep one sentence: 'Policy lives in agent-orchestration; this skill runs it.' The When to Use bullets repeat the description's 'kickoff … and after a compaction'. Drop them, or merge the 'about to type by hand' bullet into that sentence. (about 110 tokens saved)

5. **medium** · Use consistent terminology; Checklist: Consistent terminology throughout · SKILL.md step 2 (lines 49-51) vs scripts/meter.sh lines 21-22
   > On `economy`, switch authors to the
smaller model and drop second reviewers in this turn.

   Fix: meter.sh already prints the authoritative rule, which also pauses live eval rounds and forbids fan-out within 3 h. The SKILL.md paraphrase is a weaker subset that can drift. Replace it with 'Apply the rule line meter.sh prints; on `stop`, arm the wake:' and keep the wake-at command. (about 30 tokens saved)

6. **medium** · Solve, don't defer: avoid voodoo constants (Ousterhout's law) · scripts/land.sh lines 48-56; watch-gates.sh line 8; watch-inbox.sh line 6; codex-exec.sh line 9; meter.sh line 7; hooks/guard-bash.sh line 26
   > for _ in $(seq 1 120); do … sleep 20 …
for _ in $(seq 1 12); do … sleep 10

   Fix: Name these values and give each a one-line reason. land.sh's 40-minute check wait (120 polls of 20 s) is not in its usage header at all. Do the same for the 25- and 240-minute watcher caps, the 2 h codex cap and the 60 s kill-after, the 70% economy switch and the 70% inode threshold, or expose them as documented flags as --max-rounds already is.

7. **low** · Build evaluations first; Checklist: At least three evaluations created · skill folder (no evals/ directory)
   > bash tests/run.sh    # from this folder; offline, uses a throwaway directory

   Fix: tests/run.sh checks the scripts, not whether the skill triggers and is followed. Add an evals/shared-benchmark.json with at least three cases in the collection's skill-eval-harness format: 'merge this approved PR when CI is green' should run land.sh, not gh pr merge. 'Note the time we merged #12 in the state file' should run state.sh log, not a typed time. 'Clean up the finished w3 lane' should run finish-lane.sh, not git worktree remove.

8. **low** · Concise is key; Use consistent terminology (single source per fact) · SKILL.md step 5 last sentence (lines 90-91) and Common Issues row (line 120)
   > Give append-only files such as
a decision log a `merge=union` attribute so a base merge stays conflict-free.

   Fix: The merge=union advice appears twice, and the Common Issues row hard-codes one project's path (`docs/decision-log.md`). Delete the step-5 sentence and generalize the row to '<append-only file> merge=union'. (about 25 tokens saved)

## Strengths

- Every script prints one line with a fixed format and the procedure runs it in the background, so its exit wakes the orchestrator. The low-freedom design ends with 'read the result file, not the log, unless the line says timeout or failed.'
- land.sh turns a fragile, high-stakes operation into a checked sequence: it proves the carry-over, posts the proof as a PR comment, merges only with --match-head-commit, and stops once without retrying. This is the plan-validate-execute pattern done in code.
- The Common Issues table maps each exact script or hook message (`no column`, `remerge-diff touches:`, `codex=unknown`) to the fix, and the hooks come with a self-check command plus offline tests.

## Cut candidates

- Opening paragraph ('In one 173-PR build, every rule that became a script…'): author motivation, not instruction
- When to Use: repeats the description's kickoff/compaction trigger
- Step 2 economy rule prose ('On `economy`, switch authors to the smaller model…'): meter.sh prints the rule
- Step 5 last sentence on merge=union: duplicates the Common Issues row
- references/hooks.md 'Why' column anecdotes ('one stray listener then cost about 30 hours'): the hooks' deny messages already carry the reason
