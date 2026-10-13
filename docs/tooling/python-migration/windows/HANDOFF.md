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

## Step 9: smoke test (later)

The smoke test runs once phase 1 is ported. A section with its command will be added here then.
