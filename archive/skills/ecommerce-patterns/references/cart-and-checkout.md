# Cart and Checkout Implementation

Worked implementations for the cart state machine and the checkout flow. All monetary values
are integer cents — see the Price Handling section of `SKILL.md`.

## Cart: React Context + useReducer

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

## localStorage Hydration with Validation

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

**Why validate:** localStorage can contain stale data from old versions, corrupted JSON, or
items with missing fields. Always validate types and set a maximum item limit.

## ARIA Live Region + Analytics on Cart Events

```tsx
<div role="status" aria-live="polite" className="sr-only">
  {liveMessage}
</div>
```

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

---

## Shipping Address Validation

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

## Shipping Method UI Pattern

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

When more than one shipping option exists, extract this into a `ShippingOption` component
rather than repeating the markup per option.

## Payment Provider Integration

**Server: create payment intent / charge**

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

**Client: performance hints**

```html
<!-- Replace with your payment provider's hosted JS origin. -->
<link rel="dns-prefetch" href="https://js.payment-provider.example" />
<link rel="preconnect" href="https://js.payment-provider.example" />
```

## Order Number Generation

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
- Short enough to read over the phone
