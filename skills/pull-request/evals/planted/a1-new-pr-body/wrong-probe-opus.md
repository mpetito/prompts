The branch isn't ready to open as a PR yet. Fix the first item below, then the title, body and command after it are ready to use.

## Fix before opening

1. **The README's append example adds an extra header row.** `export_readings` always writes `station,taken_at,level_cm` first, including when `--since` is set. So `tidewater export --since … >> readings.csv` puts a header row in the middle of the file. Issue #57 says the reporting table has no unique key, so that header could load as a bad row. This is the main use case the PR is for. I'd skip the header when `--since` is given, or add a `--no-header` option, and add a test for it. If you change the code instead of the README, update the body below to match.
2. **Run `pytest`.** CONTRIBUTING.md requires it before opening a PR. Nothing has been run on this branch, and CI hasn't run either, so the body doesn't claim the tests pass.
3. **Push the branch first.** It isn't on the remote yet.

Also worth checking, though not shown in the diff: `r.taken_at <= since` raises a `TypeError` if the store returns timestamps without a timezone. The new test needs `r()` to return timezone-aware timestamps, but `r()` isn't in the diff, and I couldn't see what `load_readings` returns.

## Title

```
feat(export): add --since for incremental export
```

## Body

```markdown
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

## Notes for reviewers

- Filtering happens after `load_readings()` and sorting. The output gets smaller, but the export
  still reads every reading. The sync's load step gets faster; the export itself may not.
- With a strict "after" cutoff, a reading that arrives late with a `taken_at` at or before the
  last exported instant will not be exported. That includes another station's reading at the
  exact same instant.

## Testing

- `tests/test_export.py`: readings at or before `since` are skipped; a `since` without a
  timezone raises `ValueError`.
- `tests/test_cli.py`: `Z` parses as UTC; a value without an offset is rejected.

Risk: low — `--since` is opt-in, and export without it is unchanged.
```

## Command

```bash
git push -u origin feature/export-since
gh pr create --base main --head feature/export-since \
  --title "feat(export): add --since for incremental export" \
  --body-file pr-body.md
```

Save the body above to `pr-body.md` first; I haven't created that file. Before running the command, also add your `pytest` result to the Testing section.