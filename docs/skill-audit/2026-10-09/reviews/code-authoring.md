# code-authoring

Verdict: **needs-work** · SKILL.md body 229 lines · description 691 chars

The skill is compact and well structured. Its five-step loop includes a feedback loop that a reviewer can check: each guard must fail without the change and pass with it, and both results are reported. Its description is specific, carries real trigger terms and ends with near-miss exclusions. The biggest gap is that the body's "When to Use" list and intro still claim spec/plan execution. That contradicts the description's "Not for executing a numbered spec's plan (implement)" and the suite's own neg-trig-numbered-spec case. Around it are smaller redundancies: the self-review steps repeat the review skill, delegation and dependency rules appear twice, and several generic coding rules Claude already follows could go.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names concrete triggers (cleanup or retention step added to a cron job, boundary error, terse one-line fixes) and adjacent-skill exclusions. |
| Description includes both what the Skill does and when to use it | pass | "Write or change code to project conventions..." followed by "Use for any request to edit code..." and a load-first instruction; 691 characters, under the 1,024 limit. |
| SKILL.md body is under 500 lines | pass | 229 body lines excluding frontmatter. |
| Additional details are in separate files (if needed) | pass | No references/ folder. At 229 lines the standards fit inline, and the review and pr-review skills link to the Coding Standards section rather than copying it. |
| No time-sensitive information (or in an "old patterns" section) | pass |  |
| Consistent terminology throughout | partial | The body says the skill executes plan.md, but the description sends numbered-spec execution to implement. "Self-Review" (step 4) and the suggested `/review` "independent quality pass" overlap. "standards", "personal standards" and "Coding Standards" are used for the same thing. |
| Examples are concrete, not abstract | pass | The Logging section gives concrete .NET and JS idioms; the Test step names concrete proof methods (revert or plant a mutant). |
| File references are one level deep | pass | The only links are to sibling SKILL.md files and ../skill-authoring/references/agent-model-selection.md (70 lines, linked directly). |
| Progressive disclosure used appropriately | pass | Stack-specific detail is delegated to code-quality-standards and the review procedure to the review skill. |
| Workflows have clear steps | pass | Prepare → Implement → Test → Self-Review → Validate, repeated per phase. |
| Validation/verification steps for critical operations | pass | Step 3 requires a without/with proof for every guard and fix; step 5 runs lint, typecheck and IDE diagnostics. |
| Feedback loops included for quality-critical tasks | pass | "Run the existing test suite; fix any regressions before proceeding"; "resolve all errors/warnings introduced by the change". |
| No Windows-style paths (all forward slashes) | pass |  |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. |
| No "voodoo constants" (all values justified) | not-applicable | No scripts. The prose thresholds (more than 3 parameters, extract at the 3rd duplicate) are stated as preferences. |
| Scripts have clear documentation | not-applicable |  |
| Required packages listed in instructions and verified as available | not-applicable |  |
| MCP tool references use fully qualified names | partial | "Subagent with `docs-context7` / web tools" is neither a fully qualified tool name nor in the collection's capability-name style ("Context7 docs"). |
| Avoid offering too many options | partial | Validate lists `npm run lint`, `npx tsc --noEmit`, `dotnet format --verify-no-changes`, etc. without making the project's own documented commands the default. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 cases, but all are trigger cases with empty assertions. No case measures the body's with-versus-without effect. |

## Findings

1. **high** · Writing effective descriptions / Consistent terminology (checklist: Consistent terminology throughout) · SKILL.md, intro line 8 and "When to Use" (lines 10-15)
   > - A `specs/{NNN-slug}/plan.md` exists and needs to be executed
- A spec from `/spec` is ready to be built

   Fix: Delete the "When to Use" list and reword line 8 so it no longer says "from spec/plan". The body loads only after triggering, and these bullets contradict the description's "Not for executing a numbered spec's plan (implement)" and the neg-trig-numbered-spec eval. Keep the small-change paragraph and one line saying that implement calls this skill per phase. (about 110 tokens saved)

2. **medium** · Concise is key / Progressive disclosure (one home per rule) · SKILL.md, "### 4. Self-Review" (lines 68-77)
   > - Confirm DRY: no duplicated logic that an existing utility would have served
- Verify no `any`, non-null assertions, or unsafe casts were introduced

   Fix: Keep "Load review and apply it to the final diff" plus the phase-checklist and dead-code bullets. Cut the DRY, `any`/cast and narrating-comment bullets: the review skill's DRY/Clean row and comment rules, and code-quality-standards' `any` checklist, already cover them, and the narrating-comment rule also repeats Comments & Documentation. (about 90 tokens saved)

