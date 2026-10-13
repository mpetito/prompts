# Windows handoff: Python migration

For the agent on the owner's Windows machine. The repository is moving every script to Python 3
([spec](../spec.md), [plan](../plan.md)). Work happens on branch `py/orchestration` of
github.com/mpetito/prompts. Your part is to run scripts here that only Windows can answer, and to
commit what they print. Leave the port itself to the Linux session.

Standing rules:
- No AI attribution in commits.
- Commit only the results files named below, and push only branch `py/orchestration`.
- Never write a project name, session id or pull request link into tracked files.

## Step 0: probe (now)

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

## Step 0, second run: the Codex sandbox (now)

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

## Step 0, third run: the unelevated sandbox (now)

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

## Step 9: smoke test

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
   `python3 docs\tooling\python-migration\windows\smoke.py`. It takes 5–10 minutes. Its build and its
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
