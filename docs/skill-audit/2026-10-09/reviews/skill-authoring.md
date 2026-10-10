# skill-authoring

Verdict: **needs-work** · SKILL.md body 264 lines · description 881 chars

The skill carries knowledge a model would not reliably have on its own: the fencing note, skill-relative cross-links, host skill roots, the split between skill-level and worker model selection, and a strong eval suite with trap fixtures. Its biggest gap is that it restates the same rules in five overlapping lists (Top Priorities, Quality Checklist, Anti-Patterns, Good vs Poor, Validation Checklist) but has no create-versus-review procedure of its own, so it breaks its own "Procedural: numbered steps" rule while spending tokens on repetition.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names SKILL.md, frontmatter, references/, trigger phrases, model/effort pinning. |
| Description includes both what the Skill does and when to use it | pass | 'Author and fix agent skills…' then 'Use when…'. 881 of 1024 chars, but the final clause is an operational instruction, not a trigger. |
| SKILL.md body is under 500 lines | pass | 264 body lines (268 total minus 4 frontmatter lines). |
| Additional details are in separate files (if needed) | pass | Worker model policy lives in references/agent-model-selection.md. |
| No time-sensitive information | pass | The reference says precedence 'changed across releases' and tells the reader to check the installed version instead of naming dates. |
| Consistent terminology throughout | partial | 'reference skills' clashes with references/ files; 'Quality Checklist' and 'Validation Checklist' cover the same ground; the description routes evals to run-skill-eval.ps1, but the eval negative says the work belongs to skill-creator. |
| Examples are concrete, not abstract | partial | The database-migration frontmatter is concrete. The template is all placeholders, and there is no concrete before/after description example. |
| File references are one level deep | pass | SKILL.md links references/agent-model-selection.md directly. That file links only out to another skill (../../model-council/SKILL.md) and external docs. |
| Progressive disclosure used appropriately | pass | One 70-line reference file, linked from the section that needs it. |
| Workflows have clear steps | partial | Top Priorities is an ordered gate, but there is no numbered create, review or split procedure; the Template's Procedure is for target skills, not this one. |
| No Windows-style paths | pass | All paths use forward slashes. |
| Validation/verification steps for critical operations | pass | Validation Checklist: commands run, paths exist, line count, YAML, fences, no duplication. |
| Feedback loops included for quality-critical tasks | partial | 'Stop at the first violation, fix it, then continue' is a loop, but the final Validation Checklist is not tied to a re-check, and evals are never part of the loop. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts/ folder. |
| Error handling is explicit and helpful | not-applicable |  |
| No voodoo constants | not-applicable |  |
| Required packages listed and verified | not-applicable |  |
| Scripts have clear documentation | not-applicable |  |
| At least three evaluations created | pass | evals/shared-benchmark.json has 2 output-graded cases with trap fixtures plus 3 positive and 3 near-miss negative trigger cases. All are split 'tune', with no held-out case. |

## Findings

1. **high** · Concise is key; the skill's own 'Avoid duplication' rule · SKILL.md: Top Priorities (L16-24), Quality Checklist (L204-214), Anti-Patterns (L216-227), Good vs Poor Skill Candidates (L229-237), Validation Checklist (L259-268)
   > "2. **Length budget**: SKILL.md < 500 lines." / "- [ ] **Under 500 lines**: detailed content moved to `references/`" / "3. [ ] Line count under 500"

   Fix: Merge the five lists into one ordered checklist. Frontmatter, trigger clause, disambiguation, name equals folder, length, skill-relative paths, fences and no duplication each appear once. Delete Good vs Poor, whose rows repeat Anti-Patterns (Skill sprawl, Abstract principles, Unbounded scope), and keep only Anti-Patterns rows that add a fix not already in the checklist. (about 450 tokens saved)

2. **medium** · Use workflows for complex tasks; Conditional workflow pattern; checklist item 'Workflows have clear steps' · SKILL.md: whole body (no Procedure section); Quality Checklist L210
   > "- [ ] **Procedural**: numbered steps with exact commands"

   Fix: Add a short conditional procedure at the top. Creating a skill: name and folder, description, body from the template, move detail to references/, validate. Reviewing, splitting or fixing a trigger: read, apply the merged checklist in order, cut or move content, re-validate. Put the merged checklist from the first finding inside it as the final validate-and-repeat step, so the overall size still goes down.

