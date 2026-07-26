---
name: ecommerce-patterns
description: Use when building cart, checkout, payment, or order-management features.
---

# E-Commerce Patterns

## When to Use This Skill

Use when:

- Building a shopping cart system
- Implementing checkout with payment processing
- Designing order management and lifecycle
- Integrating payment provider SDKs
- Adding gift cards, wishlists, or reviews
- Implementing e-commerce analytics
- Building trust and conversion components

Worked implementations live in reference files; this file carries the rules, decisions, and
pitfalls that apply regardless of stack.

| Reference                                                                            | Contains                                                                                     |
| ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| [`references/cart-and-checkout.md`](references/cart-and-checkout.md)                 | Cart context/reducer, localStorage hydration, address validation, payment intent, order numbers |
| [`references/orders-giftcards-analytics.md`](references/orders-giftcards-analytics.md) | Order status config and schema, gift cards, `trackEcommerceEvent`, Web Vitals                |

## Price Handling (Critical)

**ALL prices must be stored and computed as integers (cents).** Never use floating-point numbers for money.

```ts
// WRONG — floating point errors
const price = 24.99;
const total = price * 3; // 74.97000000000001

// RIGHT — cents as integers
const price = 2499; // $24.99
const total = price * 3; // 7497 ($74.97)
```

**Format only at display time:**

```ts
export function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

// formatPrice(2499) → "$24.99"
// formatPrice(7497) → "$74.97"
```

This is the canonical `formatPrice`; other skills reference it rather than redefining it.

**Apply everywhere:**

- `Product.price`: cents
- `Order.subtotal` / `shipping` / `tax` / `total`: cents
- `GiftCard.amount` / `balance`: cents
- `CartItem.price`: cents
- Payment provider amounts: cents (most providers expect cents natively)

Convert to currency units only at two boundaries: display formatting, and analytics payloads
whose dashboards expect decimal values.

## Cart System

**Architecture: React Context + `useReducer`.** State lives in a reducer, persistence in
localStorage, and the drawer's open/closed state travels with the cart so "add to cart" can
auto-open it. Full implementation in
[`references/cart-and-checkout.md`](references/cart-and-checkout.md).

Rules the implementation must satisfy:

1. **Hydrate defensively.** localStorage can hold stale data from an older schema or corrupted
   JSON. Wrap `JSON.parse` in `try`/`catch`, cap the item count, and narrow every item with a
   type guard before it reaches state.
2. **Duplicate handling depends on configurability.** Non-configurable items merge by
   incrementing quantity; configurable items always become a new line, because each
   configuration is a distinct product.
3. **Floor the quantity.** `Math.max(1, quantity)` on every update — zero or negative
   quantities silently corrupt totals.
4. **Announce changes.** Cart mutations must reach an `aria-live="polite"` region, or screen
   reader users get no feedback from "Add to cart".
5. **Emit analytics from the action, not the component.** Track inside `addItem`/`removeItem`
   so every call site is covered.

## Checkout Flow

```text
Cart → Shipping Address → Shipping Method → Gift Card (optional) → Payment → Confirmation
```

Rules:

- **Validate on submit, clear on input.** Show errors after a submit attempt, then clear each
  field's error as soon as the user edits it.
- **Re-validate amounts server-side.** The client's total is a suggestion. The payment endpoint
  must independently check that the amount is an integer within a sane range before charging.
- **Preconnect to the payment provider's JS origin.** The SDK is on the critical path to
  conversion.
- **Snapshot, don't reference.** Order items store the product name and unit price as they were
  at purchase time.

## Order Lifecycle

```text
pending → confirmed → processing → fulfilled → shipped → delivered
                                                        ↘ cancelled
                                                        ↘ refunded
```

Centralize status labels and colors in one `ORDER_STATUSES` constant — see
[`references/orders-giftcards-analytics.md`](references/orders-giftcards-analytics.md), which
also covers the order schema, gift cards, and analytics events.

## Conversion Optimization Components

**Trust badges**: secure checkout badge, free returns policy, shipping estimates, payment method
logos.

**Social proof**: review count and average rating, recent purchase counts, testimonials.

**Cart drawer**: auto-opens on add-to-cart, slides in with a backdrop, shows item count,
subtotal, and checkout CTA, has a real empty state with a "Browse Products" link, and closes on
backdrop click or the X button.

For the design-quality dimensions behind these (CTA hierarchy, trust signals, guest checkout),
see the [`design-review-standards`](../design-review-standards/SKILL.md) skill, §10.

## Common Pitfalls

1. **Floating-point money**: ALWAYS use cents. `24.99 * 100` can give `2498.9999...`. Parse from APIs as integers.
2. **Cart hydration without validation**: localStorage can have stale or corrupt data. Always validate types and cap the size.
3. **Missing product snapshots**: store product name and price on order items — products change after purchase.
4. **No quantity floor**: always enforce `Math.max(1, quantity)`.
5. **Missing ARIA on cart changes**: screen readers need live regions to announce cart updates.
6. **Payment-provider amount confusion**: most providers expect cents natively — pass your cents value directly unless the SDK documents otherwise.
7. **Gift card race conditions**: validate balance server-side at payment time, not just at code entry.
8. **Trusting client-supplied totals**: recompute the order total server-side from stored prices before charging.
