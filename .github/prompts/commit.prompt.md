---
name: commit
description: Commit, push, and create/update pull request
model: GPT-5.2 (Preview) (copilot)
agent: agent
argument-hint: Optional commit message or PR context
tools:
  [
    "vscode",
    "execute",
    "read",
    "edit",
    "search",
    "web",
    "agent",
    "perplexity/search",
    "github/*",
    "github.vscode-pull-request-github/*",
    "github-pr-review-tools/*",
    "todo",
  ]
---

# Commit Prompt

You are handling git workflow for committing and creating pull requests.

## Process

### Step 1: Assess Current State

- `git branch --show-current`, `git status`, review diff with `#changes`.

### Step 2: Pre-Validation (if not already done)

Run CLI checks before committing:

- **Linting**: `npm run lint`, `dotnet format --verify-no-changes` + `#problems`
- **Formatting**: `prettier --check`, `dotnet format`
- **Type Checks**: `npx tsc --noEmit` if applicable
- **Tests**: `npm test`, `dotnet test`

If any fail, stop and report; do not commit broken code.

### Step 3: Create Branch (REQUIRED)

**CRITICAL**: Never commit directly to `main`/`master`/`develop`. If on one, **stop immediately** and run `git checkout -b <type>/<short-description>` (types: feat, fix, refactor, docs, chore, test). Do not proceed until on a feature branch.

### Step 4: Stage and Commit

- Stage all: `git add -A`.
- Conventional message `<type>(<scope>): <description>` (lowercase description, types feat/fix/refactor/docs/style/test/chore, <72 chars). Optional body allowed.

### Step 5: Push

- Push to origin with upstream tracking: `git push -u origin <branch-name>`

### Step 6: Create or Update PR

If no PR: create draft via gh CLI (temp markdown body, then delete), default draft unless requested otherwise; title matches commit type/description; include summary, modified files, context, tests.

If PR exists: append "## Update [Date/Time]" with latest changes; don't overwrite original; ensure file list is accurate.

## Commit Message Examples

```
feat(auth): add password reset functionality

Implements the password reset flow including:
- Email verification endpoint
- Token generation and validation
- Password update API
```

```
fix(api): handle null response from external service

Added null check to prevent crash when external API returns empty response.
```

```
refactor: extract common validation logic into shared utility
```

## Subagent Delegation

Use `runSubagent` to delegate analysis while preserving context:

| Scenario                      | Subagent Task                           | What to Request Back                        |
| ----------------------------- | --------------------------------------- | ------------------------------------------- |
| **Large changesets**          | Analyze diff scope                      | Grouped summary + commit message suggestion |
| **CI/build failures**         | Investigate failing tests/builds        | Root cause, affected files, suggested fix   |
| **PR description generation** | Draft PR description                    | Summary, file list, testing notes           |
| **Multi-package changes**     | Cross-package dependency/order analysis | Dependency graph, commit ordering           |

Delegate for >5-10 files or when impact analysis needed.

**Example delegation**:

```
Analyze the current git diff and provide:
1. A grouped summary of all changes by feature/area
2. A suggested conventional commit message
3. Any concerns about the changes (breaking changes, missing tests, etc.)
```

## Guidelines

- If using GH CLI, use temporary markdown files for PR descriptions to ensure proper formatting
- If using VS Code GitHub tools, format the description using Markdown directly
- Keep commit messages concise but descriptive
- Reference issue numbers if applicable: `fixes #123`
- Don't commit unrelated changes together
- Verify the push succeeded before creating PR

## Output

Confirm: branch name, commit message, PR URL (if created/updated).

## User Input

If the user provided a commit message, PR context, or other guidance below, incorporate it into the commit and PR. Otherwise, generate appropriate messages based on the changes.

```text
$ARGUMENTS
```
