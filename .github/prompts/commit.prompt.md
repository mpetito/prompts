---
name: commit
description: Commit, push, and create/update pull request
model: Gemini 3 Pro (Preview) (copilot)
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
    "github/*",
    "agent",
    "github.vscode-pull-request-github/copilotCodingAgent",
    "github.vscode-pull-request-github/issue_fetch",
    "github.vscode-pull-request-github/suggest-fix",
    "github.vscode-pull-request-github/searchSyntax",
    "github.vscode-pull-request-github/doSearch",
    "github.vscode-pull-request-github/renderIssues",
    "github.vscode-pull-request-github/activePullRequest",
    "github.vscode-pull-request-github/openPullRequest",
    "todo",
  ]
---

# Commit Prompt

You are handling the git workflow for committing and creating pull requests.

## Process

### Step 1: Assess Current State

- Check current branch with `git branch --show-current`
- Check for existing changes with `git status`
- Review the diff with `#changes`

### Step 2: Pre-Validation (if not already done)

Before committing, verify the code is ready:

- **Linting**: Run linter if available (e.g., `npm run lint`, `dotnet format --verify-no-changes`)
- **Formatting**: Ensure code is formatted (e.g., `prettier --check`, `dotnet format`)
- **Tests**: Run test suite if available (e.g., `npm test`, `dotnet test`)

If any checks fail, stop and inform the user. Do not commit broken code.

### Step 3: Create Branch (if needed)

If on `main`, `master`, or `develop`:

- Create a descriptive branch name: `<type>/<short-description>`
- Types: `feat`, `fix`, `refactor`, `docs`, `chore`, `test`
- Example: `feat/user-authentication`, `fix/null-pointer-exception`
- Create and switch to the branch

### Step 4: Stage and Commit

- Stage all changes: `git add -A`
- Create a conventional commit message:

  ```
  <type>(<optional-scope>): <description>

  [optional body with more details]
  ```

- **First letter of description must be lowercase**
- Types: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`
- Keep the first line under 72 characters

### Step 5: Push

- Push to origin with upstream tracking: `git push -u origin <branch-name>`

### Step 6: Create or Update PR

Check if a PR already exists for this branch:

**If NO existing PR:**

- Create a draft PR with:
  - Clear title matching the commit type and description
  - Detailed description including:
    - Summary of changes
    - List of modified files
    - Any relevant context
    - Testing notes if applicable

**If PR already exists:**

- Update the PR description:
  - Append a new section "## Update [Date/Time]" with the latest changes
  - Do not overwrite the original description unless it was a placeholder
  - Ensure the file list is accurate

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

## Guidelines

- If using GH CLI, use temporary markdown files for PR descriptions to ensure proper formatting
- If using VS Code GitHub tools, format the description using Markdown directly
- Keep commit messages concise but descriptive
- Reference issue numbers if applicable: `fixes #123`
- Don't commit unrelated changes together
- Verify the push succeeded before creating PR

## Output

Confirm:

- Branch name
- Commit message
- PR URL (if created/updated)

## User Input

If the user provided a commit message, PR context, or other guidance below, incorporate it into the commit and PR. Otherwise, generate appropriate messages based on the changes.

```text
$ARGUMENTS
```
