# Orders, Gift Cards, and E-Commerce Analytics

Schemas and implementations for order lifecycle, gift cards, and commerce event tracking.
All monetary values are integer cents.

## Order Status Configuration

```ts
export const ORDER_STATUSES = {
  pending: { label: "Order Placed", color: "bg-gray-400" },
  confirmed: { label: "Confirmed", color: "bg-blue-500" },
  processing: { label: "Processing", color: "bg-yellow-500" },
  fulfilled: { label: "Fulfilled", color: "bg-green-400" },
  shipped: { label: "Shipped", color: "bg-purple-500" },
  delivered: { label: "Delivered", color: "bg-green-600" },
  cancelled: { label: "Cancelled", color: "bg-red-500" },
  refunded: { label: "Refunded", color: "bg-red-400" },
} as const;

export type OrderStatus = keyof typeof ORDER_STATUSES;
```

Centralizing this prevents status labels and colors from drifting between the admin view, the
customer order history, and email templates.

## Order Schema Design (CMS or Database)

Key fields:

- `orderNumber`: unique, auto-generated, read-only
- `customer`: relationship to customers collection
- `items`: array with product snapshot (name, price, config at time of purchase)
- `subtotal` / `shipping` / `tax` / `total`: all in cents, row layout for side-by-side display
- `status`: select with 8 options, sidebar position
- `shippingAddress`: group with full address fields
- `tracking`: group with carrier, trackingNumber, shippedAt, estimatedDelivery
- `payment`: group with provider, intentId/transactionId, status; read-only, sidebar
- `notes`: internal admin notes

**Critical: snapshot product data at purchase time.** Store `productName` and `unitPrice` on
order items — product prices change after purchase, and an order must remain a faithful record
of what was bought at what price.

---

## Gift Card System

```ts
// Purchase: generate code, create gift card record
// Redeem: validate code, check balance, apply to order
// Balance tracking: deduct on use, support partial redemption

// API: POST /api/gift-cards/redeem
const res = await fetch("/api/gift-cards/redeem", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ code: code.trim() }),
});
```

### Gift Card Collection Schema

- `code`: unique text
- `amount`: original value in cents
- `balance`: remaining balance in cents
- `purchasedBy` / `recipientEmail` / `recipientName`: email fields
- `status`: active | redeemed | expired
- `expiresAt`: optional expiration date

**Validate balance server-side at payment time**, not only at code entry — otherwise concurrent
redemptions can overdraw a card.

---

## E-Commerce Analytics

Use a single `trackEcommerceEvent(event, data)` wrapper and adapt the adapter to your analytics
provider (GA4, Plausible, Segment). Components must never call vendor globals directly.

```ts
type EcommerceEvent =
  | "view_item"
  | "add_to_cart"
  | "remove_from_cart"
  | "begin_checkout"
  | "add_shipping_info"
  | "add_payment_info"
  | "purchase";

interface EcommerceData {
  item_id: string;
  item_name: string;
  price: number; // cents
  quantity: number;
  currency?: string;
  value?: number; // cents — overrides price * quantity when provided
}

interface AnalyticsAdapter {
  track: (event: EcommerceEvent, payload: Record<string, unknown>) => void;
}

const analyticsAdapter: AnalyticsAdapter = {
  track(event, payload) {
    // Forward to your analytics provider here.
  },
};

export function trackEcommerceEvent(
  event: EcommerceEvent,
  data: EcommerceData,
): void {
  if (typeof window === "undefined") return;

  const currency = data.currency ?? "USD";
  const value = data.value ?? data.price * data.quantity;

  analyticsAdapter.track(event, {
    currency,
    value: value / 100, // Convert cents to currency units for dashboards
    items: [
      {
        item_id: data.item_id,
        item_name: data.item_name,
        price: data.price / 100,
        quantity: data.quantity,
      },
    ],
    raw: { priceCents: data.price, valueCents: value },
  });
}
```

### Event Types

| Event               | When                     |
| ------------------- | ------------------------ |
| `view_item`         | Product page viewed      |
| `add_to_cart`       | Item added to cart       |
| `remove_from_cart`  | Item removed             |
| `begin_checkout`    | Checkout started         |
| `add_shipping_info` | Shipping method selected |
| `add_payment_info`  | Payment entered          |
| `purchase`          | Order completed          |

### Web Vitals Reporting

```ts
import { onCLS, onINP, onLCP, onFCP, onTTFB } from "web-vitals";

export function reportWebVitals() {
  onCLS(sendToAnalytics); // Cumulative Layout Shift
  onINP(sendToAnalytics); // Interaction to Next Paint
  onLCP(sendToAnalytics); // Largest Contentful Paint
  onFCP(sendToAnalytics); // First Contentful Paint
  onTTFB(sendToAnalytics); // Time to First Byte
}
```

This is the canonical Web Vitals implementation; the `seo-aeo-structured-data` skill wires it
into the analytics provider component and links here rather than repeating it.
