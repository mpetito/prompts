# agent-briefs

Verdict: **needs-work** · SKILL.md body 258 lines · description 1003 chars

agent-briefs is well split: a 258-line SKILL.md holds the principles, an exact standing block and a strict, parseable report contract, and it points to six copy-ready templates in a single reference file. Its biggest gap is that every rule is written three times (Principles, Before Sending, Common Issues), and its eval suite contains only trigger cases. No case checks the content of a brief.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names concrete artefacts (handoff prompt, fix-round note, review prompt, turn-capped researcher), hosts (Claude, Codex, codex exec, Herdr) and plain-language triggers. |
| Description includes both what the Skill does and when to use it | pass | Opens with what it does, then gives a 'Use whenever…' clause, then a 'Not for…' clause (a deliberate collection convention). At 1003 characters it is 21 short of the 1,024 limit. |
| SKILL.md body is under 500 lines | pass | 258 body lines, not counting the 4 frontmatter lines. |
| Additional details are in separate files (if needed) | pass | The six long templates are in references/templates.md. The standing block and report contract stay in SKILL.md because every brief pastes them. |
| No time-sensitive information (or in an 'old patterns' section) | pass | No dated or version-gated guidance. The anecdotes ('in one build…') are not time-sensitive. |
| Consistent terminology throughout | partial | The receiving role is called coordinator, orchestrator and caller. The written output is called result file, output file and long form, and the report is also called the hand-back. |
| Examples are concrete, not abstract | pass | Gives a spawn-prompt example and a filled report-contract block. Placeholders are deliberate (Principle 5). |
| File references are one level deep | pass | SKILL.md links directly to references/templates.md. templates.md only points back to SKILL.md for the standing block and report contract. Links into other skills are skill-relative, per collection convention. |
| Structure longer reference files with a table of contents | fail | references/templates.md is 358 lines and has no table of contents at the top. |
| Progressive disclosure used appropriately | partial | The split is right, but the 'It must carry' column in the Templates table repeats sections that already exist in each template. |
| Workflows have clear steps | partial | No ordered procedure. Thirteen principles come before the template pointer. The order of work (pick template, generate facts, paste blocks, check, write file, send spawn prompt) has to be inferred from several sections. |
| Validation/verification steps for critical operations | pass | The Before Sending checklist, 'grep the brief against the project's Do-Not list', and generating facts from git/gh at send time all count. |
| Feedback loops included for quality-critical tasks | pass | Before Sending works as a review-against-checklist loop. The report contract and Round N files close the loop with the agent. |
| Template pattern (strictness matched to need) | pass | The report contract and standing block are low-freedom, exact text. The brief templates allow 'delete any line that cannot apply'. |
| No Windows-style paths | pass |  |
| Scripts solve problems rather than defer / no voodoo constants / scripts documented | not-applicable | The skill has no scripts. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 near-miss negatives) but no output cases. Every 'assertions' array is empty, so nothing tests brief quality. |

## Findings

1. **medium** · Concise is key ("Does this paragraph justify its token cost?") · SKILL.md, Common Issues (lines 245-262)
   > | The agent acted on a stale SHA or an unmerged dependency | Generate facts at send time; tell it the source beats the brief |

   Fix: Delete the Common Issues table. All 14 rows restate a rule already given in Principles 3-13, the standing block, Templates, Report Contract or Follow-ups, and most of those rules are also in the Before Sending checklist. If you want to keep a symptom index, attach one 'symptom' clause to each principle instead. (about 380 tokens saved)

2. **medium** · Structure longer reference files with a table of contents · references/templates.md, top of file (lines 1-9)
   > # Brief Templates

Copy-ready skeletons for [agent-briefs](../SKILL.md). Copy the block inside the outer fence,

   Fix: Add a six-line contents list under the title that links to sections 1-6 (Author brief, Fix-round note, Reviewer brief, Investigation or flake brief, Research brief, Docs or status brief). The file is 358 lines, so a partial read may never reach the later templates.

