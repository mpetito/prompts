# word-doc-editing

Verdict: **needs-work** · SKILL.md body 155 lines · description 276 chars

The skill is a strong low-freedom toolkit. It gives exact commands, a mandatory dry run, explicit per-op statuses, verification against an accepted copy, and scripts that refuse unsafe deletes and unknown styles with specific messages. The biggest gap is that the skill ships two overlapping editors that disagree with each other and with SKILL.md. The status vocabulary is also inconsistent: the dry run reports WHATIF, which the "anything but OK" rule treats as a failure. On top of that, a COM-traps table duplicated from the reference file inflates the body.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Names .docx, Word COM, tracked changes, TOC, PDF. It lacks the plain-language terms the eval prompts use (Word document, redline/markup, contents page). It also has no 'Not for … (other-skill)' clause, although firecrawl's description points back at this skill. |
| Description includes both what the Skill does and when to use it | pass | "Edit .docx files by driving Microsoft Word via COM … Use when revising or restructuring one, auditing stale terms …" |
| SKILL.md body is under 500 lines | pass | 155 body lines. |
| Additional details are in separate files (if needed) | pass | Manifest schema and full trap explanations are in references/. The traps are also summarised inline (see findings). |
| No time-sensitive information | pass |  |
| Consistent terminology throughout | fail | The status list omits WHATIF and ERROR, which Invoke-DocxOps emits. Merge-ChangeLogs.ps1 says 'tranche' where SKILL.md says 'batch'. 'Both editors' are said to feed the change log, but only one can. |
| Examples are concrete, not abstract | partial | Commands and manifests are concrete. The sectPr check in word-com-traps.md is a code block that holds only comments. |
| File references are one level deep | pass | Both reference files link directly from SKILL.md. Neither chains to further references. |
| Progressive disclosure used appropriately | partial | The traps table repeats references/word-com-traps.md in the body, although the scripts already defend against every trap. |
| Workflows have clear steps | pass | Eight numbered steps with exact commands, plus three ordering rules. |
| Scripts solve problems rather than defer to Claude | partial | Scripts handle field mismatches, cell-final marks and row-end inserts. The ordering rules, the structural before/after comparison and the XML-level check are left to Claude by hand. |
| Error handling is explicit and helpful | pass | Unknown styles are listed alongside the available styles. deleteParas refusals quote the live text. A non-Windows run throws a clear message. |
| No voodoo constants | partial | Word enum values are named or commented. The maxParas default of 60 and the 'first 40 styles' limit have no stated rationale. |
| Required packages listed in instructions and verified as available | pass | Prerequisites list Windows, Word and pwsh. New-WordApp checks $IsWindows. |
| Scripts have clear documentation | pass | Every script has comment-based help with PARAMETER and EXAMPLE blocks, and SKILL.md has a purpose table. |
| No Windows-style paths (all forward slashes) | fail | Every command uses backslashes, e.g. .\scripts\Get-DocxOutline.ps1 '.\doc.docx'. |
| Validation/verification steps for critical operations | pass | A dry run is mandatory, deleteParas re-checks the live anchors, and verification runs on the accepted copy. |
| Feedback loops included for quality-critical tasks | pass | Dry run, then fix NOT FOUND or AMBIGUOUS, then apply, then check revisions, then check the accepted copy. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 negative) and no behaviour cases. |

## Findings

1. **high** · Avoid offering too many options / Use consistent terminology · SKILL.md The Toolkit (lines 36-46); references/manifests.md sections 'Invoke-DocxEdits.ps1' and 'Invoke-DocxOps.ps1'
   > Both editors take JSON manifests where every operation carries an `id` and a `note`
(rationale) that flow into the change log.

   Fix: Make Invoke-DocxOps.ps1 the only editor in SKILL.md and manifests.md, since the procedure already uses only that script. Drop the Invoke-DocxEdits row and its manifest section, or keep one line marking it as legacy. Invoke-DocxEdits has no -ChangeLog parameter and its output lacks the Op and Page columns Merge-ChangeLogs needs, so the quoted claim is false for it. Port `matchCase` into the Ops `replace` op: the Ops version always matches with Ordinal, although manifests.md says it takes the 'same fields as above'. (about 60 tokens saved)

2. **high** · Use consistent terminology / Workflows have clear steps · SKILL.md Procedure step 4 (lines 67-78)
   > Every op reports **OK / NOT FOUND / AMBIGUOUS / SKIPPED / PARTIAL**; treat
   anything but OK as a stop-and-look.

   Fix: Under -WhatIf, Invoke-DocxOps reports every successful op as WHATIF, never OK, and it also emits an undocumented ERROR status. Followed literally, every dry run is a stop-and-look. Change the step to list the real statuses: 'Dry run: proceed only when every row is WHATIF. Apply: proceed only when every row is OK. ERROR, NOT FOUND, AMBIGUOUS and SKIPPED mean stop.'

