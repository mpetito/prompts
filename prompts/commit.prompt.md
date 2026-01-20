---
name: commit
description: Commit changes with conventional messages and create/update pull request
---

# Commit & PR

Validate, commit with conventional messages, and submit pull requests.

## Critical Safety Rule

**Never perform destructive operations on any file** except for the temporary PR body file in `.github/`.

## Workflow

### 1. Assess State

- Run `git branch --show-current` and `git status`
- Review `#changes` for the complete diff
- Note staged vs unstaged files
- Check if on protected branch

### 2. Discover & Run Validation

Discover available commands (`npm run` to list scripts), then execute:

- **Formatting**: `format`, `prettier`, `fmt`
- **Linting**: `lint`, `eslint`
- **Type checking**: `typecheck`, `tsc`
- **Testing**: `test`
- **Building**: `build`

Check `#problems` for IDE-reported issues. **Stop and report if validation fails.**

### 3. Ensure Feature Branch

- Never commit directly to `main`, `master`, `develop`
- If on protected branch: `git checkout -b <type>/<short-description>`
- Branch types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`

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

### 5. Push

```bash
git push -u origin <branch-name>
```

### 6. Create/Update PR

**If no PR exists:**

- Create `.github/.pr-body.md` with PR description
- Run: `gh pr create --draft --body-file .github/.pr-body.md`
- Delete temp file after creation

**If PR exists:**

- Append comment with latest changes
- Update title/body if significant changes

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

## User Input

```text
$ARGUMENTS
```
