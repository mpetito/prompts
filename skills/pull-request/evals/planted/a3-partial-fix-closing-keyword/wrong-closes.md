refactor(store): build readings queries in one place

Moves every readings query into `ReadingQuery`, the first step towards applying `--since` in SQL.

- `ReadingQuery` builds the SQL and parameters for the station filter.
- `load_readings` uses it, so the station is a bound parameter.
- `tests/test_reading_query.py` pins the SQL.

Validation: `pytest`: 21 passed.

Closes #88

Risk: low - no behaviour change.
===

```bash
git push -u origin refactor/reading-query
gh pr create --base main --title "refactor(store): build readings queries in one place" --body-file pr-body.md
```
