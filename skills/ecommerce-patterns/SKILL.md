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

**Apply everywhere:**

- Product.price: cents
- Order.subtotal/shipping/tax/total: cents
- GiftCard.amount/balance: cents
- CartItem.price: cents
- Payment provider amounts: cents (many providers expect cents natively)

## Cart System

### Architecture: React Context + useReducer

```tsx
"use client";

import React, {
  createContext,
  useCallback,
  useReducer,
  useEffect,
  useState,
} from "react";

const CART_STORAGE_KEY = "cart"; // Namespace per app if needed

export interface CartItem {
  id: string; // Unique cart line ID (crypto.randomUUID())
  productId: string; // Product reference
  name: string;
  price: number; // Cents
  quantity: number;
  image?: string;
  configuration?: {
    // For configurable products
    flag?: string;
    customText?: string;
    colors?: string[];
  };
}

interface CartState {
  items: CartItem[];
  isOpen: boolean;
}

export interface CartContextType {
  items: CartItem[];
  isOpen: boolean;
  addItem: (item: Omit<CartItem, "id">) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;
  subtotal: number;
  itemCount: number;
}

export const CartContext = createContext<CartContextType | null>(null);

type CartAction =
  | { type: "ADD_ITEM"; payload: Omit<CartItem, "id"> }
  | { type: "REMOVE_ITEM"; payload: string }
  | { type: "UPDATE_QUANTITY"; payload: { id: string; quantity: number } }
  | { type: "CLEAR" }
  | { type: "OPEN" }
  | { type: "CLOSE" }
  | { type: "TOGGLE" }
  | { type: "HYDRATE"; payload: CartItem[] };

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case "ADD_ITEM": {
      const id = crypto.randomUUID();
      // Merge non-configurable duplicates; configurable items always get new entries
      const isConfigurable = !!action.payload.configuration;
      const existingIndex = isConfigurable
        ? -1
        : state.items.findIndex(
            (item) => item.productId === action.payload.productId,
          );
      if (existingIndex > -1) {
        const items = [...state.items];
        items[existingIndex] = {
          ...items[existingIndex],
          quantity: items[existingIndex].quantity + action.payload.quantity,
        };
        return { ...state, items, isOpen: true };
      }
      return {
        ...state,
        items: [...state.items, { ...action.payload, id }],
        isOpen: true, // Auto-open drawer
      };
    }
    case "REMOVE_ITEM":
      return {
        ...state,
        items: state.items.filter((item) => item.id !== action.payload),
      };
    case "UPDATE_QUANTITY":
      return {
        ...state,
        items: state.items.map((item) =>
          item.id === action.payload.id
            ? { ...item, quantity: Math.max(1, action.payload.quantity) }
            : item,
        ),
      };
    case "CLEAR":
      return { ...state, items: [] };
    case "HYDRATE":
      return { ...state, items: action.payload };
    // OPEN, CLOSE, TOGGLE for drawer state
    default:
      return state;
  }
}
```

### Key Cart Patterns

**1. localStorage Hydration with Validation**

```tsx
useEffect(() => {
  try {
    const stored = localStorage.getItem(CART_STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed) && parsed.length <= 100) {
        const valid = parsed.filter(
          (item: unknown): item is CartItem =>
            typeof item === "object" &&
            item !== null &&
            typeof (item as CartItem).id === "string" &&
            typeof (item as CartItem).productId === "string" &&
            typeof (item as CartItem).name === "string" &&
            typeof (item as CartItem).price === "number" &&
            typeof (item as CartItem).quantity === "number",
        );
        dispatch({ type: "HYDRATE", payload: valid });
      }
    }
  } catch {
    // Ignore invalid JSON — start with empty cart
  }
}, []);
```

**Why validate:** localStorage can contain stale data from old versions, corrupted JSON, or items with missing fields. Always validate types and set a maximum item limit.

**2. Duplicate Handling**

- Non-configurable items: merge by incrementing quantity
- Configurable items: always add as new line (each configuration is unique)

**3. ARIA Live Region for Screen Readers**

```tsx
<div role="status" aria-live="polite" className="sr-only">
  {liveMessage}
</div>
```

Update `liveMessage` on add/remove: "Added Sample Product to cart"

**4. Analytics on Cart Events**

```tsx
const addItem = useCallback((item: Omit<CartItem, "id">) => {
  dispatch({ type: "ADD_ITEM", payload: item });
  setLiveMessage(`Added ${item.name} to cart`);
  trackEcommerceEvent("add_to_cart", {
    item_id: item.productId,
    item_name: item.name,
    price: item.price,
    quantity: item.quantity,
  });
}, []);
```

## Checkout Flow

### Multi-Step Architecture

```
Cart → Shipping Address → Shipping Method → Gift Card (optional) → Payment → Confirmation
```

### Shipping Address Validation

```tsx
function validateShippingAddress(
  address: ShippingAddress,
): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!address.name.trim()) errors.name = "Name is required";
  if (!address.line1.trim()) errors.line1 = "Address is required";
  if (!address.city.trim()) errors.city = "City is required";
  if (!address.state.trim()) errors.state = "State is required";
  if (!address.zip.trim()) errors.zip = "ZIP code is required";
  else if (!/^\d{5}(-\d{4})?$/.test(address.zip.trim()))
    errors.zip = "Invalid ZIP code";
  return errors;
}

// In component:
const validate = useCallback(() => {
  const newErrors = validateShippingAddress(address);
  setErrors(newErrors);
  return Object.keys(newErrors).length === 0;
}, [address]);
```

