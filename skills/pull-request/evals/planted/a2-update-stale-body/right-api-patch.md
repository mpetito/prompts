feat(export): add --since for incremental export

Adds `tidewater export --since <instant>` so the nightly sync can append only the readings it has not loaded yet, instead of re-exporting and reloading every reading.

Closes #57

## Changes

- `export_readings(..., since=None)` writes only readings taken strictly after `since`, and skips the CSV header row when `since` is set, so the output appends cleanly to the previous file.
- `export --since` needs an offset or `Z`; a value without an offset is now rejected instead of being read as UTC.
- The README shows the append workflow.

## Validation

- `pytest` (e05a9d3): 17 passed.
- `ruff check .`: clean.
- Not run: a nightly sync against staging.

Risk: low - `--since` is opt-in, and export without it is unchanged.
===

```bash
gh api -X PATCH repos/kestrel-tools/tidewater/pulls/61 -F body=@pr-body.md
```

Stop after the PATCH.
