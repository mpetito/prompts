feat(export): add --since for incremental export

Adds `tidewater export --since <instant>` so the nightly sync can append only readings it has
not loaded yet, instead of re-exporting and reloading everything.

Closes #57

## What changes

- `export_readings(..., since=None)`: when `since` is set, only readings taken **strictly
  after** that instant are written. Passing the newest `taken_at` from the previous export
  therefore does not repeat it. #57 needs this because the reporting table has no unique key.
  A `since` without a timezone raises `ValueError`.
- `export --since`: accepts an ISO 8601 instant with an offset or `Z`
  (e.g. `2026-03-01T00:00:00Z`). A value without an offset is rejected rather than assumed
  to be UTC.
- README documents the incremental workflow.

Without `--since`, output is unchanged.

## Testing

- `tests/test_export.py`: readings at or before `since` are skipped; a `since` without a
  timezone raises `ValueError`.
- `tests/test_cli.py`: `Z` parses as UTC; a value without an offset is rejected.

Risk: low — `--since` is opt-in, and export without it is unchanged.
===

```bash
git push -u origin feature/export-since
gh pr create --base main --head feature/export-since \
  --title "feat(export): add --since for incremental export" \
  --body-file pr-body.md
```

Nothing has been run on this branch and CI hasn't run either, so the body doesn't claim the tests pass. Run `pytest` and add the result to the Testing section before opening.
