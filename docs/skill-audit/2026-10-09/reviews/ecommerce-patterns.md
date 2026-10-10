# ecommerce-patterns

Verdict: **needs-work** · SKILL.md body 139 lines · description 72 chars

The body is short, organized as rules plus pitfalls, and keeps the long React, checkout and analytics code one level deep in two reference files, which matches the progressive disclosure pattern. The biggest gap is the 72-character description. It names four nouns but not what the skill provides, the React/Next.js stack, or the plain-language triggers its own evals test. It also lacks the "Not for … (other-skill)" clause that sibling skills use, even though those siblings point back to this one.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | fail | "Use when building cart, checkout, payment, or order-management features." It leaves out integer cents, gift cards, cart persistence, order status, analytics and React/Next.js. |
| Description includes both what the Skill does and when to use it | fail | It gives only the when. The what (rules and worked implementations) is missing, and the body's "When to Use This Skill" list holds trigger material that the model never sees before the skill loads. |
| SKILL.md body is under 500 lines | pass | 139 body lines. |
| Additional details are in separate files (if needed) | pass | Code lives in references/cart-and-checkout.md and references/orders-giftcards-analytics.md. |
| No time-sensitive information (or in an "old patterns" section) | pass | No dated guidance. The Web Vitals list uses INP, not FID. |
| Consistent terminology throughout | partial | "Order items" and "product snapshots" mostly line up, and "collection" (CMS wording) sits beside "schema". The bigger issue is the same cents caveat hedged three times ("most providers expect cents natively"). |
| Examples are concrete, not abstract | pass | The examples are concrete: formatPrice, the float error, and the order number sample. |
| File references are one level deep | pass | Both reference files link only back to SKILL.md, not onward. |
| Progressive disclosure used appropriately | pass | A table of references with a Contains column, and pointers at the point of use. |
| Workflows have clear steps | pass | The checkout sequence and numbered cart rules are clear. This is a rules skill, so a copyable checklist is not required. |
| Reference files over 100 lines have a table of contents | fail | cart-and-checkout.md is 307 lines and orders-giftcards-analytics.md is 161 lines. Neither has a contents list. |
| No "voodoo constants" (all values justified) | partial | Reference code uses `parsed.length <= 100` and `amount < 100 || amount > 10000000` with no reason. The order-number alphabet, by contrast, is justified. |
| Validation/verification steps for critical operations | pass | Server-side amount re-validation, total recompute and gift card balance re-check at payment time are all stated. |
| No Windows-style paths (all forward slashes) | pass |  |
| Required packages listed in instructions and verified as available | partial | web-vitals is imported in the reference without being named as a dependency. createPaymentProviderClient is a placeholder, which is acceptable for a provider-neutral pattern. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 cases: 5 that should trigger and 3 that should not. All are trigger-only with `assertions: []`, so nothing tests whether the skill changes the output. |

## Findings

1. **high** · Writing effective descriptions; checklist: Description is specific and includes key terms / includes both what and when · SKILL.md frontmatter, description
   > description: Use when building cart, checkout, payment, or order-management features.

   Fix: Rewrite the description to state what the skill provides: integer-cent pricing and formatPrice, a localStorage cart with defensive hydration and a drawer, server-side amount checks, order numbers, status lifecycle and snapshots, gift card redemption, and commerce analytics, for React/Next.js. Add plain-word triggers taken from the evals: totals showing $74.97000000000001, a basket lost on reload, a slide-out cart, and a gift card balance spent twice. End with the collection's clause: Not for store-page visual or accessibility audits (design-review-standards), Product JSON-LD (seo-aeo-structured-data), or flaky purchase E2E tests (playwright-e2e).

2. **medium** · Concise is key; Writing effective descriptions (triggers belong in metadata, which is the only part preloaded) · SKILL.md, "When to Use This Skill" (lines 8-18)
   > Use when:
- Building a shopping cart system

   Fix: Delete the bulleted list. Move its trigger terms (wishlists, reviews, trust and conversion components) into the description if they are still in scope. Keep only the sentence on line 20 and the reference table. (about 90 tokens saved)

3. **medium** · Concise is key ("Does this paragraph justify its token cost?"); Use consistent terminology · SKILL.md, Common Pitfalls (lines 134-143)
   > 2. **Cart hydration without validation**: localStorage can have stale or corrupt data. Always validate types and cap the size.
