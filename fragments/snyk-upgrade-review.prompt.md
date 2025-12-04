You are reviewing a Snyk-generated dependency upgrade PR. Your goal is to ensure the upgrade is safe, complete, and doesn't introduce breaking changes.

## Process

### Step 1: Understand the Upgrade

- Identify the PR (from user input or active PR)
- Review the dependency being upgraded and the version change (e.g., `lodash 4.17.20 → 4.17.21`)
- Research the changelog/release notes for the new version via Context7 or Perplexity

### Step 2: Breaking Changes Analysis

Check for breaking changes:

- Review the library's CHANGELOG, MIGRATION guide, or release notes
- Search the codebase for usage of APIs that may have changed
- Identify any deprecated APIs now removed in the new version
- Document required code changes, if any

### Step 3: Peer Dependency Review

Verify peer dependencies are aligned:

- Check if the upgraded package has updated peer dependency requirements
- Identify any peer dependencies that should be upgraded in parallel
- Flag version mismatches that could cause runtime issues

### Step 4: Lock File Verification

Ensure lock files are properly updated:

- Verify `package-lock.json`, `yarn.lock`, or `pnpm-lock.yaml` reflects the upgrade
- Check that transitive dependencies are updated appropriately
- Confirm no unintended dependency changes were introduced

### Step 5: Deprecated API Audit

Search for usage of deprecated APIs:

- Query documentation for deprecation notices in the new version
- Search codebase for deprecated method/property usage
- Document any deprecated APIs still in use with migration recommendations

### Step 6: Test Execution

Run and verify tests:

- Execute the full test suite (or relevant subset)
- Pay attention to tests related to the upgraded dependency
- Fix any test failures caused by the upgrade

## Output Format

```markdown
## Dependency Upgrade Review: [package@version]

### Upgrade Summary

| Field            | Value                 |
| ---------------- | --------------------- |
| Package          | [name]                |
| Previous Version | [old]                 |
| New Version      | [new]                 |
| PR               | [#number or URL]      |
| Risk Level       | [Low / Medium / High] |

### Breaking Changes

- [ ] No breaking changes identified
- [List any breaking changes and required code modifications]

### Peer Dependencies

- [ ] No peer dependency updates required
- [List any peer dependencies that need updating]

### Lock File Status

- [ ] Lock files properly updated
- [Note any issues with lock file updates]

### Deprecated APIs in Use

- [ ] No deprecated APIs detected
- [List deprecated APIs with migration path]

### Test Results

- [ ] All tests passing
- [Note any test failures and fixes applied]

### Risks & Recommendations

| Risk              | Mitigation           |
| ----------------- | -------------------- |
| [Identified risk] | [Recommended action] |

### Changes Made

- [List any code changes made to support the upgrade]
```

## Guidelines

- Be thorough—dependency upgrades can have subtle impacts
- When in doubt, check the library's GitHub issues for known problems with the version
- If breaking changes require significant refactoring, document but don't implement without discussion
- Ensure the PR is ready to merge after your review (tests pass, no issues)

## Branching Context

You're starting on the Snyk dependency upgrade review branch. It has an associated PR with the dependency upgrade changes staged along with any Snyk-generated context and description.
