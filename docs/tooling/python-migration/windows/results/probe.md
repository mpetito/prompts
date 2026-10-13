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

## Second run

Date: 2026-10-13, about 19:43Z, at `7f54349`. The probe's codex check now runs with the owner's config
(`[windows] sandbox = "elevated"`). The run was otherwise as before: PowerShell 7, `HERDR_*` cleared. The
evidence folder is `py-probe-2`.

Before the run, the owner quit the Codex desktop app. Closing its window had not been enough: the app kept
running until it was quit. With it quit, `Get-Process node_repl` found **0** processes, both before and after
the run, and no process ran from `%USERPROFILE%\AppData\Local\OpenAI\Codex`. Only the
`codex-windows-sandbox-service` Windows service was running.

```
PROBE host Windows-11-10.0.26220-SP0 python=3.14.2 evidence=%USERPROFILE%/AppData/Local/Temp/py-probe-2
PROBE interpreters:python3 pass path=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\python3.EXE runs=True version='3.14.2 %USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe'
PROBE interpreters:python pass path=%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.EXE runs=True version='3.14.3 %USERPROFILE%\AppData\Local\Programs\Python\Python314\python.EXE'
PROBE interpreters:py pass path=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\py.EXE runs=True version='3.14.2 %USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe'
PROBE codex-sandbox fail launcher=codex.CMD exit=0 header='sandbox: workspace-write [workdir, /tmp, $TMPDIR, %USERPROFILE%\.orchestration-probe-49176\mail]' wrote=False
PROBE hook-fires pass fired=exec,shell exit=0 claude=2.1.296 (Claude Code)
PROBE hook-cost:exec:python3 pass median_ms=226 runs=20
PROBE hook-cost:shell:python3 pass median_ms=364 runs=20
PROBE hook-cost:exec:python pass median_ms=52 runs=20
PROBE hook-cost:shell:python pass median_ms=162 runs=20
```

Codex's output (`codex-sandbox.err.txt`): the command never ran.

```
exec
"...\pwsh.exe" -Command "python3 -c \"import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('ok')\" .../mail/probe" in ...\probe-work-i9vj5_8y
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
```

New lines in `%USERPROFILE%\.codex\.sandbox\sandbox.2026-10-13.log`, trimmed. They are the same as the first run,
with the desktop app quit:

```
setup refresh: spawning ...\codex-resources\codex-windows-sandbox-setup.exe (cwd=...\probe-work-i9vj5_8y, payload_len=5448)
failed to grant non-inheriting read-attributes ACE on user profile %USERPROFILE%: open ACL target for root-only update: The process cannot access the file because it is being used by another process. (os error 32); continuing setup
runtime read/execute validation failed: validate runtime read/execute access on %USERPROFILE%\AppData\Local\OpenAI\Codex\runtimes\cua_node\<hash>\bin\node_repl.exe: open ACL target for root-only update: The process cannot access the file because it is being used by another process. (os error 32)
granting write ACE to %USERPROFILE%\.orchestration-probe-49176\mail for sandbox group and capability SID
granting write ACE to ...\probe-work-i9vj5_8y for sandbox group and capability SID
setup refresh: processed 3 write roots (read roots delegated); errors=["runtime read/execute validation failed: ... node_repl.exe ... (os error 32)"]
setup error: setup refresh had errors
```

The first run blamed the running desktop app for the lock. This run refutes that. After the probe,
`node_repl.exe` opened fine with no sharing allowed (`FileShare.None`, for both Read and ReadWrite), so no
process held it while idle. The sharing violation therefore happens during setup itself: from the setup
helper's own access, the sandbox service, or an on-access scan. This was not narrowed further, because that
would need a handle trace (Process Monitor).

It matches public community reports of the same failure, `setup refresh had errors` with `os error 32` on
`node_repl.exe` or other files under the Codex runtime:
- https://community.openai.com/t/windows-11-setup-refresh-had-errors-blocks-commands-and-browser-tasks/1404213
- https://community.openai.com/t/codex-windows-sandbox-setup-refresh-fails-computer-use-and-node-repl-unusable/1391773

The only reported workaround is `[windows] sandbox = "unelevated"`. Users report it, but nobody has confirmed
it, and it was not tried here because it changes the owner's Codex config.

Result: codex-sandbox fails with the desktop app quit. Per the handoff, the agent stopped here and did not
run step 9.

## Third run

Date: 2026-10-13, about 19:51Z, at `0eb2f71`. The run used
`--codex-windows-sandbox unelevated`, a per-run `-c windows.sandbox="unelevated"` override. The owner's
`~/.codex/config.toml` was unchanged: its SHA-256 was the same before and after. The Codex desktop app was still
quit (0 `node_repl` processes). Otherwise the run was as before; the evidence folder is `py-probe-3`.

```
PROBE host Windows-11-10.0.26220-SP0 python=3.14.2 evidence=%USERPROFILE%/AppData/Local/Temp/py-probe-3
PROBE interpreters:python3 pass path=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\python3.EXE runs=True version='3.14.2 %USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe'
PROBE interpreters:python pass path=%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.EXE runs=True version='3.14.3 %USERPROFILE%\AppData\Local\Programs\Python\Python314\python.EXE'
PROBE interpreters:py pass path=%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\py.EXE runs=True version='3.14.2 %USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe'
PROBE codex-sandbox fail launcher=codex.CMD windows_sandbox=unelevated exit=0 header='sandbox: workspace-write [workdir, /tmp, $TMPDIR, %USERPROFILE%\.orchestration-probe-42552\mail]' wrote=False
PROBE hook-fires pass fired=exec,shell exit=0 claude=2.1.296 (Claude Code)
PROBE hook-cost:exec:python3 pass median_ms=228 runs=20
PROBE hook-cost:shell:python3 pass median_ms=340 runs=20
PROBE hook-cost:exec:python pass median_ms=54 runs=20
PROBE hook-cost:shell:python pass median_ms=169 runs=20
```

