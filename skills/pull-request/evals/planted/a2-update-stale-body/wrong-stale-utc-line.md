feat(export): add --since for incremental export

Adds `tidewater export --since <instant>` so the nightly sync can append only the readings it has not loaded yet.

Closes #57

## Changes

- `export_readings(..., since=None)` writes only readings taken strictly after `since`, and writes no header row when `since` is set.
- `export --since` takes an ISO 8601 instant. A value without an offset is read as UTC.
- The README documents the incremental workflow.

## Validation

- `pytest` on e05a9d3: 17 passed.
- `ruff check .`: clean.
- Not run: the nightly sync against staging.

Risk: low - `--since` is opt-in.
===

```bash
gh pr edit 61 --body-file pr-body.md
```
