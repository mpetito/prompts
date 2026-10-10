# pr-consolidate

Verdict: **needs-work** · SKILL.md body 195 lines · description 235 chars

The skill is short, gated behind disable-model-invocation for a destructive operation, and gives a clear dry-run mode, a fixed output template and a quick-reference table. Its core procedure does not work as written: it chains `git merge --no-commit` calls without a commit between them, which git refuses, and it omits `--no-ff`, so a fast-forward skips inspection. Around that procedure, the safety rules, the conflict steps and the command list each appear two or three times.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Names PRs, branches, integration branch, agent branches; lacks the collection's 'Not for … (other-skill)' clause and no trigger phrases like 'combine', 'stack', 'merge these PRs into one'. |
| Description includes both what the Skill does and when to use it | pass | First sentence is what; 'Use when combining multiple pull requests…' is when. |
| SKILL.md body is under 500 lines | pass | 195 body lines. |
| Additional details are in separate files (if needed) | not-applicable | Single-file skill; size does not require splitting once duplicates are removed. |
| No time-sensitive information | pass |  |
| Consistent terminology throughout | partial | Integration branch naming varies: integration/{source-summary}-{timestamp}, integration/feature-combined, integration/combined-features; 'Safety Rules' vs 'Guidelines' restate the same rules. |
| Examples are concrete, not abstract | pass | Concrete input examples, bash block and output template. |
| File references are one level deep | not-applicable | No reference files. |
| Progressive disclosure used appropriately | pass | Single file is appropriate at this size. |
| Workflows have clear steps | partial | Numbered Process exists, but step 2 creates a backup branch before step 4's dry-run exit, contradicting '--dry-run … without making changes'; steps 6-7 cannot run as written for more than one source. |
| Validation/verification steps for critical operations | partial | Backup branch, dry-run and pre-push review exist; no check that conflict markers are gone before commit and no check that the merge actually stopped (fast-forward bypasses --no-commit). |
| Feedback loops included for quality-critical tasks | fail | Step 8 runs tests but never says fix-and-rerun until green before step 9; failure path is only 'abort'. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No voodoo constants | not-applicable |  |
| Required packages listed and verified | partial | Uses `gh` without stating it must be installed and authenticated. |
| No Windows-style paths | pass |  |
| Avoid offering too many options | pass | One merge strategy with a deterministic-order default. |
| At least three evaluations created | fail | No evals/ directory. |
| Tested with real usage scenarios | not-applicable | Cannot be observed from the files. |

## Findings

1. **high** · Validation/verification steps for critical operations; Workflows have clear steps · SKILL.md, Process steps 6-9 and Consolidation Procedure (lines 65-68, 88-99)
   > git merge pr-123 --no-commit -m "Integrate PR #123"
git merge pr-456 --no-commit -m "Integrate PR #456"

   Fix: Commit after each source, then run the next merge: `git merge --no-ff --no-commit {branch}`, inspect, commit 'Integrate PR #N', repeat. The second `--no-commit` merge fails with 'You have not concluded your merge (MERGE_HEAD exists)' (confirmed in a throwaway repo). The git-merge docs say a fast-forward cannot be stopped by `--no-commit` without `--no-ff`. Put the 'Closes #N' summary in the PR body or a final squash rather than one commit that spans every merge, and drop the meaningless `-m` on a `--no-commit` merge.

2. **high** · Concise is key · SKILL.md, Guidelines (lines 174-181) vs Safety Rules (lines 35-41)
   > - Never force push without explicit confirmation.
- Preserve all work; combine, do not discard.

   Fix: Delete the Guidelines section. Its first three bullets repeat Safety Rules almost word for word. Move the two new bullets (deterministic merge order; conditional 'Closes #N') into Process steps 6 and 9. (about 90 tokens saved)

