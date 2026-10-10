## 1. Verdict table

| Skill | Body lines | Description chars | Verdict | Most important fix |
| --- | --- | --- | --- | --- |
| agent-briefs | 258 | 1003 | needs-work | Delete the Common Issues table, because every row repeats a principle. Put a six-step numbered procedure under the title. |
| agentmail | 163 | 279 | good | Delete the 8 Common Issues rows and the Untrusted Content section that repeat the body, and add a named "Not for" clause. |
| agent-orchestration | 363 | 984 | needs-work | Delete the 17-row Common Issues table and replace the section 5 merge bash with `land.sh`. |
| agents-md-authoring | 232 | 285 | needs-work | Merge Top Priorities, Format Requirements, the Quality Checklist and the Validation Checklist into one list, with the 150-line budget stated once. |
| autonomous-loops | 258 | 911 | needs-work | Replace the hand-written Copilot jq polling and the merge/deploy prose with `watch-gates.sh` and `land.sh`. |
| code-authoring | 229 | 691 | needs-work | Delete "When to Use". It claims spec/plan execution, which the description and the neg-trig eval give to implement. |
| code-quality-standards | 471 | 992 | needs-work | Fix the broken `"use client"` and `json()` examples, then cut the generic WRONG/RIGHT blocks to one-line rules. |
| commit | 185 | 850 | good | Make the 5b AB# extraction pattern match the `users/<user>/<id>-…` branches the skill creates. |
| design-review-standards | 368 | 984 | needs-work | Replace the 70-line checkbox template with a numbered procedure and an output template that has scores and ranked fixes. |
| ecommerce-patterns | 139 | 72 | needs-work | Rewrite the 72-character description to say what the skill provides, add the triggers its evals use, and add a "Not for" clause. |
| firecrawl | 203 | 967 | needs-work | Change the fix for stale content to `--max-age 0` / `maxAge: 0`. Omitting the flag still serves a 2-day cache. |
| herdr-delegation | 366 | 1006 | needs-work | Move the Codex peer flags and worktree teardown into references, and delete the Common Issues rows that repeat traps 1-4. |
| implement | 59 | 1000 | good | Shorten the "Not for drafting…" clause to "Not for writing a new spec.md or plan.md (spec)" to get room under the 1,024-character limit. |
| model-council | 114 | 280 | good | Add the "Not for" clause its negative evals already assume (pr-feedback, herdr-delegation, research). |
| orchestration-ops | 125 | 1014 | needs-work | Replace `$OPS` with the literal script path. Shell variables do not survive between Bash calls, so `"$OPS/x.sh"` runs as `/x.sh`. |
| owner-acceptance | 73 | 815 | good | Move the rule that safety or legal content gets no default answer from Common Issues into step 3.2. |
| playwright-e2e | 483 | 423 | needs-work | Delete CartPage, ProductCustomizerPage and the four generic test examples (about 1,550 tokens). |
| pr-authoring | 201 | 681 | good | Merge Common Mistakes into What to Avoid and drop the items that repeat the Core Principles. |
| pr-consolidate | 195 | 235 | needs-work | Commit after each `git merge --no-ff --no-commit`. A second `--no-commit` merge fails with "MERGE_HEAD exists". |
| pr-feedback | 176 | 943 | needs-work | Delete step 6.6. It suggests /pr-resolve and /commit after step 6 has already done both. |
| pr-resolve | 106 | 242 | needs-work | State the resolve-or-reply rule once, and make step 9 expect the reply-only threads to stay open. |
| pr-review | 155 | 278 | good | Add the plain-language triggers from its evals, and name review, pr-feedback and pr-resolve in the "Not for" clause. |
| research | 300 | 867 | needs-work | Delete Best Practices except three rules (batch, write as you go, stop at two-thirds), and delete the duplicate invocation block. |
| review | 233 | 777 | needs-work | Use one severity scale, one verdict set and one test-gap rule in both modes, and fix the eval's "Should fix". |
| seo-aeo-structured-data | 93 | 981 | needs-work | Move the HowTo and FAQ rich-result claims into an old-patterns block. Google retired or restricted both in Aug/Sep 2023. |
| session-retro | 72 | 730 | needs-work | Move owner-message filtering and the step 5 counts into `condense.py`. The narratives never contain `usage`. |
| skill-authoring | 264 | 881 | needs-work | Merge its five overlapping rule lists into one checklist, inside a numbered procedure with a create path and a review path. |
| spec | 331 | 270 | needs-work | Hand off to implement instead of code-authoring, and add the "Not for" clause its evals test. |
| story | 348 | 595 | needs-work | Pick one split threshold (13 or 8; today it is both) and delete the Quick Reference Card. |
| tt | 184 | 265 | good | Fold the Rules list into the steps, and settle step 3's contradiction about ad-hoc bug fixes. |
| upgrade | 393 | 277 | needs-work | Delete the generic classification, breaking-change, migration-pattern and error-handling tables (about 1,100 tokens). |
| word-doc-editing | 155 | 276 | needs-work | List the real statuses, WHATIF and ERROR, so a dry run doesn't count as stop-and-look, and make Invoke-DocxOps the only editor. |

