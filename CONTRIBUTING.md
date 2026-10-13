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
python3 -m unittest discover -s tests -t .
pwsh -NoProfile -File ./tests/Mcp.Tests.ps1
pwsh -NoProfile -File ./skills/pull-request/tests/Get-PrFeedback.Tests.ps1
pwsh -NoProfile -File ./skills/pull-request/tests/Resolve-PrThread.Tests.ps1
node --check statusline/statusline.js && echo '{}' | node statusline/statusline.js
python3 -m unittest discover -s skills/agent-orchestration/tests -t skills/agent-orchestration   # Python 3.12+
python3 -m unittest discover -s skills/orchestration-main/tests -t skills/orchestration-main
bash skills/model-council/tests/run.sh
```

On Windows, run the bash suite from Git Bash: PowerShell's `bash` is WSL's launcher. The
model-council suite makes native symlinks, which need Developer Mode or an elevated shell.

All eight are offline: they use disposable directories and mocked CLIs, and touch neither your
real home directory nor Docker. `.github/workflows/validate.yml` runs the same set plus a
PowerShell parse check over every `.ps1` and `.psm1`, on Windows and Ubuntu.

The orchestration scripts and hooks are **Python 3.12+**, standard library only. Skills and
agents run each one as `python3` and its quoted path under `$HOME`, never `~`, so bash and both
PowerShells can run the same command.

Scripts target **PowerShell 7.4+** on Windows, Linux, and macOS. Windows PowerShell 5.1 is not
supported, so `$IsWindows` and other PowerShell 7 built-ins are safe to rely on. `.gitattributes`
normalizes scripts and docs to LF.

## Archived skills and readmission

Every skill was archived on 2026-10-09 under `archive/skills/`, with the audit that led to it
in `docs/skill-audit/2026-10-09/`. The installer links only `skills/`, so an archived skill is
invisible to every client. A skill (old or new) enters `skills/` only through the bar in
[docs/skill-audit/readmission.md](docs/skill-audit/readmission.md): a recorded gap in
`docs/skill-audit/candidates.md`, three behaviour evals that fail without it, one named
consumer role with its line budget, no overlap with the harness or a sibling, and loads within
30 days of readmission (`python3 scripts/skill-usage.py`). Start a readmission from the
archived text and the audit's review of it, never from a blank file.

## After adding or renaming a skill

Rerun setup so each client gets the new child link:

```sh
python3 setup_skills_link.py
python3 verify_setup.py
```

Edits *inside* an already-linked skill need no rerun — they are visible immediately.

## After changing a skill

If the skill has an `evals/` suite, run it with the previous revision as the `-Baseline` arm
and compare pass rates, judge scores and trigger rates.
[docs/evaluating-skills.md](docs/evaluating-skills.md) gives the commands and says which run
fits which edit.

A shortened skill should keep its objective pass rate and trigger rate while costing fewer
tokens. A new case for an extended skill should fail on the old text and pass on the new one.
A skill whose with-versus-without delta stays near zero across runs is a removal candidate.

## Authoring standards

Do not write these from memory; the canonical guidance lives in the tree:

| Authoring | Source |
| --- | --- |
| `SKILL.md` files and skill folders | [skills/skill-authoring/SKILL.md](skills/skill-authoring/SKILL.md), plus the readmission bar above |
| `AGENTS.md`, `CLAUDE.md`, `copilot-instructions.md` | [skills/project-setup/SKILL.md](skills/project-setup/SKILL.md) |
| Cross-tool portability rules | [Cross-Tool Authoring Notes](README.md#cross-tool-authoring-notes) |
| Claude-only frontmatter keys | [Host-Specific Frontmatter](README.md#host-specific-frontmatter) |
| Worker model selection | [docs/agent-model-selection.md](docs/agent-model-selection.md) |

Two rules bite often enough to repeat here: cross-references between skills must be
skill-relative (`../other-skill/SKILL.md`), never repo-root-relative, because the tree is
symlinked into user-level folders where no repo root exists; and `agents/` is Claude Code's
format only, so keep agent bodies host-generic and free of employer, stack, or repository
specifics.
