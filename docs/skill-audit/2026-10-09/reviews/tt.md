# tt

Verdict: **good** · SKILL.md body 184 lines · description 265 chars

tt is a well-ordered, low-freedom procedure. It gives concrete good and bad note examples, a fixed format for the memory file, and a Common Issues table, and at 184 body lines it needs no references/ split. The most important gap is repetition: the never-delete, never-invent-an-id, no-changelog and no-append rules each appear two or three times. Step 3 also contradicts itself on ad-hoc bug fixes, and the evals cover only triggering, not the fragile logging behaviour.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names Harvest, Azure DevOps, time entry and /tt. Unlike the rest of the collection, it has no 'Not for ...' clause. |
| Description includes both what the Skill does and when to use it | pass |  |
| SKILL.md body is under 500 lines | pass | 184 lines |
| Additional details are in separate files (if needed) | not-applicable | Short enough to stay in one file |
| No time-sensitive information | pass | The task ids are hard-coded but described as stable, with list_tasks as a fallback |
| Consistent terminology throughout | partial | The cache is called 'agent memory', 'repo memory' and 'the host's memory location'. Asking the user is called both 'the question tool' and 'ask the user'. |
| Examples are concrete, not abstract | pass | Real note examples for Case A and Case B, plus one bad and two good notes |
| File references are one level deep | pass | No reference files |
| Progressive disclosure used appropriately | pass |  |
| Workflows have clear steps | partial | Steps 1 to 7 are clear, but step 3 conflicts with itself on whether to ask about ad-hoc bug fixes |
| Validation/verification steps for critical operations | pass | Step 6 lists today's entries before deciding between update and create; step 7 reports the entry id |
| Feedback loops included for quality-critical tasks | partial | No re-check of the composed note against the 80-character limit and format before log_time |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts |
| No voodoo constants | pass | The task ids and the 0.25h rounding are explained |
| No Windows-style paths | pass |  |
| MCP tool references are fully qualified | partial | Only list_projects is tied to Harvest. list_time_entries, log_time, update_time_entry, list_tasks and search_workitem name no server. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 cases, all trigger cases with empty assertions; none test behaviour |
| Tested with real usage scenarios | partial | The trigger prompts are realistic, but nothing tests the output (note format, rounding, update versus create) |

## Findings

1. **medium** · Concise is key; Consistent terminology · SKILL.md, '## Rules' (lines 161-170), compared with the blockquote at line 14 and steps 3, 4 and 6
   > - ❌ Never delete, zero-out, or replace an existing entry's hours with a smaller value.
- ❌ Never invent a work item id; cite only ids verified in ADO.

   Fix: The Rules list repeats rules already stated in the procedure: never delete (line 14 and step 6), never use timers (line 16), never invent an id (step 3), notes of 80 characters or fewer (step 4) and never append to a note (step 6, twice). Keep each rule in one place. Either cut Rules down to the two items found nowhere else (honest estimates; append-only mapping) or keep Rules and remove the inline restatements. (about 120 tokens saved)

2. **medium** · Workflows have clear steps; Consistent terminology · SKILL.md, step 3 'Resolve the work item' (lines 89-95)
   > ask the user for a work item id before logging** ... Only skip the question for clearly internal or
  high-level work (e.g. general meetings, pre-sales exploration, ad-hoc bug fixes with no item).

   Fix: 'Bug fix' is listed as work that must be asked about, and 'ad-hoc bug fixes' as an example of work that may skip the question. Pick one rule. Then merge the overlapping 'Finding nothing is acceptable only for…' bullet into this one, so step 3 states the ask-or-skip decision once. (about 40 tokens saved)

3. **low** · Concise is key (only metadata is pre-loaded; body text about triggering is read too late to help) · SKILL.md, '## When to Use' (lines 18-22)
   > - The user invokes `/tt` or asks to "log time", "track time", or "record hours".
- After a pull request is created or updated (invoked as a follow-up by `pr-authoring`).

   Fix: Delete the section. Triggering depends on the description, which already lists these phrases. If the pr-authoring follow-up matters for routing, move that clause into the description. (about 70 tokens saved)

4. **low** · Concise is key · SKILL.md, '## Inputs (all optional)' and '## Parsing the invocation' (lines 24-41)
   > - **A work item** — an ADO id (e.g. `41027`) or descriptive text to search for.
...
- A standalone **4–6 digit number** -> the ADO work item id.

   Fix: Both sections describe the same two optional inputs. Merge them into one 'Invocation' section: the three parsing bullets, the examples line, and the single sentence about when to use the question tool. (about 60 tokens saved)

5. **low** · Default assumption: Claude is already very smart · SKILL.md, step 1 (lines 47-48) and the '## Repo memory format' section
   > Repo→project mappings live in **agent memory** (not a checked-in file), because Harvest
projects change over time and the mapping benefits other sessions in the same workspace.

   Fix: Cut the rationale and keep only the location. Move the table template from 'Repo memory format' into step 1, where the file is first read and created, so the format sits beside its only use. Use one name for the cache throughout: the text currently says 'agent memory', 'repo memory' and 'the host's memory location'. (about 40 tokens saved)

6. **low** · MCP tool references (use fully qualified ServerName:tool_name) · SKILL.md, steps 2, 3 and 6, and Common Issues
   > 1. List today's entries for the same project with
   `list_time_entries` (`from`/`to` = today, `project_id` = resolved project).

   Fix: Prefix each tool call with its server: Harvest for list_time_entries, log_time, update_time_entry and list_tasks, and ADO for wit_get_work_item and search_workitem. The step 3 calls are already tied to ADO; the others are bare. The Azure DevOps MCP server also has project-listing tools, so a bare list_projects is ambiguous when both servers are loaded.

7. **medium** · Build evaluations first; Testing checklist (at least three evaluations, real usage scenarios) · evals/shared-benchmark.json
   > "kind": "trigger", ... "assertions": []

   Fix: All 8 cases test triggering only. Add at least three behaviour cases with assertions on the skill's fragile rules: a note of 80 characters or fewer in the '<Type> #<id>: <Title>' form; hours rounded up to 0.25; a new entry, not a note append, for different work on the same item; and no delete or zero-out when asked to lower hours.

8. **low** · Writing effective descriptions (be specific, triggers/contexts); collection 'Not for …' convention · SKILL.md frontmatter description
   > Use when logging time, recording hours, tracking time, updating a timesheet, after a pull request is created or updated, or when invoked via /tt.

   Fix: The trigger 'after a pull request is created or updated' overlaps with the commit and pr-authoring skills, and the evals already include negative cases for commit, story and standup. Add a clause such as 'Not for committing or opening a PR (commit), sizing story points (story), or a standup summary.' Also add 'bill' and 'charge' as triggers, since the eval prompts use those words.

## Strengths

- A strict output template with real good and bad examples (Case A and Case B notes, plus one bad changelog note), so the short-note style is shown, not just described.
- Invariants are framed as tool-level facts: no delete tool and no timers, so entries are only created or updated. These are rules to obey, not limitations to work around.
- A Common Issues table that maps specific tool errors (not_found, truncated: true) to the next action, which handles the failure in the skill instead of leaving it to Claude.

## Cut candidates

- ## When to Use (duplicates the description, which is the only part read for triggering)
- ## Rules (mostly repeats the absolute-rule blockquote and steps 3, 4 and 6)
- ## Inputs (all optional), merge into ## Parsing the invocation
- Step 1 rationale sentence: 'because Harvest projects change over time and the mapping benefits other sessions'
- Step 3 bullet 'Finding nothing is acceptable only for that internal/high-level work' (restates the previous bullet)
