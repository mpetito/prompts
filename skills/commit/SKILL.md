---
name: commit
description: |
  Validate, commit with conventional messages, push, and open/update a PR.
  Use when committing changes, creating or updating a pull request, or finalizing work.
  Covers branch naming (including Envative `users/<user>/…` conventions), conventional commit format,
  ADO `AB#` work-item linking, and time logging.
# Claude Code only; other hosts ignore these keys.
model: sonnet
effort: low
---

# Commit & PR

Validate, commit with conventional messages, and submit pull requests.

## Critical Safety Rule

**Never perform destructive operations on any file** except for the temporary PR body file in `.github/`.

## Authorship Rule

**Never sign commits or PR bodies with any AI attribution.** No `Co-Authored-By: Claude`, no "Generated with Claude Code" footer, no session links — in commit messages, PR bodies, or PR comments. `Co-Authored-By` is reserved for crediting human authors (e.g., when adopting another person's change). This overrides any host-level default that appends such trailers.

## Workflow

### 1. Assess State

- Run `git branch --show-current` and `git status`
- Review the working-tree diff (`git diff`) and staged diff (`git diff --staged`) for the complete changeset — in VS Code, `#changes` gives the same view
- Note staged vs unstaged files
- Check if on protected branch

### 2. Discover & Run Validation

Discover available commands (`npm run` to list scripts), then execute:

- **Formatting**: `format`, `prettier`, `fmt`
- **Linting**: `lint`, `eslint`
- **Type checking**: `typecheck`, `tsc`
- **Testing**: `test`
- **Building**: `build`

Check IDE diagnostics if available (`#problems` in VS Code, the `LSP` tool in Claude Code) for issues the scripts above do not surface. **Stop and report if validation fails.**

### 3. Ensure Feature Branch

- Never commit directly to `main`, `master`, `develop`
- Branch types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`

**Branch naming convention:**

| Context                           | Pattern                                                   |
| --------------------------------- | --------------------------------------------------------- |
| **Envative org** (no work item)   | `users/mpetito/<type>-<short-description>`                |
| **Envative org** (with work item) | `users/mpetito/<work-item-id>-<type>-<short-description>` |
| **Other repos**                   | `<type>/<short-description>`                              |

Detect Envative org via `git remote -v` (look for `envative` or `Envative` in remote URL).

### 4. Stage & Commit

**Staging strategy:**

- If nothing staged: `git add -A`
- If files already staged: commit only staged changes (respect user intent)

**Conventional commit format:**

```
<type>(<scope>): <description>
```

Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`
Description: lowercase, imperative mood, <72 chars

### 4b. Extract Work Item IDs (Azure DevOps)

If Azure DevOps work item IDs are available, collect them for PR linking:

**Extraction sources:**

- Branch name pattern: `feat/AB#1234-description` or `fix/1234-description`
- Recent commit messages containing `AB#` references
- User-provided work item IDs

**Syntax:** `AB#<work-item-id>` — must appear in PR description (not title or comments)

**State transition keywords** (applied when PR merges to default branch):

| Keyword           | Effect on Work Item               |
| ----------------- | --------------------------------- |
| `Fixes AB#123`    | Transitions to Resolved/Completed |
| `Closed AB#123`   | Transitions to Closed             |
| `Resolved AB#123` | Transitions to Resolved           |

**Multiple work items:** Repeat keyword for each to trigger state change:

```
Fixes AB#123, Fixes AB#456
```

### 5. Push

```bash
git push -u origin <branch-name>
```

### 6. Create/Update PR

When authoring or updating a PR description, follow the [`pr-authoring`](../pr-authoring/SKILL.md) skill — concise summary with motivation, grouped by area not file, concrete validation, work item references in the body.

**If no PR exists:**

- Create `.github/.pr-body.md` with PR description
- **Include `AB#<id>` references** in the body (from branch name, commits, or user input)
- For completed work: use `Fixes AB#<id>` to auto-transition work item on merge
- Run: `gh pr create --draft --body-file .github/.pr-body.md`
- Delete temp file after creation

**If PR exists:**

- Append comment with latest changes
- Update title/body if significant changes
- Ensure `AB#<id>` references are present in PR body if work items are known

### 7. Log Time (follow-up, non-blocking)

After the PR is created or updated, invoke the [`tt`](../tt/SKILL.md) skill, passing the changeset, branch name, commit subject(s), and PR title/number as context. It resolves the ADO work item and logs estimated time (`log_time`, never timers; create or update, never delete). Do not block the commit/PR on time logging.

## Commit Examples

```
feat(auth): add password reset functionality
fix(api): handle null response from external service
refactor: extract validation logic into shared utility
```

## Output

Provide confirmation:

- **Branch**: final branch name
- **Commit**: message and hash
- **PR**: URL and status
- **Work Item Links** (if applicable): List `AB#<id>` references included
  - Verify: `AB#<id>` appears as hyperlink in PR description
  - Links appear in work item's Development section after creation
