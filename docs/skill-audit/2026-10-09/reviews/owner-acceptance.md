# owner-acceptance

Verdict: **good** · SKILL.md body 73 lines · description 815 chars

The skill is short (73 body lines), does one job, uses a numbered four-step workflow, a pass/fail friction table and a strict three-line report template, so it fits the best-practice shape with almost nothing to cut. The most important gap is that the safety exception on the sample default appears only in the Common Issues table, not in step 3. Smaller gaps: no re-walk step after friction fixes, a few lines that repeat the description or each other, and no evals.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names the walk, the friction checklist and the sample-before-pipeline rule, with concrete trigger phrases. Some examples use one project's terms (a milestone id, a screen name and a piece of copy). |
| Description includes both what the Skill does and when to use it | pass | 'Gate complete on…' then 'Use whenever… Load it before writing the status that says done', plus a Not-for clause. |
| SKILL.md body is under 500 lines | pass | 73 lines. |
| Additional details are in separate files (if needed) | not-applicable | Single file; nothing needs splitting at 73 lines. |
| No time-sensitive information | pass |  |
| Consistent terminology throughout | partial | The report template uses <date -u> on one line and <date> on another. The description says 'done' while the body says 'complete'; this is minor. |
| Examples are concrete, not abstract | pass | Concrete failure cases (wrong code, expired link, slow network) and a filled report shape. |
| File references are one level deep | not-applicable | No references; the only links are skill names in the description. |
| Progressive disclosure used appropriately | pass | Small enough to live in one file. |
| Workflows have clear steps | pass | Four numbered phases, numbered sub-steps, and a record format for each step. |
| Validation/verification steps for critical operations | partial | The walk is the validation, but nothing says to walk again after friction fixes change the SHA. |
| Feedback loops included for quality-critical tasks | partial | Step 3 has a sample, review and rule-change loop. Step 2 has no fix-then-re-walk loop. |
| Template pattern strictness matches need | pass | The report block is strict ('in this shape'), and 'Anything less is built and reviewed' fixes the status vocabulary. |
| At least three evaluations created | fail | No evals/ directory. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No Windows-style paths | pass |  |

## Findings

1. **medium** · Workflows and feedback loops / Use workflows for complex tasks (clear steps prevent skipping critical validation) · SKILL.md, Common Issues row 3 vs Procedure step 3.2 (lines 55, 76)
   > | The sample review stalls because the owner is away | Default applies at the stated time for content with no safety or legal exposure; everything else waits |

   Fix: Put the exception in step 3.2 itself, e.g. 'Ask one question with a default (content with safety or legal exposure gets no default; it waits for the owner)', and delete the Common Issues row. As written, a model following the numbered steps sets a self-applying default on consent or legal copy and only learns the limit if it reads the troubleshooting table. (about 10 tokens saved)

2. **medium** · Implement feedback loops / Validation steps for critical operations · SKILL.md, Procedure step 2 and step 4 (lines 37, 63)
   > a "no" is a finding to fix before "complete", not a note for later
...OWNER PATH: walked <date -u> on <environment> at <sha>

   Fix: Add one clause to step 2: 'after fixes deploy, re-walk the affected steps on the new SHA before reporting'. Without it, the walk can be stamped at a SHA that predates the fixes, and the report's 'friction: fixed' is never verified on the owner's path.

3. **low** · Concise is key (Claude reads the description before loading; body sections that restate it cost tokens) · SKILL.md, ## When to Use (lines 13-17)
   > - Before reporting any owner-visible slice as complete, deployed or ready to demo
- Before running a pipeline over owner-facing content (copy, labels, categories, templates)

   Fix: Delete the section. The first two bullets repeat the description's 'Use whenever…' clause, and the body loads only after the skill has already triggered. If the third bullet ('show me', 'simplest', 'visible progress first') matters, move it into the description as trigger phrases. (about 60 tokens saved)

4. **low** · Concise is key / Default assumption: Claude is already very smart · SKILL.md, intro paragraph (lines 8-11) and Common Issues row 4 (line 77)
   > In one build, every owner-facing slice was declared complete on CI, reviewer approval and a live
health probe, and the owner then found the gaps on first use

   Fix: Cut the paragraph to its last two sentences ('Machine evidence proves the code does what the tests say. This gate proves the owner can use it.'). Common Issues row 4 already makes the point that CI and approvals are not enough, so the anecdote adds tokens and no instruction. (about 50 tokens saved)

5. **low** · Use consistent terminology · SKILL.md, ### 4. Report template (lines 63-65)
   > OWNER PATH: walked <date -u> on <environment> at <sha>
...CONTENT: <sampled with owner on <date> | not owner-facing>

   Fix: Use <date -u> on both lines. Also say where the per-step records from step 1 ('path step · observed · screenshot or quote') go, for example 'attach the step records below this block', so the strict template and the step-1 record format do not conflict.

6. **low** · Writing effective descriptions (specific triggers that generalise across the contexts where the skill is used) · SKILL.md frontmatter description
   > call the milestone complete, deploy the settings page to dev, check the first-run experience, draft the tag list or the onboarding copy

   Fix: Replace the project-specific examples with generic ones ('call the milestone complete', 'deploy the settings page to staging', 'draft the onboarding copy'). The skill is symlinked into every project, so its trigger phrases should match how any owner-facing build is described, not one repository. (about 5 tokens saved)

7. **low** · Evaluation and iteration / Build evaluations first (checklist: at least three evaluations) · skills/owner-acceptance/ (no evals/)
   > Anything less is "built and reviewed", which is a different status.

   Fix: Add an evals/shared-benchmark.json with about three fixture cases. For example: a lane with green CI and approvals asks for a 'complete' status (expect 'built and reviewed' plus the walk). A 70-item taxonomy is about to be generated (expect 8 to 10 samples first). Onboarding copy is waiting on an absent owner (expect no self-applying default). Add near-miss trigger negatives from review and autonomous-loops.

## Strengths

- A strict three-line report template, plus a named lesser status ('built and reviewed'), so a missing walk shows up in the status line instead of being left out.
- The friction check is a two-column pass/fail table, so the model can apply it per screen without interpreting prose.
- It covers the 'cannot walk yet' case explicitly ('listed as not walked, never as passed'), which closes the most likely shortcut.

## Cut candidates

- ## When to Use (repeats the description's 'Use whenever…' clause)
- Intro paragraph anecdote 'In one build, every owner-facing slice was declared complete…' (Common Issues row 4 already makes the point)
