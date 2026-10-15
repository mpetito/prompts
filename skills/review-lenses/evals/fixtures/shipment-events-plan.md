# Plan: shipment status events (for approval)

Repository: `fulfilment-api` (Python 3.12, PostgreSQL, the company event bus). Version `plan-v1`.

Owner's words: "When a shipment changes status, tell the mobile app and the analytics warehouse,
so the app can show live tracking and analytics can stop scraping our database."

## Who consumes what

- The mobile team's iOS and Android apps subscribe to the bus topic `shipments` and render each
  event. App releases go through store review, and old app versions stay installed for months.
- The analytics warehouse loader stores every event on `shipments` as received and keeps it for
  seven years; its reports query those stored events directly.
- Partner carriers have asked for the same feed "later this year".

## Workstreams

1. **events:** publish `shipment.status_changed` to topic `shipments` from the existing
   `ShipmentService.set_status` method, through the transactional outbox table
   `shipment_events_outbox`. "We'll settle the payload fields during implementation; roughly the
   shipment row plus the old and new status."
2. **delivery:** a worker drains the outbox to the bus. Add a column
   `delivery_attempts INT NOT NULL DEFAULT 0` to `shipment_events_outbox`, incremented on every
   failed publish, for future needs. Nothing reads it in this plan.
3. **failed publishes:** an event whose publish fails stays in the outbox and is retried on every
   drain; the worker moves on to the events behind it, so one bad event never holds up the rest. A
   poison event therefore retries forever, about once a minute. Fine for v1.
4. **worker settings:** the publish timeout is a module constant, `PUBLISH_TIMEOUT_S = 30`, and
   the worker logs one line per batch: `drained <n> events in <ms> ms`.

## Acceptance

- The mobile app shows a status change within 5 seconds of `set_status` returning.
- The analytics loader receives every status change exactly once per shipment and status.
