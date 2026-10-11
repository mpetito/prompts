refactor(store): build readings queries in one place

This fixes #88 in two steps; this PR is the first. It moves every readings query into one builder so the next PR can apply the `--since` cutoff in SQL.

- `ReadingQuery` builds the SQL and parameters for the station filter.
- `load_readings` uses it, so the station is a bound parameter.
- `tests/test_reading_query.py` pins the SQL and the rows returned.

Validation: `pytest`: 21 passed. Not run: a timed export.

Risk: low - no behaviour change.
===

```bash
git push -u origin refactor/reading-query
gh pr create --base main --title "refactor(store): build readings queries in one place" --body-file pr-body.md
```