From `codex-sandbox.err.txt`, trimmed. The setup error is gone, but the command's shell never started:

```
exec
"C:\Program Files\WindowsApps\Microsoft.PowerShell_7.6.6.0_x64__8wekyb3d8bbwe\pwsh.exe" -Command "python3 -c ... .../mail/probe" in ...\probe-work-yvz__ej0
 exited -1 in 0ms:
Failed to create unified exec process: CreateProcessAsUserW failed: 5 (Access is denied.) | cwd=...\probe-work-yvz__ej0 | cmd="C:\Program Files\WindowsApps\Microsoft.PowerShell_7.6.6.0_x64__8wekyb3d8bbwe\pwsh.exe" -Command "..." | env_u16_len=7394 | si_flags=256 | creation_flags=134743040
codex
The command could not run: process creation failed with "Access is denied." I did not retry.
```

The shell codex chose is the Microsoft Store (MSIX) build of PowerShell 7, under `C:\Program Files\WindowsApps`. An
untested hypothesis: the unelevated sandbox's restricted token cannot launch an executable from a Store package.
If so, the same block would hit `python3` and `py` here, which are WindowsApps aliases, even with a
non-Store shell. This was not tried, because it means installing a non-Store PowerShell or changing which shell
codex uses.

Result: codex-sandbox fails under the unelevated sandbox too. Per the handoff, step 9 runs with `--skip-codex`.

## Fourth run: MSI PowerShell 7 and python.org python

Date: 2026-10-13, about 21:14Z, at `a97f6e3`. PowerShell 7.6.6's MSI build was already installed at
`C:\Program Files\PowerShell\7\pwsh.exe` (`winget list` shows `Microsoft.PowerShell 7.6.6.0`, source `winget`), so
the agent ran no install. The Store build is still installed.

The agent's own PowerShell is the Store build, and PowerShell puts its own folder at the front of its children's
PATH. So the probes ran in the MSI `pwsh`, with PATH rebuilt from the registry (Machine, then User), the way a new
window starts. `HERDR_*` was cleared. The owner's `~/.codex/config.toml` was unchanged (same SHA-256), and no
`node_repl` process was running.

`(Get-Command pwsh -All).Source` in that environment:

```
C:\Program Files\PowerShell\7\pwsh.exe
%USERPROFILE%\AppData\Local\Microsoft\WindowsApps\pwsh.exe
```

The MSI build comes first, so the `--codex-drop-path WindowsApps` diagnostic was not needed.

```
PROBE codex-sandbox pass launcher=codex.CMD windows_sandbox=unelevated python=python drop_path=none shell=C:\Program Files\PowerShell\7\pwsh.exe exit=0 header='sandbox: workspace-write [workdir, /tmp, $TMPDIR, %USERPROFILE%\.orchestration-probe-15852\mail]' wrote_by=%USERPROFILE%\AppData\Local\Programs\Python\Python314\python.exe
PROBE codex-sandbox pass launcher=codex.CMD windows_sandbox=unelevated python=python3 drop_path=none shell=C:\Program Files\PowerShell\7\pwsh.exe exit=0 header='sandbox: workspace-write [workdir, /tmp, $TMPDIR, %USERPROFILE%\.orchestration-probe-27388\mail]' wrote_by=%USERPROFILE%\AppData\Local\Python\pythoncore-3.14-64\python.exe
PROBE codex-sandbox fail launcher=codex.CMD windows_sandbox=elevated python=python drop_path=none shell=C:\Program Files\PowerShell\7\pwsh.exe exit=0 header='sandbox: workspace-write [workdir, /tmp, $TMPDIR, %USERPROFILE%\.orchestration-probe-43020\mail]' wrote_by=nothing
```

The lines are in order A (unelevated, `python`), B (unelevated, `python3`), C (elevated, `python`).

- **A passes.** With the MSI `pwsh`, the unelevated sandbox runs commands, and python.org's `python` writes into
  the `--add-dir` mail folder.
- **B passes too.** The Store `python3` alias runs inside the unelevated sandbox, and the file was written by the
  Install Manager's 3.14.2. The third run's hypothesis, that the sandbox blocks every Store-packaged program, is
  wrong: only the Store-packaged `pwsh` under `C:\Program Files\WindowsApps` was refused.
- **C fails as in runs one and two.** The elevated sandbox's setup still fails on `node_repl.exe`, so the MSI
  shell changes nothing there. From `py-probe-4c\codex-sandbox.err.txt`:

```
exec
"C:\Program Files\PowerShell\7\pwsh.exe" -Command 'python -c "..." .../mail/probe' in ...\probe-work-v6ruvera
 exited -1 in 0ms:
Failed to create unified exec process: helper_unknown_error: setup refresh had errors
```

The sandbox log shows the same `runtime read/execute validation failed ... node_repl.exe ... (os error 32)` as
before.

Next (handoff step 5): A passed, so the agent asks the owner whether to set `[windows] sandbox = "unelevated"`.
