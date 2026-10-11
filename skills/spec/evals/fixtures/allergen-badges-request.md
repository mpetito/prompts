# Feature request: allergen badges on menu cards

Product: Forkline, an invented restaurant-ordering web app. Storefront is Next.js (App
Router, server-rendered); the API is ASP.NET Core. Research on the codebase is already
done and summarised below; treat it as current.

## Request from the product owner (Tamsin Reyes)

> Customers keep phoning to ask whether dishes contain nuts, gluten or dairy. Show
> allergen badges on every menu card. On phones the card already feels cramped, so the
> badges must not make that worse; match the "Menu card v3" mockup. Dishes with no nut
> ingredients should show a green badge reading "Nut-free kitchen - safe for nut
> allergies". Customers who have declared an allergy in their profile must acknowledge
> a warning before adding a dish containing that allergen to the cart. The
> acknowledgement should hold until they edit their allergy profile or empty the cart.
> Filtering the menu by allergen would be nice too, maybe later.

## Existing specs (`ls -t specs/`, most recently modified first)

```
016-menu-cards/              spec.md plan.md  (MenuCard component and grid)
018-allergen-data-import/    spec.md plan.md  (per-dish allergen flags in the menu API)
011-checkout-retry/          spec.md plan.md
017-loyalty-points/          spec.md
009-cart-persistence/        spec.md plan.md
003-auth-sessions/           spec.md plan.md
```

## Codebase research

- `apps/storefront/components/menu/MenuCard.tsx` renders photo, name, price and a "New"
  badge. The "New" badge pulses via a keyframe animation in `MenuCard.module.css`.
- `apps/storefront/components/menu/MenuGrid.tsx` lays cards out; one column below 640 px.
- `apps/storefront/lib/cart/useCart.ts` holds cart state in a reducer with actions
  `ADD_ITEM`, `REMOVE_ITEM`, `EMPTY_CART`.
- `apps/storefront/lib/profile/useProfile.ts` exposes the customer's declared allergies
  (`AllergyProfile` on the API side, `apps/api/Profile/AllergyProfile.cs`).
- `apps/api/Menu/MenuController.cs` already returns `allergens: string[]` per dish (spec
  018). Values: `nuts`, `gluten`, `dairy`, `egg`, `soy`, `shellfish`.
- The menu page renders and is readable with JavaScript disabled; adding to cart needs
  JavaScript.
- The design team checks layouts at 320, 768 and 1280 px.
- Tests: Vitest for hooks and reducers, Playwright for storefront flows.

## Team notes

- Sprint 31 starts Monday. Capacity: two frontend developers, one backend developer.
- The kitchen shares fryers between nut and non-nut dishes on weekends.
