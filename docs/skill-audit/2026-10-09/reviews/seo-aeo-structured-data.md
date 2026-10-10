# seo-aeo-structured-data

Verdict: **needs-work** · SKILL.md body 93 lines · description 981 chars

The skill is lean and uses progressive disclosure well. SKILL.md has a clear architecture, a build order and decisions, and the code lives in two reference files that SKILL.md links directly. The biggest gap is outdated content: the description and the HowTo/FAQ material still promise Google rich results that Google limited and then deprecated in Aug/Sep 2023 (HowTo removed; FAQ only for authoritative government and health sites). There is also no step that validates the generated structured data.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names Open Graph, JSON-LD, FAQPage, sitemap.xml, robots.txt, RSS, and plain-language triggers such as a link that unfurls with no image. At 981 chars it is close to the 1,024 limit. |
| Description includes both what the Skill does and when to use it | pass | What: 'Make a React or Next.js site show up well...'; when: 'Use whenever a request is about how pages appear, rank, or get quoted'. Ends with the collection's 'Not for' clause. |
| SKILL.md body is under 500 lines | pass | 93 body lines. |
| Additional details are in separate files (if needed) | pass | All code is in references/json-ld-generators.md and references/metadata-sitemap-rss.md. |
| No time-sensitive information (or in an "old patterns" section) | fail | Presents HowTo and FAQ rich results as current. Google stopped showing HowTo rich results in Sept 2023 and limited FAQ rich results to authoritative government/health sites in Aug 2023 (developers.google.com/search/blog/2023/08/howto-faq-changes). |
| Consistent terminology throughout | partial | Uses 'AI crawlers', 'AI bots', 'AI answer engines' and 'AI assistants' for the same thing. The description says 'React or Next.js', but every pattern is Next.js App Router only. |
| Examples are concrete, not abstract | pass | Complete TypeScript generators and route files. |
| File references are one level deep | partial | Both references are linked from SKILL.md. But metadata-sitemap-rss.md sends Claude to ../../ecommerce-patterns/references/orders-giftcards-analytics.md for reportWebVitals, a second hop. |
| Progressive disclosure used appropriately | pass | SKILL.md has the decisions and pitfalls; the references have the code. A table says what each reference contains. |
| Workflows have clear steps | pass | Five-step Build Order. |
| Structure longer reference files with a table of contents | fail | json-ld-generators.md (337 lines) and metadata-sitemap-rss.md (328 lines) have no TOC. |
| Validation/verification steps for critical operations | fail | Nothing tells Claude to check the JSON-LD with the Rich Results Test or Schema Markup Validator. Nothing checks that the FAQ JSON-LD text matches the visible text, though pitfall 1 says a mismatch can be penalized. |
| Feedback loops included for quality-critical tasks | fail | No validate-fix-repeat loop for structured data, the sitemap or the RSS feed. |
| No "voodoo constants" (all values justified) | partial | Hard-coded store-policy values in the reference code: shipping '5.99', handling 1-3 days, transit 3-7 days, merchantReturnDays 30. The sitemap uses `limit: 1000`, which silently drops products past 1,000 and contradicts pitfall 5. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts/ folder. |
| Scripts have clear documentation | not-applicable | No scripts. |
| Required packages listed in instructions and verified as available | not-applicable | Uses only next built-ins. |
| No Windows-style paths (all forward slashes) | pass |  |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 negative), all with empty assertions. No case checks the quality of the output. |
| Tested with real usage scenarios | partial | Trigger prompts are realistic. No with/without-skill behaviour case, for example checking that FAQ JSON-LD matches the visible text or that prices are emitted as dollars. |

## Findings

1. **high** · Avoid time-sensitive information / Checklist: No time-sensitive information · SKILL.md frontmatter description; references/json-ld-generators.md 'HowTo (for configurators/tutorials)' and 'FAQPage (critical for AEO)'
   > earn rich results such as review stars, price, or FAQ answers in Google listings
## FAQPage (critical for AEO)

   Fix: Remove 'FAQ answers' from the description's rich-results example. Put HowTo and the FAQ-rich-result claims in a collapsed 'Old patterns' block saying that Google removed HowTo rich results in Sept 2023 and limited FAQ rich results to authoritative government/health sites in Aug 2023. Keep FAQPage only as optional AEO markup, not a way to get rich results. (about 150 tokens saved)

2. **medium** · Implement feedback loops / Checklist: Validation/verification steps for critical operations · SKILL.md 'Build Order'
   > 5. **RSS + analytics/Web Vitals** last.

   Fix: Add a final step: check each page's JSON-LD with Google's Rich Results Test or the Schema Markup Validator, fix the errors, and repeat until it passes. Also confirm the FAQ JSON-LD text equals the rendered text and that /feed.xml and /sitemap.xml parse.

