# design-review-standards

Verdict: **needs-work** · SKILL.md body 368 lines · description 984 chars

The description is precise and well disambiguated, and the ten dimensions with "Check for" and "Red flags" lists give a review a clear scope. The biggest gap is that the skill asks for a score from 1 to 5 and a ranked list of fixes, but it never gives a workflow, a scoring rubric or an output format for them. It spends about 40% of its body on material that repeats itself: a checklist template that restates the dimensions, an anti-pattern list that repeats the red flags, and accessibility snippets an Opus or Sonnet model already knows.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names the dimensions, WCAG AA, dark mode and contrast, and gives plain-language triggers. At 984 of 1,024 characters it has little room left. |
| Description includes both what the Skill does and when to use it | pass | "Review and score ... then rank fixes by impact. Use whenever a request judges how pages or screens look..." |
| SKILL.md body is under 500 lines | pass | 368 body lines. |
| Additional details are in separate files (if needed) | partial | No references/ folder. About 65 lines of accessibility TSX snippets and the e-commerce conversion section are inline, though they apply only some of the time. |
| No time-sensitive information | pass | Nothing is dated. "WCAG AA" names no version, though the 44px target is a WCAG 2.1 AAA / platform guideline value, not 2.2 AA. |
| Consistent terminology throughout | partial | Uses "design tokens", "CSS custom properties", "CSS variables" and "brand tokens" interchangeably. Font-count and body-size thresholds differ between sections. |
| Examples are concrete, not abstract | pass | Uses concrete px, ratio and ARIA examples, plus WRONG/RIGHT code pairs. |
| File references are one level deep | not-applicable | The skill has no reference files. |
| Progressive disclosure used appropriately | partial | Conditional content (e-commerce conversion, cart and 3D-viewer items, accessibility code library) always loads instead of sitting behind a conditional pointer. |
| Workflows have clear steps | fail | The only procedure is "Score each 1-5, prioritize fixes by impact." There are no steps for gathering evidence, no rubric and no ranked-fix output. |
| Validation/verification steps for critical operations | partial | Contrast pass/fail is the most error-prone judgment, but the skill has no step to measure it (tool or computed ratio) before reporting. |
| Feedback loops included for quality-critical tasks | fail | There is no re-check after fixes and no review-against-checklist loop before reporting. |
| No voodoo constants | partial | #CDCCCA on #171614, -0.01em, py-12 to py-20 and 200ms page transitions appear with no rationale or source. |
| No Windows-style paths | pass | No paths are used. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 5 positive and 3 negative trigger cases, but no behavior case with assertions, so the with-vs-without quality delta is never measured. |
| Avoid offering too many options | partial | Section 7 requires both "Bottom navigation bar on mobile" and "Navigation collapses to hamburger menu" with no default. |

## Findings

1. **high** · Use workflows for complex tasks / Implement feedback loops / Template pattern · SKILL.md, Review Framework (line 21) and Review Checklist Template (lines 290-361)
   > Evaluate every design review across these 10 dimensions. Score each 1-5, prioritize fixes by impact.

   Fix: Replace the one-line instruction with 4-5 numbered steps: render the pages at 375px and 1280px in light and dark; measure contrast with a tool rather than estimating it; score each dimension against a one-line rubric for 1, 3 and 5; list fixes ranked by impact × effort; re-check the fixed items. Replace the checkbox template with an output template that has a score row for each dimension and a ranked-fix table, because the current template has neither, though the description promises both.

2. **high** · Concise is key / Use consistent terminology (duplicated content) · SKILL.md, Review Checklist Template (lines 290-361) and Common Anti-Patterns (lines 363-372)
   > ### Typography
- [ ] Display vs body fonts properly applied ... 7. **Font soup**: 3+ font families, 4+ weights, no clear hierarchy.

   Fix: Delete the 70-line checkbox template, which restates the Check-for lists, and the anti-pattern list, which repeats the red flags (contrast, font soup, missing states, token usage, mobile afterthought). Keep only "The AI Aesthetic" and "Decoration over information", folding them into section 9 or the red-flag lists, since they are the only new content.

