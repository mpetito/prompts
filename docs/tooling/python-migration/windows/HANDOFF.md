# Windows handoff: Python migration

For the agent on the owner's Windows machine. The repository is moving every script to Python 3
([spec](../spec.md), [plan](../plan.md)). Work happens on branch `py/orchestration` of
github.com/mpetito/prompts. Your part is to run scripts here that only Windows can answer, and to
commit what they print. Leave the port itself to the Linux session.

Standing rules:
- No AI attribution in commits.
- Commit only the results files named below, and push only branch `py/orchestration`.
- Never write a project name, session id or pull request link into tracked files.

## Step 0: probe (done)

The probe checks three things before phase 1 is ported:
- that `python3` runs inside a Codex sandbox and can write a mail folder;
- whether exec-form hooks fire in Claude Code;
- what each hook form costs on Windows.

Run it from PowerShell, not Git Bash, so codex starts the way a PowerShell-hosted lane would:

```powershell
git fetch mpetito py/orchestration
git worktree add -b py/orchestration ..\prompts-py mpetito/py/orchestration
cd ..\prompts-py
python3 docs\tooling\python-migration\windows\probe.py $env:TEMP\py-probe
```

It makes two short model calls, one to codex and one to claude, and takes about a minute. It
prints one `PROBE` line per check and exits 1 if any check failed.

Then write `docs/tooling/python-migration/windows/results/probe.md` containing:
- the date;
- the `PROBE` lines, verbatim;
- `claude --version` and `codex --version`;
- where `codex` resolves (`(Get-Command codex).Source`);
- for any failed check, the matching `*.err.txt` from the evidence folder, trimmed to the lines
  that explain it.

Commit that one file, then `git pull --rebase mpetito py/orchestration` (the Linux session pushes
to the same branch) and `git push mpetito py/orchestration`.

What the Linux session does with each result:
- **`codex-sandbox` fails:** stop and ask the owner. Lanes started from PowerShell could not
  report by mail.
- **`hook-fires` reports only `shell`:** hooks stay in shell form, and the hook budget becomes
  bash plus Python.
- **The `hook-cost` lines:** they set what the 700 ms hook bound has to absorb.

## Step 0, second run: the Codex sandbox (done)

The first run is recorded in `results/probe.md`. codex-sandbox failed: with the owner's config, every command in
the sandbox failed with `setup refresh had errors`. The sandbox log blamed `node_repl.exe` files that the running
Codex desktop app held open. The owner chose to test that explanation:

1. Pull the branch. The probe's codex check no longer passes `--ignore-user-config`, so it runs with the owner's
   `[windows] sandbox` setting, as a real lane does.
2. The owner closes the Codex desktop app. Confirm that no `node_repl.exe` from
   `%USERPROFILE%\AppData\Local\OpenAI\Codex\runtimes` is still running
   (`Get-Process node_repl -ErrorAction SilentlyContinue`).
3. Run the probe again from PowerShell, exactly as before.
4. Append a "Second run" section to `results/probe.md`. Include:
   - the `PROBE` lines, verbatim;
   - whether any `node_repl` process was running;
   - if codex-sandbox fails again, the new lines of `%USERPROFILE%\.codex\.sandbox\sandbox.<date>.log`.
5. Commit, pull with rebase, and push, as before. The owner can reopen the Codex app afterwards.

If codex-sandbox passes, go on to step 9 with the Codex app still closed. If it fails, stop and report: the
Linux session takes it to the owner.

## Step 0, third run: the unelevated sandbox (done)

The second run (`results/probe.md`) confirmed a known Codex bug, openai/codex#52488. With
`[windows] sandbox = "elevated"`, setup fails with os error 32, and no command runs, whether the desktop app is open
or not. The reported workaround is the `unelevated` sandbox. It uses a restricted token derived from the owner's
own user instead of a separate sandbox user, and it blocks the network through environment variables, not firewall
rules. The owner chose to test it without editing their config:

1. Pull the branch. The probe now takes `--codex-windows-sandbox`, which passes a `-c` override for the codex
   check alone.
2. From PowerShell, run:
   `python3 docs\tooling\python-migration\windows\probe.py $env:TEMP\py-probe-3 --codex-windows-sandbox unelevated`
3. Append a "Third run" section to `results/probe.md`: the `PROBE` lines, verbatim, and, if codex-sandbox fails, the
   matching `codex-sandbox.err.txt` lines. Commit, then pull with rebase and push.
4. Then:
   - **codex-sandbox passes:** ask the owner whether to set `[windows] sandbox = "unelevated"` in
     `~/.codex/config.toml`. A lane uses the owner's config, so the smoke test's Codex lane needs it. Never edit it
     yourself. If the owner switches it, run step 9 in full. If not, run step 9 with `--skip-codex`.
   - **codex-sandbox fails:** run step 9 with `--skip-codex`.

