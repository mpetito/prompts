---
name: upgrade
description: Review and upgrade outdated dependencies safely end-to-end
---

# Upgrade Dependencies

Safely upgrade project dependencies with research, risk assessment, and validation. This prompt references the **upgrade** skill for detailed procedures.

## Process

1. **Inventory**: Run `npm outdated` or `dotnet list package --outdated` to identify outdated packages.

2. **Classify**: Categorize by security (critical), patch (low risk), minor (medium), major (needs research).

3. **Research**: For major upgrades, check changelogs, migration guides, and GitHub issues for breaking changes.

4. **Sequence**: Order upgrades from lowest to highest risk—security patches first, majors last.

5. **Implement**: Upgrade incrementally. Apply code changes alongside each upgrade to maintain a buildable state.

6. **Validate**: After each group, run tests, linting, type checks, and security audit.

## Guidelines

- One logical change per commit—group related packages
- Always commit lockfiles with manifest changes
- Research breaking changes before major upgrades
- Use CLI for package operations, not manual manifest edits

## Boundaries

- ✅ Run full validation after upgrades
- ✅ Research breaking changes before major upgrades
- ⚠️ Ask first: Major version upgrades or framework upgrades
- 🚫 Never: Skip validation or ignore test failures
- 🚫 Never: Force-push lockfile changes without review

## Output

```markdown
## Upgrade Summary

### Upgraded

| Package | From | To  | Type | Notes |
| ------- | ---- | --- | ---- | ----- |

### Deferred

| Package | From | To  | Reason |
| ------- | ---- | --- | ------ |

### Validation

- [ ] Tests passing
- [ ] Linting passing
- [ ] Build succeeds
- [ ] No new vulnerabilities
```

Suggest `/commit` to commit changes and create/update a pull request.

## User Input

```text
$ARGUMENTS
```
