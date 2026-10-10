# code-quality-standards

Verdict: **needs-work** · SKILL.md body 471 lines · description 992 chars

The description is specific and well disambiguated, and the closing copyable review checklist is a good self-check. The main gap is that the 471-line body sits just under the 500-line limit and is mostly generic WRONG/RIGHT TypeScript examples that Opus or Sonnet already knows. Several of those examples are themselves wrong or tied to an old Next.js version, so the skill should become a short rules-and-checklist SKILL.md with any remaining examples moved to a references/ file.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names .ts/.tsx, API route, localStorage schema drift, memoization, unchecked casts, implicit any. |
| Description includes both what the Skill does and when to use it | pass | 'Apply React, Next.js, and TypeScript standards…' then 'Use when writing, fixing…' plus a Not-for clause. 992 chars leaves only 32 chars under the 1,024 limit. |
| SKILL.md body is under 500 lines | partial | 471 body lines: technically under the limit, but past the point where the guide says to split. |
| Additional details are in separate files (if needed) | fail | No references/ folder. About 330 lines of code examples are inline. |
| No time-sensitive information (or in an 'old patterns' section) | fail | The 'use client' and dynamic-import examples use pre-Next-15 APIs (synchronous params, ssr:false) and name no version. |
| Consistent terminology throughout | partial | Uses both 'sanitization' and 'validation' for the same checks. Calls the sections 'Review Categories' although the skill also covers writing code. |
| Examples are concrete, not abstract | partial | Examples are concrete, but some RIGHT examples are incorrect: a parenthesized directive, await in a non-async function, and an unchecked annotation on json(). |
| File references are one level deep | pass | All links go straight from SKILL.md to sibling skills. There are no nested reference files. |
| Progressive disclosure used appropriately | fail | Long code examples sit in SKILL.md, against the collection's own Progressive Disclosure rule (references/ carries code libraries and long worked examples). |
| Workflows have clear steps | partial | High-freedom 'apply only the relevant checks' suits a standards skill. The final checklist template is never tied to a step (when to copy it, and that it is checked before reporting done). |
| Validation/verification steps for critical operations | partial | The checklist works as a validator, but some of its items (data-testid, dangerouslySetInnerHTML, focus styles, naming) have no matching guidance in the body. |
| Feedback loops included for quality-critical tasks | partial | Has a checklist but no review, fix and re-check loop for security audits. |
| Scripts solve problems rather than defer to Claude | not-applicable | The skill has no scripts. |
| No 'voodoo constants' (all values justified) | partial | Example limits such as max = 100, length > 30, amount < 100 || > 10000000 and the deviceSizes list have no rationale, and models tend to copy them. |
| No Windows-style paths (all forward slashes) | pass |  |
| At least three evaluations created | partial | The suite has 8 trigger cases (5 positive, 3 negative) but no behavior or quality cases, so it cannot show whether the body improves output. |
| Tested with real usage scenarios | partial | Trigger prompts are realistic. No with_skill vs without_skill task cases measure the content. |

## Findings

1. **high** · Concise is key ('Default assumption: Claude is already very smart'); Progressive disclosure patterns · SKILL.md §2 DRY Principles (lines 137-233), §4 Performance (313-365), §1 Content Security (121-135)
   > // RIGHT — extract ShippingOption component
interface ShippingOptionProps {

