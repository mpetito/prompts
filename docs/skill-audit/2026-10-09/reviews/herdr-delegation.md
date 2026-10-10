# herdr-delegation

Verdict: **needs-work** · SKILL.md body 366 lines · description 1006 chars

The skill's guidance comes from observed failures: exact error strings, the exit-0-on-blocked trap, dialog defaults and teardown ordering, each with a concrete command. Its main gap is size. A single 366-line file repeats its traps in a Common Issues table, carries Codex flag detail, worktree teardown and version provenance inline, and absorbs orchestration content (budget meter, multi-peer sweeps) that its own description assigns to agent-orchestration.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names Herdr, panes, splits, worktrees, Codex/Claude/Copilot, approval dialogs, plus a disambiguation clause. |
| Description includes both what the Skill does and when to use it | pass | What: drive agents in Herdr panes; when: 'Use whenever a request puts an agent in another terminal, pane, or split'. At 1006 of 1024 chars it leaves no room for any trigger edit. |
| SKILL.md body is under 500 lines | pass | 366 body lines (370 total minus 4 frontmatter). |
| Additional details are in separate files (if needed) | fail | No references/ folder. Codex start flags, worktree teardown, the budget meter and version provenance all sit inline. |
| No time-sensitive information (or in an 'old patterns' section) | partial | Verification Status pins Claude Code v2.1.x, gpt-5.6-sol, Codex CLI 0.157.1, herdr 0.9.1 in the main body. |
| Consistent terminology throughout | pass | peer / agent / harness / settled / result file are used consistently. |
| Examples are concrete, not abstract | pass | Every trap has an exact command and error string. |
| File references are one level deep | partial | codex-exec.sh and meter.sh are reached through ../orchestration-ops/SKILL.md rather than linked directly. |
| Progressive disclosure used appropriately | partial | herdr --skill is delegated well, but the skill's own detail is not split out. |
| Workflows have clear steps | pass | Delegating to a Peer is numbered 1-5; Teardown order is sequenced and verified. |
| Scripts solve problems rather than defer to Claude | not-applicable | No bundled scripts; uses orchestration-ops scripts by reference. |
| No 'voodoo constants' (all values justified) | partial | --timeout 5400000 is unexplained, and 120000 contradicts the text saying the 30s default is usually fine. |
| Required packages listed in instructions and verified as available | partial | Prerequisites check HERDR_ENV, but every status snippet also needs jq, and nothing checks for it. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | Check the status rather than the exit code, check that the result file exists, read the dialog before sending keys, and verify teardown with workspace list and ls. |
| Feedback loops included for quality-critical tasks | pass | 'After any blocked episode, check the peer's result against everything you asked it.' |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 negative) but no behavior cases with assertions, so the trap guidance itself is untested. |

## Findings

1. **medium** · Concise is key · SKILL.md, Common Issues (lines 337-356)
   > | `agent_prompt_stalled` | Text in composer, unsubmitted | `agent send-keys <name> enter`; never re-prompt |
| Exit 0 but nothing happened | `--wait` settled on `blocked` | Branch on `.result.agent.agent_status` |

   Fix: About 12 of the 16 rows restate traps 1-4, Blocked Agents and Teardown order nearly word for word. Keep only the rows with no section of their own (the --approve-for-me/--sandbox conflict, done vs idle, the per-commit .git approval), or fold those into their sections and delete the table. (about 350 tokens saved)

2. **medium** · Progressive disclosure patterns / Additional details are in separate files · SKILL.md, Delegating to a Peer step 2 (lines 82-101), Worktree Delegation and Teardown order (lines 289-323)
   > - Codex keeps `<writable root>/.git` read-only, including the git directory that a worktree's
  `.git` file points to.

   Fix: Move the long-lived Codex peer flags and sandbox notes to references/codex-peer.md, and move Worktree Delegation with its teardown sequence to references/worktrees.md. Link both directly from SKILL.md with a one-line 'For a long-lived Codex peer, see …' (Pattern 3, conditional details). (about 900 tokens saved)

