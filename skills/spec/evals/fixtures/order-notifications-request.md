# Feature request: order-status notifications

Product: Quayside, an invented grocery-delivery service with iOS and Android apps and a
.NET API. Research on the codebase is already done and summarised below.

## Request from the product manager (Jonah Pell)

> Customers want to know when their order is picked, out for delivery and delivered.
> Send them notifications for each status. Ideally the order screen updates live while
> the app is open, like the courier apps do. Respect quiet hours (no pushes between
> 22:00 and 07:00). The opt-in screen should say "We never share your data with third
> parties." Let's get it into the 3.8 release.

## Existing specs (`ls specs/`)

```
019-courier-tracking/   spec.md plan.md
020-substitutions/      spec.md plan.md
021-saved-baskets/      spec.md
022-push-tokens/        spec.md plan.md  (registers device tokens with PushRelay)
```

## Codebase research

- `services/orders/OrderStatusChanged.cs` is published on the internal event bus for every
  status change: `Placed`, `Picking`, `Picked`, `OutForDelivery`, `Delivered`, `Cancelled`.
- `services/notify/PushSender.cs` (spec 022) sends pushes through PushRelay, a third-party
  push vendor that receives device tokens and message bodies.
- There is no websocket or server-sent-events infrastructure anywhere in the platform.
  The infra team says a new realtime gateway needs an architecture review and a budget
  line; the alternative is push-only delivery plus the order screen polling every 30 s.
- The product manager has not decided between live updates in v1 or push-only with
  polling; the request above says "ideally".
- The iOS and Android teams build their notification handlers against a payload
  contract. No payload schema exists yet; both teams asked to review it before they
  start.
- Customers have a `TimeZone` on their account, but many never set it; devices report
  their own zone.
- Status events can arrive out of order when a courier app reconnects.

## Team notes

- Release 3.8 branches in five weeks. Capacity: one backend, two mobile developers.
- Privacy and consent wording is owned by the data protection officer, Mirela Hask.
- Copy for notification bodies is owned by the content team.
