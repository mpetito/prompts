# agent-orchestration

Verdict: **needs-work** · SKILL.md body 363 lines · description 984 chars

The skill is well organised: two per-turn rules up front, a routing table to sibling skills, a numbered kickoff and a five-step loop, and a state-file reference whose template carries the resume procedure, all within 363 body lines. The main gap is repetition. Each core rule appears two or three times (the Every Turn rules, the loop, the Common Issues table and the state template), there are about a dozen "In one build…" anecdotes, and inline bash repeats the carry-over and merge logic that `land.sh` in orchestration-ops already runs. Cutting these would save roughly 1,500 tokens and leave one source of truth for the fragile merge step.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names lanes, file ownership, merge gates, decisions list, compaction, Herdr/Codex peers; plain-words triggers; Not-for clause per collection convention. |
| Description includes both what the Skill does and when to use it | pass | What: 'Run a multi-agent build as its orchestrator…'; when: 'Use whenever one build is spread across several agents…'. At 984 of 1,024 characters it has almost no headroom. |
| SKILL.md body is under 500 lines | pass | 363 body lines (367 total minus 4 frontmatter lines), about 3,900 words. |
| Additional details are in separate files (if needed) | partial | The state template is in references/state-file.md, but conditional material (section 6 release safety when every merge deploys, the Away Protocol) stays inline. |
| No time-sensitive information (or in an 'old patterns' section) | partial | Mostly durable. Host behaviour claims such as 'AskUserQuestion stays open until answered by default' and Copilot setting names may drift; the Copilot names are at least linked to GitHub docs. |
| Consistent terminology throughout | fail | 'owner' means both a lane/file owner and the human; 'coordinator' alternates with 'orchestrator'; 'human queue', 'handoff', 'decision queue' and 'decisions list' overlap. |
| Examples are concrete, not abstract | pass | Concrete approval-matrix rows, the wake-source table, exact gh/git commands, and phrasing examples such as 'applies at 18:00Z unless you object'. |
| File references are one level deep | pass | SKILL.md links references/state-file.md directly. The state file's links go to sibling skills (autonomous-loops, orchestration-ops), not to deeper files of this skill. |
| Progressive disclosure used appropriately | partial | Good routing table to sibling skills, but the body re-teaches rules that orchestration-ops scripts already enforce, and keeps conditional sections inline. |
| Workflows have clear steps | pass | Kickoff has 13 numbered decisions; The Loop has five named steps (wake, sweep, act, arm, record); Away Protocol and Close-Out are numbered. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts in this skill. Its helpers live in orchestration-ops. |
| Scripts have clear documentation | partial | SKILL.md names `meter.sh`, `decisions.sh due`, `wake-at.sh` and 'the state helper' with no path or invocation. The state-file Helper scripts table omits meter.sh, decisions.sh and state.sh. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | Carry-over proof, `--match-head-commit`, verify-read-publish (section 8), post-deploy live checks, re-verifying IDs after compaction. |
| Feedback loops included for quality-critical tasks | pass | Review rounds with a cap of three, delta reviews, ruling triage before relay. |
| At least three evaluations created | partial | 8 cases in evals/shared-benchmark.json, but every one is kind 'trigger'. There are no behaviour cases, so the with_skill vs without_skill delta of the body is never measured. |
| Tested with real usage scenarios | pass | The rules and anecdotes come from real builds (646-minute stall, 70 idle hours, a 173-PR build in the sibling skill). |

## Findings

1. **high** · Concise is key; Provide utility scripts (prefer scripts for deterministic operations; make execution intent clear) · SKILL.md section 5 Review and Merge Gates, lines 225-248
   > test "$(git rev-parse "$NEW^1")" = "$APPROVED"     # one merge on top of the approved head
git show --remerge-diff --format= "$NEW"           # empty: no conflict edits or extra changes

   Fix: Replace both bash blocks (the status/merge pair and the three-line carry-over proof) with one instruction: run `$OPS/land.sh <PR> <worktree> …` from orchestration-ops, which already merges the base, proves the carry-over, records it on the PR and merges with `--match-head-commit`. Keep the one-sentence rule (approval is a required status on the exact head; never `--admin`). This leaves one source of truth for a fragile, low-freedom operation. (about 220 tokens saved)

