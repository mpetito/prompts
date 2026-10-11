refactor(store): build readings queries in one place

The export still reads every reading and filters `--since` in Python, which is why it takes about 40 minutes (#88). This is the first of two PRs: it moves every readings query into one builder, so the next PR can push the `--since` cutoff into the SQL. It changes no behaviour and does not make the export faster yet.

- **Store:** `ReadingQuery` is an immutable builder; `.sql()` returns the SQL text and its parameters. It supports the station filter, the only one `load_readings` uses today.
- **Source:** `load_readings` gets its SQL from `ReadingQuery`, so the station is a bound parameter instead of an f-string. The rows returned are the same.
- **Tests:** `tests/test_reading_query.py` pins the SQL for no filter and a station filter, and checks `load_readings` returns the same readings for a 3-station fixture database.

Validation: `pytest` on the branch head: 21 passed. Not run: a timed export.

Refs #88

Risk: low - a refactor with pinned SQL and unchanged results.
===

```bash
git push -u origin refactor/reading-query
gh pr create --base main --title "refactor(store): build readings queries in one place" --body-file pr-body.md
```

I stop after `gh pr create`.
