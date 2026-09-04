# Status Line

Claude Code's custom status line: the single line under the input box showing where you are, what
the repository looks like, which model is answering, and how much of the context window is gone.

```
 ~/prompts │  Envative/prompts │  main ✓ │ 󰚩 Opus 5  high │  43%
   cwd            repo             branch + git state      model + effort    context
```

`statusline.js` reads the session JSON on stdin and prints that one line. Claude Code re-runs it
on every render, so it has to be fast and it has to exit — both are load-bearing, see below.

## Setup

`setup-skills-link.ps1` in the repository root links this file to `~/.claude/statusline.js`, the
same single-file link it already makes for `instructions/CLAUDE.md`.

The link is only half of it — Claude Code does not pick the script up until `~/.claude/settings.json`
points at it:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node \"C:/Users/<you>/.claude/statusline.js\"",
    "padding": 0
  }
}
```

`settings.json` is deliberately **not** tracked here: it holds machine-specific paths and secrets
(API tokens, OTLP headers). Only the script is shared.

`padding: 0` lets the line start at the left edge. `type: "command"` is the only documented type.

### Font

Every icon is a [Nerd Font](https://www.nerdfonts.com/) glyph, so the terminal font must be a
Nerd Font patched build or the line renders as a row of boxes. Cascadia Code NF installs per-user
with no admin rights; point Windows Terminal at it under `profiles.defaults.font.face`.

The glyphs were each checked against the font's `cmap` table rather than trusted from a codepoint
chart. Three that a chart would offer are **not in Cascadia Code NF** — `U+2387` (the conventional
branch mark), `U+2717` and `U+2718` (ballot X). Verify before reaching for a new one.

| Element  | Codepoint  | Glyph                |
| -------- | ---------- | -------------------- |
| cwd      | `U+F07C`   | fa folder-open       |
| repo     | `U+F401`   | octicon repo         |
| branch   | `U+E725`   | devicon git-branch   |
| clean    | `U+2713`   | check                |
| dirty    | `U+25CF`   | filled circle        |
| conflict | `U+F071`   | fa warning           |
| model    | `U+F06A9`  | md robot             |
| effort   | `U+F0E7`   | fa bolt              |
| context  | `U+F437`   | octicon graph        |
| divider  | `U+2502`   | box-drawing vertical |

The source stays **pure ASCII** — every glyph is written as a `\u` escape. Editing it through a
shell heredoc has already corrupted a backslash escape once; keeping the file ASCII makes that
class of damage impossible to reintroduce silently.

## Segments

| Segment     | Source                            | Notes                                                            |
| ----------- | --------------------------------- | ---------------------------------------------------------------- |
| cwd         | `workspace.current_dir`           | `$HOME` collapsed to `~`, backslashes normalized to `/`          |
| repo        | `workspace.repo.{owner,name}`     | omitted outside a known remote                                    |
| branch      | `worktree.branch`, else `git`     | `users/<user>/` prefix dropped, capped at 32 chars                |
| git state   | `git status --porcelain=v1`       | green clean / yellow `● N` dirty / red warning + count on conflict |
| model       | `model.display_name`              |                                                                   |
| effort      | `effort.level`                    | rides with the model; absent when the model takes no effort       |
| context     | `context_window.used_percentage`  | green, yellow at 60%, red at 80%                                  |

Deliberately omitted: `session_name` (the TUI shows it beside the input box), `vim.mode` and
`pr.number` (Claude Code renders both natively — the `-- INSERT --` indicator and the footer PR
badge). The payload also carries `cost.*` and `rate_limits.*`, unused here.

The permission mode (`auto mode on`) cannot be hidden today —
[anthropics/claude-code#89126](https://github.com/anthropics/claude-code/issues/89126).

## Two things not to undo

**The watchdog.** Claude Code spawns the script with a stdin pipe and separately spawns MCP servers
via `cmd.exe`, which inherit open handles. A grandchild holding the write end means EOF never
arrives, so waiting on `'end'` alone leaks one wedged Node process per session — they accumulate
silently at 0% CPU. This machine had 23 of them. The documented Node example in Claude Code's own
statusline docs has the same bug. `DEADLINE_MS` renders on whichever comes first, EOF or the
deadline, and always exits explicitly.

**`git status --porcelain=v1 --branch`, not `git rev-parse`.** One call returns the branch *and*
the working-tree state, so the git indicator costs no extra subprocess — measured at 94ms vs 75ms
on a large monorepo, ~95ms end to end. Two parsing traps are handled and easy to reintroduce:
split the header on the literal `...` upstream separator rather than on any dot, or a branch named
`release/1.2.0` gets truncated; and count porcelain *lines*, not index/worktree flags, or a file
staged and then modified again (`MM`) counts twice.
