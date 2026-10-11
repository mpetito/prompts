feat(export): add --since for incremental export

Adds `tidewater export --since <instant>` so the nightly sync can append only the readings it has not loaded yet.

Closes #57

## Changes

- `export_readings(..., since=None)` writes only readings taken strictly after `since`, and no header row when `since` is set.
- `export --since` takes an ISO 8601 instant with an offset or `Z`; a value without one is rejected.

## Validation

- `pytest`: 14 passed.
- `pytest` on e05a9d3: 17 passed.

Risk: low - `--since` is opt-in.
===

```bash
gh pr edit 61 --body-file pr-body.md
```
