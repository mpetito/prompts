# Contributing

This repository is the source of truth for agent configuration that is symlinked into live
client folders. An edit here changes every agent session on the machine immediately — there
is no build step and no deploy.

## Commit directly to `main`

**Do not create a feature branch and do not open a pull request.** Commit to `main` and push.

This is a single-maintainer configuration repository: branch-and-PR ceremony adds latency
without adding review. Agents following a generic "never commit to `main`" rule should treat
this file as the override.

Use [Conventional Commits](https://www.conventionalcommits.org/) — `feat`, `fix`, `refactor`,
`docs`, `style`, `test`, `chore` — with a lowercase, imperative subject under 72 characters.
Split unrelated work into separate commits rather than one mixed commit.

Never sign a commit with AI attribution. No `Co-Authored-By: Claude`, no "Generated with"
footer, no session links. `Co-Authored-By` is reserved for crediting human authors.

## Validate before committing

There is no package manager here. Run what CI runs, from the repository root:

```sh
pwsh -NoProfile -File ./tests/Setup.Tests.ps1
pwsh -NoProfile -File ./tests/Mcp.Tests.ps1
pwsh -NoProfile -File ./skills/pr-scripts/tests/Get-PrFeedback.Tests.ps1
node --check statusline/statusline.js && echo '{}' | node statusline/statusline.js
```

All four are offline: they use disposable directories and mocked CLIs, and touch neither your
real home directory nor Docker. `.github/workflows/validate.yml` runs the same set plus a
PowerShell parse check over every `.ps1` and `.psm1`, on Windows and Ubuntu.

Scripts target **PowerShell 7.4+** on Windows, Linux, and macOS. Windows PowerShell 5.1 is not
supported, so `$IsWindows` and other PowerShell 7 built-ins are safe to rely on. `.gitattributes`
normalizes scripts and docs to LF.

## After adding or renaming a skill

Rerun setup so each client gets the new child link:

```sh
pwsh -NoProfile -File ./setup-skills-link.ps1
pwsh -NoProfile -File ./verify-setup.ps1
```

Edits *inside* an already-linked skill need no rerun — they are visible immediately.

## Authoring standards

Do not write these from memory; the canonical guidance lives in the tree:

| Authoring | Source |
| --- | --- |
| `SKILL.md` files and skill folders | the `skill-authoring` skill |
| `AGENTS.md`, `CLAUDE.md`, `copilot-instructions.md` | the `agents-md-authoring` skill |
| Cross-tool portability rules | [Cross-Tool Authoring Notes](README.md#cross-tool-authoring-notes) |
| Claude-only frontmatter keys | [Host-Specific Frontmatter](README.md#host-specific-frontmatter) |
| Worker model selection | `skills/skill-authoring/references/agent-model-selection.md` |

Two rules bite often enough to repeat here: cross-references between skills must be
skill-relative (`../other-skill/SKILL.md`), never repo-root-relative, because the tree is
symlinked into user-level folders where no repo root exists; and `agents/` is Claude Code's
format only, so keep agent bodies host-generic and free of employer, stack, or repository
specifics.