## Codex lanes on Windows: PowerShell 7 from the MSI, and python.org's python (now)

The third probe showed that the unelevated sandbox gets through setup but can't launch Codex's shell. Codex runs
every command in `pwsh` when PATH has it, falling back to Windows PowerShell 5.1, and offers no setting for the shell
(openai/codex#49716, #53160). On this machine `pwsh` is the Microsoft Store build, and the sandbox refuses to launch
it (`CreateProcessAsUserW ... Access is denied`). `python3` is also a Store alias here, while `python` is a
python.org install.

The owner chose to install PowerShell 7's MSI build, which isn't Store-packaged, and to have Codex lanes on Windows
run python.org's `python`. The question is whether the unelevated sandbox runs commands with both. Don't edit
`~/.codex/config.toml` or PATH yourself.

1. **Install PowerShell 7 from the MSI.** The owner approved it:
   `winget install --id Microsoft.PowerShell --source winget`. The owner answers the UAC prompt. Leave the Store
   build installed.
2. **Check which `pwsh` comes first.** In a new PowerShell window, so PATH is refreshed, record
   `(Get-Command pwsh -All).Source`. The first entry should be `C:\Program Files\PowerShell\7\pwsh.exe`. If the
   WindowsApps alias still comes first, Codex would keep picking the Store build. Run probe A once more with
   `--codex-drop-path WindowsApps` as a diagnostic, which hides the Store aliases from codex alone, then stop and
   report.
3. **Pull the branch, then run the probe three times from that window.** The probe now takes `--codex-python`,
   `--codex-drop-path` and `--only codex`, and reports which shell codex launched and which interpreter wrote the
   file:
   - (A) The target setup:
     `python3 docs\tooling\python-migration\windows\probe.py $env:TEMP\py-probe-4a --only codex --codex-windows-sandbox unelevated --codex-python python`
   - (B) Whether the Store `python3` alias can run in the sandbox. Same as A, with `--codex-python python3` and
     `py-probe-4b`.
   - (C) Whether the elevated sandbox now works. Same as A, with `--codex-windows-sandbox elevated` and
     `py-probe-4c`.
4. **Record the results.** Append a "Fourth run" section to `results/probe.md` with:
   - the `pwsh` list from step 2;
   - the three `PROBE codex-sandbox` lines, verbatim;
   - for each failure, the matching `codex-sandbox.err.txt` lines.

   Commit, then pull with rebase and push.
5. **Then:**
   - **A or C passes:** a lane uses the owner's config, so ask the owner whether to set `[windows] sandbox` to the
     mode that passed. If C passed, the owner's current `elevated` may already be right. Once the config holds a
     passing mode, run the smoke test with the Codex lane:
     `python3 docs\tooling\python-migration\windows\smoke.py --codex-python python`. Do this from %TEMP%, with the
     branch checked out in `D:\prompts` as before, and record it as "Second run, with Codex" in
     `results/smoke.md`.
   - **A and C both fail:** stop and report.

## Step 9: smoke test (done without Codex)

`smoke.py` runs one throwaway build with real agents and real herdr: a thread, a Claude lane and a Codex lane. Along
the way it checks:
- that the guards refuse writes into the checkout;
- that finish_lane refuses a running lane, however its path is spelled;
- that the thread rotates and the build closes;
- what each hook costs when started the way Claude Code starts it.

It passed every item on Linux on 2026-10-13.

1. **Make the branch what `~/.claude` runs.** The installed skills and agents link into `D:\prompts`. Check out the
   phase branch's head there, detached, since the branch may be checked out in another worktree:
   `git -C D:\prompts fetch mpetito` and then
   `git -C D:\prompts checkout --detach mpetito/py/orchestration`. Every session on this machine now runs the
   branch, so first make sure no orchestration build is running (`python3 ...\thread.py list` prints NONE, or
   check `threads.tsv`).
2. **Run it from a PowerShell pane inside herdr,** so codex starts the way a PowerShell-hosted lane would:
   `python3 docs\tooling\python-migration\windows\smoke.py`, adding `--skip-codex` when step 0 says to. It takes
   5–10 minutes. Its build and its
   `ORCHESTRATION_HOME` live in a temporary folder.
3. **The owner answers the startup prompts.** Each new folder gets Claude Code's trust prompt: the thread's
   workspace and possibly the Claude lane's worktree. The Codex lane may show its own first-run prompt. The script
   prints `BLOCKED <agent>` and waits up to 15 minutes for each. Never answer a trust prompt yourself.
4. **Put `D:\prompts` back on main:** `git -C D:\prompts checkout main`.

Then write `docs/tooling/python-migration/windows/results/smoke.md` containing:
- the date;
- every `SMOKE` line, verbatim;
- `claude --version`, `codex --version` and `herdr --version`;
- for a failed item, what the agent's pane showed.

Commit and push it as in step 0. If the script is interrupted, check that no `smk*` agents are left
(`herdr agent list`); its cleanup closes them and removes its temporary folder.

## Phase 2: one blind round of the model council (now)

The model council's scripts are Python now, on branch `py/council`. The Codex member runs
`codex exec --ignore-user-config`, which also drops the owner's `[windows] sandbox` setting, so on
Windows `codex_member.py` passes `-c windows.sandbox="unelevated"` itself. `council_round.py` runs one
real blind round, a Codex member and a Claude member on a throwaway repository, and proves from Codex's
own sandbox log which mode ran the member's commands. Don't edit `~/.codex/config.toml`.

1. **Check out the branch:** `git fetch mpetito py/council`, then
   `git worktree add -b py/council ..\prompts-council mpetito/py/council` and `cd ..\prompts-council`.
2. **Close every Codex session:** the desktop app, any `codex` CLI session or herdr lane, and an IDE's
   Codex extension. Confirm with `Get-Process codex*, node_repl -ErrorAction SilentlyContinue`, which
   should print only `codex-windows-sandbox-service`: that is Codex's sandbox service, which is expected
   to keep running, so leave it. Every other session writes `%USERPROFILE%\.codex\.sandbox\sandbox.<date>.log`,
   the log the round reads, so the round's preflight refuses to start while any other `codex*` process
   runs, and sandbox-mode fails if one appears during the round.
3. **Run the round from PowerShell 7's MSI build,** in a new window, so a non-Store `pwsh` comes first
   on PATH as in the fourth probe run:
   `python3 docs\tooling\python-migration\windows\council_round.py`. It makes one Codex call and one
   Claude call, takes about five minutes, and prints one `ROUND` line per check. It builds its throwaway
   repository beside the checkout (`D:\council-round-<hex>` for `D:\prompts-council`) and removes it at
   the end.
   - The first round built it under `%TEMP%` with `tempfile.mkdtemp`, which on Python 3.13+ gets an ACL
     for the current user and administrators only. Codex's unelevated sandbox could list that folder
     but read none of its files.
   - A real council runs on a checkout like `D:\prompts`, whose files inherit the drive's ACL. So the
     round's repository now lives there too, created with the parent's inherited permissions.
   - Each member must quote a `REVIEW_PIN` value that exists only in the repository's `cache.py`. A member
     that could not read the repository fails `codex-member` or `claude-member`, and so does any command
     refused with "access denied".
4. **Record the results.** The script writes `docs/tooling/python-migration/windows/results/council-round-windows/`,
   already scrubbed for a public repository (`%USERPROFILE%`, `<user>`, `<session>`, no command output).
   The `scrubbed` check fails if anything survives; then commit nothing and report. Otherwise read every
   file in the folder before committing: the answers and Codex's messages are kept verbatim, and nothing
   in them may name a project, a person or a private path. Then commit that folder,
   `git pull --rebase mpetito py/council` and `git push mpetito py/council`.
5. **Then:**
   - **Every check passes:** report that, and the round is done. If sandbox-mode's facts say
     `unverified for this version`, the installed Codex is not the release the log rule was read from
     (0.162.1). Report it with the version, and the Linux session rechecks the rule against that release.
   - **`preflight` fails with `other_codex=...`:** a Codex process is still running. Close it (step 2)
     and run the round again.
   - **`sandbox-mode` fails with `sandbox_log_setup_helper` above 0:** Codex took the elevated path, so
     the override did not reach it. Stop and report the `ROUND` lines. The sandbox log is shared and is
     never committed.
   - **`sandbox-mode` fails with `other_codex=...`:** another Codex process started during the round.
     Close it and run the round again.
   - **`sandbox-mode` fails with `sandbox_log_start=0`:** no command went through the Windows sandbox.
     If `round0-codex.log` shows `CreateProcessAsUserW ... Access is denied`, the Store `pwsh` came first
     on PATH: record `(Get-Command pwsh -All).Source`. Stop and report.
   - **`codex-member` fails with `pin_quoted=False` or `access_denied` above 0:** the Codex member could
     not read the repository even beside the checkout. Stop and report the `ROUND` lines and
     `(Get-Acl D:\).Access | Format-Table IdentityReference, FileSystemRights`.
   - **Any other failure:** stop and report the `ROUND` lines and the matching evidence file.