3. **medium** · Concise is key (Claude is already very smart) / Progressive disclosure Pattern 3 · SKILL.md, section 6 Implementation patterns (lines 139-203)
   > // WRONG — icon without label
<button><SearchIcon /></button>

   Fix: Move the five TSX snippets (semantic nav, aria-label, skip link, aria-live, aria-pressed) to references/accessibility-patterns.md, linked from section 6 with one line, or cut them; the Check-for bullets already name each pattern. Keep the sentence saying this skill is the canonical home for accessibility, because code-quality-standards links to section 6.

4. **medium** · Progressive disclosure Pattern 2 (domain-specific organization) / Concise is key · SKILL.md, sections 3, 6, 7, 8, 9, 10
   > Auto-rotate 3D models with pause on interaction
Brand palette defined in one place (globals.css @theme block)

   Fix: Remove the leftovers from a single project (3D viewer, `container-page` pattern, globals.css @theme, cart drawer, cart announcements, community storytelling), or generalise them, for example "announce async state changes". Move section 10 Conversion and the cart items to a conditional reference such as references/ecommerce-conversion.md, loaded only when the site sells something.

5. **medium** · Use consistent terminology / Avoid offering too many options · SKILL.md, section 1 (lines 28-38), section 7 (lines 210, 217), Anti-Patterns item 7
   > Maximum 2 fonts, 2-3 weights ... More than 3 font families ... Font soup: 3+ font families, 4+ weights

   Fix: Pick one threshold for each rule: fonts (2, with 3 as the red flag, or 3 everywhere), weights and body size (the check says 16px minimum, the red flag says below 14px). Choose one default mobile nav pattern with an escape hatch instead of requiring both a bottom bar and a hamburger menu. Use "design tokens" throughout instead of also writing "CSS variables", "CSS custom properties" and "brand tokens".

6. **low** · Solve, don't defer: voodoo constants (configuration values justified) · SKILL.md, sections 1, 3, 4, 7, 8
   > Pure white text on pure black (#FFFFFF on #000000) — too harsh. Use #CDCCCA on #171614

   Fix: Either justify or drop the prescriptive values (#CDCCCA/#171614, -0.01em, py-12 to py-20, 200ms page transitions). Label the 44x44px target with its source (WCAG 2.5.5 AAA / platform guidelines) and note that 2.2 AA requires 24x24px, since the section is titled WCAG AA.

7. **low** · Concise is key (when-to-use belongs in the description) · SKILL.md, When to Use This Skill (lines 8-17)
   > Use when:
- Conducting a design or UI/UX review of a web application

   Fix: Delete the section. The body is read only after the description has triggered the skill, and the description already covers these cases more precisely.

8. **low** · Build evaluations first / Testing: at least three evaluations · evals/shared-benchmark.json
   > "kind": "trigger" (all 8 cases); "assertions": []

   Fix: Add at least three behavior cases with assertions, for example "output scores all 10 dimensions", "flags the 3.2:1 grey-on-white body text as failing AA" and "fixes are ranked by impact". The with_skill vs without_skill delta that CONTRIBUTING relies on cannot show up with trigger cases alone.

## Strengths

- The description gives plain-language triggers ("looks cheap, dated, cluttered", "keyboard-only or screen-reader users", "after a theme or dark mode change") and a precise "Not for" clause naming three sibling skills.
- Each dimension has a uniform "Check for" / "Red flags" pair, which makes the review scope easy to scan and hard to skip.
- The trigger eval suite pairs five positive cases with three near-miss negatives that map one-to-one to the "Not for" clause, so the disambiguation can be tested.

## Cut candidates

- When to Use This Skill (repeats the description)
- Review Checklist Template (restates the ten Check-for lists, about 70 lines)
- Common Anti-Patterns items 3-8 (repeat the red flags)
- Section 6 Implementation patterns TSX snippets (move to references/ or cut; Opus knows aria-label, skip links and aria-live)
- Section 8 font-display/preload bullets (duplicate section 1)
- Section 10 Conversion Optimization (move to a conditional e-commerce reference)