3. **medium** · MCP tool references / Avoid offering too many options / Concise is key · SKILL.md, "## Subagent Delegation (Optional)" (lines 87-106) and lines 46-47
   > | Codebase pattern discovery      | `Explore` agent, "find all usages of X with thoroughness medium" |
| Standalone documentation lookup | Subagent with `docs-context7` / web tools                        |

   Fix: Replace the five-row table with three lines: fan out read-only work, delegate writes only over disjoint file sets, and apply agent-model-selection first. Merge in the duplicate model-selection note from lines 46-47. That note warns that `Explore` is not a cheap default, yet the table recommends `Explore` twice. The table also names `docs-context7` as a literal tool id, which the collection's capability-naming rule avoids. (about 200 tokens saved)

4. **medium** · Concise is key ("Default assumption: Claude is already very smart") · SKILL.md, Coding Standards: Naming & Readability, Data & Types, Control Flow & Iteration, Classes vs Functions, Version Control (lines 121-211)
   > - Template literals for string interpolation
- Functional methods (`map`, `filter`, `reduce`) for transformations

   Fix: Cut bullets that restate default behaviour for Opus and Sonnet: template literals, short iterator names, grouping lines with blank lines, map/filter/reduce versus loops, async/await, optional chaining, annotating signatures, classes for stateful things, and feature-complete commits. Keep the real preferences: braces only on guards, interface versus type, extract at the 3rd duplicate, options objects over 3 params, the fail-closed validator rule and the state-by-event table. (about 180 tokens saved)

5. **low** · Consistent terminology / Workflows have clear steps · SKILL.md, "## Output" (lines 230-233)
   > - `/review` for an independent quality pass

   Fix: Drop the `/review` suggestion, or limit it to an independent reviewer for high-risk changes. Step 4 already loads review and says "do not defer self-review to an optional follow-up command", so suggesting review again as an optional next step contradicts it. (about 15 tokens saved)

6. **low** · Concise is key (duplicate instructions) · SKILL.md, "## Context Sources" (lines 26-30) and "## Boundaries" (lines 213-219)
   > - ✅ Use CLI for dependency operations
- 🚫 Never skip the Test or Validate steps

   Fix: Delete Context Sources, since Project Conventions First already states the precedence order. Delete the Boundaries lines that repeat step 2 (CLI for packages) or are implied by the protocol (implement directly, run tests). Keep only the ask-first and protected-branch lines. (about 110 tokens saved)

7. **low** · Avoid offering too many options (default with an escape hatch) · SKILL.md, "### 5. Validate" (line 81)
   > - Run linters and type-checks: `npm run lint`, `npx tsc --noEmit`, `dotnet format --verify-no-changes`, etc.

   Fix: Say: "Run the lint, typecheck and format commands the project documents (AGENTS.md, package scripts, CI)". Drop the ecosystem sample list, which Claude does not need and which can conflict with a project's own command contract. (about 20 tokens saved)

8. **low** · Build evaluations first (checklist: At least three evaluations created; Tested with real usage scenarios) · evals/shared-benchmark.json
   > "kind": "trigger", ... "assertions": []

   Fix: Add three behaviour cases, each with a fixture under evals/fixtures/ and assertions tied to rules a model without the skill plausibly breaks. Good candidates: reporting the without/with result for a new guard, running the package CLI instead of hand-editing a lockfile, and comments that explain why rather than narrate. Without them the paired delta that justifies the body's tokens cannot be measured.

## Strengths

- Step 3 turns a vague 'add tests' into a check others can verify: a new guard or fix must fail without the change ('revert it or plant a mutant') and pass with it, and the Output section requires reporting both results.
- The description names concrete, plainly worded triggers ('terse one-line fixes with no spec', a cleanup step added to a cron job), says to load the skill before searching for files, and backs its 'Not for' clause with near-miss negative trigger evals.
- The Coding Standards are kept in one place: review, pr-review, code-quality-standards and spec all link to this section instead of copying it, which follows the skill's own 'One home per rationale' rule.

## Cut candidates

- When to Use (body list duplicating and contradicting the description)
- Context Sources (priority order) — duplicates Project Conventions First
- Subagent Delegation (Optional) table — Explore/docs-context7 rows
- Self-Review bullets on DRY, any/non-null casts and narrating comments — covered by review and code-quality-standards
- Naming & Readability — template literals, short iterator names, grouping lines
- Control Flow & Iteration
- Classes vs Functions
- Version Control
- Boundaries ✅ lines (implement directly; use CLI for dependency operations)
- Validate — sample command list for npm/tsc/dotnet
