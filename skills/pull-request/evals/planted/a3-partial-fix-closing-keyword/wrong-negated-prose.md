refactor(store): build readings queries in one place

Groundwork for #88: moves every readings query into one builder. On its own this does not fix #88; the follow-up PR applies `--since` in SQL.

- `ReadingQuery` builds the SQL and parameters for the station filter.
- `load_readings` uses it, so the station is a bound parameter.
- `tests/test_reading_query.py` pins the SQL.

Validation: `pytest`: 21 passed.

Risk: low - no behaviour change.
===

```bash
git push -u origin refactor/reading-query
gh pr create --base main --title "refactor(store): build readings queries in one place" --body-file pr-body.md
```