3. **medium** · Concise is key ('Default assumption: Claude is already very smart') · SKILL.md: Core Principles (L241-255)
   > "**Agents are already competent.** Only add context they don't already have. Do not explain the language, the framework, or general engineering practice."

   Fix: Cut the section. 'Context window is a public good' repeats the 600-line point at L48, and 'Write for agents' repeats the checklist. Move the three-row freedom table next to the Template, or into the merged checklist as one line such as 'Fragile steps get exact commands or a script'. (about 220 tokens saved)

4. **medium** · Concise is key; Avoid deeply nested references; Structure longer reference files with a table of contents · SKILL.md: Anatomy > Progressive Disclosure (L38-48)
   > "**This is the main lever for oversized skills.** A 600-line SKILL.md loads all 600 lines on every match."

   Fix: Delete the three-level load table and the 600-line arithmetic, which describe host mechanics the model already knows. Keep the 'Move to references/ when' list and replace the cut text with the two rules the skill never states: link every reference file directly from SKILL.md (one level deep), and start any reference file over 100 lines with a table of contents. (about 120 tokens saved)

5. **medium** · Writing effective descriptions; Consistent terminology · SKILL.md frontmatter description (final clause); evals/shared-benchmark.json neg-trig-benchmark-skill
   > "this skill has no eval procedure, so run scripts/run-skill-eval.ps1 directly (Evaluating Skills in the README)."

   Fix: Cut the clause to a plain disambiguation, such as 'and not for running or benchmarking a skill's evals (README Evaluating Skills)'. The description loads in every session, and this instruction uses a repo-root path that does not resolve from the symlinked skill folder. Make the eval's expected_behavior name the same destination instead of 'skill-creator'. (about 30 tokens saved)

6. **medium** · Build evaluations first; checklist item 'At least three evaluations created' · SKILL.md: Validation Checklist (L259-268)
   > "1. [ ] Commands actually work when executed" … "6. [ ] No content duplicated from another skill"

   Fix: Add one checklist line saying when a skill needs an evals/shared-benchmark.json suite, with at least three cases, fixture traps and near-miss trigger negatives, and saying to rerun it before and after an edit, pointing to the README's Evaluating Skills section. Right now the collection's eval convention is visible only in CONTRIBUTING.md and README.

7. **medium** · Writing effective descriptions (when-to-use belongs in metadata); Template pattern (state strictness) · SKILL.md: Template (L140-198)
   > "## When to Use\n\n- User asks to [specific action]\n- [Condition] requires this procedure"

   Fix: Drop the body 'When to Use' section from the template. The body loads only after the description has already matched, so trigger conditions belong in the description, which the template already requires. Label the template as an adaptable default, and make Rollback conditional on destructive steps. (about 40 tokens saved)

8. **low** · Use consistent terminology · SKILL.md: Choosing model and effort (L127); references/agent-model-selection.md L67
   > "**Do not set `model` on reference skills** — ones consumed *inside* another task rather than invoked directly."

   Fix: Rename 'reference skills' to a term that cannot be confused with references/ files, such as 'consumed skills', matching README's 'consumed inside another task'. Use the same term in agent-model-selection.md.

## Strengths

- The fencing note (L200) names a quiet, hard-to-spot defect and its exact fix (a wider outer fence). It is the kind of knowledge a model lacks and a skill should carry.
- The model guidance separates the skill-level `model`/`effort` setting from worker model selection, and it tells consumed skills not to pin a model and says why.
- The evals pair realistic trap fixtures (wrong folder name, haiku pin, repo-root link, copied section, nested fence) with assertions that each trace to a rule in the skill, plus near-miss trigger negatives for adjacent skills (agents-md-authoring, commit).

## Cut candidates

- Core Principles
- Good vs Poor Skill Candidates
- Progressive Disclosure: the three-level load table and the '600-line SKILL.md' paragraph
- Validation Checklist (merge into one checklist with Quality Checklist and Top Priorities)
- Anti-Patterns rows that repeat the checklist (Missing frontmatter, Weak descriptions, Repo-relative paths)
- Template: '## When to Use' section
