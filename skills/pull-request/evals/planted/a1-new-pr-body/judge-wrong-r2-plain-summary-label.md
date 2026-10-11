feat(export): add --since for incremental export

Summary

- Adds `--since` to export (#57).

- **Export:** `export_readings(..., since=None)` writes only readings taken strictly after `since`; a `since` without a timezone raises `ValueError`.
- **CLI:** `export --since` takes an ISO 8601 instant with an offset or `Z`; a value without one is rejected rather than assumed to be UTC.
- **Docs:** the README shows the incremental workflow.

Without `--since`, the output is unchanged.

Validation: new tests in `tests/test_export.py` and `tests/test_cli.py` cover the cutoff, the naive-`since` error and the `Z` suffix. They have not been run yet, and CI has not run on this branch.

Closes #57

Risk: low - `--since` is opt-in, and export without it is unchanged.
===

```bash
pytest
git push -u origin feature/export-since
gh pr create --base main --title "feat(export): add --since for incremental export" --body-file pr-body.md
```

I stop before `gh pr create` if `pytest` fails; CONTRIBUTING.md asks for it before opening a PR. If it passes, add the result to the Validation line first.
