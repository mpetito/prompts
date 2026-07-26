---
name: design-review-standards
description: Use when reviewing UI/UX implementations, auditing design quality or accessibility, or establishing design standards for a web application.
---

# Design Review and UI/UX Standards

## When to Use This Skill

Use when:

- Conducting a design or UI/UX review of a web application
- Auditing a site for design consistency and quality
- Establishing or enforcing design standards
- Reviewing accessibility compliance
- Evaluating responsive design implementation
- Assessing conversion optimization and trust signals

## Review Framework

Evaluate every design review across these 10 dimensions. Score each 1-5, prioritize fixes by impact.

### 1. Typography Hierarchy

**Check for:**

- Display font (headings) vs body font (text) clearly differentiated
- Maximum 2 fonts, 2-3 weights
- Heading sizes follow consistent scale (not arbitrary)
- `letter-spacing: -0.01em` on display headings for polish
- Body text 16px minimum, 1.5-1.6 line height
- `font-display: swap` on all web fonts
- Font preloading for critical fonts

**Red flags:**

- Body text below 14px
- More than 3 font families
- Headings and body text look the same
- Missing font loading optimization (FOIT/FOUT)

### 2. Color Token Consistency

**Check for:**

- All colors reference design tokens (CSS custom properties), not hardcoded hex values
- Brand palette defined in one place (globals.css @theme block)
- Semantic color usage: muted for secondary text, border for dividers, surface for backgrounds
- Accessible contrast ratios: 4.5:1 for body text, 3:1 for large text
- No rogue colors that aren't in the design system
- Sufficiently dark variants of saturated brand colors for text on light backgrounds, meeting WCAG AA (e.g., darken a vivid red until it passes 4.5:1)

**Red flags:**

- Hardcoded hex values scattered across components
- Different shades of the same color used inconsistently
- Text color that fails WCAG AA contrast
- Brand colors used for decoration rather than meaning

### 3. Spacing and Layout

**Check for:**

- Consistent spacing scale (4px base: 4, 8, 12, 16, 24, 32, 48, 64)
- Section padding increases with viewport: 1rem mobile, 1.5rem tablet, 2rem desktop
- Container max-width with responsive padding (`container-page` pattern)
- Content sections have breathing room (py-12 to py-20)
- Cards and components use consistent internal padding
- Grid gaps are proportional to content density

**Red flags:**

- Inconsistent padding between similar sections
- Content touching container edges on mobile
- Cramped layouts with no visual breathing room
- Massive whitespace that feels like a bug

### 4. Dark Mode

**Check for:**

- CSS variable overrides (not Tailwind dark: classes for brand tokens)
- Background/surface colors properly inverted
- Text colors maintain readability
- Border colors adjusted for dark backgrounds
- Images/icons remain visible
- System preference support (`prefers-color-scheme: dark`)
- Manual toggle available

**Red flags:**

