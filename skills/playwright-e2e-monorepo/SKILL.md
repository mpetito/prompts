---
name: playwright-e2e-monorepo
description: Set up and write Playwright end-to-end tests in an npm monorepo with Page Object Model (POM) pattern. Covers playwright.config.ts with webServer for monorepo dev server, Desktop + Mobile Chrome projects, POM architecture with data-testid selectors, test patterns for e-commerce flows (cart, checkout, configurator), localStorage handling, and CI configuration. Use when writing e2e tests, setting up Playwright in a monorepo, or implementing the Page Object Model pattern.
metadata:
  author: probably-printing
  version: "1.0"
---

# Playwright E2E Testing in Monorepo

## When to Use This Skill

Use when:

- Setting up Playwright in an npm workspaces monorepo
- Writing end-to-end tests with the Page Object Model pattern
- Testing e-commerce flows (cart, checkout, configurator)
- Configuring multi-device testing (desktop + mobile)
- Handling localStorage-dependent state in tests
- Setting up CI for Playwright tests

## Project Structure

```
project-root/
├── package.json          # Root with workspace scripts
├── apps/
│   └── web/              # Next.js app
└── packages/
    └── e2e/
        ├── package.json
        ├── playwright.config.ts
        ├── pom/                    # Page Object Models
        │   ├── HomePage.ts
        │   ├── CartPage.ts
        │   ├── ConfiguratorPage.ts
        │   ├── CheckoutPage.ts
        │   ├── ProductPage.ts
        │   └── AccountPage.ts
        └── tests/                  # Test specs
            ├── homepage.spec.ts
            ├── cart.spec.ts
            ├── configurator.spec.ts
            ├── checkout.spec.ts
            ├── products.spec.ts
            ├── order-history.spec.ts
            └── auth.spec.ts
```

## Instructions

### Step 1: Package Configuration

```json
// packages/e2e/package.json
{
  "name": "@my-project/e2e",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "test": "playwright test",
    "test:ui": "playwright test --ui",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug"
  },
  "devDependencies": {
    "@playwright/test": "^1.50.0"
  }
}
```

**Root package.json scripts:**

```json
{
  "scripts": {
    "test:e2e": "npm run test --workspace=packages/e2e",
    "test:e2e:ui": "npm run test:ui --workspace=packages/e2e"
  }
}
```

### Step 2: Playwright Configuration for Monorepo

```ts
// packages/e2e/playwright.config.ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "html",

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 5"] },
    },
  ],

  webServer: {
    command: "npm run dev -w apps/web",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    cwd: "../../", // CRITICAL: relative to packages/e2e/
  },
});
```

**Key configuration points:**

- `cwd: '../../'` — runs the dev server command from the monorepo root
- `reuseExistingServer: !process.env.CI` — uses running dev server locally, starts fresh in CI
- `fullyParallel: true` — tests run concurrently for speed
- `retries: 2` in CI — flaky test mitigation
- `workers: 1` in CI — prevent resource contention
- Two projects: Desktop + Mobile ensures responsive testing

### Step 3: Page Object Model (POM) Pattern

**POM encapsulates page selectors and actions.** Tests read like user stories, selectors stay in one place.

```ts
// pom/HomePage.ts
import { type Page, type Locator } from "@playwright/test";

export class HomePage {
  readonly page: Page;
  readonly heroHeading: Locator;
  readonly shopButton: Locator;
  readonly buildBrickButton: Locator;
  readonly featuredProducts: Locator;
  readonly missionSection: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heroHeading = page.getByTestId("hero-heading");
    this.shopButton = page.getByTestId("hero-shop-button");
    this.buildBrickButton = page.getByTestId("hero-build-brick-button");
    this.featuredProducts = page.getByTestId("featured-products");
    this.missionSection = page.getByTestId("mission-section");
  }

  async goto() {
    await this.page.goto("/");
  }

  async clickShop() {
    await this.shopButton.click();
  }

  async clickBuildBrick() {
    await this.buildBrickButton.click();
  }
}
```

**Cart POM (complex interactions):**

