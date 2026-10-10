# Plan: order CSV export (draft, for approval)

Owner's request, verbatim: "Let store owners download their orders as a CSV so they can do their
books."

Facts: a store has at most 20,000 orders a year (the 99th-percentile store has 6,000). The app is
a Node API on Postgres. It already has a job runner (`jobs/`) and S3 with presigned URLs.

## Workstreams

1. **export-ledger:** a new `export_requests` table recording every request with its status,
   retry count and checksum, plus a nightly job that reconciles ledger rows against S3 objects.
2. **export-worker:** a new SQS queue and a worker that renders the CSV in 5,000-row chunks,
   retries with exponential backoff up to 8 times, and sends failures to a dead-letter queue with
   an alarm. SQS guarantees exactly-once delivery, so the worker needs no idempotency handling.
3. **export-api:** `POST /exports` creates a request, `GET /exports/:id` returns its status, and
   a WebSocket pushes completion to the browser.
4. **export-ui:** a "Download orders" button that shows progress, then a link when ready.
5. **admin-dashboard:** an admin page listing every export request, with filters.

Open: whether refunded orders appear in the export has not been decided.

## Acceptance

- Exports are robust and scalable.
- The UI is responsive.
