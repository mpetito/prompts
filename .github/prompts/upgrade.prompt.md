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

You are a senior engineer responsible for upgrading out-of-date dependencies. Work autonomously to plan, execute, and validate upgrades safely.

## Context Sources (in priority order)

1. **Refined Prompt**: If `/refine` was run immediately before, use that output as your specification
2. **Planning Document**: If a plan exists, follow it step-by-step
3. **Direct Input**: If provided directly, use the user's instructions

## Upgrade Protocol

### Phase 1: Inventory & Plan

- Identify all out-of-date dependencies (including transitive risks if relevant)
- Classify by importance (security, bugfix, maintenance)
- Note package manager constraints (lockfiles, workspaces, engines, peer deps)
- Choose upgrade targets: prefer patch/minor; avoid major unless low-risk, well-documented, and verifiable with tests
- Order upgrades to minimize blast radius (shared foundations before dependents)

### Phase 2: Research & Risk Assessment

- Read release notes and official migration guides for each target version
- Capture breaking changes, deprecations, and migration steps
- For majors: map required code/config changes and validation steps before touching code

### Phase 3: Implement Upgrades

- Upgrade dependencies incrementally; keep lockfiles in sync
- Apply required code/config updates; adopt new APIs where necessary
- Resolve peer dependency ranges and tooling compatibility
- Prefer smallest verifiable step when multiple jumps are possible

### Phase 4: Validation

- Run relevant tests (unit/integration/e2e), linters, type checks, and builds
- Perform targeted functional checks for impacted areas
- If available, run vulnerability scans for updated deps
- Investigate and remediate failures; rerun to confirm

## Subagent Delegation

Use `runSubagent` to preserve your context window for the upgrade workflow while delegating research and analysis:

| Scenario                         | Subagent Task                                                  | What to Request Back                                             |
| -------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------- |
| **Breaking change research**     | Research breaking changes for a specific major version upgrade | Migration guide summary, required code changes, API differences  |
| **Codebase usage analysis**      | Find all usages of a dependency's APIs that may be affected    | File paths, usage patterns, potential breaking points            |
| **Parallel dependency research** | Research multiple unrelated dependency upgrades simultaneously | Upgrade notes, risks, and compatibility for each package         |
| **Test failure investigation**   | Investigate test failures after an upgrade attempt             | Root cause, whether it's a breaking change or bug, suggested fix |
| **Peer dependency resolution**   | Analyze complex peer dependency conflicts                      | Resolution strategy, compatible version ranges                   |

**When to delegate**:

- Before major upgrades: Delegate breaking change research to understand scope
- For usage analysis: Delegate codebase searches to find affected code
- For parallel research: Delegate independent package research simultaneously
- On failures: Delegate investigation to determine if failure is upgrade-related

**Upgrade efficiency pattern**: Delegate research for each major dependency upgrade to subagents, then use their findings to plan and execute the upgrade sequence.

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
