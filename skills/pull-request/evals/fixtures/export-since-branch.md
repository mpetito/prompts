# Branch context: kestrel-tools/tidewater, feature/export-since (fictional)

## Session notes

- Repository `kestrel-tools/tidewater`, base branch `main`, current branch `feature/export-since`
  (4 commits ahead of `main`, not yet pushed; no pull request exists yet).
- The branch adds tests in `tests/test_export.py` and `tests/test_cli.py`.
- No tests, linters or builds have been run in this session, and CI has not run on this branch.
- The sections below are the command outputs and files for this branch, including the
  motivating issue and `CONTRIBUTING.md` from the repository root.

## git status

```
On branch feature/export-since
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
43238d1 docs: document export --since
0a7caef test: cover --since filtering and parsing
0adb29c feat(cli): add --since to export
f587f85 feat(export): skip readings at or before a since instant
7c2e915 fix(source): close the readings file after loading
9d04ab3 feat(export): write readings oldest first
1e6f0c8 chore: add pytest to the dev extras
```

## git log main..HEAD --oneline

```
43238d1 docs: document export --since
0a7caef test: cover --since filtering and parsing
0adb29c feat(cli): add --since to export
f587f85 feat(export): skip readings at or before a since instant
```

## git diff main...HEAD --stat

```
 README.md               |  5 +++++
 src/tidewater/cli.py    | 19 ++++++++++++++++++-
 src/tidewater/export.py | 16 +++++++++++++---
 tests/test_cli.py       | 12 ++++++++++++
 tests/test_export.py    | 14 ++++++++++++++
 5 files changed, 62 insertions(+), 4 deletions(-)
```

## git diff main...HEAD

```diff
diff --git a/README.md b/README.md
index 7da5a3e..63fa681 100644
--- a/README.md
+++ b/README.md
@@ -3,3 +3,8 @@
 Export tide-gauge readings to CSV.
 
     tidewater export [--station PIER-1] > readings.csv
+
+Incremental export: pass the newest `taken_at` from the previous file. Readings at that
+instant are not repeated.
+
+    tidewater export --since 2026-03-01T00:00:00Z >> readings.csv
diff --git a/src/tidewater/cli.py b/src/tidewater/cli.py
index 034d1c0..a28131e 100644
--- a/src/tidewater/cli.py
+++ b/src/tidewater/cli.py
@@ -1,5 +1,6 @@
 import argparse
 import sys
+from datetime import datetime
 
 from .export import export_readings
 from .source import load_readings
@@ -10,9 +11,25 @@ def main(argv=None) -> int:
     sub = parser.add_subparsers(dest="command", required=True)
     exp = sub.add_parser("export", help="export readings as CSV")
     exp.add_argument("--station", help="only this station")
+    exp.add_argument(
+        "--since",
+        type=_utc_instant,
+        help="only readings taken after this ISO 8601 instant, e.g. 2026-03-01T00:00:00Z",
+    )
     args = parser.parse_args(argv)
 
     readings = load_readings(station=args.station)
-    count = export_readings(readings, sys.stdout)
+    count = export_readings(readings, sys.stdout, since=args.since)
     print(f"exported {count} readings", file=sys.stderr)
     return 0
+
+
+def _utc_instant(text: str) -> datetime:
+    """Parse an ISO 8601 instant; a value without an offset is rejected, not assumed UTC."""
+    try:
+        value = datetime.fromisoformat(text.replace("Z", "+00:00"))
+    except ValueError:
+        raise argparse.ArgumentTypeError(f"not an ISO 8601 instant: {text!r}")
+    if value.tzinfo is None:
+        raise argparse.ArgumentTypeError(f"--since needs an offset or Z: {text!r}")
+    return value
diff --git a/src/tidewater/export.py b/src/tidewater/export.py
index c914998..6c6004d 100644
--- a/src/tidewater/export.py
+++ b/src/tidewater/export.py
@@ -1,18 +1,28 @@
 import csv
 from datetime import datetime
-from typing import Iterable, TextIO
+from typing import Iterable, Optional, TextIO
 
 from .store import Reading
 
 FIELDS = ["station", "taken_at", "level_cm"]
 
 
-def export_readings(readings: Iterable[Reading], out: TextIO) -> int:
-    """Write readings as CSV, oldest first, and return how many were written."""
+def export_readings(
+    readings: Iterable[Reading], out: TextIO, since: Optional[datetime] = None
+) -> int:
+    """Write readings as CSV, oldest first, and return how many were written.
+
+    With ``since``, only readings taken strictly after that instant are written, so a
+    caller can pass the newest ``taken_at`` from its previous export without duplicates.
+    """
+    if since is not None and since.tzinfo is None:
+        raise ValueError("since must be timezone-aware")
     writer = csv.writer(out)
     writer.writerow(FIELDS)
     count = 0
     for r in sorted(readings, key=lambda r: r.taken_at):
+        if since is not None and r.taken_at <= since:
+            continue
         writer.writerow([r.station, r.taken_at.isoformat(), r.level_cm])
         count += 1
     return count
diff --git a/tests/test_cli.py b/tests/test_cli.py
new file mode 100644
index 0000000..e7f385c
--- /dev/null
+++ b/tests/test_cli.py
@@ -0,0 +1,12 @@
+import pytest
+
+from tidewater.cli import _utc_instant
+
+
+def test_z_suffix_parses_as_utc():
+    assert _utc_instant("2026-03-01T00:00:00Z").utcoffset().total_seconds() == 0
+
+
+def test_naive_instant_is_rejected():
+    with pytest.raises(Exception):
+        _utc_instant("2026-03-01T00:00:00")
diff --git a/tests/test_export.py b/tests/test_export.py
index 7881a2d..2c0f654 100644
--- a/tests/test_export.py
+++ b/tests/test_export.py
@@ -15,3 +15,17 @@ def test_writes_header_and_rows_oldest_first():
     lines = out.getvalue().splitlines()
     assert lines[0] == "station,taken_at,level_cm"
     assert "00:01" in lines[1]
+
+
+def test_since_skips_readings_at_or_before_the_instant():
+    out = io.StringIO()
+    since = r(2).taken_at
+    assert export_readings([r(1), r(2), r(3)], out, since=since) == 1
+    assert "00:03" in out.getvalue()
+
+
+def test_since_must_be_timezone_aware():
+    import pytest
+
+    with pytest.raises(ValueError):
+        export_readings([r(1)], io.StringIO(), since=datetime(2026, 3, 1))
```

## gh issue view 57

```markdown
# Issue #57: Nightly sync re-exports every reading

Opened by a harbour-operations analyst.

The nightly sync job runs `tidewater export > readings.csv` and then loads the whole file into
the reporting database. There are now about 2.1 million readings across 14 stations, the export
takes about 40 minutes, and the load step truncates and reloads the table every night.

We only need the readings taken since the previous run. If `export` could take a starting
instant, the job could pass the newest `taken_at` it already loaded and append only new rows.
Duplicates are a problem for us: the reporting table has no unique key, so a reading exported
twice is counted twice.
```

## CONTRIBUTING.md

```markdown
# Contributing to tidewater

Run `pytest` before you open a pull request.

## Pull requests

- Every pull request body ends with a `Risk:` line: `low`, `medium` or `high`, followed by one
  sentence saying why.
```
