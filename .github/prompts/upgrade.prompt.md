---
name: upgrade
description: Review and upgrade dependencies safely end-to-end
model: GPT-5.1-Codex-Max (Preview) (copilot)
agent: agent
argument-hint: List the packages or dependency areas to review (or leave blank to scan all)
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "web",
    "agent",
    "todo",
    "perplexity/*",
    "docs-context7/*",
  ]
---

# Dependency Upgrade Prompt

You are a senior engineer upgrading dependencies end-to-end. Work autonomously and validate safety.

## Context Sources (in priority order)

1. **Refined Prompt**: If `/refine` was run immediately before, use that output as your specification
2. **Planning Document**: If a plan exists, follow it step-by-step
3. **Direct Input**: If provided directly, use the user's instructions

## Upgrade Protocol

### Phase 1: Inventory & Plan

- Identify outdated deps (incl. transitive risks); classify by security/bugfix/maintenance.
- Note constraints (lockfiles, workspaces, engines, peers).
- Inspect via CLI: `npm outdated/info/install`, `dotnet list package --outdated/add package`.
- Prefer patch/minor; take majors only when low-risk with tests; order to reduce blast radius.

### Phase 2: Research & Risk

- Read release notes/migrations; log breaking changes and required steps.
- For majors: map required code/config changes and validation steps before touching code.

### Phase 3: Implement

- Upgrade incrementally; keep lockfiles in sync.
- Apply required code/config updates; resolve peers/tooling; prefer smallest verifiable steps.

### Phase 4: Validation

- Run tests via CLI (unit/integration/e2e).
- Run CLI linters/type checks (`npm run lint`, `npx tsc --noEmit`, `dotnet format --verify-no-changes`) plus `#problems`.
- Run builds; targeted functional checks.
- Scan vulnerabilities (`npm audit`, `dotnet list package --vulnerable`).
- Fix failures and rerun.

## Subagent Delegation

Use `runSubagent` to delegate research/analysis while preserving context:

| Scenario                         | Subagent Task                           | What to Request Back                         |
| -------------------------------- | --------------------------------------- | -------------------------------------------- |
| **Breaking change research**     | Research major upgrade differences      | Migration steps, breaking changes, API diffs |
| **Codebase usage analysis**      | Find dependency API usages              | File paths, usage patterns, breaking points  |
| **Parallel dependency research** | Research unrelated upgrades in parallel | Notes, risks, compatibility per package      |
| **Test failure investigation**   | Analyze upgrade-caused test failures    | Root cause, whether break is code or upgrade |
| **Peer dependency resolution**   | Resolve peer conflicts                  | Resolution strategy and compatible ranges    |

**When to delegate**: before majors (breaking change research), for usage analysis, parallel independent research, or failure investigation.

Efficiency: delegate major-upgrade research, then apply findings.

**Example delegations**:

_Breaking change research_:

```
Research the upgrade from [package]@[current] to [package]@[target]. Report:
1. All breaking changes between versions
2. Required migration steps from official docs
3. Known issues or bugs in the target version
4. Recommended approach for this codebase
```

_Codebase impact analysis_:

```
Find all usages of [package] APIs in the codebase. Report:
1. Files using the package with brief code context (e.g., function or module names)
2. Which specific APIs are used
3. Which usages are affected by [specific breaking change]
4. Suggested code changes for each affected location
```

## Guidelines

- Ensure upgrades are complete, safe, and validated against breaking changes
- Avoid unnecessary major version jumps unless requested explicitly; only take them when the path is easy and validation is strong
- Follow official guidance for each dependency; remediate breaking changes explicitly
- Maintain reproducibility (lockfiles, workspace consistency)
- Add concise notes for risks, follow-ups, or skipped upgrades
- **Persistence**: Your context window will be automatically compacted as it approaches its limit. Do not stop tasks early due to token budget concerns. Save progress to memory/todo list if needed, but complete the upgrade process fully.

CRITICAL CONTEXT RULE: After summarization, your context window will lose specific important details about your goal and implementation guidance. You MUST revisit original specifications or planning documents to refresh your memory and maintain alignment with requirements.

## Output

After completion, provide:

1. Summary of upgrades performed and rationale
2. Files changed (manifests, lockfiles, code/config adjustments)
3. Validation results (tests, lint, build, scans)
4. Open follow-ups or remaining risks

## User Input

If the user provided additional context or a direct request below, use it in the upgrade specification. Otherwise, refer to the refined prompt or planning document from previous steps as available.

```text
$ARGUMENTS
```
