---
name: code-quality-standards
description: Use when conducting code reviews, auditing code quality, or establishing coding standards for Next.js + React + TypeScript projects.
---

# Code Quality and Security Standards

## When to Use This Skill

Use when:

- Conducting code reviews on React/Next.js/TypeScript projects
- Auditing code for security vulnerabilities
- Enforcing DRY principles and code organization
- Checking for correctness issues (type safety, boundary conditions)
- Reviewing performance patterns
- Establishing coding standards for a team

## Review Categories

### 1. Security and Input Validation

#### API Route Hardening

**Always validate request body in API routes:**

```ts
// WRONG — trusting client input
export async function POST(req: NextRequest) {
  const { amount } = await req.json();
  // Using amount directly...
}

// RIGHT — validate type, range, and format
export async function POST(req: NextRequest) {
  try {
    const { amount } = await req.json();

    if (typeof amount !== "number" || amount < 100 || amount > 10000000) {
      return NextResponse.json({ error: "Invalid amount" }, { status: 400 });
    }

    // Safe to use amount
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}
```

**String input sanitization:**

```ts
// Validate lengths
if (typeof text !== "string" || text.length > 30) {
  return NextResponse.json({ error: "Invalid text" }, { status: 400 });
}

// Trim whitespace
const cleanText = text.trim();

// Email validation
if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
  return NextResponse.json({ error: "Invalid email" }, { status: 400 });
}
```

#### Regex Safety

**Anchor regex patterns to prevent partial matches:**

```ts
// WRONG — allows "12345abc" to match
if (/\d{5}/.test(zip)) { ... }

// RIGHT — anchored, allows optional ZIP+4
if (/^\d{5}(-\d{4})?$/.test(zip.trim())) { ... }
```

#### localStorage Validation

**Never trust data from localStorage.** It can hold stale data from an older schema, corrupted
JSON, or values a user edited by hand.

```ts
// WRONG — direct parse and use
const items = JSON.parse(localStorage.getItem("items") || "[]");

// RIGHT — parse defensively, then narrow with a type guard
function readStored<T>(key: string, isValid: (v: unknown) => v is T, max = 100): T[] {
  try {
    const stored = localStorage.getItem(key);
    if (!stored) return [];
    const parsed: unknown = JSON.parse(stored);
    if (!Array.isArray(parsed) || parsed.length > max) return [];
    return parsed.filter(isValid);
  } catch {
    return []; // Invalid JSON
  }
}
```

Three things must always be present: a `try`/`catch` around `JSON.parse`, an upper bound on
collection size, and a per-item type guard. A worked cart example is in the
[`ecommerce-patterns`](../ecommerce-patterns/SKILL.md) skill.

#### Content Security

**Escape user content in dangerous contexts:**

```ts
// XML/RSS output
function escapeXml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}
```

### 2. DRY Principles

#### Extract Shared Constants

```ts
// WRONG — magic strings repeated across files
const status = order.status === 'pending' ? 'Order Placed' : ...
// In another file:
const label = status === 'pending' ? 'Order Placed' : ...

// RIGHT — centralized constant
export const ORDER_STATUSES = {
  pending:   { label: 'Order Placed', color: 'bg-gray-400' },
  confirmed: { label: 'Confirmed',    color: 'bg-blue-500' },
  processing: { label: 'Processing',   color: 'bg-yellow-500' },
  // ...
} as const

export type OrderStatus = keyof typeof ORDER_STATUSES
```

#### Extract Utility Functions

```ts
// WRONG — price formatting duplicated
<span>${(item.price / 100).toFixed(2)}</span>
// In another file:
<p>{new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price / 100)}</p>

// RIGHT — single utility
export function formatPrice(cents: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(cents / 100)
}
```

#### Shared Type Definitions

