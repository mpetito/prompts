# pr-feedback

Verdict: **needs-work** · SKILL.md body 176 lines · description 943 chars

The skill has a well-ordered workflow: collect, verify, fix, draft, get approval, then post. It treats feedback as evidence-backed claims, puts a disposition table and a strict summary template up front, and ends with a script check on thread resolution. The most important gap is that the closing sections repeat and contradict the workflow. Step 6.6 suggests running /pr-resolve and /commit after step 6 has already committed, replied and resolved. The disposition, reply and resolution steps use three different sets of category names, and the Guidelines section repeats rules the steps already state.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names Copilot, CI, CodeQL, collapsed/suppressed review sections and null-check pushback. At 943 chars it is close to the 1,024 limit, so there is little room left for edits. |
| Description includes both what the Skill does and when to use it | pass | "Triage review feedback…" plus "Use whenever someone or something has commented on a PR you opened"; the Not-for clause follows collection convention. |
| SKILL.md body is under 500 lines | pass | 176 body lines. |
| Additional details are in separate files (if needed) | pass | Script invocation, the resolution matrix, reply templates and common issues are in ../pr-scripts/REFERENCE.md. |
| No time-sensitive information | pass | Nothing dated in SKILL.md. The shared REFERENCE.md mentions "its consolidated successor" for an MCP tool, which is borderline. |
| Consistent terminology throughout | fail | The disposition table (Confirmed defect, Worthwhile improvement, False positive, Unnecessary complexity…), the step 4 reply types (fixed, explained, deferred, declined, outdated) and the step 6 / REFERENCE matrix thread types (fixed, answered, design explained, disagreement) are three vocabularies for one decision. |
| Examples are concrete, not abstract | partial | The output template is concrete. The reply examples sit in REFERENCE.md. The SKILL.md script call in step 6.2 uses placeholders without the path or how to invoke it. |
| File references are one level deep | partial | SKILL.md links REFERENCE.md directly. REFERENCE.md then defers script parameters to pr-scripts/README.md, a second level. |
| Progressive disclosure used appropriately | partial | The reference split is good. However, the 153-line REFERENCE.md has no table of contents and must be read in full "before the first call". |
| Workflows have clear steps | partial | Steps 1–6 are numbered and clear, but step 6.6 contradicts steps 6.1–6.4, and Guidelines repeats the step rules. |
| Scripts have clear documentation | partial | Documented in the shared REFERENCE.md. SKILL.md names scripts bare ("Run `Get-PrFeedback.ps1`") without the ../pr-scripts/ path or the pwsh -NoProfile -File form a Bash host needs. |
| Required packages listed in instructions and verified as available | partial | pwsh 7 and an authenticated gh are listed only in REFERENCE.md, with a fallback path. SKILL.md does not say to check for them. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | A user-approval gate before commit/push/reply, Test-PrThreadsResolved.ps1, and a separate check for findings that exist only in review bodies. |
| Feedback loops included for quality-critical tasks | pass | Step 2.4 has the checker fail on the pre-fix state. Step 3 runs the smallest relevant tests per fix. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts in this skill folder; it uses the shared pr-scripts collection. |
| At least three evaluations created | partial | The 8 cases in evals/shared-benchmark.json are all trigger cases with empty assertions. None tests the skill's behaviour: pushing back on blanket null checks, inspecting suppressed sections, or not posting before approval. |
| Tested with Haiku, Sonnet, and Opus | not-applicable | Cannot observe. The frontmatter pins model: sonnet. |

## Findings

1. **high** · Workflows have clear steps / Use workflows for complex tasks · SKILL.md, ### 6. Commit, Reply, Resolve After Approval, lines 164-166
   > 6. Suggest next steps:
   - `/pr-resolve` — reply to and resolve remaining PR review threads.
   - `/commit` — commit, push, and update the PR.

   Fix: Delete step 6.6. Steps 6.1–6.5 have already committed, pushed, replied, resolved and verified, so suggesting /commit and /pr-resolve afterwards contradicts the workflow and invites a duplicate push or duplicate replies. (about 40 tokens saved)

2. **medium** · Use consistent terminology · SKILL.md, disposition table (lines 85-93), ### 4 Prepare Responses (lines 111-113), ### 6 steps 2-4 (lines 159-161)
   > | Unnecessary complexity | No sufficient benefit for the added machinery | Decline with rationale |
... fixed, explained, deferred, declined, outdated, or a clarification request.

   Fix: Add a single column to the disposition table naming the reply template and whether the thread is resolved or left open (for example "Unnecessary complexity → Declined template, leave open"). Then use the disposition names in steps 4 and 6 and drop the separate prose lists in 6.2–6.4. (about 60 tokens saved)