- Pure white text on pure black (#FFFFFF on #000000) — too harsh. Use #CDCCCA on #171614
- Colored text that was accessible on light but fails on dark
- Images with white backgrounds that don't adapt
- Missing dark mode entirely

### 5. Component Patterns

**Check for:**

- Button variants: primary, outline, ghost, danger — each with clear visual hierarchy
- Input fields: labels, error states, focus rings, placeholder text
- Loading states: skeleton shimmer, not spinners for content areas
- Empty states: helpful message + CTA (not just blank space)
- Error states: inline error messages near the field, not just toast
- Badge component for counts and status indicators
- Consistent border-radius across the design system

**Red flags:**

- Buttons that all look the same (no visual hierarchy)
- Missing loading states (content pops in)
- Error messages far from the field that caused them
- No empty states (blank pages when data is missing)

### 6. Accessibility (WCAG AA)

**Check for:**

- Skip-to-content link as first focusable element
- `:focus-visible` styles with visible outline + offset
- ARIA labels on icon-only buttons
- `aria-live="polite"` regions for dynamic content changes (cart updates)
- `aria-pressed` on toggle buttons
- Semantic HTML: `<nav>`, `<main>`, `<section>`, `<article>`, `<aside>`
- Form labels associated with inputs (not just placeholder text)
- `aria-hidden` on decorative elements
- Keyboard navigation works for all interactive elements
- Screen reader announcements for cart add/remove

**Red flags:**

- No focus styles visible
- Icon buttons without labels
- Missing landmark elements
- Cart changes not announced to screen readers
- Tab order doesn't match visual order

**Implementation patterns.** This skill is the canonical home for accessibility guidance; code-level reviews reach it from `code-quality-standards`.

Semantic HTML over div soup:

```tsx
// WRONG — div soup
<div className="nav">
  <div className="nav-item">...</div>
</div>

// RIGHT — semantic elements
<nav aria-label="Main navigation">
  <a href="/products">Shop</a>
</nav>
```

Icon-only buttons need an accessible name:

```tsx
// WRONG — icon without label
<button><SearchIcon /></button>

// RIGHT
<button aria-label="Search products">
  <SearchIcon className="w-5 h-5" />
</button>
```

Skip navigation — the first focusable element on the page:

```tsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:bg-white focus:px-4 focus:py-2 focus:rounded-lg focus:shadow-lg"
>
  Skip to main content
</a>
```

Announce dynamic changes to screen readers:

```tsx
<div role="status" aria-live="polite" className="sr-only">
  {liveMessage}
</div>;

// Update on actions
setLiveMessage(`Added ${item.name} to cart`);
```

Toggles need programmatic state, not just a visual one:

```tsx
// WRONG — no programmatic state
<button onClick={toggle}>Dark Mode</button>

// RIGHT — aria-pressed for toggles
<button
  onClick={toggle}
  aria-pressed={theme === 'dark'}
  aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
>
  {theme === 'light' ? <MoonIcon /> : <SunIcon />}
</button>
```

### 7. Responsive Design

**Check for:**

- Mobile-first approach (base styles for mobile, media queries for larger screens)
- Bottom navigation bar on mobile (thumb-friendly)
- Touch targets minimum 44x44px
- Text readable without zooming on 375px viewport
- Images responsive with appropriate sizes
- Horizontal scroll prevented
- Mobile-specific search UI
- Cart drawer works on mobile
- Navigation collapses to hamburger menu

**Red flags:**

- Content overflowing viewport on mobile
- Tiny tap targets
- Desktop layout forced on mobile
- Missing mobile navigation
- Fixed-width elements that break on small screens

### 8. Loading and Performance

**Check for:**

- Skeleton loading states for content areas
- Page transition animations (subtle, 200ms)
- `font-display: swap` to prevent FOIT
- Image optimization: AVIF/WebP, responsive sizes, lazy loading
- Critical font preloading
- DNS prefetch for external domains (payment provider, analytics)
- Heavy dependencies loaded on demand (3D viewer library via dynamic import)

**Red flags:**

- Content pop-in without skeletons
- Layout shift during loading (CLS)
- Large unoptimized images
- All JavaScript loaded upfront
- No loading indicators on async actions

### 9. Micro-interactions and Polish

**Check for:**

- Hover states on interactive elements (color transitions, subtle scale)
- Transition timing: `transition-colors` for color changes, 150-200ms
- Auto-open cart drawer on add-to-cart
- Error messages clear when user starts correcting
- Button loading states with spinner
- Auto-rotate 3D models with pause on interaction
- Quantity controls disabled at boundaries (can't go below 1)
- Mobile nav smooth collapse/expand animation

**Red flags:**

- No hover feedback on clickable elements
- Abrupt state changes (no transitions)
- Cart requires manual opening after add
- Errors persist after correction
- No visual feedback during async operations

### 10. Conversion Optimization (E-commerce)

**Check for:**

- Trust badges near payment (secure checkout, return policy)
- Social proof (reviews, "X people bought this")
- Clear CTA hierarchy (one primary CTA per section)
- Guest checkout option
- Shipping estimates visible before checkout
- Progress indicator in checkout flow
- Free shipping threshold communicated
- Product page: image, price, CTA above the fold
- Community/mission storytelling (builds brand connection)

**Red flags:**

- No trust signals near payment
- Multiple competing CTAs
- No guest checkout
- Shipping cost surprise at checkout
- Product pages that require scrolling to see price

## Review Checklist Template

```markdown
## Design Review: [Page/Component Name]

### Typography

- [ ] Display vs body fonts properly applied
- [ ] Heading hierarchy is clear and consistent
- [ ] Font loading optimized (preload, swap)

### Color

- [ ] All colors use design tokens
- [ ] Contrast ratios meet WCAG AA
- [ ] Semantic color usage (not decorative)

### Spacing

- [ ] Consistent spacing scale used
- [ ] Responsive padding increases with viewport
- [ ] Adequate breathing room between sections

### Dark Mode

- [ ] CSS variables properly overridden
- [ ] Text readable on dark backgrounds
- [ ] No white-on-black harshness

### Components

- [ ] Button hierarchy clear (primary/secondary/ghost)
- [ ] Input fields have labels, errors, focus states
- [ ] Loading skeletons for async content
- [ ] Empty states with helpful messaging

### Accessibility

- [ ] Skip-to-content link present
- [ ] Focus styles visible
- [ ] ARIA labels on icon buttons
- [ ] Screen reader announcements for dynamic changes
- [ ] Keyboard navigation works

### Responsive

- [ ] Works at 375px (mobile) and 1280px+ (desktop)
- [ ] Touch targets 44px minimum
- [ ] No horizontal overflow
- [ ] Mobile navigation present

### Performance

- [ ] Skeleton loaders, not spinners
- [ ] Images optimized (AVIF/WebP, responsive)
- [ ] Heavy deps loaded on demand
- [ ] No layout shift

### Polish

- [ ] Hover states on interactive elements
- [ ] Smooth transitions (150-200ms)
- [ ] Button loading states
- [ ] Error messages clear on input

### Conversion (E-commerce)

- [ ] Trust badges present
- [ ] CTA hierarchy clear
- [ ] Social proof visible
- [ ] Shipping/returns info accessible
```

## Common Anti-Patterns

1. **The AI Aesthetic**: Generic gradient backgrounds, oversized hero text, stock photo placeholder, lack of brand personality. Every site looks the same.
2. **Decoration over information**: Colors, icons, and ornaments that don't encode meaning. Every element should answer "what does this help the user understand?"
3. **Inconsistent token usage**: Brand colors defined in one place but hardcoded hex values throughout components.
4. **Mobile as afterthought**: Desktop-first designs that get "responsive" treatment by shrinking everything.
5. **Missing states**: No loading, empty, or error states — the happy path is designed, but edge cases are ignored.
6. **Contrast failures**: Light gray text on white backgrounds. Dark text on dark mode surfaces.
7. **Font soup**: 3+ font families, 4+ weights, no clear hierarchy.
8. **Transition-free interactions**: Elements appear/disappear instantly with no animation.
