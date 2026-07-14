---
name: pr-consolidate
description: |
  Consolidate multiple PRs or branches into a unified, conflict-free integration branch.
  Use when combining multiple pull requests, integrating dependent branches, merging agent branches, or preparing one branch from several related PRs.
---

# PR Consolidate

Use this skill to merge multiple pull requests or branches into a unified integration branch while preserving all work and handling conflicts safely.

## Input Format

Accept PR numbers, PR URLs, or branch names. Optional flags:

- `--target <branch>`: specify the target branch.
- `--dry-run`: preview validation, target choice, merge order, and expected commands without making changes.

Examples:

```text
#123 #456 --target integration/auth-stack
feature/login-ui feature/api-auth --dry-run
```

## Use Cases

- Overlapping PRs: two PRs with similar scope should become one branch.
- Dependent PRs: one PR depends on another and needs unified review.
- Agent branches: multiple agents worked on related branches and their work must be merged.

## Safety Rules

- Never force push or modify remote branches without explicit confirmation.
- Preserve all work; combine changes instead of discarding one side.
- Create a backup branch before risky merges.
- Use `--no-commit` so each merge can be inspected before committing.
- Fail safe: if conflict intent is unclear, stop and ask.

## Target Determination

```text
IF --target specified:
    Use specified target.
ELSE IF on protected branch (main/master/develop):
    Create integration/{source-summary}-{timestamp}.
ELSE:
    Use current branch as target.
```

## Process

1. Parse user input into PR sources, branch sources, optional target branch, and dry-run mode.
2. Validate sources:
   - Check for uncommitted work.
   - Fetch source branches.
   - Read PR metadata for PR sources.
   - Create a backup branch for the current state.
3. Determine target branch using the rules above.
4. In dry-run mode, print the planned commands and stop before changing branches.
5. Checkout or create the target branch.
6. Merge each source sequentially with `git merge {branch} --no-commit`.
7. Resolve conflicts by combining intent, then stage resolved files.
8. Run relevant tests, linters, and type checks for the integrated branch.
9. Prepare a consolidated commit message with all integrated sources and `Closes #N` references.
10. Present results for user review before pushing or opening/updating any PR.

## Consolidation Procedure

```bash
# Fetch PR branches
git fetch origin pull/123/head:pr-123
git fetch origin pull/456/head:pr-456

# Inspect PR metadata
gh pr view 123 --json number,title,headRefName
gh pr view 456 --json number,title,headRefName

# Create a backup of the current state
git branch backup/pr-consolidate-YYYYMMDD-HHMMSS

# Create an integration branch when needed
git checkout -b integration/feature-combined

# Merge each source without auto-committing
git merge pr-123 --no-commit -m "Integrate PR #123"
git merge pr-456 --no-commit -m "Integrate PR #456"

# List conflicts if a merge stops
git diff --name-only --diff-filter=U

# After resolving files, stage them
git add path/to/resolved-file

# Commit the integration
git commit -m "Consolidate: Feature X

This branch integrates:
- PR #123: Add authentication
- PR #456: Add login UI

Closes #123
Closes #456"
```

## Conflict Resolution Strategy

1. Identify the conflict type:
   - Both sides add to the same location: combine additions.
   - Both sides modify the same code: understand both intents and merge the logic.
   - Dependency version conflicts: usually use the higher compatible version, then test.
2. Preserve all work unless the user explicitly says one side should be discarded.
3. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) after editing.
4. Stage each resolved file with `git add {file}`.
5. Run verification after resolution.
6. If stuck or the merge is wrong, abort with `git merge --abort` before trying another approach.

## Quick Reference

| Task | Command |
| --- | --- |
| Fetch PR branch | `git fetch origin pull/{n}/head:{local-branch}` |
| View PR metadata | `gh pr view {n} --json number,title,headRefName` |
| Create backup branch | `git branch backup/pr-consolidate-{timestamp}` |
| Create integration branch | `git checkout -b integration/{summary}-{timestamp}` |
| Merge without auto-commit | `git merge {branch} --no-commit` |
| List conflict files | `git diff --name-only --diff-filter=U` |
| Stage resolved file | `git add {file}` |
| Abort merge | `git merge --abort` |

## Output Format

````markdown
## Integration Summary

### Sources Integrated

| Source | Type | Title/Description | Status |
| ------ | ---- | ----------------- | ------ |
| #123 | PR | "Add feature" | ✅ Merged |

### Target Branch

`integration/combined-features`

### Conflicts Resolved

| File | Resolution |
| ---- | ---------- |
| `src/file.ts` | Combined implementations |

### Verification Results

- [ ] Tests passing
- [ ] Linter passing

### Prepared Commit Message

```text
Consolidate: Feature integration

Closes #123
Closes #456
```

---

**Ready to proceed?**
````

## Guidelines

- Never force push without explicit confirmation.
- Preserve all work; combine, do not discard.
- Fail safe: if unsure about conflict resolution, ask.
- Prefer a deterministic merge order, such as dependency-first or oldest PR first.
- Write descriptive commit messages listing every integrated source.
- Include `Closes #N` for each PR being consolidated when the consolidated branch supersedes those PRs.

## Error Handling

### Merge Conflicts

1. List conflicts: `git diff --name-only --diff-filter=U`.
2. Open each file and look for conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
3. Resolve by editing to combine both changes.
4. Stage resolved files: `git add {file}`.
5. Run relevant tests and linters.
6. If stuck, abort: `git merge --abort`.

### Dirty Working Tree

- Stop before merging.
- Ask whether to commit, stash, or create a backup branch if user confirmation is available.
- In autonomous contexts, avoid destructive cleanup; report the blocker.

### Source Branch Missing

- Refresh remotes with `git fetch --all --prune`.
- For PRs, retry `git fetch origin pull/{n}/head:{local-branch}`.
- Verify PR existence with `gh pr view {n} --json number,title,headRefName`.

## User Input

```text
$ARGUMENTS
```
