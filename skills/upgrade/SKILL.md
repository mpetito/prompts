---
name: upgrade
description: "Procedural knowledge for safely upgrading dependencies across ecosystems with proper research, risk assessment, and validation. Use when upgrading dependencies, updating packages, reviewing outdated libraries, or resolving security vulnerabilities."
---

# Dependency Upgrade Skill

Procedural knowledge for safely upgrading dependencies across ecosystems with proper research, risk assessment, and validation.

Per-ecosystem commands (npm, dotnet) for every phase live in
[`references/ecosystem-commands.md`](references/ecosystem-commands.md) — consult it rather than
recalling flags from memory.

## Upgrade Protocol Overview

| Phase               | Goal                                                    | Primary Output                  |
| ------------------- | ------------------------------------------------------- | ------------------------------- |
| 1. Inventory & Plan | Find outdated deps, classify by urgency, sequence them  | Prioritized upgrade sequence    |
| 2. Research & Risk  | Identify breaking changes and required code changes     | Migration steps, API changes    |
| 3. Implement        | Execute incrementally, keeping lockfiles consistent     | Applied changes, modified files |
| 4. Validation       | Prove nothing broke                                     | Test/lint/build/scan results    |

---

## Phase 1: Inventory & Plan

### Classification

| Category    | Description                | Priority             |
| ----------- | -------------------------- | -------------------- |
| Security    | CVE or known vulnerability | Critical             |
| Bug Fix     | Patch-level fixes          | High                 |
| Maintenance | Minor improvements, types  | Medium               |
| Major       | Breaking changes           | Low (needs research) |

### Constraint Checklist

Before planning upgrades, identify:

- [ ] Lockfile state (`package-lock.json`, `packages.lock.json`)
- [ ] Workspace/monorepo structure
- [ ] Engine requirements (`node` version, `.NET` version)
- [ ] Peer dependency requirements
- [ ] CI/CD compatibility requirements

### Prioritization Strategy

```text
Order upgrades by:
1. Security patches (any version) → immediate
2. Patch updates (x.x.PATCH) → low risk, batch together
3. Minor updates (x.MINOR.x) → may have new features
4. Major updates (MAJOR.x.x) → requires research first

Sequence to minimize blast radius:
- Leaf dependencies first (no dependents)
- Shared dependencies last (many dependents)
- Group related packages (e.g., @typescript-eslint/*)
```

### Inventory Output Template

```markdown
## Dependency Inventory - {date}

### Security (Critical)

| Package | Current | Target  | CVE/Advisory   |
| ------- | ------- | ------- | -------------- |
| lodash  | 4.17.15 | 4.17.21 | CVE-2021-23337 |

### Patch Updates (Low Risk)

| Package | Current | Target | Notes |
| ------- | ------- | ------ | ----- |

### Minor Updates (Medium Risk)

| Package | Current | Target | Notes |
| ------- | ------- | ------ | ----- |

### Major Updates (Needs Research)

| Package | Current | Target | Breaking Changes? |
| ------- | ------- | ------ | ----------------- |

### Constraints

- Node engine: >=18.0.0
- Peer dependencies: React 18.x required by @mui/\*
- Lockfile: package-lock.json v3
```

---

## Phase 2: Research & Risk

Research each non-trivial upgrade to identify breaking changes, migration steps, and required code modifications.

### Research Sources

1. **Official changelog/release notes** (GitHub releases, CHANGELOG.md)
2. **Migration guides** (official docs)
3. **Context7 docs** (whichever Context7 MCP tool the host exposes — see the [`research`](../research/SKILL.md) skill)
4. **npm/NuGet package page** (release history)
5. **GitHub issues** (known problems with the target version)

### Breaking Change Categories

| Type             | Impact   | Example                                     |
| ---------------- | -------- | ------------------------------------------- |
| API Removal      | High     | `deprecated function removed`               |
| Signature Change | High     | `function now requires additional param`    |
| Default Change   | Medium   | `default timeout changed from 30s to 5s`    |
| Type Change      | Medium   | `return type changed from string to object` |
| Behavior Change  | Medium   | `validation now stricter`                   |
| Peer Requirement | Low-High | `now requires React 18+`                    |

### Research Checklist Per Package

- [ ] Read release notes for all versions between current and target
- [ ] Check for a migration guide
- [ ] Search for breaking changes in the changelog
- [ ] Verify peer dependency compatibility
- [ ] Check GitHub issues for upgrade-related bugs
- [ ] Note any deprecation warnings

Then find affected call sites in the codebase — see **Phase 2** in
[`references/ecosystem-commands.md`](references/ecosystem-commands.md).

### Risk Assessment Template

```markdown
## Risk Assessment: {package} {current} → {target}

### Breaking Changes

1. `oldFunction()` removed → use `newFunction()` instead
2. Config property `timeout` renamed to `requestTimeout`

### Required Code Changes

- [ ] `src/api/client.ts`: Update function call
- [ ] `src/config.ts`: Rename config property

### Peer Dependencies

- Requires: typescript >=4.7 (current: 4.9 ✓)

### Known Issues

- Issue #1234: Memory leak in v3.0.0, fixed in v3.0.1

### Risk Level: Medium

Reason: Two API changes, well-documented migration path
```

---

## Phase 3: Implement

### Principles

1. **One logical change per commit** — group related packages
2. **Keep lockfiles in sync** — always commit lockfile with manifest
3. **Apply code changes with the upgrade** — don't leave broken intermediate states
4. **Smallest verifiable steps** — easier to bisect if issues arise

### Execution Order

