# Plan: public webhooks v1 (for approval)

Owner's words: "Partners want to be told when an order changes so they can stop polling us."

## Workstreams, all starting Monday in parallel

1. **webhook-core:** deliver events to partner URLs. Event names follow our table names, for
   example `order_tbl.updated` and `order_line_tbl.inserted`. The payload is the changed database
   row serialised as JSON, internal columns included. "We'll finalise the payload shape during
   implementation."
2. **partner-sdk:** TypeScript and Python SDKs that parse webhook payloads, published to npm and
   PyPI at the end of week 1.
3. **docs:** public reference docs for every event.
4. **retries:** retry a failed delivery 3 times.

Versioning: none for v1. "We can add it later if needed."

## Acceptance

- Partners receive events.
