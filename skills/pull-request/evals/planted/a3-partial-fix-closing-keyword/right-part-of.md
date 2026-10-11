refactor(store): build readings queries in one place

Part of #88. The export filters `--since` in Python after reading all 2.1 million readings; this PR prepares the fix by moving every readings query into one builder. The follow-up PR moves the cutoff into SQL, and that one makes the export faster. Merging this one changes no behaviour.

- `ReadingQuery` builds the SQL text and bound parameters; today it has the station filter only.
- `load_readings` uses it, so the station is a bound parameter rather than an f-string.
- `tests/test_reading_query.py` pins the SQL and checks the rows are unchanged.

Validation: `pytest`: 21 passed. Not run: a timed export.

Risk: low - pinned SQL, unchanged results.
===

```bash
git push -u origin refactor/reading-query
gh pr create --base main --title "refactor(store): build readings queries in one place" --body-file pr-body.md
```
