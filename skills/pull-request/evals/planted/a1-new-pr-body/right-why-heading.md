feat(export): add --since for incremental export

## Why

The nightly sync re-exports every reading and reloads the whole reporting table (#57). It only needs the readings since its last run, and since the table has no unique key, a reading exported twice is counted twice.

## Changes

- `export_readings` takes `since` and writes only readings strictly after it, so the boundary reading is never repeated.
- `export --since` accepts an instant with an offset or `Z` and rejects one without.
- The README shows the append workflow.

## Validation

New tests cover the cutoff and the parsing. Not run yet: `pytest`, and CI has not run on this branch.

Closes #57

Risk: low - opt-in flag; export without it is unchanged.
===

```bash
pytest
git push -u origin feature/export-since
gh pr create --base main --title "feat(export): add --since for incremental export" --body-file pr-body.md
```

Stop if `pytest` fails.