```text
FOR each upgrade group (security → patch → minor → major):
    1. Create checkpoint (git stash or commit)
    2. Update package manifest(s)
    3. Update lockfile (npm install / dotnet restore)
    4. Apply required code changes
    5. Run quick validation (build + unit tests)
    6. Commit if passing, rollback if failing
```

### Commit Message Format

```text
chore(deps): upgrade <package> from <old> to <new>

- <reason for upgrade: security fix / new feature / maintenance>
- <breaking changes addressed, if any>
- <code changes made, if any>
```

---

## Phase 4: Validation

### Validation Checklist

- [ ] **Unit tests pass**
- [ ] **Integration tests pass**
- [ ] **Build succeeds**
- [ ] **Type checking passes**
- [ ] **Linting passes**
- [ ] **No new vulnerabilities**
- [ ] **App starts successfully** (manual smoke test)
- [ ] **No new IDE diagnostics** (`#problems` in VS Code, the `LSP` tool in Claude Code)

Commands per ecosystem: **Phase 4** in [`references/ecosystem-commands.md`](references/ecosystem-commands.md).

### Failure Investigation

When tests fail after an upgrade:

1. **Identify scope**: which tests fail? Related to the upgraded package?
2. **Check test assumptions**: does the test rely on old behavior?
3. **Review breaking changes**: did we miss a required code change?
4. **Isolate the upgrade**: rollback and upgrade packages one at a time
5. **Search for known issues**: check GitHub issues for the package

### Validation Report Template

```markdown
## Validation Report - {date}

### Test Results

- Unit Tests: ✓ 342 passed, 0 failed
- Integration Tests: ✓ 28 passed, 0 failed
- E2E Tests: ✓ 12 passed, 0 failed

### Static Analysis

- TypeScript: ✓ No errors
- ESLint: ✓ No errors
- Build: ✓ Success

### Security

- npm audit: ✓ 0 vulnerabilities
- Snyk: ✓ No new issues

### Manual Verification

- App starts: ✓
- Key flows tested: ✓

### Issues Found

None

### Status: PASS
```

---

## Security Considerations

### CVE Response Priority

| Severity | Response Time | Action                                  |
| -------- | ------------- | --------------------------------------- |
| Critical | Immediate     | Hotfix, bypass normal process if needed |
| High     | Same day      | Prioritize over feature work            |
| Medium   | Within sprint | Schedule in current iteration           |
| Low      | Backlog       | Track and batch with other updates      |

### Before Upgrading Security Packages

1. **Verify the vulnerability applies** — check whether your usage is affected
2. **Check for patches** — sometimes a patch exists without a major upgrade
3. **Review upgrade path** — ensure no breaking changes, or have a migration plan
4. **Test thoroughly** — security packages often have broad impact

---

## Breaking Change Handling

### Common Migration Patterns

| Pattern             | Before                      | After                            |
| ------------------- | --------------------------- | -------------------------------- |
| Renamed export      | `import { old } from 'pkg'` | `import { new } from 'pkg'`      |
| Moved to subpath    | `import x from 'pkg'`       | `import x from 'pkg/subpath'`    |
| Config restructure  | `{ option: value }`         | `{ options: { option: value } }` |
| Callback to Promise | `fn(callback)`              | `await fn()`                     |
| Class to function   | `new Client()`              | `createClient()`                 |

Codemod and search-replace commands: **Migration Automation** in
[`references/ecosystem-commands.md`](references/ecosystem-commands.md).

### When to Defer Major Upgrades

- Current version still receives security patches
- Migration guide is incomplete or unclear
- Critical deadline approaching
- Insufficient test coverage for affected areas

Document deferred upgrades:

```markdown
## Deferred: {package} {current} → {target}

**Reason**: Migration requires 2+ days, not critical
**Security**: Current version patched through {date}
**Revisit**: Next quarter or when {condition}
```

---

## File-Based Handoff

For complex upgrades spanning multiple sessions, persist each phase's output:

```text
docs/upgrades/
├── {date}-inventory.md      # Phase 1 output
├── {package}-migration.md   # Phase 2 research
├── {date}-validation.md     # Phase 4 report
└── README.md                # Upgrade history index
```

Later phases read the earlier files rather than re-deriving them. When delegating phases to
subagents, note that subagents are stateless and do not auto-load skills — embed the relevant
phase of this skill in each prompt.

---

## Error Handling

### "Peer dependency conflict"

1. Check which package requires the conflicting version
2. Verify whether a newer version of the requiring package exists
3. Use `--legacy-peer-deps` as a temporary workaround
4. Consider upgrading the requiring package first

### "Cannot find module after upgrade"

1. Clear node_modules: `rm -rf node_modules && npm install`
2. Clear build cache: `npm run clean` or delete `dist/`
3. Restart the TypeScript server in your editor
4. Check whether the import path changed in the new version

### "Type errors after upgrade"

1. Check whether the `@types/` package needs a separate update
2. Review breaking type changes in the changelog
3. TypeScript itself may need updating
4. Check for new generic parameters or stricter types

### "Tests fail after upgrade"

1. Check whether the test relies on mocked old behavior
2. Review whether assertions match new return types
3. Check for timing changes (async behavior)
4. Review snapshot updates needed

---

## Output Format

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

---

## Boundaries

- ✅ **Always**: Run full validation after upgrades
- ✅ **Always**: Keep lockfiles in sync with manifests
- ✅ **Always**: Research breaking changes before major upgrades
- ⚠️ **Ask first**: Major version upgrades
- ⚠️ **Ask first**: Upgrades with known breaking changes
- ⚠️ **Ask first**: Security patches that require major upgrades
- 🚫 **Never**: Skip validation or ignore test failures
- 🚫 **Never**: Upgrade without checking peer dependencies
- 🚫 **Never**: Force-push lockfile changes without review