2. **medium** · Concise is key ("Does this paragraph justify its token cost?") · SKILL.md Common Issues, lines 347-367
   > | The loop stalls for hours; a lane idles overnight | A blocking question prompt waits on the human | Ask in a message with a default and keep dispatching ([Every turn](#every-turn)) |

   Fix: Delete the 17-row table, about 590 words. Every row except two restates a rule already in the body, and most link back to it. Move the two that add something (start peers in a stable directory; research briefs of about five questions with the output file written first) into section 2 Sweep and section 1 item 9 as one clause each. (about 700 tokens saved)

3. **medium** · Concise is key ("Default assumption: Claude is already very smart") · SKILL.md lines 23, 63-64, 85-86, 142-143, 146-147, 186, 202, 220-221, 250, 281-283, 321, 322-324
   > In one build, 21 such prompts held the loop for 646 minutes.
the orchestrator still idled about 70 hours on questions whose answers matched the defaults.

   Fix: Keep at most two or three anecdotes where the rule is counter-intuitive (the 646-minute blocking prompt, the 500K-token context), and cut the rest to the bare rule. A capable model follows 'ask once, before the human leaves, for the class' without the seven-hour story. If the history must survive, put the war stories in a references/evidence.md that SKILL.md never needs to load. (about 350 tokens saved)

4. **medium** · Use consistent terminology · SKILL.md lines 48, 73, 85-86, 194, 202, 323; section 3 and Away Protocol
   > surprise in the human queue with an owner.
one build the owner asked for visible progress … the owner never saw.

   Fix: Use 'human' only for the person and 'lane owner' only for file ownership (or say 'owner-facing' only inside the owner-acceptance link). Replace 'coordinator' with 'orchestrator' (lines 202, 323). Choose two queue names, 'decision queue' (decisions.md) and 'handoff' (the four-section file), and use them in place of 'human queue', 'decisions list' and 'needs-human'.

5. **medium** · Concise is key; Progressive disclosure (SKILL.md as overview, not repetition) · SKILL.md Every Turn (lines 17-24) vs section 2 step 4 Arm (115-122) vs section 3 opening (132-135); section 2 step 1 vs section 9 meter bullet (322-330); section 3 decision-queue bullet vs Away Protocol step 4 (167-169)
   > Never block on a question tool while other work can move.
**Ask without blocking.** Put the question in a normal message with a recommendation, a default,

   Fix: State each rule once and refer to it elsewhere by name. Fold the section 3 opening into Every Turn rule 2. Reduce the section 9 meter bullet to the thresholds, since section 2 Wake already says to read the meters. Shorten Away Protocol step 4 to 'apply due defaults per the decision queue; human-before items wait'. The state-file template's duplicate of the Every Turn rules is deliberate and documented, so leave it. (about 200 tokens saved)

6. **low** · Provide utility scripts (document each script with its command line; make execution intent clear) · SKILL.md section 2 Wake (lines 99-101), Record (124), section 9 (324-329); references/state-file.md Helper scripts table (116-128)
   > Read both budget meters
   (`meter.sh` for Codex; the harness's usage view for Claude) and record them. List the decisions
   whose default is due (`decisions.sh due`)

   Fix: Write every helper as `$OPS/<script>` and name it the same way each time (`state.sh log`, not 'the state helper'). Add meter.sh, decisions.sh and state.sh rows to the state-file Helper scripts table, which today lists only six other scripts, so a resumed orchestrator has every invocation in one place.

7. **low** · Progressive disclosure, Pattern 3 conditional details · SKILL.md section 6 Release Safety When Every Merge Deploys (lines 256-275)
   > ## 6. Release Safety When Every Merge Deploys

   Fix: This section applies only to builds with auto-deploy. Move it to references/release-safety.md and leave one line in SKILL.md: 'If every merge deploys, follow references/release-safety.md before enabling auto-deploy.' The reference stays one level deep. (about 250 tokens saved)

8. **low** · Build evaluations first; Testing checklist (at least three evaluations, real usage scenarios) · evals/shared-benchmark.json
   > "variants": ["with_skill", "without_skill"],
…every case: "kind": "trigger"

   Fix: Add three behaviour cases with assertions that a skill-less run fails. Examples: the human goes offline with three lanes in flight, so the run must arm a wake source per lane and must not call a blocking question tool; a reviewer remedy conflicts with the contract, so the run must rule before relaying; a merge-of-base head, so the run must run the carry-over check rather than re-review. Without these, CONTRIBUTING's paired-delta check cannot show the 363-line body earns its tokens.

## Strengths

- Puts the two highest-cost failure rules ('every in-flight lane has a wake source', 'never block on a question tool') in a short Every Turn section above everything else, and repeats them in the state template so they survive compaction.
- A 'Where Other Work Belongs' routing table sends each sub-concern (briefs, panes, review, loops, scripts) to exactly one sibling skill, which keeps this skill about judgment rather than mechanics.
- The state-file reference is a copyable template with an explicit after-compaction procedure that re-verifies IDs and SHAs against their sources. That is a structured intermediate output with a built-in validation step.

## Cut candidates

- Common Issues (whole table; it restates body rules, except two rows that should move into the body)
- Section 5 Review and Merge Gates: the two bash blocks that duplicate orchestration-ops land.sh
- 'In one build…' anecdotes throughout (Every Turn rule 2, Kickoff items 3 and 11, section 3, section 4, section 5, section 7 opening paragraph, section 9)
- Section 3 The Human: the opening 'Ask without blocking' paragraph (duplicates Every Turn rule 2)
- Section 9 Cost and Throughput: the meter sub-bullets that repeat section 2 Wake and orchestration-ops meter.sh
- Section 6 Release Safety When Every Merge Deploys (move to a conditional reference rather than delete)