3. **medium** · Concise is key (repetition between sections) · SKILL.md 'Key Decisions' (lines 62-86) vs 'Common Pitfalls' (lines 88-97)
   > **Prices are cents internally, dollars in schema.org.** ...
3. **Price format in JSON-LD**: use dollars with 2 decimal places (`"24.99"`), not cents.

   Fix: Merge the two sections into one list. FAQ mismatch, price format, robots.txt AI bots and Speakable selectors each appear in both. Keep pitfalls only for canonicals, dynamic sitemap, OG image and escapeXml. Also delete the repeats in json-ld-generators.md: the 'Note the units' paragraph, the speakable selector advice, and the 'Why dual rendering' paragraph. (about 220 tokens saved)

4. **medium** · Concise is key / Writing effective descriptions (body 'when to use' duplicates metadata) · SKILL.md 'When to Use This Skill' (lines 8-17)
   > ## When to Use This Skill

Use when:

   Fix: Delete the section. The body loads only after the description has already triggered, so this list adds nothing. It also lists 'Monitoring Core Web Vitals', which the description does not claim and which the skill hands to ecommerce-patterns. (about 80 tokens saved)

5. **medium** · Avoid deeply nested references / Checklist: File references are one level deep · references/metadata-sitemap-rss.md 'Analytics Provider Wiring'; SKILL.md Architecture tree and 'One analytics pipeline'
   > `reportWebVitals` itself is defined in the `ecommerce-patterns` skill —
[`references/orders-giftcards-analytics.md`](../../ecommerce-patterns/references/orders-giftcards-analytics.md).

   Fix: Analytics is not SEO and is not in the description. Remove the Analytics Provider Wiring section, the analytics.ts/web-vitals.ts/AnalyticsProvider entries in the Architecture tree, and Build Order step 5's analytics part. Replace them with one line in SKILL.md: '...see ../ecommerce-patterns/SKILL.md for analytics and Web Vitals'. Claude then never follows a reference-to-reference link. (about 120 tokens saved)

6. **low** · Structure longer reference files with a table of contents · references/json-ld-generators.md (337 lines); references/metadata-sitemap-rss.md (328 lines)
   > # JSON-LD Generators and Components

Generator functions for `lib/structured-data.ts` and the components that render them.

   Fix: Add a short contents list under each H1 naming its sections, so a partial read still shows the full scope. For example: Renderer, Organization, Product, FAQPage, BreadcrumbList, HowTo (legacy), Speakable, FAQ component, Page usage.

7. **low** · No "voodoo constants" (all values justified) · references/json-ld-generators.md 'Product'; references/metadata-sitemap-rss.md 'Dynamic XML Sitemap'
   > const products = await cms.find({ collection: "products", limit: 1000 });
value: "5.99",

   Fix: Make shipping rate, handling/transit days and return days parameters of productJsonLd, or mark them as placeholders for store policy. Page the CMS query, or note the 50,000-URL sitemap limit, instead of truncating silently at 1,000. As written it contradicts the skill's own 'Sitemap without dynamic pages' pitfall.

8. **low** · Use consistent terminology · SKILL.md description, 'Key Decisions', 'Common Pitfalls'
   > Explicitly allow AI crawlers if you want AEO.
4. **robots.txt blocking AI bots**

   Fix: Pick one term, 'AI crawlers', for the user agents and keep 'AI answer engines' for the products. Change the description's 'React or Next.js' to 'Next.js (App Router)', because every pattern depends on the Next.js Metadata API and metadata routes. (about 5 tokens saved)

## Strengths

- SKILL.md is a 93-line overview. It has a reference table saying exactly what each file contains, and the code is pushed into one-level-deep references.
- A 'shape matters more than file names' statement and a dependency-ordered Build Order give Claude the architecture and sequence without over-specifying.
- The trigger evals include near-miss negatives (checkout coupon, PageSpeed loop, scraping meta tags) that match the description's 'Not for' clause one to one.

## Cut candidates

- SKILL.md 'When to Use This Skill': repeats the description, which has already triggered
- SKILL.md 'Common Pitfalls' items 1, 3, 4 and 7: restate Key Decisions
- references/json-ld-generators.md 'Note the units' paragraph, Speakable selector advice and 'Why dual rendering' paragraph: restate SKILL.md
- references/metadata-sitemap-rss.md 'Analytics Provider Wiring': off-scope, a generic provider-agnostic wrapper Claude can write itself, and it belongs to ecommerce-patterns
- references/metadata-sitemap-rss.md 'Link it in the layout' RSS <link> snippet: standard markup Claude already knows