```ts
// pom/CartPage.ts
export class CartPage {
  readonly page: Page;
  readonly cartDrawer: Locator;
  readonly cartItems: Locator;
  readonly cartButton: Locator;
  readonly cartCount: Locator;
  readonly checkoutButton: Locator;
  readonly emptyCartMessage: Locator;
  readonly clearCartButton: Locator;
  readonly cartDrawerClose: Locator;

  constructor(page: Page) {
    this.page = page;
    this.cartDrawer = page.getByTestId("cart-drawer");
    this.cartItems = page.getByTestId("cart-item");
    this.cartButton = page.getByTestId("header-cart-button");
    this.cartCount = page.getByTestId("header-cart-count");
    this.checkoutButton = page.getByRole("link", {
      name: /continue to checkout/i,
    });
    this.emptyCartMessage = page.getByText("Your cart is empty");
    this.clearCartButton = page.getByText("Clear Cart");
    this.cartDrawerClose = page.getByTestId("cart-drawer-close");
  }

  async openCartDrawer() {
    await this.cartButton.click();
  }
  async closeDrawer() {
    await this.cartDrawerClose.click();
  }
  async clearCart() {
    await this.clearCartButton.click();
  }

  async getItemCount() {
    const text = await this.cartCount.textContent();
    return parseInt(text ?? "0", 10);
  }

  async updateQuantity(index: number, qty: number) {
    const item = this.cartItems.nth(index);
    const currentQtyText = await item
      .getByTestId("cart-item-quantity")
      .textContent();
    const currentQty = parseInt(currentQtyText ?? "1", 10);

    if (qty > currentQty) {
      for (let i = 0; i < qty - currentQty; i++) {
        await item.getByTestId("cart-item-increase").click();
      }
    } else if (qty < currentQty) {
      for (let i = 0; i < currentQty - qty; i++) {
        await item.getByTestId("cart-item-decrease").click();
      }
    }
  }

  async removeItem(index: number) {
    await this.cartItems.nth(index).getByTestId("cart-item-remove").click();
  }

  async getCartItemName(index: number) {
    return this.cartItems.nth(index).locator("h3").textContent();
  }
}
```

**Configurator POM:**

```ts
// pom/ConfiguratorPage.ts
export class ConfiguratorPage {
  readonly page: Page;
  readonly configurator: Locator;
  readonly brickScene: Locator;
  readonly flagSelector: Locator;
  readonly customTextInput: Locator;
  readonly configSummary: Locator;
  readonly addToCartButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.configurator = page.getByTestId("brick-configurator");
    this.brickScene = page.getByTestId("brick-scene");
    this.flagSelector = page.getByTestId("flag-selector");
    this.customTextInput = page.getByTestId("custom-text-input");
    this.configSummary = page.getByTestId("config-summary");
    this.addToCartButton = page.getByTestId("configurator-add-to-cart");
  }

  async goto() {
    await this.page.goto("/build-your-brick");
  }
  async selectFlag(name: string) {
    await this.page.getByTestId(`flag-option-${name}`).click();
  }
  async setCustomText(text: string) {
    await this.customTextInput.fill(text);
  }
  async addToCart() {
    await this.addToCartButton.click();
  }

  getFlagOptions() {
    return this.flagSelector.locator('button[data-testid^="flag-option-"]');
  }
}
```

### Step 4: Test Patterns

**localStorage cleanup for cart isolation:**

```ts
test.describe("Shopping Cart", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => localStorage.removeItem("pp-cart"));
  });

  test("should show empty cart message", async ({ page }) => {
    const cart = new CartPage(page);
    await cart.openCartDrawer();
    await expect(cart.emptyCartMessage).toBeVisible();
  });
});
```

**Helper function for common setup:**

```ts
async function addItemToCart(page: Page) {
  await page.goto("/");
  await page.evaluate(() => localStorage.removeItem("pp-cart"));
  const configurator = new ConfiguratorPage(page);
  await configurator.goto();
  await configurator.addToCart();
  const cart = new CartPage(page);
  await cart.closeDrawer();
}
```

**Multi-step flow test:**

