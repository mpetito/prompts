# agents-md-authoring

Verdict: **needs-work** · SKILL.md body 232 lines · description 285 chars

The skill has a precise, trigger-rich description, a usable template, a sharp nested-file conflict policy, and an evals suite with realistic fixtures and negative trigger cases. Its biggest gap is repetition. The 150-line budget, the Do Not example, the See Also example and the "check the commands work" rule each appear two to five times, across Top Priorities, a Format table, two separate checklists, an Anti-Patterns table and a Core Principles section. Roughly a quarter of the body could go with no loss of guidance.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names all three filenames, nested per-package files and onboarding; the one vague phrase is 'agent instructions or config' |
| Description includes both what the Skill does and when to use it | pass | 'Author or review ...' plus 'Use when ...' plus the collection's 'Not SKILL.md (skill-authoring)' clause; 285 chars |
| SKILL.md body is under 500 lines | pass | 232 lines |
| Additional details are in separate files (if needed) | not-applicable | No references/ folder; at 232 lines none is needed once the duplication is removed |
| No time-sensitive information | partial | '`AGENTS.md` (the emerging standard)' will go stale |
| Consistent terminology throughout | partial | The length limit appears as '≤ 150 lines', '~150 lines' and 'under 150 lines'; Conflict Resolution step 4's 'no top priority applies' is ambiguous |
| Examples are concrete, not abstract | pass | Do Not examples name the alternatives; the template mixes placeholders with one concrete path |
| File references are one level deep | pass | The only link is ../skill-authoring/SKILL.md, which is skill-relative as the collection requires |
| Progressive disclosure used appropriately | pass | Single file at a reasonable size |
| Workflows have clear steps | partial | Top Priorities is ordered and Validation Checklist is numbered, but the create path and the review/trim path are never separated, and the two checklists overlap |
| Validation/verification steps for critical operations | pass | Validation Checklist: 'Commands actually work when executed', 'File paths exist in the repository' |
| Feedback loops included for quality-critical tasks | partial | 'Stop at the first violation, fix it, then continue' gives a loop for the priorities only; the final Validation Checklist has no re-check-after-fix step |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts |
| No Windows-style paths | pass |  |
| At least three evaluations created | pass | evals/shared-benchmark.json has 2 functional cases with fixtures plus 6 trigger cases (3 positive, 3 negative) |
| Tested with real usage scenarios | pass | Fixtures model realistic repos: stale yarn commands, a 430-line root file, an unlabeled nested conflict |

## Findings

1. **high** · Concise is key / Consistent terminology throughout · SKILL.md: Top Priorities (L18), Format Requirements (L58-65), Quality Checklist (L156-165), Anti-Patterns (L175), Validation Checklist (L227-236)
   > "1. **Length budget**: ≤ 150 lines." / "| Maximum length | ~150 lines |" / "- [ ] **Concise**: under 150 lines" / "4. [ ] Under 150 lines"

   Fix: State the budget once, as one hard number with one wording, in Top Priorities. Delete the Format Requirements table: 'Pure Markdown', 'Copy-pasteable' and 'not prose' are already priorities 1-2. Merge Quality Checklist and Validation Checklist into a single final checklist; today they repeat concise/commands/README/Do Not almost line for line. (about 230 tokens saved)

2. **medium** · Concise is key · SKILL.md: Content Deduplication > Effective "Do Not" Section (L202-213) and the See Also example (L192-200)
   > "- ❌ Hard-code colors — use design tokens from `src/theme/tokens.ts`
- ❌ Use `any` types — add proper type annotations"

   Fix: Cut both code blocks. They repeat the template's Do Not (L138-141) and See Also (L148-151) sections almost verbatim. Keep the one-line takeaway 'each prohibition names its alternative' as a template comment or a checklist item. (about 170 tokens saved)

