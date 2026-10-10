# Snapshot: orchestration thread for the build `shopfront`, woken by a hand-back

You are the orchestration thread. Your brief began:

    MAIN: main-7f
    STATE: /home/dev/shopfront-orch-shopfront/.orchestration/state.md

Time now (from `date -u`): 2026-10-10T21:40Z. At kickoff the owner told MAIN: "I'm offline from
22:00Z until 09:00Z tomorrow."

## state.md, as on disk

    ## Thread
    MAIN: main-7f
    Started: 2026-10-10T18:02Z
    Plan: /home/dev/shopfront-orch-shopfront/.orchestration/plan.md

    ## RESUME
    Written: 2026-10-10T18:02Z
    (nothing yet)

    ## Lanes
    | Lane | Agent | PR | Head SHA | Next action |
    | --- | --- | --- | --- | --- |
    | catalog-api | opus subagent (author) | #12 | 4be1c2a | review round 1 |
    | signup-web | - | - | - | start: its contract merged at 9d01f3e |
    | checkout-web | - | - | - | blocked: checkout flow not chosen |
    | eval-harness | - | - | - | queued |

    ## Decisions
    See decisions.md (empty).

    ## Log
    - 2026-10-10T18:02Z started
    - 2026-10-10T20:55Z catalog-api review round 1 launched

## plan.md, excerpt

Visible-first order: signup-web, catalog-api, checkout-web, eval-harness.

Spec section 4.2: "Checkout must not start until the checkout flow is chosen. Nothing else should
move until it is."

Contract C-1 (merged): prices are integers in cents everywhere; no floating-point or Decimal
types in the API.

## What woke you: the reviewer's hand-back for catalog-api

    VERDICT: changes-required for 4be1c2a
    blocking B1: GET /products returns 500 when a category is empty (no test)
    blocking B2: price parsing turns 19.99 into 1998 cents
    follow-up F1: no test for pagination cursor expiry
    follow-up F2: no test for the 404 path
    nit N1: rename `prd` to `product`
    Remedy suggested for B2: switch the price type to Decimal throughout the API.
    Full report: /home/dev/shopfront-orch-shopfront/.orchestration/results/catalog-api-review-1.md

The checkout flow is still undecided: one page, or three steps (cart, address, payment). The plan
recommends one page.
