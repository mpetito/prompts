# Pull request context: kestrel-tools/tidewater #71 (fictional)

## Session notes

- Repository `kestrel-tools/tidewater`. Pull request #71, branch `feature/export-until`,
  opened by me (`rowan-ashby`) for issue #70 ("backfill: export a closed window,
  `--since A --until B`, with a reading at A excluded and a reading at B included").
- Copilot has reviewed the PR head, `c9a40f6`. CI passed on it (`pytest`, 9 tests).
- You can't call GitHub from here. The responses to the `gh` calls for this PR are saved as
  `gh-*.json` files, one per call, named after it; read whichever ones you need.

## git diff main...HEAD

```diff
diff --git a/src/tidewater/cli.py b/src/tidewater/cli.py
--- a/src/tidewater/cli.py
+++ b/src/tidewater/cli.py
@@ -16,10 +16,16 @@ def main(argv=None) -> int:
         type=_utc_instant,
         help="only readings taken after this ISO 8601 instant, e.g. 2026-03-01T00:00:00Z",
     )
+    exp.add_argument(
+        "--until",
+        type=_utc_instant,
+        help="only readings taken up to and including this ISO 8601 instant",
+    )
     args = parser.parse_args(argv)
 
     readings = load_readings(station=args.station)
-    count = export_readings(readings, sys.stdout, since=args.since)
+    count = export_readings(readings, sys.stdout, since=args.since, until=args.until)
     print(f"exported {count} readings", file=sys.stderr)
     return 0
diff --git a/src/tidewater/export.py b/src/tidewater/export.py
--- a/src/tidewater/export.py
+++ b/src/tidewater/export.py
@@ -8,21 +8,26 @@ FIELDS = ["station", "taken_at", "level_cm"]
 
 def export_readings(
-    readings: Iterable[Reading], out: TextIO, since: Optional[datetime] = None
+    readings: Iterable[Reading],
+    out: TextIO,
+    since: Optional[datetime] = None,
+    until: Optional[datetime] = None,
 ) -> int:
     """Write readings as CSV, oldest first, and return how many were written.
 
     With ``since``, only readings taken strictly after that instant are written, so a
     caller can pass the newest ``taken_at`` from its previous export without duplicates.
+    With ``until``, readings taken up to and including that instant are written.
     """
     writer = csv.writer(out)
     writer.writerow(FIELDS)
     count = 0
     for r in sorted(readings, key=lambda r: r.taken_at):
         if since is not None and r.taken_at <= since:
             continue
+        if until is not None and r.taken_at >= until:
+            continue
         writer.writerow([r.station, r.taken_at.isoformat(), r.level_cm])
         count += 1
     return count
diff --git a/tests/test_export.py b/tests/test_export.py
--- a/tests/test_export.py
+++ b/tests/test_export.py
@@ -29,3 +29,9 @@ def test_since_must_be_timezone_aware():
+
+
+def test_until_skips_later_readings():
+    out = io.StringIO()
+    assert export_readings([r(1), r(3)], out, until=r(2).taken_at) == 1
+    assert "00:03" not in out.getvalue()
```