3. **medium** · Concise is key (Claude is already very smart) · SKILL.md: Core Principles (L217-223), Behavior (L44), intro (L8, L24)
   > "**Context window is a public good.** This file is loaded on every turn ..." / "it costs tokens on every turn, which is why the length budget matters"

   Fix: Delete the Core Principles section and the Behavior bullet on token cost. Both restate Top Priority 1, and a skill-loading model already knows the rationale. Fold 'do not explain the language or framework' into one Anti-Patterns row. Drop the 'onboarding documentation' sentence and 'All other guidance below elaborates on these five.' (about 170 tokens saved)

4. **medium** · Use workflows for complex tasks / Conditional workflow pattern · SKILL.md: Top Priorities (L14-24) through Validation Checklist (L227-236)
   > "Enforce these in order. Stop at the first violation, fix it, then continue."

   Fix: After removing the duplicates, restructure as two short paths. Creating: verify the commands, then fill in the template, then run the checklist. Reviewing or trimming: measure the length, move content using the Content Deduplication table, fix unlabeled nested conflicts, then run the checklist. Both end with 'fix and re-run the checklist until it passes'. The description promises 'Author or review', and an eval case asks to trim a 400-line CLAUDE.md, but the body gives no review path.

5. **low** · Concise is key / Avoid offering too many options · SKILL.md: Hierarchy Strategy (L67-92) and Anti-Patterns 'Over-nesting' row
   > "| **Subdirectory**     | When the directory has conventions that differ from root       |"

   Fix: Keep either the tree diagram (its inline '← If distinct stack/conventions' notes already state the criteria) or the Placement Criteria table, not both. Drop the 'Over-nesting' and 'Mega-files' anti-pattern rows, which restate Top Priority 5 and the length budget. (about 120 tokens saved)

6. **low** · Consistent terminology throughout · SKILL.md: Conflict Resolution Between Nested Files, steps 1, 4 and 5 (L50-54)
   > "4. **When ambiguous and no top priority applies, prefer the stricter rule**" / "5. **No explicit override provided**: if nested files contradict without a label, warn"

   Fix: Make step 1 ('closest ancestor wins') and step 5 (an unlabeled contradiction triggers a warning) agree. For example: the closest file wins, but an unlabeled contradiction is also reported. Replace 'top priority' with a reference that actually exists, or delete it. (about 20 tokens saved)

7. **low** · Consistent terminology / Template pattern · SKILL.md: Template (L98-152) vs Validation Checklist item 6 and the 'Implicit knowledge' Anti-Patterns row
   > "6. [ ] All project-specific terms are defined"

   Fix: Add a one-line '## Terms' placeholder to the template. Then delete the 'Implicit knowledge' anti-pattern row, since the template carries that rule. The checklist and the eval (defines-project-terms) require a terms section that the template never shows. (about 10 tokens saved)

8. **low** · Avoid time-sensitive information / Writing effective descriptions · SKILL.md: File Names by Tool table (L34); frontmatter description
   > "| Cross-tool     | `AGENTS.md` (the emerging standard)                       |" / "Use when writing agent instructions or config"

   Fix: Remove '(the emerging standard)'. In the description, replace 'or config' with a concrete trigger such as 'trimming an oversized CLAUDE.md'. 'Config' can match subagent definitions or settings.json requests that belong to other skills. (about 5 tokens saved)

## Strengths

- The evals suite pairs realistic repo fixtures (stale yarn commands, a 430-line root file, an unlabeled nested conflict) with regex and judge assertions, plus negative trigger cases for SKILL.md, README and CONTRIBUTING
- The Content Deduplication table routes each kind of content to its home file, which is a compact decision aid for trimming
- Conflict Resolution Between Nested Files gives an explicit, ordered policy, including a labeled-override convention ('> Overrides root AGENTS.md: uses pnpm instead of npm')

## Cut candidates

- Format Requirements
- Quality Checklist (merge into Validation Checklist)
- Content Deduplication > Effective "Do Not" Section
- Content Deduplication > See Also example block
- Core Principles
- Behavior > token-cost bullet
- Hierarchy Strategy > Placement Criteria (duplicates the tree annotations)
- Anti-Patterns rows: Over-nesting, Mega-files, Missing boundaries
