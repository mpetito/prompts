# Windows smoke test results (step 9)

Date: 2026-10-13, about 19:55Z–19:58Z, at `b457f17`. The checkout that `~/.claude` links to was detached on
that commit for the run, then put back on `main`. Before the run, `thread.py list` printed `NONE`.

The test ran with `--skip-codex`, because the Codex sandbox cannot run commands on this machine (see
`probe.md`, third run). It ran from PowerShell 7 inside a herdr pane, with `HERDR_ENV=1`. The owner answered the
thread's startup trust prompt. The lane and the rotated thread showed none.

- `claude --version`: `2.1.296 (Claude Code)`
- `codex --version`: `codex-cli 0.161.0` (not exercised: `--skip-codex`)
- `herdr --version`: `herdr 0.9.3`

## Result: every item passed (second attempt)

```
SMOKE preflight pass missing=none hooks_linked=True inside_herdr=True
SMOKE setup build=smkc1eb root=C:/Users/<user>/AppData/Local/Temp/orch-smoke-vk93_4lf
SMOKE launch:start pass BLOCKED smkc1eb waiting on a startup prompt: answer it in workspace smkc1eb
SMOKE launch pass mail=1
SMOKE thread-guard pass file_written=False said=['STATUS: working - smoke thread up; guard refused']
SMOKE lane-start:cl pass LANE smkc1eb-cl pane=w11:p2 kind=claude
SMOKE lanes pass mail=1 committed={'cl': True}
SMOKE lane-guard pass file_written=False
SMOKE finish-running pass refused={'native': True, 'slashes': True, 'relative': True}
SMOKE finish-closed pass retired={'cl': True}
SMOKE rotate pass ROTATED smkc1eb
SMOKE hook-cost:guard_bash pass median_ms=230 runs=20 exit=0
SMOKE hook-cost:guard_writes pass median_ms=336 runs=20 exit=0
SMOKE hook-cost:guard_timestamps pass median_ms=284 runs=20 exit=0
SMOKE close pass CLOSED smkc1eb archive=C:/Users/<user>/AppData/Local/Temp/orch-smoke-vk93_4lf/orch/archive/smkc1eb-20261013T195805Z
SMOKE cleanup pass agents=[] worktrees=1 branches=[] rows=0
```

Exit status 0. The user name in the temp paths is replaced with `<user>`.

For comparison, the bash hooks on `main` took these medians on the same machine earlier the same day (20 runs,
started from Git Bash): `guard-bash.sh` about 2,850 ms and `guard-writes.sh` about 1,560 ms.

## Two smoke.py bugs found on Windows

**1. `finish-running` crashes when the script starts on a different drive from the temp folder.**
The first attempt (build `smkfa7d`) ran from `D:\prompts`, as step 9 says, while `tempfile` put the build on
`C:`. `os.path.relpath(wt)` raises on Windows when the two paths are on different drives:

```
SMOKE lanes pass mail=1 committed={'cl': True}
SMOKE lane-guard pass file_written=False
SMOKE cleanup fail agents=[] worktrees=2 branches=['+', 'lane/cl'] rows=0
  File "...\smoke.py", line 227, in smoke
    spellings = {"native": str(wt), "slashes": wt.as_posix(), "relative": os.path.relpath(wt)}
ValueError: path is on mount 'C:', start on mount 'D:'
```

The `cleanup` failure is a consequence of the crash: the lane's worktree still existed. The `'+'` is
`git branch`'s marker for a branch checked out in another worktree, not a branch name. Before the crash, the
same items passed as in the second attempt. The second attempt started the same script from `%TEMP%`, on `C:`.

Possible fix: take the relative spelling against a start directory on the same drive, for example
`os.path.relpath(wt, root.parent)` with `cwd=root.parent` for that call, or skip that spelling when the drives
differ.

**2. The temp folder survives cleanup on Windows.** Both attempts left
`orch-smoke-*\smoke-repo\.git\objects\...` behind, 5 files, all read-only. Git marks object files
read-only, `shutil.rmtree` cannot delete read-only files on Windows, and `ignore_errors=True` hides the
failure. The agent removed both folders by hand afterwards. Possible fix: pass `rmtree` an error handler
(`onexc=` on Python 3.12+) that clears the read-only bit (`os.chmod(path, stat.S_IWRITE)`) and retries.

## Second run, with Codex

Date: 2026-10-13, about 21:22Z–21:29Z, at `9a7ae82`. The checkout that `~/.claude` links to was detached on that
commit for the run, then put back on `main`. Before the run, `thread.py list` printed `NONE`.

Setup for the Codex lane, per the fourth probe:
- The owner set `[windows] sandbox = "unelevated"` in `~/.codex/config.toml`.
- The owner restarted herdr from the MSI PowerShell 7. The herdr server's parent and the pane shells are now
  `C:\Program Files\PowerShell\7\pwsh.exe`, so the MSI `pwsh` comes first on every pane's PATH. Before the
  restart, herdr had been started from the Store build. Each pane then put that build first on PATH, and a Codex
  lane would have launched it, which the unelevated sandbox refuses.
- No `node_repl` process was running.

The command was `python3 ...\smoke.py --codex-python python`, run from `%TEMP%` in PowerShell 7 (MSI) inside a
herdr pane. The owner answered two prompts: the thread's trust prompt and the Codex lane's startup prompt.

- `claude --version`: `2.1.296 (Claude Code)`
- `codex --version`: `codex-cli 0.161.0`
- `herdr --version`: `herdr 0.9.3`

Every item passed. Exit status 0. The user name in the temp paths is replaced with `<user>`.

```
SMOKE preflight pass missing=none hooks_linked=True inside_herdr=True
SMOKE setup build=smk8242 root=C:/Users/<user>/AppData/Local/Temp/orch-smoke-cgvks5iq
SMOKE launch:start pass BLOCKED smk8242 waiting on a startup prompt: answer it in workspace smk8242
SMOKE launch pass mail=1
SMOKE thread-guard pass file_written=False said=['STATUS: working - smoke thread up; guard refused']
SMOKE lane-start:cl pass LANE smk8242-cl pane=wR:p2 kind=claude
SMOKE lane-start:cx pass BLOCKED smk8242-cx waiting on a startup prompt: answer it in workspace smk8242, tab cx
SMOKE lane-ready:cx pass
SMOKE lanes pass mail=2 committed={'cl': True, 'cx': True}
SMOKE lane-guard pass file_written=False
SMOKE finish-running pass refused={'native': True, 'slashes': True, 'relative': True}
SMOKE finish-closed pass retired={'cl': True, 'cx': True}
SMOKE rotate pass ROTATED smk8242
SMOKE hook-cost:guard_bash pass median_ms=209 runs=20 exit=0
SMOKE hook-cost:guard_writes pass median_ms=298 runs=20 exit=0
SMOKE hook-cost:guard_timestamps pass median_ms=247 runs=20 exit=0
SMOKE close pass CLOSED smk8242 archive=C:/Users/<user>/AppData/Local/Temp/orch-smoke-cgvks5iq/orch/archive/smk8242-20261013T212839Z
SMOKE cleanup pass agents=[] worktrees=1 branches=[] rows=0
```

Both `smoke.py` fixes held:
- The relative-path spelling now runs from the worktree's parent and was refused like the others.
- The temp folder was removed with no `could not remove` line, so the read-only git objects no longer survive.

No `smk*` agent was left afterwards.

A requirement for Codex lanes on Windows came out of this run. Configuring Codex is not enough: whatever starts
herdr, and so every pane, must put a non-Store `pwsh` first on PATH. Starting herdr from the MSI PowerShell 7
does that.