```ts
// WRONG — interface duplicated across components
interface CartItem { id: string; name: string; price: number; ... }
// Same interface in another file

// RIGHT — export from one location
// types/cart.ts
export interface CartItem {
  id: string
  productId: string
  name: string
  price: number
  quantity: number
  image?: string
  configuration?: { option?: string; customText?: string; colors?: string[] }
}
```

#### Component Extraction

```ts
// WRONG — 50+ lines of JSX repeated for each shipping option
<label className={`flex items-center gap-4 p-4 rounded-lg border-2 ...`}>
  <input type="radio" ... />
  <Icon ... />
  <div>...</div>
  <span>$5.99</span>
</label>
// Same pattern repeated for priority shipping

// RIGHT — extract ShippingOption component
interface ShippingOptionProps {
  value: string
  icon: React.ComponentType<{ className?: string }>
  label: string
  description: string
  price: number       // cents
  selected: boolean
  onChange: () => void
}

function ShippingOption({ value, icon: Icon, label, description, price, selected, onChange }: ShippingOptionProps) {
  return (
    <label className={`flex items-center gap-4 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
      selected ? 'border-primary bg-surface' : 'border-border'
    }`}>
      <input type="radio" name="shipping" value={value} checked={selected} onChange={onChange} className="sr-only" />
      <Icon className="h-5 w-5 text-muted" />
      <div className="flex-1">
        <p className="text-sm font-medium">{label}</p>
        <p className="text-xs text-muted">{description}</p>
      </div>
      <span className="text-sm font-semibold">{formatPrice(price)}</span>
    </label>
  )
}
```

### 3. Correctness

#### Type Safety

```ts
// WRONG — any types or unsafe casts
const data = response.data as any;
const user = data.user; // Could be undefined

// RIGHT — proper typing
interface ApiResponse {
  user: { id: string; email: string } | null;
}
const data: ApiResponse = await response.json();
if (data.user) {
  // Safe to use data.user.id
}
```

#### Boundary Conditions

```ts
// WRONG — no floor on quantity
dispatch({ type: "UPDATE_QUANTITY", payload: { id, quantity } });

// RIGHT — enforce minimum
dispatch({
  type: "UPDATE_QUANTITY",
  payload: { id, quantity: Math.max(1, quantity) },
});
```

```ts
// WRONG — no max length enforcement
const [text, setText] = useState('')
<input onChange={(e) => setText(e.target.value)} />

// RIGHT — enforce limits
<input
  maxLength={30}
  onChange={(e) => {
    if (e.target.value.length <= 30) setText(e.target.value)
  }}
/>
```

#### Error Handling

```ts
// WRONG — unhandled promise rejection
const res = await fetch("/api/endpoint");
const data = await res.json();

// RIGHT — handle errors
try {
  const res = await fetch("/api/endpoint");
  if (!res.ok) {
    const error = await res.json();
    setError(error.message || "Something went wrong");
    return;
  }
  const data = await res.json();
  // Use data
} catch {
  setError("Network error. Please try again.");
}
```

#### Ambiguous Character Avoidance

```ts
// WRONG — confusable characters in codes
const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

// RIGHT — remove 0/O, 1/I/L confusion
const chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
```

### 4. Performance

#### React Memoization

```ts
// WRONG — recalculated every render
function Component({ items }) {
  const total = items.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0,
  );
  // total recalculates even when items haven't changed
}

// RIGHT — memoize expensive computations
function Component({ items }) {
  const total = useMemo(
    () => items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    [items],
  );
}
```

```ts
// Memoize callbacks to prevent child re-renders
const handleClick = useCallback(() => {
  dispatch({ type: "CLEAR" });
}, []);
```

#### Dynamic Imports for Heavy Dependencies

```ts
// WRONG — Three.js imported at page load
import { Canvas } from '@react-three/fiber'

// RIGHT — dynamic import, loaded on demand
const Scene = dynamic(() => import('./Scene').then(m => m.Scene), {
  ssr: false,
  loading: () => <SceneSkeleton />,
})
```

#### Image Optimization