3. **medium** · Concise is key · SKILL.md, ## Guidelines, lines 168-177
   > - Wait for user approval before committing, pushing, replying, or resolving.
- Be respectful; accept good suggestions and justify disagreements professionally.

   Fix: Cut the Guidelines bullets that repeat step 5/6 rules or REFERENCE.md: approval gate, "Never resolve without replying first", commit SHAs, respectful tone. Remove "Ask first, code second", which conflicts with step 2's "Investigate what can be verified locally before asking". Move the one new rule (batching deferred low-severity items per area) into the Deferred row or step 4. (about 110 tokens saved)

4. **medium** · Structure longer reference files with a table of contents / Avoid deeply nested references · SKILL.md ## Tooling (lines 27-29); ../pr-scripts/REFERENCE.md (153 lines)
   > the resolution decision matrix, and the reply templates are in
[`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md). Read it before the first call.

   Fix: Add a short table of contents to REFERENCE.md, which is over 100 lines and has none. In SKILL.md, link the specific anchors (#invocation, #reply-templates, #common-issues) where each is needed rather than asking for a full read up front. REFERENCE.md also defers script parameters to pr-scripts/README.md, a second level; either bring the parameters it needs into REFERENCE.md or link README.md from SKILL.md directly.

5. **medium** · Provide utility scripts (make execution intent clear; document command line) · SKILL.md, ### 1 step 2 (line 40) and ### 6 step 2 (line 159)
   > 2. Run `Get-PrFeedback.ps1` — one call returns unresolved review threads, full review bodies
... with `Resolve-PrThread.ps1 -ThreadId ... -Body "..."`.

   Fix: Give the exact command once in step 1: `pwsh -NoProfile -File ../pr-scripts/Get-PrFeedback.ps1 [-Pr <n>]`, with a note that it needs pwsh 7 and an authenticated gh, and to use the fallback in REFERENCE.md#invocation otherwise. Then delete the bare-name list in ## Tooling (lines 31-33), which repeats REFERENCE.md. (about 30 tokens saved)

6. **low** · Concise is key (default assumption: Claude is already very smart) · SKILL.md, lines 10-23 (intro, ## Related Skills, ## Inputs and Context)
   > Use this skill to resolve pull request feedback systematically before posting replies or resolving threads.
- [pr-review](../pr-review/SKILL.md) — an independent review of someone else's PR

   Fix: Cut the intro sentence, which restates the description. Cut ## Related Skills: pr-review is already in the description's Not-for clause and model-council is linked again in step 2.6. Merge the PR-identification bullets in Inputs and Context into step 1.1, which already says "explicit input, VS Code PR context, current branch, or `gh pr view`". (about 130 tokens saved)

7. **low** · Concise is key · SKILL.md, suppressed-comment reminders at lines 43-46, 55, 82-83, 115-117, 130, 147, 162-163
   > Suppression is neither proof of a false positive nor a reason to skip inspection.
... A suppressed label alone does not trigger a council

   Fix: Keep the suppressed-section rule once in step 1.3, plus the Coverage line in the template and the 6.5 body-only check. Remove the repeats at line 55, line 82's second sentence and line 115's first sentence. REFERENCE.md lines 49-52 say the same again. (about 70 tokens saved)

8. **low** · Build evaluations first / At least three evaluations created · evals/shared-benchmark.json
   > "kind": "trigger", ... "assertions": []

   Fix: All eight cases test triggering only. Add at least three behaviour cases with assertions for the gaps the skill exists to close: declining blanket null checks with evidence, inspecting a collapsed or suppressed review section, and stopping at the step 5 summary without committing or posting.

## Strengths

- The disposition table pairs each verdict with its meaning and its action, and step 2 requires evidence before every disposition, including a quote from the docs before changing code over a platform-behaviour claim. That is a good non-code feedback loop.
- There is a strict output template with an explicit approval gate before any commit, push, reply or resolve. The scripted check (Test-PrThreadsResolved.ps1) is backed by an explicit reminder that it covers threads only.
- Script usage, reply templates and the resolution matrix live in one shared reference (pr-scripts/REFERENCE.md) used by three skills, which stops copies from drifting apart. The eval negative cases name the sibling skill that should trigger instead.

## Cut candidates

- Intro sentence under # PR Feedback (restates the description)
- ## Related Skills (pr-review is in the description's Not-for clause; model-council is repeated in step 2.6)
- ## Inputs and Context, first two bullets (repeated in step 1.1)
- ## Tooling, list of script names (repeats REFERENCE.md#invocation)
- ## Guidelines (repeats the approval gate, never-resolve-without-replying, commit SHAs and respectful tone)
- ### 6 step 6 Suggest next steps (contradicts steps 6.1-6.4)
- Repeated suppressed-comment reminders in step 2 intro, step 2.6 and step 4
