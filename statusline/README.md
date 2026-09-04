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

Three steps, none of which the others imply. The link alone shows nothing; the `settings.json`
entry without the font shows a row of boxes.

### 1. Link the script

`setup-skills-link.ps1` in the repository root links this file to `~/.claude/statusline.js`, the
same single-file link it already makes for `instructions/CLAUDE.md`. Nothing else to do here.

### 2. Point `settings.json` at it

Claude Code does not run the script until `~/.claude/settings.json` names it:

```json
{
  "statusLine": {
    "type": "command",
    "command": "node \"C:/Users/<you>/.claude/statusline.js\"",
    "padding": 0
  }
}
```

`padding: 0` lets the line start at the left edge. `type: "command"` is the only documented type.

`settings.json` is deliberately **not** tracked here: it holds machine-specific paths and secrets
(API tokens, OTLP headers). Only the script is shared, so this entry is a manual step on each
new machine.

### 3. Install a Nerd Font and point the terminal at it

Every icon is a [Nerd Font](https://www.nerdfonts.com/) glyph. Without one the line renders as a
row of empty boxes — the script is working, the font simply has no glyph at those codepoints.

Microsoft's own Cascadia Code release ships the patched `NF` variants, so no third-party build is
needed. It installs **per-user with no admin rights**: fonts go in `%LOCALAPPDATA%\Microsoft\Windows\Fonts`
and register under `HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts`.

```powershell
# Download the current release (v2407.24 at time of writing) and install Cascadia *NF per-user.
$rel   = Invoke-RestMethod https://api.github.com/repos/microsoft/cascadia-code/releases/latest
$asset = $rel.assets | Where-Object { $_.name -like 'CascadiaCode-*.zip' }
$zip   = Join-Path $env:TEMP $asset.name
Invoke-WebRequest $asset.browser_download_url -OutFile $zip

$dest = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'
$reg  = 'HKCU:\Software\Microsoft\Windows NT\CurrentVersion\Fonts'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
if (-not (Test-Path $reg)) { New-Item -Path $reg -Force | Out-Null }

Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead($zip)
foreach ($e in $z.Entries | Where-Object { $_.FullName -match '^ttf/static/Cascadia(Code|Mono)NF-.*\.ttf$' }) {
    $file = Split-Path $e.FullName -Leaf
    $out  = Join-Path $dest $file
    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($e, $out, $true)
    # "CascadiaCodeNF-SemiBoldItalic.ttf" -> "Cascadia Code NF Semi Bold Italic (TrueType)"
    $fam, $sty = [IO.Path]::GetFileNameWithoutExtension($file) -split '-', 2
    $fam = $fam -replace 'Cascadia(Code|Mono)NF', 'Cascadia $1 NF'
    $sty = $sty -creplace '([a-z])([A-Z])', '$1 $2'
    New-ItemProperty -Path $reg -Name "$fam $sty (TrueType)" -Value $out -PropertyType String -Force | Out-Null
}
$z.Dispose()
```

That installs 24 faces — `Cascadia Code NF` (with ligatures) and `Cascadia Mono NF` (without).
Either works; pick `Mono` if you dislike `!=` and `=>` being drawn as single glyphs.

**Windows Terminal.** Set it as the default for every profile, in
`%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`:

```json
"profiles": {
    "defaults": {
        "font": {
            "face": "Cascadia Code NF"
        }
    },
    "list": [ ... ]
}
```

Editing `profiles.defaults` rather than an individual entry in `profiles.list` means every
profile — PowerShell, WSL, Git Bash — picks it up. The GUI equivalent is
**Settings → Profiles → Defaults → Appearance → Font face**.

**VS Code's integrated terminal** reads its own setting and ignores the Windows Terminal one:

```json
"terminal.integrated.fontFamily": "Cascadia Code NF"
```

**Restart the terminal afterwards.** Windows Terminal enumerates fonts at startup, so until it is
fully closed and reopened the icons keep rendering as boxes even though everything is configured
correctly. Verify with:

```powershell
'{}' | node "$env:USERPROFILE\.claude\statusline.js"
```

(PowerShell has no `<` input redirection — piping is how you hand it stdin.) That prints the cwd
and git segments with no session data. If the glyphs are boxes but the text and colours are right,
it is the font; if nothing prints, it is step 1 or 2.

### Choosing new glyphs

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
