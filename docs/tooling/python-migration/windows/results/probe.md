# Windows probe results (step 0)

Date: 2026-10-13, about 19:20Z. The probe ran from PowerShell 7 on the owner's Windows 11 machine, with
`HERDR_*` cleared so the model calls could not reach herdr. The PROBE lines below are verbatim, except that
the user profile path is shortened to `%USERPROFILE%`.

```
PROBE host Windows-11-10.0.26220-SP0 python=3.14.2 evidence=%USERPROFILE%/AppData/Local/Temp/py-probe
PROBE interpreters:python3 pass path=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\python3.EXE runs=True version='3.14.2 %USERPROFILE%\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe'
PROBE interpreters:python pass path=%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.EXE runs=True version='3.14.3 %USERPROFILE%\\AppData\\Local\\Programs\\Python\\Python314\\python.EXE'
PROBE interpreters:py pass path=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\py.EXE runs=True version='3.14.2 %USERPROFILE%\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe'
PROBE codex-sandbox fail launcher=codex.CMD exit=0 header='sandbox: read-only' wrote=False
PROBE hook-fires pass fired=exec,shell exit=0 claude=2.1.296 (Claude Code)
PROBE hook-cost:exec:python3 pass median_ms=233 runs=20
PROBE hook-cost:shell:python3 pass median_ms=342 runs=20
PROBE hook-cost:exec:python pass median_ms=57 runs=20
PROBE hook-cost:shell:python pass median_ms=181 runs=20
```

Exit status 1, because of the codex-sandbox failure.

- `claude --version`: `2.1.296 (Claude Code)`
- `codex --version`: `codex-cli 0.161.0`
- `(Get-Command codex).Source`: `C:\nvm4w\nodejs\codex.ps1`. PowerShell picks the `.ps1` shim. The probe's
  `shutil.which` picks `codex.CMD`, because Python's `PATHEXT` lookup has no `.PS1`. Both are npm shims for the
  same `codex.js`.
- `python3` and `py` reach 3.14.2 through WindowsApps aliases (Python Install Manager). `python` is a
  separate python.org 3.14.3 install. Both interpreters run; packages installed into one are missing from
  the other.

## codex-sandbox: why it failed

From `codex-sandbox.err.txt` (header only; the run executed no command):

```
approval: never
sandbox: read-only
```

The cause is not `cmd.exe` quoting. Four more runs of the same task, all through `subprocess` as in the
probe, isolate it:

| Variant | Sandbox header | File written |
| --- | --- | --- |
| shim, `-s workspace-write`, `--ignore-user-config` | `read-only` | no |
| `node codex.js` directly (no cmd.exe), quoted `-c`, `--ignore-user-config` | `read-only` | no |
| shim, `-s workspace-write` and `-c windows.sandbox=elevated`, `--ignore-user-config` | `workspace-write [workdir, /tmp, $TMPDIR, <mail dir>]` | no: every exec failed |
| shim, probe-style quoted `-c 'sandbox_mode="workspace-write"'`, `-c 'windows.sandbox="elevated"'` | `workspace-write [..., <mail dir>]` | no: every exec failed |
| shim, probe-style quoted `-c`, the owner's full user config (as `lane.sh` runs) | `workspace-write [..., <mail dir>]` | no: every exec failed |

What the table shows:
1. **On Windows, workspace-write needs `[windows] sandbox`.** The owner's `~/.codex/config.toml` sets
   `sandbox = "elevated"`. `--ignore-user-config` drops it, and codex silently falls back to `read-only`.
   The probe's `--ignore-user-config` therefore tests a configuration no real lane uses.
2. **Quoted `-c` values survive the npm `codex.CMD` shim.** With `windows.sandbox` set, the probe-style
   quoted form produced the workspace-write header, including the `--add-dir` folder.
3. **With the sandbox active, no command runs.** Every exec failed with:
   `exited -1 in 0ms: Failed to create unified exec process: helper_unknown_error: setup refresh had errors`.

The sandbox setup log (`%USERPROFILE%\.codex\.sandbox\sandbox.2026-10-13.log`), trimmed:

```
failed to grant non-inheriting read-attributes ACE on user profile %USERPROFILE%: open ACL target for root-only update: The process cannot access the file because it is being used by another process. (os error 32); continuing setup
runtime read/execute validation failed: validate runtime read/execute access on %USERPROFILE%\AppData\Local\OpenAI\Codex\runtimes\cua_node\<hash>\bin\node_repl.exe: open ACL target for root-only update: The process cannot access the file because it is being used by another process. (os error 32)
granting write ACE to %USERPROFILE%\.orchestration-probe-<pid>\mail for sandbox group and capability SID
setup refresh completed with errors: ["runtime read/execute validation failed: ... node_repl.exe ..."]
setup error: setup refresh had errors
```

At the time, the Codex desktop app was running, with two `node_repl.exe` processes from that same
`runtimes\cua_node` folder. Those processes are the likely holders of the lock. Whether closing the
desktop app lets setup succeed was not tested, because that means closing the owner's running apps. The
mail-folder write ACE itself was granted, so the `--add-dir` mail folder is not the problem.

For the Linux session: by the handoff's rule this is a codex-sandbox failure, so ask the owner. On this
machine, as configured, a Codex lane started from PowerShell or Python cannot run any command in its
sandbox, including the mail send. The open question is whether that only happens while the Codex desktop
app holds its runtime files.
