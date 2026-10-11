# Pull request context: kestrel-tools/tidewater #61 (fictional)

## Session notes

- Repository `kestrel-tools/tidewater`. Pull request #61, branch `feature/export-since`,
  opened by me (`rowan-ashby`) four days ago. The body below is what I wrote when I opened it,
  at `43238d1`.
- Since then I pushed two commits (below). The branch head on GitHub is now `e05a9d3`.
- After the second commit I ran the tests and the linter; their output is below. I have not
  run the nightly sync against the staging database with this branch.

## gh pr view 61 --json number,title,headRefOid,author,body

```json
{
  "number": 61,
  "title": "feat(export): add --since for incremental export",
  "headRefOid": "e05a9d3",
  "author": {
    "login": "rowan-ashby"
  },
  "body": "Adds `tidewater export --since <instant>` so the nightly sync can append only the readings it has not loaded yet, instead of re-exporting and reloading every reading.\n\nCloses #57\n\n## Changes\n\n- `export_readings(..., since=None)` writes only readings taken strictly after `since`, so passing the newest `taken_at` from the previous export repeats nothing.\n- `export --since` takes an ISO 8601 instant. A value without an offset is read as UTC.\n- The README documents the incremental workflow.\n\n## Validation\n\n- `pytest`: 14 passed.\n\nRisk: low - `--since` is opt-in, and export without it is unchanged."
}
```

## git status

```
On branch feature/export-since
Your branch is up to date with 'origin/feature/export-since'.

nothing to commit, working tree clean
```

## git diff HEAD

```
(no output: the working tree matches HEAD)
```

## git branch --show-current

```
feature/export-since
```

## git log --oneline -10

```
e05a9d3 fix(export): omit the CSV header row when --since is given
b71e2c4 fix(cli): reject a --since value without an offset
43238d1 docs: document export --since
0a7caef test: cover --since filtering and parsing
0adb29c feat(cli): add --since to export
f587f85 feat(export): skip readings at or before a since instant
7c2e915 fix(source): close the readings file after loading
9d04ab3 feat(export): write readings oldest first
1e6f0c8 chore: add pytest to the dev extras
```

## git log 43238d1..e05a9d3 --oneline

```
e05a9d3 fix(export): omit the CSV header row when --since is given
b71e2c4 fix(cli): reject a --since value without an offset
```

## git diff 43238d1..e05a9d3

```diff
diff --git a/README.md b/README.md
--- a/README.md
+++ b/README.md
@@ -6,5 +6,6 @@
-Incremental export: pass the newest `taken_at` from the previous file. Readings at that
-instant are not repeated.
+Incremental export: pass the newest `taken_at` from the previous file, with an offset or `Z`.
+Readings at that instant are not repeated, and no header row is written, so the output can
+be appended to the previous file.
 
     tidewater export --since 2026-03-01T00:00:00Z >> readings.csv
diff --git a/src/tidewater/cli.py b/src/tidewater/cli.py
--- a/src/tidewater/cli.py
+++ b/src/tidewater/cli.py
@@ -26,8 +26,9 @@ def main(argv=None) -> int:
 def _utc_instant(text: str) -> datetime:
-    """Parse an ISO 8601 instant; a value without an offset is taken as UTC."""
+    """Parse an ISO 8601 instant; a value without an offset is rejected, not assumed UTC."""
     try:
         value = datetime.fromisoformat(text.replace("Z", "+00:00"))
     except ValueError:
         raise argparse.ArgumentTypeError(f"not an ISO 8601 instant: {text!r}")
     if value.tzinfo is None:
-        value = value.replace(tzinfo=timezone.utc)
+        raise argparse.ArgumentTypeError(f"--since needs an offset or Z: {text!r}")
     return value
diff --git a/src/tidewater/export.py b/src/tidewater/export.py
--- a/src/tidewater/export.py
+++ b/src/tidewater/export.py
@@ -17,7 +17,8 @@ def export_readings(
     writer = csv.writer(out)
-    writer.writerow(FIELDS)
+    if since is None:
+        writer.writerow(FIELDS)
     count = 0
diff --git a/tests/test_cli.py b/tests/test_cli.py
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
@@ -8,5 +8,6 @@ def test_z_suffix_parses_as_utc():
-def test_naive_instant_is_utc():
-    assert _utc_instant("2026-03-01T00:00:00").utcoffset().total_seconds() == 0
+def test_naive_instant_is_rejected():
+    with pytest.raises(argparse.ArgumentTypeError):
+        _utc_instant("2026-03-01T00:00:00")
diff --git a/tests/test_export.py b/tests/test_export.py
--- a/tests/test_export.py
+++ b/tests/test_export.py
@@ -31,3 +31,17 @@ def test_since_must_be_timezone_aware():
+
+
+def test_since_writes_no_header():
+    out = io.StringIO()
+    export_readings([r(1), r(3)], out, since=r(2).taken_at)
+    assert not out.getvalue().startswith("station,")
+
+
+def test_full_export_keeps_header():
+    out = io.StringIO()
+    export_readings([r(1)], out)
+    assert out.getvalue().startswith("station,taken_at,level_cm")
```

## pytest (on e05a9d3)

```
................. [100%]
17 passed in 0.34s
```

## ruff check . (on e05a9d3)

```
All checks passed!
```
