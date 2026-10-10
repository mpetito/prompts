# commit

Verdict: **good** · SKILL.md body 185 lines · description 850 chars

The commit skill is a compact 185-line numbered workflow. A project CONTRIBUTING guide comes first and overrides the defaults, validation is driven by CI, the skill hands off to pr-authoring and tt instead of summarizing them, and the description is trigger-specific and backed by 8 trigger evals. The most important gap is its Azure DevOps and branch terminology: the AB# extraction patterns contradict the branch names the skill itself creates, and the AB# placement rule is repeated in four places. The eval suite also tests only triggering, never the skill's safety-critical behaviors.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names commit, push, branch, pull request, CONTRIBUTING, AB#, Envative, and excludes pr-authoring, review and pr-feedback. |
| Description includes both what the Skill does and when to use it | pass | Opens with what it does, then 'Use whenever…' with concrete situations, and states when to load it ('before running git status'). |
| SKILL.md body is under 500 lines | pass | 185 body lines; the description is 850 characters, under the 1,024 limit. |
| Additional details are in separate files (if needed) | partial | No references/. Step 5b's ADO keyword table applies only to ADO repos but sits inline in the always-loaded body. |
| No time-sensitive information (or in an "old patterns" section) | pass |  |
| Consistent terminology throughout | partial | The description says `users/<user>/…` but the table says `users/mpetito/`. Branch types and commit types are two different lists. AB# extraction patterns contradict the branch-naming table. |
| Examples are concrete, not abstract | pass | Commit Examples gives three concrete messages, and the closing-keyword rule includes a good/bad pair. |
| File references are one level deep | pass | Links go only to sibling skills (pr-authoring, tt), which is the collection's skill-relative convention. |
| Progressive disclosure used appropriately | partial | Delegation to pr-authoring and tt is good. The ADO-only material could be conditional (Pattern 3). |
| Workflows have clear steps | pass | Numbered steps 1–8, with a conditional table in step 1 saying which steps to skip. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| Error handling is explicit and helpful | partial | 'Stop and report if validation fails' is explicit. There is no guidance if push or `gh pr create` fails. |
| No "voodoo constants" (all values justified) | not-applicable |  |
| Required packages listed in instructions and verified as available | partial | Uses `gh` without stating it must be installed and authenticated. |
| Scripts have clear documentation | not-applicable |  |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | partial | Strong CI-driven validation and re-run-after-change rule. However, `git add -A` has no check of untracked files before committing. |
| Feedback loops included for quality-critical tasks | pass | 'If anything changes after validation, run the list again'; 'Re-read the live body'. |
| At least three evaluations created | partial | 8 trigger cases (5 positive, 3 negative). No behavior cases with assertions, so `assertions` is empty for every case. |
| Tested with Haiku, Sonnet, and Opus | partial | Pinned to `model: sonnet`, `effort: low`. Nothing shows that the judgment-heavy step 3 (CI discovery, clean-worktree run) was exercised at that tier. |

## Findings

1. **medium** · Use consistent terminology · SKILL.md, 4. Ensure Feature Branch table vs 5b. Extract Work Item IDs
   > `users/mpetito/<work-item-id>-<type>-<short-description>` ... Branch name pattern: `feat/AB#1234-description` or `fix/1234-description`

   Fix: Make the 5b extraction source match the branch pattern the skill creates, for example: 'the work-item id in the branch name (users/<user>/<id>-…)'. Use one placeholder for the user segment, either `<user>` (as in the description) or `mpetito`, in both the description and the table.

2. **medium** · Use consistent terminology / Concise is key · SKILL.md, 5b, 7. Create/Update PR, Output
   > **Syntax:** `AB#<work-item-id>` — must appear in PR description ... **Include `AB#<id>` references** in the body ... Ensure `AB#<id>` references are present in PR body

   Fix: State the AB# placement rule once in 5b. In step 7, replace the three AB# bullets with 'Put the 5b references in the body'. Cut the Output sub-bullets about the Development section, which Claude cannot verify within the session. (about 60 tokens saved)

3. **medium** · Validation/verification steps for critical operations · SKILL.md, 5. Stage & Commit
   > - If nothing staged: `git add -A`

   Fix: Before `git add -A`, review `git status --short` for untracked files that are not part of the change (secrets, build output, scratch files). Exclude them, or stop and ask. This matches step 3's rule 'Leave no unrelated edits'.

4. **medium** · Build evaluations first / Testing checklist: At least three evaluations · evals/shared-benchmark.json
   > "kind": "trigger" ... "assertions": []

   Fix: Add at least three behavior cases with assertions for the skill's fragile rules. Examples: CONTRIBUTING says commit to main, so no branch and no PR; no AI attribution trailer in the commit or PR body; only already-staged files are committed. Run them at the pinned `sonnet`/`low` tier.

5. **low** · Additional details are in separate files / Progressive disclosure Pattern 3 (conditional details) · SKILL.md, 5b. Extract Work Item IDs
   > **State transition keywords** (applied when PR merges to default branch): | `Fixes AB#123` | Transitions to Resolved/Completed |

   Fix: Move the keyword table and the multiple-items example to references/azure-devops.md. Leave one line in SKILL.md: 'Azure DevOps repo: see references/azure-devops.md for AB# keywords.' Most repos then never load it. (about 120 tokens saved)

6. **low** · Concise is key (Claude already knows this) · SKILL.md, 2. Assess State and 6. Push
   > - Note staged vs unstaged files
- Check if on protected branch

   Fix: Collapse step 2 to one line: 'Run git status and review both staged and unstaged diffs.' The protected-branch check is already step 4. Fold step 6's bare `git push -u origin <branch-name>` block into step 5 or 7 as one clause. (about 50 tokens saved)

7. **low** · Concise is key / MCP tool references · SKILL.md, 7. Create/Update PR and 8. Log Time
   > No summary of its rules appears here on purpose: a summary reads as self-contained ... (`log_time`, never timers; create or update, never delete)

   Fix: Cut the author-facing rationale sentence in step 7. Cut the tt rule summary in step 8: it contradicts step 7's own no-summary principle, and its bare `log_time` is an unqualified tool ID, which the collection's capability-naming convention avoids. (about 45 tokens saved)

8. **low** · Use consistent terminology · SKILL.md, 4. Ensure Feature Branch vs 5. Stage & Commit
   > Branch types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test` ... Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`

   Fix: Define the type list once, in step 5, and have step 4 say '<type> is the commit type'. Also drop the repeated 'skip this step and step 7' clause from step 4, since step 1's table already says it. (about 30 tokens saved)

## Strengths

- A project CONTRIBUTING guide is read first and explicitly outranks every default. A small 'If the guide says / Then' table maps each override to the step it changes, and the output must state which source was followed.
- It defers to sibling skills (pr-authoring, tt) by invocation, with a stated reason never to restate their rules. This keeps the body short and avoids drift.
- Validation is driven by CI files rather than memory. It includes a feedback loop: re-run checks after any change, and run once from a clean worktree before the first push.

## Cut candidates

- 2. Assess State (git status/diff narration and the VS Code #changes aside)
- 6. Push (bare git push -u code block)
- 7. Create/Update PR: the 'No summary of its rules appears here on purpose' rationale sentence
- 8. Log Time: parenthetical restating tt's rules
- 5b. Extract Work Item IDs: State transition keywords table (move to a conditional reference)
- Output: Work Item Links verify sub-bullets
