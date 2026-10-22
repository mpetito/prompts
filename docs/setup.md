# Setup

Setup needs **Python 3.12+**, run as `python3`, on Windows, Ubuntu, and macOS. On Windows,
`python3` must reach an installed Python: verification rejects the Microsoft Store placeholder
that only offers to install one. Keep a local clone on each machine and sync the source through
Git; the installer derives the checkout location from its own script, so the clone can live
anywhere.

## Link and verify

From the repository root, these commands work from Bash or PowerShell:

```sh
# Preview setup for clients detected on PATH, then apply and verify it.
python3 setup_skills_link.py --what-if
python3 setup_skills_link.py
python3 verify_setup.py

# Select clients explicitly, including clients not installed yet.
python3 setup_skills_link.py --tools codex,claude,opencode
python3 verify_setup.py --tools codex,claude,opencode
```

Automatic detection checks the `codex`, `claude`, `opencode`, and `copilot` commands on PATH.
For desktop/IDE-only clients, or to prepare files before installing a CLI, use `--tools`.
When adding a client, install it and rerun setup. No client authentication or Docker is needed
for skill linking. Windows symlinks require Developer Mode or an elevated shell;
Linux and macOS need no elevation when writing your own home directory. Run as your normal user.

| Repository source | Client | Default destination |
| --- | --- | --- |
| `skills/*` | Codex and OpenCode | `~/.agents/skills/*` |
| `skills/*` | Claude Code | `~/.claude/skills/*` |
| `skills/*` | GitHub Copilot | `~/.copilot/skills/*` |
| `agents/` | Claude Code | `~/.claude/agents` |
| `instructions/CLAUDE.md` | Claude Code | `~/.claude/CLAUDE.md` |
| `statusline/statusline.py` | Claude Code | `~/.claude/statusline.py` |

[Codex](https://learn.chatgpt.com/docs/build-skills) and
[OpenCode](https://opencode.ai/docs/skills/) both discover `~/.agents/skills`.
Skills are linked individually, so the destination remains a real directory and client-managed
entries stay local. Global Claude instructions and agents keep their Claude-specific formats.

## Environment overrides

The installer honors `CLAUDE_CONFIG_DIR` for Claude destinations and `CODEX_HOME` when migrating
old Codex links. Shared skills remain under the user's `~/.agents/skills`, independent of
`CODEX_HOME`. `--home-directory <path>` redirects **all skill destinations** to an isolated home
and ignores these environment overrides; use it for testing, not to configure a client that
still reads your normal home.

## Conflicts and migration

Setup is idempotent. Conflicting files, directories, and foreign links are preserved and reported
as incomplete setup (nonzero exit). To replace them deliberately, preview with
`--replace-conflicts --what-if`, then rerun with `--replace-conflicts`. Originals move to a unique
folder under `~/.prompts-backups`, outside skill discovery. Nothing is silently overwritten.
Missing source files and link failures are errors, with a Windows privilege hint when applicable.

Existing whole-folder skill links to this checkout are converted to real directories containing
per-skill links. With Codex selected, old repo-owned links under `~/.codex/skills` are removed
only after their replacements exist under `~/.agents/skills`; unrelated entries and `.system`
remain. Broken links are pruned only when their target exactly matches this checkout's expected
skill path. Tool-managed content previously written through a whole-folder link must still be
moved out of the repository manually; setup warns when converting it.

## When to rerun

After adding or renaming a top-level skill, rerun setup. Edits inside already-linked skills are
visible immediately after `git pull`; restart clients if they cache their skill lists.

## Optional dependencies and MCP

- PR helpers use Python 3.12+ and an authenticated `gh` CLI on Windows, Linux, or macOS. Invoke them
  with `python3 <script.py>` from Bash or PowerShell.
- The Claude status line needs Python 3.12+, Git, a machine-local `settings.json` entry and a
  Nerd Font; see [`statusline/README.md`](../statusline/README.md).
- Commit and PR attribution is off in each machine's `~/.claude/settings.json`:
  `"attribution": { "commit": "", "pr": "", "sessionUrl": false }`. Without it, Claude Code tells
  every session and subagent to add a `Co-Authored-By: Claude` trailer, and workers follow that
  over the CLAUDE.md rule
  ([settings reference](https://code.claude.com/docs/en/settings-reference#attribution)).
- Claude Code plugins are not linked; install them from the list in [plugins.md](plugins.md).
- MCP configuration is a separate opt-in step; see [`mcp/README.md`](../mcp/README.md). Docker
  Engine alone is insufficient: the profiles also require the Docker MCP Toolkit and their
  configured secret backend. Credentials and generated configuration stay machine-local.

## Validation

```sh
python3 -m unittest discover -s tests -t .
```

These offline tests create temporary homes, exercise migration and conflicts, and mock MCP CLI
commands. The GitHub Actions workflow runs them on Windows and Ubuntu. The same scripts are
written for macOS, but macOS is not currently in the CI matrix. The full set CI runs is in
[CONTRIBUTING.md](../CONTRIBUTING.md#validate-before-committing).