3. **medium** · Concise is key; Use consistent terminology (scope matches the description's own disambiguation) · SKILL.md, Cross-Harness Prompt Contract 'The budget' bullet (lines 178-187), and the queue-file and sweep bullets in Watching Long Tasks (lines 148-158)
   > Above 70%, stop launching
  new Codex lanes; the switch and the limit-stop checklist are in
  [agent-orchestration](../agent-orchestration/SKILL.md). One build exhausted the weekly meter in
  36 hours

   Fix: The description excludes 'orchestrating lanes … for a whole build (agent-orchestration)' and brief writing (agent-briefs), yet the body carries the meter procedure, a 70% lane threshold, an anecdote, and multi-peer sweep policy. Replace these with one line: 'For a metered Codex peer, put the remaining budget in the prompt; reading the meter and lane limits are in agent-orchestration and orchestration-ops.' (about 300 tokens saved)

4. **medium** · Avoid time-sensitive information · SKILL.md, Verification Status (lines 360-370)
   > Behavior confirmed on Windows 11 with Herdr panes running Claude Code v2.1.x and Codex (`gpt-5.6-sol`).
The Codex notes were observed with Codex CLI 0.157.1 on Linux, driven by herdr 0.9.1

   Fix: Keep one sentence in SKILL.md: 'Harness-specific notes are verified only for Claude Code and Codex; re-check them for other kinds.' Move the version-pinned provenance to the references file or to a collapsed <details> block. (about 220 tokens saved)

5. **medium** · Provide utility scripts / Set appropriate degrees of freedom (low freedom for fragile operations) · SKILL.md, Delegating step 4, Watching Long Tasks bullets 2-3, Reading Peer State traps 1-3
   > Claude Code appends an
  `[exited with code N]` line to the task output, so parse only the first line as JSON. `idle` or `done` means
  the peer settled, not that it succeeded.

   Fix: Classifying a wait is a fragile sequence spread across three sections: parse the first line, branch on agent_status or error.code, check that the result file exists, and spot an instant return. Put it in scripts/wait-peer.sh <name> <result-path> <timeout-ms>, which prints one verdict (ok, blocked, stalled, no-result, timeout), and have the prose say 'Run it and act on the verdict'. (about 150 tokens saved)

6. **low** · No 'voodoo constants' (Solve, don't defer) · SKILL.md, Delegating step 2 (lines 77-80) and Watching Long Tasks (line 131)
   > Startup ran ~5s for both `claude` and `codex` even with a large MCP config. A 120s timeout is ample; 30s (the default) is usually fine.

   Fix: The example passes --timeout 120000 while the next sentence says the default is usually fine. Drop the flag or the sentence. Label --timeout 5400000 inline as 90 minutes and say why that window was chosen. (about 30 tokens saved)

7. **low** · Concise is key (Claude reads SKILL.md only after the description triggers) · SKILL.md, intro and When to Use (lines 10-21)
   > This skill covers what that costs in practice: the handoff contract, the failure modes, and the safety rules.
...
## When to Use

   Fix: The When to Use bullets repeat the description, and the meta sentence describes the skill to itself. Delete both and keep the HERDR_ENV paragraph and the 'Run `herdr --skill` for command syntax' pointer. Similar provenance asides ('Four traps, each observed in practice', 'verified byte-identical screen afterward') can go too. (about 130 tokens saved)

8. **low** · Avoid deeply nested references / Avoid assuming tools are installed · SKILL.md, Peer or Subagent? (lines 45-50) and Prerequisites (lines 23-29)
   > Use the launcher in
[orchestration-ops](../orchestration-ops/SKILL.md) (`codex-exec.sh`)

   Fix: Link the scripts directly (../orchestration-ops/scripts/codex-exec.sh, ../orchestration-ops/scripts/meter.sh) so Claude does not need a second SKILL.md hop to find them. Add `command -v jq` to the Prerequisites check, since every status snippet depends on jq.

## Strengths

- Each failure mode is written as an exact error string, its cause and a copy-ready recovery command (for example, agent_prompt_stalled means the text landed but Enter did not: send-keys enter, never re-prompt). That is concrete, verifiable guidance a model cannot infer on its own.
- It delegates generic CLI syntax to `herdr --skill` ('Do not restate them here') and spends its tokens only on behavior the vendor docs do not cover.
- Claims are scoped to what was tested: the skill names which harnesses and platforms were verified and says to re-check notes for unexercised kinds, so the rules do not overgeneralize.

## Cut candidates

- When to Use (duplicates the description)
- Intro sentence 'This skill covers what that costs in practice…'
- Common Issues table rows that restate Reading Peer State traps 1-4, Blocked Agents and Teardown order
- Cross-Harness Prompt Contract: 'The budget, for a metered peer' bullet (meter procedure, 70% threshold, 36-hour anecdote belong to agent-orchestration/orchestration-ops)
- Watching Long Tasks: 'When several agents are running, sweep every one…' bullet (orchestration policy)
- Verification Status version provenance (Claude Code v2.1.x, gpt-5.6-sol, Codex CLI 0.157.1, herdr 0.9.1)
