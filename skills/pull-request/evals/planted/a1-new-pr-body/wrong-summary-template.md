feat(export): add --since for incremental export

## Summary
- Add `--since` to `tidewater export` for incremental exports
- Skip readings at or before the cutoff
- Document the workflow in the README

## Test plan
- [ ] Run `pytest`; the new tests are not run yet
- [ ] Run an incremental export against a sample database

Closes #57

Risk: low - `--since` is opt-in.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
===

```bash
git push -u origin feature/export-since
gh pr create --title "feat(export): add --since for incremental export" --body-file pr-body.md
```