4. **No quantity floor**: always enforce `Math.max(1, quantity)`.

   Fix: Pitfalls 1-5 and 8 repeat Price Handling, cart rules 1, 3 and 4, and the checkout rules "Snapshot, don't reference" and "Re-validate amounts server-side" almost word for word. Keep only the items that appear nowhere else: the gift card race (7) and the provider amount unit (6). Alternatively, move those two into the Checkout rules and drop the section. (about 170 tokens saved)

4. **medium** · Concise is key (Default assumption: Claude is already very smart) · SKILL.md, Conversion Optimization Components (lines 120-132)
   > **Trust badges**: secure checkout badge, free returns policy, shipping estimates, payment method
logos.

**Social proof**: review count and average rating, recent purchase counts, testimonials.

   Fix: Cut the trust badge and social proof lists: Claude already knows these generic UI inventories, and design-review-standards §10 owns them. Keep one line saying that add-to-cart auto-opens the drawer and that the drawer needs a real empty state, plus the pointer to design-review-standards. (about 110 tokens saved)

5. **low** · Concise is key; Use consistent terminology · SKILL.md, Price Handling (lines 28-67)
   > // WRONG — floating point errors
const price = 24.99;
...
- Payment provider amounts: cents (most providers expect cents natively)

   Fix: Claude knows binary floating point, so drop the WRONG/RIGHT block and keep the one-line rule plus formatPrice. State the provider-unit caveat once, in the integer cents rule (pass cents unless the SDK documents a decimal amount or a zero-decimal currency). It currently repeats in line 64, pitfall 6 and the reference's route comment. (about 90 tokens saved)

6. **medium** · Structure longer reference files with a table of contents · references/cart-and-checkout.md (307 lines); references/orders-giftcards-analytics.md (161 lines)
   > # Cart and Checkout Implementation

Worked implementations for the cart state machine and the checkout flow.

   Fix: Add a short contents list under each title so a partial read still shows the full scope. For cart-and-checkout.md: Cart reducer, localStorage hydration, ARIA live region and analytics, address validation, shipping method UI, payment intent, order numbers. For orders-giftcards-analytics.md: order statuses, order schema, gift cards, analytics wrapper, event table, Web Vitals.

7. **low** · Solve, don't defer: no "voodoo constants" · references/cart-and-checkout.md, localStorage hydration (line 125) and payment route (lines 254-255)
   > if (Array.isArray(parsed) && parsed.length <= 100) {
      amount < 100 ||
      amount > 10000000

   Fix: Name the values and give a one-line reason for each, for example MAX_CART_LINES = 100 (bounds the cost of parsing a tampered entry) and MIN_CHARGE_CENTS = 100, MAX_CHARGE_CENTS = 10_000_000 (the provider minimum and a fraud ceiling to tune per store). The model will copy these numbers into production code.

8. **low** · Concise is key; Use consistent terminology (claims must hold across the collection) · SKILL.md line 56; references/orders-giftcards-analytics.md lines 160-161
   > This is the canonical `formatPrice`; other skills reference it rather than redefining it.

   Fix: Delete both maintainer notes. They tell Claude nothing it can act on, and the formatPrice one is false: code-quality-standards/SKILL.md lines 167-172 redefines formatPrice in full. (about 45 tokens saved)

## Strengths

- A clean split between SKILL.md and references: SKILL.md holds stack-independent rules and pitfalls, and the reference table has a Contains column so Claude knows which file to open before opening it.
- Rules carry their reason in one clause ("configurable items always become a new line, because each configuration is a distinct product"), which justifies them without over-explaining.
- Server-side checks are written into the rules for the money operations: re-validate the amount, recompute the total from stored prices, and re-check the gift card balance at payment time.

## Cut candidates

- When to Use This Skill (the bullet list duplicates what should be in the description)
- Common Pitfalls items 1-5 and 8 (they restate Price Handling, the Cart System rules and the Checkout Flow rules)
- Conversion Optimization Components: Trust badges and Social proof lists (generic UI knowledge, owned by design-review-standards §10)
- Price Handling: WRONG/RIGHT floating-point demonstration block
- Price Handling: "This is the canonical formatPrice; other skills reference it rather than redefining it."
- references/orders-giftcards-analytics.md: closing note that the seo-aeo-structured-data skill links here