```ts
// next.config.mjs
images: {
  formats: ['image/avif', 'image/webp'],
  deviceSizes: [640, 750, 828, 1080, 1200, 1920],
  minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
}
```

### 5. Accessibility

Accessibility standards and their implementation patterns live in the
[`design-review-standards`](../design-review-standards/SKILL.md) skill (§6, WCAG AA) — semantic
HTML, icon-button labels, skip navigation, `aria-live` announcements, and toggle state. Load
that skill when a diff touches markup or interactive elements.

The checklist below carries the minimum a code review must confirm; anything deeper belongs to
that skill.

### 6. Code Organization

#### File Structure Convention

Group components by feature/domain, with dedicated folders for primitives and cross-cutting concerns:

```
components/
├── layout/          # App shell: header, footer, navigation
├── {feature}/       # One folder per feature/domain (e.g. products/, cart/, checkout/)
├── ui/              # Reusable primitives: Button, Input, Badge, Skeleton, Toast
└── shared/          # Cross-cutting: ErrorBoundary, Logo, OptimizedImage
```

- A component belongs in `{feature}/` when it encodes domain logic; in `ui/` when it is generic and reusable; in `shared/` when it is app-specific but used across features
- Follow the target project's existing structure when one is established

#### 'use client' Discipline

```tsx
// WRONG — marking everything as client
"use client"; // On a page that only renders HTML

// RIGHT — 'use client' only where needed
// Server Component (default) — no directive needed
export default function ProductPage({ params }) {
  const product = await getCmsClient().then((cms) =>
    cms.findBySlug("products", params.slug),
  );
  return <ProductDetail product={product} />;
}

// Client Component — only for interactivity
("use client");
export function AddToCartButton({ product }) {
  const { addItem } = useCart();
  return <button onClick={() => addItem(product)}>Add to Cart</button>;
}
```

## Common Mistakes

1. **`any` as escape hatch**: Casting to `any` to silence TypeScript errors instead of fixing the underlying type mismatch — creates silent runtime failures
2. **Unanchored regex**: Forgetting `^` and `$` anchors on validation patterns allows partial matches to pass (e.g., `test@evil.com<script>`)
3. **Boolean prop flags**: `<Modal isLarge isDismissable isAnimated>` — use a variant enum or options object instead
4. **`||` for defaults**: Using `||` instead of `??` causes falsy values like `0` or `""` to trigger the default unexpectedly
5. **Index keys in dynamic lists**: Using array index as React `key` on lists that can reorder, filter, or grow — use stable IDs from data

---

## Code Review Checklist

```markdown
## Code Review: [PR/Component Name]

### Security

- [ ] API routes validate input types and ranges
- [ ] String inputs trimmed and length-checked
- [ ] Regex patterns anchored (^ and $)
- [ ] localStorage data validated on read
- [ ] No user content in dangerouslySetInnerHTML without escaping

### DRY

- [ ] No duplicated constants or magic strings
- [ ] Shared utility functions for common operations
- [ ] Types exported from single location
- [ ] Repeated JSX patterns extracted to components

### Correctness

- [ ] TypeScript types properly applied (no `any`)
- [ ] Boundary conditions handled (min/max values)
- [ ] Error states caught and displayed
- [ ] Null/undefined checks before property access

### Performance

- [ ] Heavy dependencies dynamically imported
- [ ] Expensive computations memoized (useMemo)
- [ ] Callbacks stable (useCallback)
- [ ] Images optimized (AVIF/WebP, responsive sizes)

### Accessibility

- [ ] Semantic HTML elements used
- [ ] Icon buttons have aria-labels
- [ ] Focus styles visible
- [ ] Dynamic changes announced (aria-live)
- [ ] Toggle states indicated (aria-pressed)

### Organization

- [ ] Components in correct directory
- [ ] 'use client' only where needed
- [ ] Consistent naming convention
- [ ] data-testid on interactive elements
```