## 2. Cross-cutting patterns

Ranked by tokens saved or risk removed. Token figures add up the reviewers' estimates and are approximate.

| # | Deviation (rule) | Affected skills | One remedy for all | Gain |
| --- | --- | --- | --- | --- |
| 1 | Generic knowledge Opus and Sonnet already have, such as WRONG/RIGHT code, taxonomies, troubleshooting playbooks and research etiquette (Concise is key: "Claude is already very smart") | code-quality-standards, playwright-e2e, upgrade, research, design-review-standards, code-authoring, spec, story, ecommerce-patterns, pr-authoring (Title block), commit (step 2) | Keep only rules a model without the skill gets wrong (each should be backed by an eval trap). Turn each example block into a one-line rule, and move any code worth keeping to `references/examples.md`. | ~5,500 tokens |
| 2 | Common Issues, Pitfalls, Mistakes or Rules tables that repeat the body | agent-briefs, agentmail, agent-orchestration, herdr-delegation, firecrawl, autonomous-loops, ecommerce-patterns, playwright-e2e, pr-authoring, seo-aeo-structured-data, story, pr-consolidate, session-retro, tt | Keep only rows whose symptom→fix appears nowhere else, such as exact error strings. Fold each surviving row into the step it belongs to, or keep it as a table of new facts only. | ~3,300 tokens |
| 3 | Several overlapping checklists, Guidelines, Boundaries or output templates that restate the procedure | skill-authoring, agents-md-authoring, research, design-review-standards, pr-resolve, pr-review, review, pr-feedback, spec, upgrade, code-authoring, pr-consolidate, model-council | One rule, one home. Use a single final checklist inside the procedure, and keep Boundaries to the never-rules not stated in the steps. | ~3,200 tokens |
| 4 | "When to Use", intro, Overview, Inputs or Related Skills sections that repeat the description, which has already fired by the time the body loads | 26 skills: agent-briefs, agentmail, autonomous-loops, code-authoring, code-quality-standards, design-review-standards, ecommerce-patterns, herdr-delegation, implement, model-council, orchestration-ops, owner-acceptance, playwright-e2e, pr-authoring, pr-consolidate, pr-feedback, pr-resolve, pr-review, research, review, seo-aeo-structured-data, spec, story, tt, word-doc-editing, plus the skill-authoring template | Delete them. Move any trigger phrase the description lacks into the description. Remove "## When to Use" from the skill-authoring template so new skills stop inheriting it. | ~2,300 tokens |
| 5 | No behaviour evals, so no cut above can be checked against the with/without delta that CONTRIBUTING requires (Build evaluations first) | Trigger cases only: 22 skills. No `evals/` at all: orchestration-ops, owner-acceptance, pr-consolidate, session-retro. Two behaviour cases only: review, spec, story, skill-authoring, pr-authoring, agents-md-authoring | Before cutting, add three behaviour cases per skill in the `pr-authoring/evals` format. Each assertion should trace to a rule and have a trap in the fixture. Run before and after every cut. | Risk |
| 6 | Hand-offs that contradict the workflow or the owning sibling skill | spec (to code-authoring), code-authoring (claims spec execution; optional `/review`), implement (optional `/review`), pr-feedback (step 6.6), pr-resolve (`/commit` after pushing), upgrade (`/commit` against per-group commits), commit (summarises tt despite its no-summary rule) | End with only the skill that owns the next action, as a skill-relative link. Never offer as optional a step the workflow already required. | Risk |
| 7 | Fragile or deterministic sequences rebuilt by hand when a script exists or should exist (Solve, don't defer; Provide utility scripts) | autonomous-loops, agent-orchestration (`land.sh`, `watch-gates.sh`), session-retro (`condense.py`), word-doc-editing (structural stats, ordering checks), herdr-delegation (wait verdict) | Use the existing script with its exact command line. Move counts, filters and checks into the script and have the prose read its single output line. | Risk, ~400 tokens |
| 8 | Build anecdotes and statistics in the instructions ("In one build…", "173-PR build", "1,100 findings") | agent-orchestration, agent-briefs, orchestration-ops, owner-acceptance, review, herdr-delegation, autonomous-loops | Keep the rule sentence. Delete the story, or move it to a `references/evidence.md` that SKILL.md never asks the model to load. | ~1,000 tokens |
| 9 | No named "Not for … (sibling)" clause (skill-authoring's own Disambiguated check) | agentmail, ecommerce-patterns, model-council, playwright-e2e, pr-resolve, pr-review (names no sibling), spec, tt, upgrade, word-doc-editing | Write the clause from each skill's existing negative eval cases, which already name the siblings. | Risk |
| 10 | Descriptions within ~60 characters of the 1,024 limit | orchestration-ops 1014, herdr-delegation 1006, agent-briefs 1003, implement 1000, code-quality-standards 992, agent-orchestration 984, design-review-standards 984, seo-aeo-structured-data 981, firecrawl 967 | Collapse the "what" list to one clause, keep the plain-words triggers and the "Not for" clause, and aim for 900 characters or fewer so trigger tuning has room. Rerun the trigger evals afterwards. | Risk |
| 11 | Reference files over 100 lines with no table of contents | agent-briefs, ecommerce-patterns (2), firecrawl (3), pr-feedback/pr-resolve (`pr-scripts/REFERENCE.md`), playwright-e2e, seo-aeo-structured-data (2), story, upgrade, word-doc-editing (2) | Add a linked contents list under the H1. It costs nothing at load time. | Risk |
| 12 | Host-specific tool IDs or syntax, against the README's Cross-Tool Authoring Notes ("describe tools as capabilities") | review (`#activePullRequest`…), pr-review (`get_file_contents`), code-authoring (`docs-context7`, `Explore`), commit (`log_time`), research (invocation block), agentmail ("names begin with `list_inboxes`") | Use capability wording that names the server in prose ("the host's active-PR context, else `gh pr view`"). | Risk |
| 13 | Version-specific or decaying facts given as current | seo-aeo-structured-data, code-quality-standards (APIs from before Next 15), playwright-e2e (Node 20, ^1.50), firecrawl, herdr-delegation, agentmail, upgrade (`eslint --ext`), agents-md-authoring, research | State the rule without a version. Date any observed behaviour and put it in a collapsed "Old patterns / observed" block. | Risk |
| 14 | Unexplained constants in scripts and reference code | orchestration-ops, session-retro, ecommerce-patterns, seo-aeo-structured-data, herdr-delegation, design-review-standards, word-doc-editing | Make each a named constant with a one-line reason, or a documented flag (`--max-rounds` is the model to follow). | Risk |
| 15 | Synonyms for one concept within a skill (Use consistent terminology) | Most skills. Worst: review, story, pr-feedback, agent-orchestration, word-doc-editing | Add a short collection glossary to skill-authoring. Use "orchestrator" for the sender role everywhere (see section 5, item 8). | Risk |

## 3. Top 15 fixes

1. **pr-consolidate**, Process steps 6-9. Rule: validation for critical operations. Fix: run `git merge --no-ff --no-commit`, inspect, then commit for each source. Chained `--no-commit` merges fail, and without `--no-ff` a fast-forward skips the inspection.
2. **orchestration-ops**, Prerequisites and every command block. Rule: test file access with real requests. Fix: write `~/.claude/skills/orchestration-ops/scripts/<x>.sh` literally, or prefix `OPS=… ;` in the same command.
3. **firecrawl**, Common Issues row "Content is stale" and the Discipline bullet. Rule: validation for critical operations. Fix: use `--max-age 0` / `maxAge: 0` for a live fetch, and say that a cache of up to 2 days is the default.
4. **word-doc-editing**, Procedure step 4. Rule: consistent terminology. Fix: "Dry run: proceed only when every row is WHATIF. Apply: proceed only when every row is OK. ERROR, NOT FOUND, AMBIGUOUS or SKIPPED: stop."
5. **spec**, Output. Rule: workflows have clear steps. Fix: point to `implement` (`/implement spec NNN`) instead of code-authoring, whose description excludes spec execution.
6. **code-authoring**, intro and When to Use. Rule: consistent terminology and descriptions. Fix: delete the bullets that claim `plan.md` execution (a cut of about 110 tokens).
7. **pr-feedback**, step 6.6. Rule: workflows have clear steps. Fix: delete the step. It invites a second push and duplicate replies.
8. **review**, Protocol step 5, Delegated mode and the eval. Rule: consistent terminology. Fix: map Critical/Important/Suggestion to blocking/follow-up/nit once, include data integrity in both test-gap rules, use one verdict set including `close`, and change the eval's "Should fix" to "Follow-up".
9. **code-quality-standards**, sections 2, 3, 4 and 6. Rule: examples must be correct, and concise. Fix: delete the `await`-in-non-async `"use client"` example and the unchecked `json()` annotation, then cut the generic blocks to one-line rules (about 1,500 tokens).
10. **playwright-e2e**, the POM and Test Patterns sections. Rule: concise. Fix: keep one trimmed HomePage POM and the `beforeEach` isolation block, and delete the rest (about 1,550 tokens).
11. **upgrade**, Classification, Breaking Change Categories, Common Migration Patterns, Error Handling and CVE Priority. Rule: concise. Fix: delete them and keep only "upgrade the requiring package first" for peer conflicts (about 1,100 tokens).
12. **agent-orchestration**, Common Issues and the section 5 bash. Rule: concise and low freedom. Fix: delete the table (move its 2 unique rows into the body) and replace the two bash blocks with `land.sh` (about 920 tokens).
13. **autonomous-loops**, B (Copilot polling) and D (Merge and Release). Rule: provide utility scripts. Fix: `watch-gates.sh <pr> <head-sha> --bot copilot --minutes 15` and `land.sh`. Matching on review `commit_id` is more reliable than comparing timestamps.
14. **seo-aeo-structured-data**, the description, HowTo and FAQPage. Rule: avoid time-sensitive information. Fix: drop "FAQ answers" from the rich-result examples and put HowTo/FAQ under a dated old-patterns `<details>` block (about 150 tokens).
15. **story**, Story Points / Common Mistakes and the Quick Reference Card. Rule: consistent terminology and concise. Fix: state "13 is the maximum and a split candidate" once, and delete the card (about 235 tokens).

## 4. Strengths to propagate

- **Low-freedom scripts that print one fixed-format line and refuse with specific reasons.** Modelled by orchestration-ops (`land.sh` proves the carry-over, merges with `--match-head-commit` and stops once) and word-doc-editing (lists the available styles; quotes the paragraph text when it refuses). Copy this into autonomous-loops, herdr-delegation and session-retro.
- **Short hard safety rules at the top.** Modelled by agentmail (in-scope and out-of-scope lists plus two absolute rules). Copy it to any skill whose tool can reach real people or production, such as pr-review posting or tt.
- **Strict, parseable report contracts.** Modelled by agent-briefs (STATUS/VERDICT on line 1), review (a delegated report of at most 40 lines tied to the head SHA) and owner-acceptance (a three-line block plus a named lesser status, "built and reviewed").
- **Behaviour evals with fixture traps and near-miss negatives.** Modelled by pr-authoring (the reference suite), spec, skill-authoring, review and story. Pattern 5 needs this most.
- **Pointing to the skill that owns a rule instead of restating it.** Modelled by implement (59 lines: hands off to code-authoring and spec Phase 6), commit (pr-authoring and tt "on purpose") and herdr-delegation (`herdr --skill` for syntax).
- **Labelling where each claim comes from.** Modelled by research (DOCS/SOURCE/INFERRED/UNVERIFIED) and playwright-e2e ("observed in 1.63; the docs don't say"). Use it wherever a skill states third-party behaviour.
- **Explicit stop conditions with an honest "unresolved" outcome.** Modelled by autonomous-loops (ordered checks: success, budget, no progress, repeated failure) and model-council (stop at the budget and report "unresolved").
- **One shared reference for sibling skills.** Modelled by `pr-scripts/REFERENCE.md`, used by pr-feedback, pr-resolve and pr-review. It only needs a table of contents.
- **Reference tables with a "Contains" column, so the model picks the right file before opening it.** Modelled by ecommerce-patterns and seo-aeo-structured-data.
- **State that survives compaction.** Modelled by agent-orchestration (state template with a resume procedure) and implement (re-read `spec.md`/`plan.md`; tick off plan steps).
- **Gating a destructive skill from auto-invocation.** Modelled by pr-consolidate (`disable-model-invocation: true` with the reason given).

## 5. Disputed or weak findings

1. **Use fully qualified `ServerName:tool_name` MCP names** (tt, agentmail, story). This contradicts the README Cross-Tool Authoring Notes, which say to describe tools as capabilities. I kept the underlying ambiguity (Harvest and ADO both have list tools) and replaced the remedy with "name the server in prose".
2. **"Every `assertions` array is empty"**, counted as a defect in about 20 reviews. In the skill-eval-harness format, trigger cases measure firing and carry no assertions by design. The real gap is the missing behaviour cases (pattern 5).
3. **pr-consolidate's description lacks triggers and a "Not for" clause, and the skill has no trigger suite.** The skill sets `disable-model-invocation: true`, and the README says such skills carry no trigger suite. Behaviour cases still apply.
4. **commit: "Tested with Haiku, Sonnet, Opus: partial".** No evidence was quoted either way. Pinning to `sonnet` is a deliberate choice, not a defect.
5. **skill-authoring: delete the three-level load table because the model already knows host mechanics.** How skills load is exactly what an author needs to know. I kept it and cut only the 600-line arithmetic.
6. **agentmail: remove the Tool Catalog because the connected server already lists its tools.** On hosts with deferred tool loading (this one included), only the names are visible. The catalog's purpose mapping costs little, so I set this aside.
7. **model-council: replace the CLI flag table with exact pinned commands.** The skill reads `--help` on purpose because flags drift, and pinned commands would add version-specific content (pattern 13). At most, add one dated example with a `--help` fallback.
8. **agent-briefs: use "coordinator" everywhere.** This conflicts with the agent-orchestration and orchestration-ops reviews, which both say "orchestrator". I adopted "orchestrator", which matches the skill names. The project's own docs say "coordinator", but those are project docs, not the collection.
9. **code-authoring: cut the generic Coding Standards bullets.** Partly set aside. That section is the canonical standards list that review, pr-review and code-quality-standards link to and check against, so cutting it changes what reviewers enforce. Cut only bullets no reviewer would ever cite.
10. **code-quality-standards: "SKILL.md under 500 lines: partial"** at 471 lines. That passes the rule. I treated the length as a conciseness problem (pattern 1), not a limit breach.
11. **agent-orchestration: host claims such as AskUserQuestion "may drift".** Speculative, with no evidence of drift. Weak.
12. **word-doc-editing: Windows-style paths.** Downgraded rather than dropped. The skill only runs on Windows with Word, so backslashes work there. The real defect is that the `.\scripts\` paths are relative to the current directory.
13. **implement: "frees about 110 of the 24 characters now left".** The arithmetic in that evidence is garbled. The fix still stands on the 1,000/1,024 count alone.

Verified while synthesising: `code-quality-standards/SKILL.md:167` does redefine `formatPrice`, so ecommerce-patterns' "canonical" note is false. The README does say tools are "described as capabilities".

## 6. Skills not reviewed

None. All 32 skills were reviewed.