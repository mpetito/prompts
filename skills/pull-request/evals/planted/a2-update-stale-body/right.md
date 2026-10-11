feat(export): add --since for incremental export

Adds `tidewater export --since <instant>` so the nightly sync can append only the readings it has not loaded yet, instead of re-exporting and reloading every reading.

Closes #57

## Changes

- `export_readings(..., since=None)` writes only readings taken strictly after `since`, so passing the newest `taken_at` from the previous export repeats nothing. With `since` it writes no CSV header row, so the output can be appended to the previous file.
- `export --since` takes an ISO 8601 instant with an offset or `Z`; a value without an offset is rejected.
- The README documents the incremental workflow, including the append.

## Validation

- `pytest` on e05a9d3: 17 passed.
- `ruff check .`: all checks passed.
- Not run: the nightly sync against the staging database.

Risk: low - `--since` is opt-in, and export without it is unchanged.
===

```bash
gh pr edit 61 --body-file pr-body.md
```

I stop after the edit; the title still fits.
