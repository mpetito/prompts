# pr-authoring

Verdict: **good** · SKILL.md body 201 lines · description 681 chars

pr-authoring is a tight, example-led skill. It gives concrete Changes and Validation snippets, a two-workflow split for new and updated PRs, and real feedback loops: re-reading the live body and checking closingIssuesReferences. Its main gap is repetition: the Core Principles, What to Avoid and Common Mistakes sections cover the same ground, and When This Skill Applies repeats the description, so about 300 tokens of the body say the same thing two or three times.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | 681 chars; names PR title/body/description, summary, write-up, updating after pushes, and the commit-skill hand-off; ends with the collection's Not-for clause. |
| Description includes both what the Skill does and when to use it | pass | Opens with what it writes, then 'Use when …' triggers and 'Load it before running git'. |
| SKILL.md body is under 500 lines | pass | 201 body lines (209 total minus 8 frontmatter lines). |
| Additional details are in separate files (if needed) | not-applicable | At 201 lines with no large tables or code libraries, no references/ split is needed. |
| No time-sensitive information (or in an 'old patterns' section) | pass |  |
| Consistent terminology throughout | partial | The commit skill is called the 'commit prompt' on lines 26 and 34 but the 'commit skill' on line 154. 'description' and 'body' are used for the same thing. |
| Examples are concrete, not abstract | pass | Real Summary, Before sign-off, Changes, Implementation Notes and Validation snippets with numbers. |
| File references are one level deep | pass | No reference files; only named sibling skills (commit, tt). |
| Progressive disclosure used appropriately | pass | A single file is right at this size. |
| Workflows have clear steps | pass | Numbered 'Updating an Existing PR' (7 steps) and 'Procedure' (9 steps). The new-or-update decision point sits near the end, after about 165 lines of format guidance. |
| Validation/verification steps for critical operations | pass | Re-read the live body after create or edit; check closingIssuesReferences before merge; re-check factual lines after a push. |
| Feedback loops included for quality-critical tasks | pass | 'Self-review against "What to Avoid" before saving the body file' works as a style-guide validator. |
| No Windows-style paths (all forward slashes) | pass |  |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No 'voodoo constants' (all values justified) | not-applicable | No scripts. The length targets in the prose are presented as heuristics. |
| Required packages listed in instructions and verified as available | partial | Uses the `gh` CLI throughout without stating it is required. The collection README lists gh as a requirement, so this is minor. |
| At least three evaluations created | pass | 8 cases: 2 output-quality cases with fixtures and assertions, 3 positive trigger cases, 3 negative trigger cases. |
| Tested with real usage scenarios | partial | The fixtures are realistic branch contexts, but only the authoring-from-scratch workflow is exercised. The update-after-push workflow and the closing-keyword check have trigger cases at most. |

## Findings

1. **medium** · Concise is key; Core quality checklist: Consistent terminology / no duplication · SKILL.md, Common Mistakes (lines 201-209) vs What to Avoid (129-139) and Core Principles (14-22)
   > 6. **Duplicating spec content** — paraphrasing the spec wastes space and goes stale; link it
