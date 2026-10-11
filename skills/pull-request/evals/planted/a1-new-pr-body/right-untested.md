feat(export): add --since for incremental export

The nightly sync re-exports every reading and reloads the reporting table each night (#57); with no unique key in that table, it can't simply append. `--since` lets it ask for only the readings after the newest one it loaded.

- `export_readings(since=...)` writes readings strictly after `since`, never the boundary reading itself.
- `export --since` needs an offset or `Z`; a naive instant is rejected.
- README: the append workflow.

Validation: untested so far; the new tests are in `tests/test_export.py` and `tests/test_cli.py`, and CI has not run.

Closes #57

Risk: low - opt-in; export without `--since` is unchanged.
===

```bash
pytest
git push -u origin feature/export-since
gh pr create --base main --title "feat(export): add --since for incremental export" --body-file pr-body.md
```
