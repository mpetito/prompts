# story

Verdict: **needs-work** · SKILL.md body 348 lines · description 595 chars

The description is specific and trigger-rich, the ADO payloads live in a one-level reference file, and the evals pair realistic fixtures with objective assertions. The main gap is repetition: the description, acceptance-criteria and story-point formats are each restated two to four times, and some restatements contradict each other (split above 8 or above 13; bug content in Description or in ReproSteps). About a third of the body could go.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names ADO, User Stories/Issues/Bugs, Fibonacci story points, repro steps, severity, acceptance criteria. |
| Description includes both what the Skill does and when to use it | pass | What + 'Use when …' + collection-standard 'Not for …' clause; 595 chars, under 1,024. |
| SKILL.md body is under 500 lines | pass | 348 body lines, but much of it is duplication. |
| Additional details are in separate files (if needed) | pass | Field reference names and JSON payloads are in references/ado-field-examples.md. |
| No time-sensitive information | pass |  |
| Consistent terminology throughout | fail | The split threshold is 13 in one place and 8 in another. The Bug template targets 'Description' while the reference puts the same content in ReproSteps. 'Additional Context' is an H2 in one template and an H4 in another. |
| Examples are concrete, not abstract | pass | The AC examples and the reference payloads are concrete. |
| File references are one level deep | pass | SKILL.md links only references/ado-field-examples.md, which links nothing further. |
| Progressive disclosure used appropriately | partial | Payloads are split out, but the same templates repeat inside SKILL.md instead of appearing once. |
| Workflows have clear steps | partial | The 5-step creation workflow is clear, but the clarification gate and the 'read the reference first' instruction sit in separate sections after the workflow, not inside its steps. |
| Structure longer reference files with a table of contents | fail | references/ado-field-examples.md is 115 lines with no contents list. |
| MCP tool references (fully qualified names) | partial | Uses `azure-devops/wit_create_work_item`, a VS Code-style prefix. That is neither the ServerName:tool_name form nor the collection's capability-description convention. |
| No Windows-style paths | pass | The only backslash is in an ADO iteration path value (ProjectName\Sprint 1), which is correct. |
| Validation/verification steps for critical operations | partial | There is a pre-create clarification checklist. Nothing confirms the created item's fields after wit_create_work_item returns. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No voodoo constants | not-applicable | No scripts. |
| At least three evaluations created | pass | evals/shared-benchmark.json has 2 behavioural cases with fixtures, regex and judge assertions, plus 6 trigger and negative-trigger cases. |

## Findings

1. **high** · Use consistent terminology · SKILL.md, Story Points Estimation / Common Mistakes (lines 127-131, 345, 354)
   > "**Maximum is 13 points** - If larger, split into multiple stories" vs "Overloaded stories: … split when estimated above 8 points"

   Fix: Pick one split rule (13 is the maximum and an estimate of 13 is a split candidate, matching the table and the evals) and state it once under Estimation. Remove the conflicting 'above 8' clause from Common Mistakes. (about 15 tokens saved)

2. **high** · Use consistent terminology · SKILL.md, Description Formats > Bug Description Format (lines 92-114) vs references/ado-field-examples.md, Bug
   > SKILL.md: "### Bug Description Format … ## Expected Behavior … ## Environment"; reference: "Bugs put expected/actual behavior and reproduction steps in `ReproSteps`, not `Description`."

   Fix: Rename the template 'Bug Repro Steps format' and order it as the reference does (Steps, Expected, Actual). Move the Environment block to the System Info field. One structure, one field mapping. (about 20 tokens saved)

3. **high** · Concise is key / Progressive disclosure (no duplicated content) · SKILL.md, Quick Reference Card (lines 314-346)
   > "### Story Format … As a [user type], I want to [action] so that [benefit]." / "### Story Points Quick Guide - **1-2**: Simple…"

   Fix: Delete the whole Quick Reference Card. The story, issue and AC formats and the points scale are already defined above, and the Title Guidelines are generic knowledge. (about 220 tokens saved)

4. **medium** · Concise is key / Use consistent terminology · SKILL.md, Markdown Formatting for Azure DevOps (lines 206-243)
   > "### Description Structure … #### Additional Context" (Description Formats uses "## Additional Context"); "### Acceptance Criteria Structure" repeats the AC template at lines 183-202

   Fix: Keep the four formatting rules and delete both structure blocks. Make the Description Formats templates the single source and choose one heading level for Additional Context, matching the H4 in the reference payloads. (about 160 tokens saved)

5. **medium** · Concise is key / Workflows have clear steps · SKILL.md, Clarification Checklist (lines 267-300)
   > "For bugs: expected-vs-actual behavior is missing, reproduction steps are missing or unclear, environment details are unavailable…" then "### For Bugs - [ ] Expected behavior described - [ ] Actual behavior described…"

   Fix: Keep only the per-type checkbox lists, cut the prose 'Clarification First Gate' bullets that duplicate them, and make 'check the clarification checklist; ask if any box fails' step 1 of the creation workflow. (about 110 tokens saved)

6. **medium** · Concise is key (Claude is already very smart) · SKILL.md, Acceptance Criteria Guidelines > Good Examples / Bad Examples; Common Mistakes 1 and 5; Overview; Estimation Guidelines
   > "- ❌ \"Code is clean\" - ❌ \"Application is fast\" - ❌ \"Design looks nice\"" / "This skill provides guidelines for creating well-structured Azure DevOps work items…"

   Fix: Cut the Overview paragraph and the seven-item Good Examples list, since the patterns table already pairs each pattern with an example. Trim Bad Examples to three. Drop Common Mistakes 1 and 5, which repeat them, and the generic 'Relative sizing / Include all work / Account for unknowns' bullets. (about 230 tokens saved)

7. **low** · Workflows have clear steps / Provide utility files with clear execution intent · SKILL.md, Azure DevOps Creation Workflow step 3 and Example Field Specifications (lines 252-263)
   > "Read that file before composing a create call." (a separate section after the workflow)

   Fix: Fold the reference pointer into workflow step 3: 'Read references/ado-field-examples.md for field reference names, then call …'. Delete the standalone section. (about 40 tokens saved)

8. **low** · Structure longer reference files with a table of contents · references/ado-field-examples.md (115 lines)
   > "# Azure DevOps Field Specification Examples" with no contents list before the field table

   Fix: Add a one-line contents list (Field names, User Story, Bug, Issue) under the title. While there, add the System.IterationPath entry to the Bug and Issue payloads so they match SKILL.md's required-fields tables.

## Strengths

- Its evals pair realistic fixtures that hide a trap with objective assertions: a request filed as a Bug that is really a missing feature, non-Fibonacci estimates, and an oversized estimate that must be split. Each one aims at a specific instruction in the skill.
- Its description ends with a precise 'Not for' clause naming the neighbouring skills (pr-authoring, spec, tt), and negative trigger cases in the evals test each one.
- Bulky field reference names and JSON payloads sit in a single one-level reference file that is read only before a create call.

## Cut candidates

- Overview
- Quick Reference Card (entire section)
- Markdown Formatting for Azure DevOps > Description Structure and Acceptance Criteria Structure
- Acceptance Criteria Guidelines > Good Examples
- Estimation Guidelines (relative sizing, include all work, account for unknowns)
- Clarification Checklist > Clarification First Gate prose bullets
- Common Mistakes 1 and 5
- Quick Reference Card > Title Guidelines
