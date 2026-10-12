Title: **Add `--since` filtering for incremental CSV exports**

The command below includes the PR body. Before running it, run the required `pytest` check and push `feature/export-since`; neither has been done in this session.

```bash
gh pr create \
  --base main \
  --head feature/export-since \
  --title 'Add --since filtering for incremental CSV exports' \
  --body-file - <<'EOF'
Nightly sync currently re-exports every reading. Add `tidewater export --since` so callers can pass the newest previously loaded `taken_at` and export only readings strictly after that instant, excluding the boundary to avoid duplicate readings.

Accept ISO 8601 timestamps with Z or an explicit offset, and reject timestamps without timezone information. Add the optional `since` argument to `export_readings` and document CLI usage. Exports without `--since` retain their existing behavior.

Tests added cover cutoff filtering, rejection of naive timestamps, and Z-suffix parsing. Tests, linters, and builds have not been run in this session; CI has not run on this branch.

Closes #57.

Risk: low — Filtering is opt-in and preserves existing export behavior when no cutoff is supplied.
EOF
```