3. **medium** · Build evaluations first / Checklist: At least three evaluations created · evals/shared-benchmark.json
   > "kind": "trigger", ... "assertions": []

   Fix: Add at least three output cases with fixtures and assertions, each tied to a rule a model without the skill is likely to break: an author brief whose fixture has a stale SHA (assert a facts table checked with commands, plus 'source beats this brief'); a fix-round note (assert verbatim findings with IDs, a class-closure-by-grep instruction, and STATUS as line 1); and a research brief (assert the output file is written first, at most 5 questions, and provenance tags).

4. **medium** · Use workflows for complex tasks / Checklist: Workflows have clear steps · SKILL.md, Principles through Before Sending (lines 37-243)
   > ## Templates

Copy-ready skeletons are in [references/templates.md](references/templates.md). Pick one per

   Fix: Put a short numbered procedure right after the title: 1 select the model, 2 pick a template, 3 generate facts and preconditions with git/gh, 4 fill the template and paste the standing block and report contract, 5 run Before Sending, 6 write the brief to a file and send the spawn prompt. Then move the 13 principles below it as reference material. Writing the procedure should cost about as many tokens as trimming the overlap with Before Sending saves.

5. **low** · Use consistent terminology · SKILL.md lines 24, 69, 103, 90, 199; references/templates.md line 295
   > Fill the placeholders from the shared-machine plan (...), which the
orchestrator settles at kickoff.

   Fix: Use 'coordinator' everywhere for the sender role, replacing 'orchestrator' (line 103) and 'the caller' (line 24). Use 'result file' everywhere for the agent's written output, replacing 'Output file' in the research template and Common Issues. Drop the 'hand-back' synonym for 'report'. (about 5 tokens saved)

6. **low** · Progressive disclosure patterns (SKILL.md as a table of contents, not a copy) · SKILL.md, Templates table (lines 151-158)
   > | Author brief | A lane, phase or fix | Owns, lockstep and Never-touch lists; numbered changes with sources; invariants; stop triggers; validation built from CI; red-without-change proof; self-check |

   Fix: Remove the 'It must carry' column and keep 'Template' and 'Use for'. Each template's headings already list what it must carry, so the column is a second copy of templates.md loaded every time. (about 170 tokens saved)

7. **low** · Concise is key (Default assumption: Claude is already very smart) · SKILL.md, When to Use (lines 11-18) and Claude Code note (lines 138-142)
   > **Claude Code note:** in an isolated worktree, Claude Code refuses a command when it can't
verify from the text that the command's git stays inside the worktree,

   Fix: Delete the When to Use list. It repeats the description, which already did its job by the time the body loads. Shrink the Claude Code note to one clause at the end of the standing block's first bullet ("Claude Code refuses commands it can't prove stay in the worktree"), with the doc link. (about 150 tokens saved)

8. **low** · Concise is key / Writing effective descriptions (1,024-character limit) · SKILL.md Principles 4, 11 and Report Contract; frontmatter description
   > in
   one build, wrong coordinator claims cost about one review round in five.

   Fix: Cut the build anecdotes in Principles 4 and 11 and in the 'Round 2 closes the class' bullet. Each rule already states its own reason. Separately, trim the description, which is 21 characters under the 1,024 limit (for example drop 'resuming an agent for another round;', which overlaps with 'a note asking a reviewer to re-check new commits'), so later trigger tuning has room. (about 70 tokens saved)

## Strengths

- Strict template pattern used for the parts that must be machine-readable: the report contract's first line (STATUS / VERDICT) is fixed so a coordinator can parse it, while the brief bodies are adaptable skeletons.
- Low-freedom, copy-exact standing block for fragile shared-machine work (ports, TMPDIR, PIDs, no pkill, no stash or rebase), with 'delete a line only when it cannot apply' as the only escape.
- Trigger evals whose negatives are near-misses that match the description's 'Not for' clause one for one (agent-orchestration, herdr-delegation, review).

## Cut candidates

- Common Issues (entire table; every row repeats a principle, the standing block or a template)
- When to Use (repeats the frontmatter description)
- Templates table 'It must carry' column (repeats the template headings in references/templates.md)
- Claude Code note after The Standing Block (fold into one clause)
- Anecdotal justifications in Principles 4 and 11 and the 'Round 2 closes the class' bullet
