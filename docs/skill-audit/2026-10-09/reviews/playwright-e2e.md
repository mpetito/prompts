# playwright-e2e

Verdict: **needs-work** · SKILL.md body 483 lines · description 423 chars

The skill's distinctive value is real and well organised: a single-level reference, references/stability.md, holds a numbered flake-triage workflow, a concrete stability-gate command and non-obvious pitfalls such as vacuous absence checks and secrets in traces. The most important gap is that SKILL.md spends about 480 lines, close to the 500-line ceiling, on storefront boilerplate that Opus and Sonnet already know (three full POM classes, five generic test examples and a "When to Use" list that repeats the description), while the description never says what the skill does and drops the collection's "Not for …" clause.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names POM, locators, data-testid, npm-workspaces, test.fixme, flaky/CI-only, quarantine, rollback smoke tests. |
| Description includes both what the Skill does and when to use it | partial | All 'Use when…'; no leading statement of what the skill provides, and no 'Not for …' disambiguation although evals test negatives against design-review-standards, ecommerce-patterns and code-authoring. |
| SKILL.md body is under 500 lines | partial | 483 body lines: technically under, but at the 'approaching the limit' point where the doc says to split. |
| Additional details are in separate files (if needed) | partial | Stability material is split out well; worked storefront code that should be cut or moved stays inline. |
| No time-sensitive information (or in an 'old patterns' section) | fail | Pins @playwright/test ^1.50.0, node-version: 20 and actions/*@v4 in SKILL.md while stability.md cites Playwright 1.63. |
| Consistent terminology throughout | fail | The data-testid convention says {action}-{target} (button-submit), but every example uses {area}-{target}-{action} (hero-shop-button, customizer-add-to-cart, cart-item-increase). |
| Examples are concrete, not abstract | pass | Concrete, though too many. |
| File references are one level deep | pass | SKILL.md links only references/stability.md; stability.md links back and to sibling skills (collection convention), not to further in-skill files. |
| Progressive disclosure used appropriately | partial | Good routing to stability.md anchors; but the stack-specific setup and long worked examples are the bulk of SKILL.md. |
| Workflows have clear steps | pass | Flake Triage is an 8-step ordered workflow; stability gate gives an exact command. |
| Structure longer reference files with a table of contents | partial | stability.md is 171 lines; its opening sentence lists the topics in prose but there is no linked contents list. |
| Validation/verification steps for critical operations | pass | Stability gate, planted-marker secret scan, activation audit for un-fixme, N-run restore rule. |
| Feedback loops included for quality-critical tasks | pass | Quarantine and restore loop, forced-on pass, control PR. |
| Avoid offering too many options | pass | Selector priority gives one ordered default. |
| No Windows-style paths | pass |  |
| Scripts solve problems rather than defer / scripts documented / no voodoo constants | not-applicable | No scripts/ folder. Config constants (retries 2, workers 1) are justified inline. |
| Required packages listed and verified as available | partial | CI installs chromium only; stability.md requires 'Every project, WebKit and phone profiles included' but neither the config nor the install step covers WebKit. |
| At least three evaluations created | partial | 8 trigger cases (5 positive, 3 negative) in evals/shared-benchmark.json, but no behaviour case with assertions, so no eval exercises the skill's non-obvious rules. |
| Tested with real usage scenarios | partial | Trigger prompts are realistic; output quality untested. |

## Findings

1. **high** · Concise is key ('Default assumption: Claude is already very smart'); Progressive disclosure (split when approaching 500 lines) · SKILL.md, Test Authoring > Page Object Model (POM) Pattern, lines 154-307
   > **Cart POM (complex interactions):** ... **Application-specific interactive flow POM (example product customizer):**

   Fix: Keep one short POM (HomePage, trimmed to two locators and one action) to show the testid-in-constructor convention, and delete CartPage and ProductCustomizerPage. Opus and Sonnet write standard POM classes unaided. If later examples still need CartPage, list only its locator names. (about 900 tokens saved)

2. **high** · Concise is key; Examples pattern (examples only where output quality depends on them) · SKILL.md, Test Patterns (lines 309-386) and Persisted-State Test (lines 426-445)
   > **Form validation test:** ... **Error clearing test:** ... // Reload the page

   Fix: Cut the multi-step, form-validation, error-clearing and persisted-state examples, which are generic Playwright usage. Keep the beforeEach localStorage-clear block as the single isolation pattern and fold the helper into it. Delete the narrating comments. (about 650 tokens saved)

3. **medium** · Writing effective descriptions (what it does AND when to use it); checklist 'Description includes both what the Skill does and when to use it' · SKILL.md frontmatter description
   > Use when writing Playwright end-to-end tests, applying the Page Object Model, choosing
  locators, ...

   Fix: Open with one clause saying what the skill does, for example 'Write and stabilise Playwright end-to-end suites: POM, locators, data-testid convention, monorepo and CI wiring, flake triage and quarantine.' Add the collection's closing clause, 'Not for unit tests (code-authoring), accessibility or UI audits (design-review-standards), or building cart/checkout features (ecommerce-patterns)', which matches the three negative eval cases.

4. **medium** · Concise is key (body loads only after triggering, so trigger lists there are dead weight) · SKILL.md, When to Use This Skill, lines 13-31
   > ## When to Use This Skill

Use when:

   Fix: Delete the 10-bullet list, which repeats the description. Replace it with a two-line router: 'Setup: Monorepo Wiring. Writing tests: Test Authoring. Flakes, quarantine, test.fixme, rollback smoke tests, CI artifacts, secrets, shared hosts: references/stability.md.' Also drop the duplicate 'The rest of this skill is stack-agnostic.' at line 152. (about 220 tokens saved)

5. **medium** · Use consistent terminology · SKILL.md, data-testid Convention, lines 388-404, against the POM examples
   > Interactive elements: {action}-{target}
  button-submit, input-email, link-profile, header-cart-button

   Fix: Pick one pattern and make every example follow it. The skill's own testids (hero-shop-button, customizer-add-to-cart, cart-item-increase) follow {area}-{target}[-{action}], while 'button-submit' is {type}-{target}, so neither matches the stated {action}-{target}. Rewrite the rule as '{area}-{element}[-{action}]' and fix the listed examples.

6. **medium** · Avoid time-sensitive information; consistent terminology · SKILL.md, Package Configuration (line 80) and CI Configuration (lines 458-461); references/stability.md line 10
   > "@playwright/test": "^1.50.0" ... node-version: 20

   Fix: Drop the pinned versions from the examples, or state one version consistent with stability.md's 'Playwright 1.63' baseline. Node 20 is past end of life as of this review; use the project's Node or `node-version-file`. Replace the generic package.json scripts block with the two root workspace scripts, which carry the monorepo-specific content. (about 120 tokens saved)

7. **low** · Concise is key (no duplication between sections) · SKILL.md, Common Pitfalls items 1, 3, 7, 8 against Key configuration points (lines 139-148)
   > 7. **CI memory**: Use `workers: 1` in CI to prevent OOM. ... `workers: 1` in CI — prevent resource contention

   Fix: Pitfalls 1 (cwd), 7 (workers) and 8 (reuseExistingServer/E2E_PORT) repeat the key-config bullets, so merge each into its config bullet. Drop 3 (auto-wait, which the model knows) and the storefront-specific 5 (cart drawer timing). Keep 9-11, which carry the non-obvious content, at the top of the list. (about 200 tokens saved)

8. **low** · Structure longer reference files with a table of contents; Build evaluations first · references/stability.md lines 3-5; evals/shared-benchmark.json
   > Load this from [playwright-e2e](../SKILL.md) when a suite must stay trustworthy as it grows:
CI artifacts, the stability gate for new tests, flake triage, ...

   Fix: stability.md is 171 lines: turn the prose topic list into a linked contents list of its seven ## anchors. Separately, add two or three behaviour cases with assertions to the eval suite, for example vacuous toBeHidden after a testid rename, trace mode for a CI-only flake, and the stability gate before a PR, because all eight current cases are trigger-only.

## Strengths

- Puts the advanced material in one reference file and links to it from SKILL.md with anchors pointing at the exact sections (references/stability.md#flake-triage, #secrets-in-artifacts), so a partial read lands on the right section.
- Flake Triage is an ordered, falsifiable workflow: a control PR, a no-feature control, N sized from the failure rate, a time-boxed quarantine with a restore rule, and 'Not reproduced, no fix claimed' accepted as an outcome. Fragile work gets low freedom.
- Separates documented Playwright behaviour from behaviour observed in one version ('observed in 1.63; the docs don't say'), so claims stay tied to their evidence.

## Cut candidates

- When to Use This Skill (duplicates the description)
- Page Object Model (POM) Pattern: CartPage and ProductCustomizerPage classes
- Test Patterns: Multi-step flow test, Form validation test, Error clearing test
- Persisted-State Test (localStorage)
- Package Configuration: the e2e package.json scripts block (test:ui, test:headed, test:debug)
- Project Structure: the enumerated six POM files and seven spec files
- Common Pitfalls 3 (Flaky waits / auto-wait) and 5 (Cart drawer timing)
- Common Pitfalls 1, 7 and 8, which repeat Key configuration points
