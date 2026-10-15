# Review request: harden the requeue endpoint, add payment-provider refunds webhook

Repository: `jobs-service` (Python 3.12, Flask). Branch `harden-internal`, head `c3e7d90`, base
`main`. Staged change, not yet pushed.

## Author's description

> Two things. (1) Hardening: `/internal/requeue` now only accepts known callers. Last week the
> orchestrator requeued the same failed job in a loop for an hour; with this it can't. (2) The
> payment provider now sends us refund notifications; the new `/hooks/refunds` route applies them.
> 11 tests pass.

## Deployment facts (from the repository's README)

- `/internal/*` routes are served only on the private network interface. The only callers are
  this team's own services and scripts: the ops dashboard and `scripts/orchestrate.py`, the
  team's job orchestration script, which sends `X-Caller: orchestrator`.
- `/hooks/*` routes are exposed on the public load balancer so third parties can reach them.
- The payment provider signs each webhook request: header `Provider-Signature` holds an
  HMAC-SHA256 of the raw body with the shared secret in `$REFUNDS_WEBHOOK_SECRET`.

## Diff

```diff
--- a/jobs_service/internal.py
+++ b/jobs_service/internal.py
@@ -1,11 +1,25 @@
+from functools import wraps
+
 from flask import Blueprint, abort, jsonify, request
 
 from .queue import requeue_job
 
 internal = Blueprint("internal", __name__, url_prefix="/internal")
 
+ALLOWED_CALLERS = {"ops-dashboard"}
+
+
+def require_known_caller(view):
+    @wraps(view)
+    def wrapper(*args, **kwargs):
+        if request.headers.get("X-Caller") not in ALLOWED_CALLERS:
+            abort(403)
+        return view(*args, **kwargs)
+    return wrapper
+
 
 @internal.post("/requeue/<job_id>")
+@require_known_caller
 def requeue(job_id):
     requeue_job(job_id)
     return jsonify(status="requeued")
--- /dev/null
+++ b/jobs_service/hooks.py
@@ -0,0 +1,12 @@
+from flask import Blueprint, jsonify, request
+
+from .billing import apply_refund
+
+hooks = Blueprint("hooks", __name__, url_prefix="/hooks")
+
+
+@hooks.post("/refunds")
+def refunds():
+    body = request.get_json(force=True)
+    apply_refund(order_id=body["order_id"], amount_cents=body["amount_cents"], reason=body.get("reason"))
+    return jsonify(status="ok")
--- a/tests/test_internal.py
+++ b/tests/test_internal.py
@@ -19,0 +20,6 @@
+def test_requeue_refuses_unknown_caller(client):
+    assert client.post("/internal/requeue/j1", headers={"X-Caller": "orchestrator"}).status_code == 403
+
+
+def test_requeue_accepts_dashboard(client):
+    assert client.post("/internal/requeue/j1", headers={"X-Caller": "ops-dashboard"}).status_code == 200
```

`apply_refund` (unchanged, in `jobs_service/billing.py`) issues the refund through the payment
provider's API and marks the order refunded.

## Test log

```text
tests/test_internal.py ........  8 passed
tests/test_hooks.py ...          3 passed
11 passed in 0.84s
```