3. **Burying the motivation under "Changes"** — the `## Summary` should answer "why merge this?"

   Fix: Merge Common Mistakes into What to Avoid. Keep only items said nowhere else (writing from git log rather than intent, the AB# reference belongs in the body, stale body after a push, draft PRs get full quality). Drop #2, #3 and #6, which restate Principles 1, 2 and 5. Also drop the What to Avoid bullets 'Restating what the spec says' and '"Tested locally"', which restate Principles 5 and 3. (about 180 tokens saved)

2. **medium** · Concise is key; Writing effective descriptions (the description, not the body, decides triggering) · SKILL.md, When This Skill Applies (lines 24-30)
   > - The `commit` prompt is creating a new PR body file
- The user asks to update an existing PR description

   Fix: Delete the section. The body is read only after the skill has triggered, so these five bullets repeat the description's 'Use when …' list. The one cue the description lacks ('A push to your own open PR may have made its body untrue') is already step 0 of 'Updating an Existing PR' ('After every push to your own PR'). (about 75 tokens saved)

3. **low** · Use consistent terminology · SKILL.md lines 26, 34 vs 154; Updating an Existing PR
   > Use the conventional commit format already enforced by the `commit` prompt:
(see the `commit` skill for full syntax)

   Fix: Call `commit` a skill everywhere. In the body, use 'body' for the PR text (for example 'whenever asked to update a description' becomes 'update the body'), and leave 'description' only in the frontmatter, where it serves as a trigger term.

4. **low** · Conditional workflow pattern; Use workflows for complex tasks · SKILL.md, Updating an Existing PR (167-177) and Procedure (179-189), placed after all format guidance
   > ## Procedure (when authoring from scratch)

   Fix: Move both procedures, or a two-line router ('New PR? follow Procedure. Existing PR? follow Updating.'), directly after Core Principles. The section menu (Title through Work Item References) then reads as the reference that the steps point into. This adds no tokens and puts the decision point first.

5. **low** · Concise is key (Claude already knows this) · SKILL.md, intro line 12 and Title (32-42)
   > Guidelines for writing pull request descriptions that respect a reviewer's time while giving them what they need to merge confidently.

   Fix: Cut the intro sentence. Shrink Title to one line: 'Conventional-commit subject, lowercase imperative, no period, under ~72 chars; cite the spec number when one exists', followed by the spec-number example. Drop the generic `<type>(<scope>)` code block, which Claude knows. (about 70 tokens saved)

6. **low** · Concise is key; Avoid offering too many options · SKILL.md, File-by-File Tables — When They Earn Their Space (141-149)
   > A `| File | Change |` table is justified only when:

   Fix: Fold this into the existing 'File-by-file changelogs' bullet in What to Avoid as one clause: 'a | File | Change | table only for new modules whose names are the design, refactors where moves matter, or a sprawling change that needs a map'. Then delete the section. (about 55 tokens saved)

7. **low** · Concise is key · SKILL.md, Procedure step 9 (line 189) and Length Heuristics table (193-197)
   > invoke the **tt** skill, passing the changeset, branch name, commit subject(s), and PR title/number as context so it can resolve the ADO work item and log estimated time. ... Never delete entries.

   Fix: Reduce step 9 to 'If a time-tracking tool is available, invoke tt as a non-blocking follow-up; otherwise skip and say so'. The tt skill already owns its inputs and its no-delete rule. Strip the ~90-character column padding from the Length Heuristics table. (about 70 tokens saved)

8. **low** · Build evaluations first; Testing checklist: Tested with real usage scenarios · evals/shared-benchmark.json
   > "id": "trig-refresh-after-push", "kind": "trigger", ... "assertions": []

   Fix: Add one output-quality case with an existing body plus new commits. Assert that Validation is replaced rather than appended, that a now-false 'unchanged' or 'not run' claim is removed, and that the author's Out of Scope section is kept. Optionally include a prose 'closes #N' trap. This covers the update workflow, the skill's most fragile path, which today has only a trigger check.

## Strengths

- Each format rule comes with a short, concrete snippet that has real numbers ('`pnpm vitest run`: 418 passed, 0 failed'), and the snippets show tone and level of detail better than the prose could.
- It builds real feedback loops into fragile operations: it re-reads the live body after `gh pr create`/`edit`, verifies `closingIssuesReferences` before merge, and uses a per-branch, per-task body-file path so parallel agents cannot overwrite each other's PR.
- Its eval suite pairs realistic branch fixtures with deterministic assertions (no file table, no bare changelog bullets, 'DocumentBuilder … unchanged') plus a judge rubric, and covers both positive and negative triggers.

## Cut candidates

- When This Skill Applies (repeats the description)
- Common Mistakes items 2, 3 and 6 (repeat Core Principles 1, 2 and 5 and What to Avoid)
- What to Avoid: 'Restating what the spec says' and '"Tested locally"' bullets (repeat Principles 5 and 3)
- Intro sentence under '# PR Authoring'
- Title: the generic conventional-commit code block
- File-by-File Tables — When They Earn Their Space (fold into one What to Avoid clause)
- Procedure step 9 detail on tt inputs and 'Never delete entries' (owned by the tt skill)