```ts
test("should update cart count after adding item", async ({ page }) => {
  const configurator = new ConfiguratorPage(page);
  await configurator.goto();
  await configurator.addToCart();

  const cart = new CartPage(page);
  await expect(cart.cartCount).toBeVisible();
  expect(await cart.getItemCount()).toBe(1);
});
```

**Form validation test:**

```ts
test("should show validation errors for empty required fields", async ({
  page,
}) => {
  await addItemToCart(page);
  const checkout = new CheckoutPage(page);
  await checkout.goto();
  await checkout.submitShippingForm();

  await expect(page.getByText("Name is required")).toBeVisible();
  await expect(page.getByText("Address is required")).toBeVisible();
  await expect(page.getByText("City is required")).toBeVisible();
});
```

**Error clearing test:**

```ts
test("should clear error when user starts typing", async ({ page }) => {
  await addItemToCart(page);
  const checkout = new CheckoutPage(page);
  await checkout.goto();
  await checkout.submitShippingForm();
  await expect(page.getByText("Name is required")).toBeVisible();

  await checkout.nameInput.fill("J");
  await expect(page.getByText("Name is required")).not.toBeVisible();
});
```

### Step 5: data-testid Convention

Every interactive or meaningful element gets a `data-testid`:

```
Interactive elements: {action}-{target}
  button-submit, input-email, link-profile, header-cart-button

Display elements: {type}-{content}
  text-username, badge-cart-count, status-payment

Dynamic elements: {type}-{description}-{id}
  card-product-${productId}, flag-option-${flagName}, faq-item-${index}

Component containers: {component-name}
  brick-configurator, cart-drawer, checkout-form
```

**In JSX:**

```tsx
<button data-testid="configurator-add-to-cart">Add to Cart</button>
<div data-testid="cart-drawer">...</div>
<button data-testid={`flag-option-${flag}`} aria-pressed={selected}>...</button>
<details data-testid={`faq-item-${i}`}>...</details>
```

### Step 6: Selector Priority

Use this hierarchy in POM locators:

1. **`getByTestId`** — most stable, survives content/style changes
2. **`getByRole`** — good for generic actions: `getByRole('link', { name: /checkout/i })`
3. **`getByText`** — useful for visible content: `getByText('Your cart is empty')`
4. **CSS selectors** — last resort: `locator('button[aria-pressed="true"]')`

**Avoid:** IDs, class names, tag hierarchies — all too brittle.

### Step 7: Cart Persistence Test

```ts
test("should persist cart across page reloads", async ({ page }) => {
  const configurator = new ConfiguratorPage(page);
  await configurator.goto();
  await configurator.addToCart();

  const cart = new CartPage(page);
  await cart.closeDrawer();
  await expect(cart.cartCount).toBeVisible();

  // Reload the page
  await page.reload();

  // Cart should survive (localStorage)
  await expect(cart.cartCount).toBeVisible();
  expect(await cart.getItemCount()).toBeGreaterThan(0);
});
```

## CI Configuration

**GitHub Actions:**

```yaml
name: E2E Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps chromium
      - run: npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: playwright-report
          path: packages/e2e/playwright-report/
```

## Common Pitfalls

1. **`cwd` in webServer**: Must be relative to `packages/e2e/` — use `../../` to reach monorepo root.
2. **localStorage not cleared**: Cart state bleeds between tests. Always clear in `beforeEach`.
3. **Flaky waits**: Use `expect(locator).toBeVisible()` not `waitForTimeout()`. Playwright auto-waits.
4. **Mobile-specific tests**: Some elements are hidden on mobile. Test mobile layout separately with the mobile project.
5. **Cart drawer timing**: After `addToCart()`, the drawer animates open. Wait for `expect(cart.cartDrawer).toBeVisible()` before interacting.
6. **Parallel test isolation**: Each test gets a fresh browser context, but the dev server is shared. Avoid server-side state mutations in tests.
7. **CI memory**: Use `workers: 1` in CI to prevent OOM. Playwright + Next.js dev server is memory-intensive.
8. **`reuseExistingServer`**: Set to `true` locally (fast), `false` in CI (clean state). The `!process.env.CI` pattern handles this.
