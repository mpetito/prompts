# review

Verdict: **needs-work** · SKILL.md body 233 lines · description 777 chars

The skill has a strong, low-freedom core: a clear Protocol, a diff-to-proof table, and a fixed delegated report template, with the mutation and flake procedures split into a single reference file under 100 lines. Its biggest gap is inconsistent terminology. There are two severity vocabularies, two verdict vocabularies and two different test-gap severity rules, and the eval expects a "Should fix" section that the template does not contain. On top of that, about a fifth of the body repeats the description or gives generic advice an Opus or Sonnet model doesn't need.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | 777 chars; names diff, staged changes, merge verdict, mutation-testing and delegated reviewer, and ends with the collection's Not-for clause. |
| Description includes both what the Skill does and when to use it | pass | Opens with what it does (review, prove, report, verdict), then gives a 'Use when' list and a load-timing cue. |
| SKILL.md body is under 500 lines | pass | 233 body lines. |
| Additional details are in separate files (if needed) | pass | Probe procedures and the mutant table format are in references/adversarial-probes.md. |
| No time-sensitive information (or in an 'old patterns' section) | partial | Protocol step 5 cites one build's counts ('about 1,100 findings', '3 times in 175 reviews'), which will go stale and are anecdote rather than instruction. |
| Consistent terminology throughout | fail | Severity is Critical/Important/Suggestion in one place and blocking/follow-up/nit in another. Verdicts are APPROVE/REQUEST CHANGES/NEEDS DISCUSSION in one place and approve/changes-required/close in another. The test-gap rule includes 'data integrity' in one mode and omits it in the other. The eval expects 'Should fix'. |
| Examples are concrete, not abstract | pass | Mutant table rows, a filled delegated report skeleton and the flaky-run sizing example (5% flake needs about 60 runs) are concrete. |
| File references are one level deep | pass | SKILL.md links adversarial-probes.md directly, and that file links only back to SKILL.md. The cross-skill links follow the collection's convention. |
| Progressive disclosure used appropriately | pass | The diff-to-proof table stays in SKILL.md and the detailed procedures load on demand. |
| Workflows have clear steps | pass | The Protocol has 7 numbered steps; In-Review Change Requests is a 3-branch decision tree. |
| Validation/verification steps for critical operations | pass | Prove the Change Can Fail requires mutants, restoring the bug and comparing test counts, and checks the author's own evidence. |
| Feedback loops included for quality-critical tasks | pass | A surviving mutant becomes a finding with a killing assertion; a suggested fix is validated before it is reported; a wrong finding is withdrawn in the next round. |
| No Windows-style paths (all forward slashes) | pass | Every path uses forward slashes. |
| Avoid assuming tools are installed / MCP tool references | partial | Relies on VS Code chat variables (#changes, #activePullRequest, #openPullRequest, #problems) that other hosts lack, against the README rule to describe tools as capabilities. |
| Scripts solve problems rather than defer to Claude | not-applicable | The skill bundles no scripts. It calls ../pr-scripts/Get-PrThreads.ps1, which is a shared helper. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 2 behavioural cases (interactive, delegated) and 6 trigger cases. Best practice asks for three scenarios, and no case exercises In-Review Change Requests or the no-behavior-change proof. |
| Tested with real usage scenarios | pass | The fixtures are realistic: SQL injection with a skipped test, and a flaky-fix PR on a moved base with an inflated claim. |

## Findings

1. **high** · Use consistent terminology · SKILL.md Protocol step 5 vs Delegated Report-Only Mode; evals/shared-benchmark.json pos-delegated-flaky-fix
   > "A missing or weak test is Important unless it guards a safety invariant, an auth boundary or data integrity" vs "A test gap is `follow-up` unless it guards a safety invariant or an auth boundary."

   Fix: Keep one severity scale and map it once, for example 'Critical = blocking, Important = follow-up, Suggestion = nit'. Then state the test-gap rule once, with data integrity in both modes. Change the eval's expected_behavior 'Should fix' to 'Follow-up' so it matches the template. (about 30 tokens saved)

2. **medium** · Use consistent terminology · SKILL.md Output Format vs Prove the Change Can Fail vs Delegated template
   > "**Overall Assessment**: APPROVE / REQUEST CHANGES / NEEDS DISCUSSION" vs "VERDICT: approve | changes-required | close"; ""Close, don't merge" is a valid verdict"

   Fix: Use one verdict set in both templates (approve, changes-required, close, needs-discussion), so the close verdict endorsed under Prove the Change Can Fail is available in interactive reviews too.

3. **medium** · Concise is key (Default assumption: Claude is already very smart) · SKILL.md title paragraph and When to Use (lines 6-21)
   > "Procedural knowledge for performing structured, multi-dimensional code reviews on a diff or pull request." / "- A user asks to review changes, a PR, or a diff"

   Fix: Delete the intro sentence and the When to Use bullets, which repeat the description that has already triggered the skill. Keep only the 'Scale review depth to the risk' sentence and the pointer to Delegated Report-Only Mode. The pr-review/pr-feedback routing is already in the description's Not-for clause. (about 170 tokens saved)

4. **medium** · Concise is key; Avoid time-sensitive information · SKILL.md Protocol step 5 (lines 79-83)
   > "In one build a quarter of about 1,100 findings were missing-mutant tests ... reviewers raised it 3 times in 175 reviews while the owner raised it on most status calls."

   Fix: Cut the statistics and keep the two rules: a weak-test severity rule and 'Over-engineering is a finding at the severity of the maintenance cost it adds, never a style note.' The counts are rationale from one build and will go stale. (about 70 tokens saved)

5. **medium** · Concise is key (remove explanations Claude does not need) · SKILL.md Guidelines and Coding Standards (verify against)
   > "- Be constructive, not critical
- Explain **why** something is an issue"

   Fix: Delete Guidelines. Its points are generic reviewer etiquette already covered by Coding Standards ('Require a concrete code path ... not a preference'). Merge the one useful line, 'Do not nitpick style if it matches the surrounding codebase', into Coding Standards, which already repeats 'Apply the canonical standards linked above' from Review Scope. (about 90 tokens saved)

6. **low** · Concise is key / Use consistent terminology (one statement per rule) · SKILL.md Protocol step 7, Delegated Report-Only Mode, Boundaries
   > "🚫 Delegated mode: never edit the change, post, or start subagents" (already stated as "Do not post, push, commit, reply to or resolve threads, or start subagents.")

   Fix: Make Boundaries cover interactive mode only, or drop it. The fix-minor-items rule appears three times, and the delegated no-edit, no-post and no-subagent rules appear twice. Keep each rule in one place. (about 80 tokens saved)

7. **low** · MCP tool references / Avoid assuming tools are installed (collection Cross-Tool Authoring Notes: describe tools as capabilities) · SKILL.md Review Scope, PR Context Check, Boundaries
   > "Use `#activePullRequest` / `#openPullRequest` to identify if changes belong to a PR"

   Fix: Describe the capabilities instead, for example 'the host's changed-files or active-PR context, otherwise `gh pr view` / `git diff`' and 'IDE diagnostics'. The VS Code `#` variables do not exist in Claude Code or Codex. Also drop PR Context Check step 3, which only repeats the pr-feedback/pr-resolve routing. (about 40 tokens saved)

8. **low** · Build evaluations first (at least three evaluations) · evals/shared-benchmark.json
   > "id": "pos-interactive-discount-review" ... "id": "pos-delegated-flaky-fix" (the only two non-trigger cases)

   Fix: Add a third behavioural case for the riskiest branch the current cases skip. Either a mid-review request for a non-trivial change, which must deliberate rather than implement, or a 'no behavior change' refactor, which must demand a mechanical identity proof.

## Strengths

- The 'Prove the Change Can Fail' table maps each kind of diff to the proof it requires. It gives low freedom exactly where the work is fragile and keeps the procedures in a single reference file under 100 lines.
- The delegated report is a strict text template with a 40-line cap, IDs, a verdict bound to the head SHA and a 'Not verified' line. It also sends the long form to a file, which keeps the caller's context small.
- The evals test rules a model would otherwise break: a brief that pressures it to lower severity by round number, CI evidence from a base that has since moved, and a 'no line numbers' assertion for interactive mode.

## Cut candidates

- Code Review Skill (intro sentence)
- When to Use (repeats the description and the Not-for routing)
- Protocol step 5 statistics paragraph (the 1,100-findings and 175-reviews anecdote)
- Guidelines (generic reviewer etiquette)
- Coding Standards (verify against) first sentence (repeats the Review Scope pointer to code-authoring)
- Boundaries (repeats Protocol step 7 and the Delegated Report-Only Mode prohibitions)
- PR Context Check step 3 (repeats the pr-feedback/pr-resolve routing)