**Clear errors on input:**

```tsx
function updateField(field: keyof ShippingAddress, value: string) {
  setAddress((prev) => ({ ...prev, [field]: value }));
  if (errors[field]) {
    setErrors((prev) => ({ ...prev, [field]: undefined }));
  }
}
```

### Shipping Method UI Pattern

```tsx
<label
  className={`flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
    selected
      ? "border-token-foreground bg-token-surface"
      : "border-token-border hover:border-token-foreground"
  }`}
>
  <input
    type="radio"
    name="shippingMethod"
    value="standard"
    className="sr-only"
  />
  <Icon className="h-5 w-5 text-token-muted flex-shrink-0" />
  <div className="flex-1">
    <p className="text-sm font-medium">Standard Shipping</p>
    <p className="text-xs text-token-muted">5-7 business days</p>
  </div>
  <span className="text-sm font-semibold">$5.99</span>
</label>
```

### Payment Provider Integration

**Server: Create Payment Intent / Charge**

```ts
// app/api/create-payment-intent/route.ts
import { NextRequest, NextResponse } from "next/server";

const paymentProvider = createPaymentProviderClient(
  process.env.PAYMENT_PROVIDER_SECRET_KEY!,
);

export async function POST(req: NextRequest) {
  try {
    const { amount } = await req.json();

    if (
      typeof amount !== "number" ||
      !Number.isInteger(amount) ||
      amount < 100 ||
      amount > 10000000
    ) {
      return NextResponse.json({ error: "Invalid amount" }, { status: 400 });
    }

    const paymentIntent = await paymentProvider.createPaymentIntent({
      amount, // Already in cents; many providers expect cents natively
      currency: "usd",
    });

    return NextResponse.json({ clientSecret: paymentIntent.clientSecret });
  } catch {
    return NextResponse.json(
      { error: "Failed to create payment intent" },
      { status: 500 },
    );
  }
}
```

**Client: Performance hints**

```html
<!-- Replace with your payment provider's hosted JS origin. -->
<link rel="dns-prefetch" href="https://js.payment-provider.example" />
<link rel="preconnect" href="https://js.payment-provider.example" />
```

### Order Number Generation

```ts
const ORDER_PREFIX = "ORD"; // Configure per app

export function generateOrderNumber(): string {
  const date = new Date();
  const dateStr = date.toISOString().slice(0, 10).replace(/-/g, "");
  const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // No 0/O/1/I confusion
  const randomBytes = new Uint8Array(4);
  globalThis.crypto.getRandomValues(randomBytes);
  const rand = Array.from(randomBytes)
    .map((b) => chars[b % chars.length])
    .join("");
  return `${ORDER_PREFIX}-${dateStr}-${rand}`;
}
// ORD-20260326-A7K2
```

**Design decisions:**

- Date prefix for human-sortable order history
- Excluded ambiguous characters (0/O, 1/I)
- Cryptographic randomness for uniqueness
- Short enough to read over phone

## Order Lifecycle

### Status State Machine

```
pending → confirmed → processing → fulfilled → shipped → delivered
                                                        ↘ cancelled
                                                        ↘ refunded
```

### Status Configuration

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
```

### Order Schema Design (CMS or Database)

Key fields:

- `orderNumber`: unique, auto-generated, read-only
- `customer`: relationship to customers collection
- `items`: array with product snapshot (name, price, config at time of purchase)
- `subtotal/shipping/tax/total`: all in cents, row layout for side-by-side display
- `status`: select with 8 options, sidebar position
- `shippingAddress`: group with full address fields
- `tracking`: group with carrier, trackingNumber, shippedAt, estimatedDelivery
- `payment`: group with provider, intentId/transactionId, status; read-only, sidebar
- `notes`: internal admin notes

**Critical: Snapshot product data at purchase time.** Store `productName` and `unitPrice` on order items — product prices can change after purchase.

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
- `purchasedBy/recipientEmail/recipientName`: email fields
- `status`: active | redeemed | expired
- `expiresAt`: optional expiration date

## E-Commerce Analytics

### Analytics Provider Abstraction

Use a single `trackEcommerceEvent(event, data)` wrapper and adapt the adapter to your analytics provider (for example, GA4, Plausible, or Segment).

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

## Conversion Optimization Components

### Trust Badges

- Secure checkout badge
- Free returns policy
- Shipping estimates
- Payment method logos (Visa, Mastercard, Apple Pay, Google Pay)

### Social Proof

- Review count and average rating
- "X people bought this today"
- Community stories / testimonials

### Cart Drawer Pattern

- Auto-opens on add-to-cart
- Slide-in from right with backdrop
- Shows item count, subtotal, checkout CTA
- Empty state with "Browse Products" link
- Close on backdrop click or X button

## Common Pitfalls

1. **Floating-point money**: ALWAYS use cents. `24.99 * 100` can give `2498.9999...`. Parse from API as integers.
2. **Cart hydration without validation**: localStorage can have stale/corrupt data. Always validate types.
3. **Missing product snapshots**: Store product name/price on order items — products change after purchase.
4. **No quantity floor**: Always enforce `Math.max(1, quantity)` — zero or negative quantities break totals.
5. **Missing ARIA on cart changes**: Screen readers need live regions to announce cart updates.
6. **Payment-provider amount confusion**: Many providers expect cents natively — pass your cents value directly unless your chosen SDK documents otherwise.
7. **Gift card race conditions**: Validate balance server-side at payment time, not just at code entry.
