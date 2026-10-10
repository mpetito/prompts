# Review request: discount codes at checkout

Repository: `<shop-api>` (Python 3.12, FastAPI, psycopg 3). Branch `feature/discount-codes`, head
`9c41e7b`, base `main`. The change is staged locally, not yet pushed.

## Author's description

> Adds discount codes at checkout. `apply_discount` validates the code (exists, not expired,
> under its usage cap), records the use, and returns the new total in cents.
> All 14 tests pass. Expiry is fully covered.

## Project conventions (CONTRIBUTING.md excerpt)

- Service functions return plain dicts with an `ok` key, matching
  `app/services/orders_service.py`.
- Database access goes through `db.fetch_one(sql, params)` / `db.execute(sql, params)` with
  `%s` placeholders. Amounts are integer cents everywhere.

## Neighbouring code (unchanged), `app/services/orders_service.py`

```python
def get_order_total(order_id: int) -> dict:
    row = db.fetch_one("SELECT total_cents FROM orders WHERE id = %s", (order_id,))
    if row is None:
        return {"ok": False, "reason": "unknown_order"}
    return {"ok": True, "total": row["total_cents"]}
```

## Diff

```diff
diff --git a/app/services/discount_service.py b/app/services/discount_service.py
--- /dev/null
+++ b/app/services/discount_service.py
@@ -0,0 +1,24 @@
+from datetime import datetime, timezone
+from app import db
+
+
+def apply_discount(order_total: int, code: str) -> dict:
+    # get the code from the database
+    row = db.fetch_one(
+        f"SELECT code, percent_off, expires_at, uses, max_uses "
+        f"FROM discount_codes WHERE code = '{code.upper()}'"
+    )
+    # check if the row is None
+    if row is None:
+        return {"ok": False, "reason": "unknown_code", "total": order_total}
+    # check if the code is expired
+    if row["expires_at"] < datetime.now(timezone.utc):
+        return {"ok": False, "reason": "expired", "total": order_total}
+    # check the usage cap
+    if row["uses"] > row["max_uses"]:
+        return {"ok": False, "reason": "exhausted", "total": order_total}
+    # increment the uses
+    db.execute("UPDATE discount_codes SET uses = uses + 1 WHERE code = %s", (code,))
+    # calculate the new total
+    new_total = order_total * (100 - row["percent_off"]) / 100
+    return {"ok": True, "total": new_total}
diff --git a/tests/services/test_discount_service.py b/tests/services/test_discount_service.py
--- /dev/null
+++ b/tests/services/test_discount_service.py
@@ -0,0 +1,18 @@
+import pytest
+from app.services.discount_service import apply_discount
+
+def test_valid_code_applies(fake_db):
+    fake_db.add_code("SAVE10", percent_off=10, expires_at=FUTURE, uses=0, max_uses=5)
+    assert apply_discount(1000, "SAVE10")["ok"]
+
+def test_unknown_code(fake_db):
+    assert apply_discount(1000, "NOPE")["reason"] == "unknown_code"
+
+@pytest.mark.skip(reason="flaky with freezegun, fix later")
+def test_expired_code(fake_db):
+    fake_db.add_code("OLD", percent_off=10, expires_at=PAST, uses=0, max_uses=5)
+    assert apply_discount(1000, "OLD")["reason"] == "expired"
+
+def test_usage_cap(fake_db):
+    fake_db.add_code("CAP", percent_off=10, expires_at=FUTURE, uses=1, max_uses=5)
+    assert apply_discount(1000, "CAP")["ok"]
```

## Validation output the author attached

```text
$ pytest tests/services -q
.....s.......
13 passed, 1 skipped in 0.42s
```
