feat(export): add --since for incremental export

Adds `tidewater export --since <instant>` so the nightly sync can append only the readings it has not loaded yet, instead of re-exporting and reloading every reading.

Closes #57

## Changes

- `export_readings(..., since=None)` writes only readings taken strictly after `since`, so passing the newest `taken_at` from the previous export repeats nothing.
- `export --since` takes an ISO 8601 instant. A value without an offset is read as UTC.
- The README documents the incremental workflow.

## Validation

- `pytest`: 14 passed.

## Update

- `--since` now rejects a value without an offset.
- No header row is written when `--since` is given.
- `pytest` on e05a9d3: 17 passed; `ruff check .` clean.

Risk: low - `--since` is opt-in, and export without it is unchanged.
===

```bash
gh pr edit 61 --body-file pr-body.md
```