   Fix: Replace the generic WRONG/RIGHT blocks with one-line rules: Component Extraction (39 lines), Shared Type Definitions, Extract Utility Functions (formatPrice), escapeXml, Image Optimization config, the basic useMemo/useCallback and fetch try/catch. For example: 'Extract JSX repeated across 2+ options into a component; export shared types and constants from one module.' Opus and Sonnet already know these patterns. (about 1500 tokens saved)

2. **high** · Examples pattern / Checklist: Examples are concrete, not abstract (examples must be correct, because Claude copies them) · SKILL.md §6 'use client' Discipline (lines 394-415) and §3 Type Safety (lines 239-252)
   > export default function ProductPage({ params }) {
  const product = await getCmsClient()… / ("use client");

   Fix: Fix or delete the example. It uses await inside a non-async function, and the Prettier-mangled `("use client");` is not a valid directive. Also change the Type Safety RIGHT case: `const data: ApiResponse = await response.json()` is an unchecked assertion that contradicts the skill's own validate-untrusted-input rule. Replace it with a runtime guard or schema parse. (about 150 tokens saved)

3. **medium** · Avoid time-sensitive information · SKILL.md §4 Dynamic Imports (lines 343-354) and §6 'use client' Discipline
   > const Scene = dynamic(() => import('./Scene').then(m => m.Scene), {
  ssr: false,

   Fix: State the rule without version-specific API: 'Lazy-load heavy client-only libraries behind a client boundary; mark only interactive leaves use client.' Alternatively, pin the examples to a named Next.js version. Next 15+ makes params a Promise and rejects ssr:false in Server Components. (about 120 tokens saved)

4. **medium** · Concise is key (body loads only after triggering; do not repeat the description) · SKILL.md 'When to Use This Skill' and 'Related Skills' (lines 17-32)
   > Use when:
- Implementing, fixing, refactoring, or reviewing React/Next.js/TypeScript code

   Fix: Delete both sections. The trigger list repeats the description, which has already fired by the time the body loads. 'Related Skills' repeats the code-authoring link from 'Apply in Context', and the review/pr-review pointer can join that paragraph as one clause. (about 160 tokens saved)

5. **medium** · Checklist: Validation/verification steps for critical operations; Consistent terminology · SKILL.md Code Review Checklist (lines 427-475) vs body
   > - [ ] No user content in dangerouslySetInnerHTML without escaping
- [ ] data-testid on interactive elements

   Fix: Make the checklist match the body. Drop items with no guidance in the body or owned by another skill (data-testid belongs to playwright-e2e; focus styles and aria items belong to design-review-standards, which §5 says owns accessibility). Either add a one-line rule for dangerouslySetInnerHTML or reword the item to match the escapeXml section. Also rename the 'String input sanitization' heading to 'validation' to match the checklist. (about 60 tokens saved)

6. **medium** · Progressive disclosure patterns (Pattern 1: high-level guide with references); collection README 'Progressive Disclosure' · SKILL.md whole body; skill folder has no references/
   > #### localStorage Validation … #### Regex Safety … #### API Route Hardening

   Fix: Keep in SKILL.md the non-obvious rules (localStorage triple: try/catch, size bound, per-item guard; anchored regex; validate route bodies; ?? not ||; stable keys), the Common Mistakes list and the checklist. Move any code examples worth keeping to references/examples.md and link it once. (about 800 tokens saved)

7. **low** · Use workflows for complex tasks / Implement feedback loops · SKILL.md 'Apply in Context' and 'Code Review Checklist'
   > Apply only the relevant checks below.

   Fix: Add one sentence tying the checklist to the procedure: 'For an audit or review, copy the checklist and report each failed item with file:line; when writing, re-check changed code against the relevant sections before reporting done.'

8. **low** · Build evaluations first (evaluation scenarios test behaviour, not just triggering) · evals/shared-benchmark.json
   > "kind": "trigger" (all 8 cases)

   Fix: Add at least three task cases with expected_behavior assertions, such as a localStorage reader with no size bound or type guard, an unanchored validation regex, and an `as any` cast. With these, the with_skill vs without_skill delta can show whether the body is worth its tokens before and after the cuts above.

## Strengths

- The description pairs concrete trigger phrasings (drifted localStorage schema, unchecked casts, needless re-renders) with a Not-for clause naming the sibling skills. The eval suite's negative trigger cases check exactly those boundaries.
- 'Apply in Context' gives project conventions precedence and warns against copying sample helpers, so it limits the over-application that example-heavy standards skills usually cause.
- The localStorage section reduces a fragile pattern to three mandatory elements (try/catch, size bound, per-item guard). This is the kind of short, non-obvious rule the rest of the skill should be cut down to.

## Cut candidates

- When to Use This Skill
- Related Skills
- Component Extraction
- Shared Type Definitions
- Extract Utility Functions
- Content Security (escapeXml)
- Image Optimization
- Error Handling
- React Memoization
- Ambiguous Character Avoidance
- File Structure Convention