3. **medium** · Concise is key / Progressive disclosure patterns (Pattern 3, conditional details) · SKILL.md Word COM Traps (lines 122-136)
   > These cost real debugging time; the scripts already defend against them, but any ad-hoc
COM you write must too. Full explanations: [`references/word-com-traps.md`]

   Fix: Replace the 8-row table with one conditional pointer: 'Writing COM code outside these scripts? Read references/word-com-traps.md first.' The traps that matter when only running the scripts are already covered: deleted text still being searchable (step 7), highlights (Working Style) and section-break pastes (Common Issues). (about 450 tokens saved)

4. **medium** · Solve, don't defer / Create verifiable intermediate outputs · SKILL.md Working Style (lines 145-146) and Procedure step 7 (lines 102-104); references/word-com-traps.md sections 4 and 9
   > - **Verify structurally after big passes:** compare paragraph/table/field counts and
  bold/italic character coverage before vs after; unexplained drops mean content loss.

   Fix: The trap reference says this check alone caught a material content loss that every op report had marked OK. Yet no script does it, and the sectPr check in word-com-traps.md is a code block of comments only. Add a small Get-DocxStats.ps1, or extra output columns on Update-DocxFields.ps1, that emits paragraph, table, field, bookmark and section counts plus page geometry and bold/italic character coverage. Make step 7 run it on the source and the accepted copy and compare the two.

5. **medium** · Solve, don't defer / Validation steps for critical operations · SKILL.md Ordering Rules (lines 112-120)
   > ## Ordering Rules (violations cause silent damage)

   Fix: A rule whose violation causes silent damage should be checked by Invoke-DocxOps during the -WhatIf pre-pass, not just stated in prose. Flag an insertTable followed by other ops on the same region, anchorIndex ops not in descending order, and an insert that comes before a delete sharing its anchor. Report each as a status, so the existing dry-run loop catches it. The prose can then shrink to one line per rule. (about 40 tokens saved)

6. **medium** · Avoid Windows-style paths · SKILL.md Procedure (lines 54-110), Common Issues (line 154); references/manifests.md Batching and chaining
   > .\scripts\Get-DocxOutline.ps1 '.\doc.docx' -HeadingsOnly -Format Table

   Fix: Use forward slashes, which pwsh accepts on Windows. Write script paths relative to the skill directory, for example `<skill-dir>/scripts/Get-DocxOutline.ps1 ./doc.docx`. The current `.\scripts\` form only resolves when the working directory is the skill folder, while `'.\doc.docx'` assumes the document's folder.

7. **low** · Writing effective descriptions (collection 'Not for … (other-skill)' convention) · SKILL.md frontmatter description
   > Edit .docx files by driving Microsoft Word via COM — tracked changes, formatting preserved. … Requires Windows with Word.

   Fix: Add the user-facing trigger terms the eval prompts use: 'Word document', 'redline or markup to approve', 'contents page'. End with the collection's disambiguation clause, e.g. 'Not for converting a .docx to markdown to read (firecrawl) or generating .docx from application code (code-authoring).' This matches the eval negatives and the back-reference in firecrawl's description.

8. **low** · Structure longer reference files with a table of contents · references/word-com-traps.md (117 lines); references/manifests.md (121 lines)
   > # Word COM Traps — Full Explanations

Every one of these was hit in production and cost real debugging time.

   Fix: Both files are over 100 lines and have no contents list. Add a short contents list at the top of each: the nine numbered traps, and the manifest sections (ops table, safety guards, example batch, chaining, CSV columns).

## Strengths

- Low-freedom, verifiable workflow: the dry run is mandatory, every op gets an explicit status, and nothing changes silently, which is the feedback-loop pattern done properly.
- Scripts give specific, actionable error messages. Unknown styles are listed with the styles that do exist, and deleteParas refusals quote the live paragraph text and enforce a maxParas guard.
- Verification runs on the materialised final state (New-DocxAccepted.ps1, then Find-DocxTerms.ps1) rather than the marked-up file, and the skill explains in one line why that matters.

## Cut candidates

- Opening paragraph under '# Word Document Editing (COM Automation)': the explanation of why Word does the writing and why OOXML surgery is risky can shrink to one sentence.
- '## When to Use': repeats the description, and the body only loads after the skill has triggered.
- '## Word COM Traps' table: duplicates references/word-com-traps.md and the scripts already defend against every trap.
- '## Working Style That Holds Up': the 'Batch + manifest + log' and 'narrowed replacement' bullets repeat the Procedure and manifests.md.
- '## Common Issues': the 'range check failed' and 'Accepted page count differs' rows repeat manifests.md and the traps; 'Word dialog appeared' duplicates the 'Script hangs' row.
