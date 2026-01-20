---
name: pr-consolidate
description: Consolidate multiple PRs or branches into a unified integration branch
---

# Consolidate PRs/Branches

Merge multiple pull requests or branches into a unified, conflict-free integration branch. This prompt references the **pr-management** skill for detailed tool usage.

## Input Format

Accepts PR numbers (`#123`) or branch names (`feature-branch`). Optional flags:

- `--target <branch>`: Specify target branch
- `--dry-run`: Preview without making changes

## Process

1. **Parse Input**: Identify sources (PRs/branches), target, and mode.

2. **Validate**: Fetch source branches, check for uncommitted changes, create backup.

3. **Execute Integration**: Checkout/create target, merge each source sequentially.

4. **Resolve Conflicts**: For each conflict, analyze both sides and propose resolution.

5. **Verify**: Run tests, linters, and type checks on integrated branch.

6. **Prepare Commit**: Generate consolidated commit message with `Closes #PR` references.

7. **Present Results**: Show summary for user review before any remote operations.

## Target Determination

```
IF --target specified → Use specified target
ELSE IF on protected branch (main/master/develop) → Create integration/{source-summary}-{timestamp}
ELSE → Use current branch as target
```

## Output Format

```markdown
## Integration Summary

### Sources Integrated

| Source | Type | Title/Description | Status    |
| ------ | ---- | ----------------- | --------- |
| #123   | PR   | "Add feature"     | ✅ Merged |

### Target Branch

`integration/combined-features`

### Conflicts Resolved

| File          | Resolution               |
| ------------- | ------------------------ |
| `src/file.ts` | Combined implementations |

### Verification Results

- [ ] Tests passing
- [ ] Linter passing

### Prepared Commit Message
```

Consolidate: Feature integration

Closes #123
Closes #456

```

---
**Ready to proceed?**
```

## Guidelines

- Never force push without explicit confirmation
- Preserve all work—combine, don't discard
- Fail safe—if unsure about conflict resolution, ask

## User Input

```text
$ARGUMENTS
```
