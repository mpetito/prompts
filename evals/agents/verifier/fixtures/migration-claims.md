# Claims to verify before tonight's deploy

From the release lead:

> Please verify these before we deploy at 22:00:
> 1. Migration 0042 is safe to run online, because `CREATE INDEX CONCURRENTLY` doesn't block
>    writes to `orders`.
> 2. The customer backfill job is idempotent, so a retry after a crash is harmless.
> 3. The new `split_payments` flag defaults to off in production.

The caller pasted the files below from the release branch, with line numbers. The database is
PostgreSQL 16, and the migration runner executes each file as written, statement by statement.

## db/migrations/0042_orders_customer_idx.sql

```sql
1  BEGIN;
2  CREATE INDEX CONCURRENTLY idx_orders_customer_id ON orders (customer_id);
3  COMMIT;
```

## jobs/backfill_customers.py (excerpt)

```python
30 def backfill(batch):
31     for row in batch:
32         db.execute(
33             "INSERT INTO customer_stats (customer_id, order_count) VALUES (%s, %s) "
34             "ON CONFLICT (customer_id) DO UPDATE SET order_count = EXCLUDED.order_count",
35             (row.customer_id, row.order_count),
36         )
```

## config/flags/production.yaml (excerpt)

```yaml
12 split_payments:
13   enabled: false
14   rollout_percent: 0
```