3. **high** · Concise is key · SKILL.md, Error Handling > Merge Conflicts (lines 185-192) vs Conflict Resolution Strategy (lines 109-119)
   > 1. List conflicts: `git diff --name-only --diff-filter=U`.
2. Open each file and look for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).

   Fix: Delete Error Handling > Merge Conflicts. It repeats Conflict Resolution Strategy steps 3-6 and the Quick Reference rows. Keep one conflict section, holding only the conflict-type heuristics (combine additions, merge both intents, higher compatible dependency version). (about 110 tokens saved)

4. **medium** · Concise is key (Default assumption: Claude is already very smart) · SKILL.md, Consolidation Procedure bash block (lines 73-107) vs Quick Reference table (lines 121-132)
   > | Stage resolved file | `git add {file}` |
| Abort merge | `git merge --abort` |

   Fix: Keep one command listing. Keep the Quick Reference table (parameterised) and drop the example bash block, or the reverse. Drop rows Claude already knows, such as `git add {file}`, conflict-marker syntax and `git merge --abort`. Keep only the non-obvious ones: `pull/{n}/head` fetch, `--diff-filter=U`, and the backup and integration naming. (about 250 tokens saved)

5. **medium** · Workflows have clear steps; Create verifiable intermediate outputs · SKILL.md, Input Format (line 20) and Process steps 2-4 (lines 57-63)
   > - `--dry-run`: preview validation, target choice, merge order, and expected commands without making changes.
…   - Create a backup branch for the current state.

   Fix: Move 'Create a backup branch' out of validation into a step after the dry-run exit, so a dry run really makes no changes. Have the dry run print the ordered merge plan, and have the real run work from that plan. That is the plan-validate-execute shape the best-practices doc recommends for destructive batch operations.

6. **medium** · Implement feedback loops · SKILL.md, Process steps 7-9 (lines 66-68)
   > 8. Run relevant tests, linters, and type checks for the integrated branch.
9. Prepare a consolidated commit message

   Fix: Replace step 8 with a loop: confirm no unmerged paths or leftover markers (`git diff --check`, `git diff --name-only --diff-filter=U` empty), run the project's checks, fix and re-run until green, and only then proceed. Abort only when the fix needs a ruling.

7. **low** · Concise is key; Writing effective descriptions · SKILL.md, intro and Use Cases (lines 13, 29-33)
   > - Agent branches: multiple agents worked on related branches and their work must be merged.

   Fix: Delete the Use Cases section and the one-line intro. Both restate the description, which already lists overlapping, dependent and agent branches. Any trigger phrase missing from the description belongs there. (about 80 tokens saved)

8. **low** · Use consistent terminology · SKILL.md, Target Determination (line 49), Consolidation Procedure (line 86), Output Format (line 147)
   > Create integration/{source-summary}-{timestamp}.
…git checkout -b integration/feature-combined

   Fix: Use one integration-branch pattern everywhere, `integration/{summary}-{timestamp}`, as in the Quick Reference. Also make Process step 9 apply 'Closes #N' only when the branch supersedes the PRs, matching the condition in Guidelines.

## Strengths

- Puts a destructive, cross-branch operation behind `disable-model-invocation: true`, with a frontmatter comment that says why, so the model never starts it on its own.
- Defines a fixed Output Format template that ends with 'Ready to proceed?', so every run stops at the same review gate before anything is pushed.
- Writes target-branch selection as short IF/ELSE pseudocode, which fixes the decision without prose.

## Cut candidates

- Use Cases (restates the description)
- Guidelines (duplicates Safety Rules)
- Error Handling > Merge Conflicts (duplicates Conflict Resolution Strategy and Quick Reference)
- Consolidation Procedure bash block or Quick Reference table (one duplicates the other)
- Conflict-marker syntax and `git add`/`git merge --abort` explanations (Claude knows git)
- Error Handling > Dirty Working Tree 'In autonomous contexts' bullet (the skill is user-invoked only in Claude Code)
