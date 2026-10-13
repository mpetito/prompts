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
