# Plan: one scripting language, Python 3

Spec: [spec.md](spec.md). This plan follows the spec's decisions:
- `python3`, version 3.12 or later.
- Exec-form hooks if the probe allows them.
- Hooks under 700 ms on Windows and under 100 ms on Linux.
- Options in Python's form.
- Git Bash on Windows, never a `bash` found on PATH, for a lane's check command.
- One pull request per phase.
- Windows probe and smoke-test scripts the owner runs, then eval runs, before a phase lands.

Paths are from the repository root. Work happens in a worktree, `../prompts-py`, on one branch per
phase, `py/<phase>`. Push the branch and open its pull request, so CI runs on it. A phase lands
when its steps are ticked, CI is green and the owner merges the pull request. Close every orchestration build before phase 1 lands.

## Conventions for every step

**Names and entry points.**
- Script files are snake_case (`wake_at.py`), so tests can import them. Each script keeps its
  header comment as its contract. It defines `main(argv) -> int`, and its `__main__` block sets
  stdin and stdout to UTF-8 and exits with `main`'s return value. Setting UTF-8 only there keeps
  the test runner's streams alone. Windows Python 3.14 does not default to UTF-8.
- Usage errors exit 1, as the bash scripts do. Use argparse with `exit_on_error=False`, or a
  parser subclass whose `error()` raises, rather than argparse's default exit code 2.
- Scripts run as `python3 <path>`, never with `-I`. `-I` implies `-P`, which drops the script's own
  folder from `sys.path`, so a sibling import fails; this was checked on 3.14.4. A script imports
  helpers from its own folder. A hook in `hooks/`, and `thread.py`, add the right `scripts/`
  folder to `sys.path` relative to `__file__`, as `thread.sh` sources
  `../../agent-orchestration/scripts/lib.sh` today.
- In prose, a script's path starts `$HOME/.claude/skills/...`, never `~/...`.

**Spawning external commands.** Each component's spawn helper `run()` does all of it:
- It resolves the command with `shutil.which` and runs the resolved path. It sets
  `NoDefaultCurrentDirectoryInExePath`, so a `git.cmd` in a worktree is never picked.
- It passes a list of arguments with `shell=False`, and decodes text as UTF-8.
- On timeout it kills the process tree: `start_new_session` and `os.killpg` on POSIX, and
  `taskkill /T /F /PID` on Windows.

**Paths.** Store `os.path.realpath(p)`, which also resolves 8.3 names for existing paths. Compare
with `same_path(a, b)`, which uses `os.path.normcase` on both. Write a path into prose with
`Path(p).as_posix()`. The default `ORCHESTRATION_HOME` is `Path.home() / ".orchestration"`; on
Windows that is USERPROFILE, which the smoke test confirms matches Git Bash's `$HOME`.

**Tests.**
- Tests use `unittest` in each component's `tests/` folder, with a `tests/__init__.py`. Run them
  with `python3 -m unittest discover -s <component>/tests -t <component>`.
- They call `main()` in-process with `run()` faked for herdr, gh, codex, claude and docker; git is
  real.
- Each entry point also gets one subprocess case that checks its usage error and exit 1.
- Port every bash or PowerShell assertion one for one. Each step's check compares the new case
  count with the source suite's assertion count for the cases it moves, and names any case it
  drops.
- Every new assertion is shown to fail against a planted mutant before its step is ticked.

**References.** The `git grep` checks below exclude the archive, fixture code and dated or
finished records:
`':!archive' ':!docs/skill-audit' ':!docs/orchestration/20*' ':!docs/orchestration/herdr-rework' ':!docs/tooling/python-migration' ':!**/evals/fixtures/**/*.ts' ':!**/evals/fixtures/**/*.py'`
(checked on 0ba7828: today it matches only live references and the scripts themselves).
Fixture prose in `.md` files is updated with its skill.

## Phase 0: Windows probe (before any port)

- [x] 0. `docs/tooling/python-migration/windows/probe.py`, `docs/tooling/python-migration/windows/HANDOFF.md`.
  The probe is a script the owner's Windows agent runs from PowerShell. It also runs on Linux, which
  checks the script itself. It prints one `PROBE` line per check and saves its evidence to a folder.
  Porting goes on while the results are pending; the results go into this plan under the step.
  - (a) A Codex lane, started from PowerShell with `--add-dir` on a mail folder, runs
    `python3 -c "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('ok')" <mail folder>/probe`
    inside its sandbox.
  - (b) A probe hook in exec form, `command: python3` with
    `args: ["-c", "import os,runpy,sys; runpy.run_path(os.path.expanduser('~/.claude/probe_hook.py'), run_name='__main__')"]`,
    is compared with the same hook in shell form, `python3 "$HOME/.claude/probe_hook.py"`.
    - A `claude -p` run with each form in `--settings` shows whether that form fires.
    - The median of 20 spawns along the chain Claude Code uses gives each form's cost: Git Bash
      `bash -c` for shell form, a direct spawn for exec form.
    - Record the Claude Code version.
  - (c) From Python on Windows, `subprocess.run([shutil.which("codex"), "exec", "-c", 'sandbox_mode="read-only"', "--help"])`
    reaches codex with the `-c` value intact through `codex.cmd`.

  Check: (a) writes the file; (b) gives both medians and says whether exec form ran; (c) shows
  the value unchanged. If (a) or (c) fails, stop and ask the owner. (b) decides the hook form for
  step 2.

  Windows, 2026-10-13 (`windows/results/probe.md`; Claude Code 2.1.296, codex-cli 0.161.0):
  - **(b) passed.** Exec-form and shell-form hooks both fire. Median spawn costs were exec 233 ms and shell 342 ms
    with `python3`, which goes through the App Execution Alias, and exec 57 ms and shell 181 ms with `python`.
  - **(c) passed.** A quoted `-c` reaches codex intact through the npm `codex.CMD` shim.
  - **(a) failed, and is waiting on the owner.** It failed for a reason outside this migration. The probe passed
    `--ignore-user-config`, which drops the owner's `[windows] sandbox = "elevated"`, so codex fell back to
    read-only. That flag is now gone. With the owner's config, the sandbox comes up with the `--add-dir` folder
    granted, but every command fails with `setup refresh had errors`. The sandbox log names `node_repl.exe` files
    locked by the running Codex desktop app (os error 32). No command runs in that sandbox, in any language.
  - **Second run, desktop app quit:** the same os error 32. This is a known Codex bug, openai/codex#52488.
  - **Third run, `-c windows.sandbox="unelevated"`, config untouched:** setup succeeds, but the sandbox can't start
    the shell Codex picks, the Microsoft Store build of PowerShell 7 (`CreateProcessAsUserW ... Access is denied`).
  - **Owner's call:** phase 1 goes ahead without a Codex lane on Windows; see Follow-ups. (a) stays failed,
    blocked outside this migration. (b) chose exec form and (c) passed.

## Phase 1: orchestration and its hooks (branch `py/orchestration`)

- [x] 1. `skills/agent-orchestration/scripts/lib.py`, `skills/agent-orchestration/tests/__init__.py`,
  `skills/agent-orchestration/tests/test_lib.py`. Port every helper in `lib.sh`:
  - `utc_now`, `fmt_utc`, `to_epoch`, `need_value`
  - `toplevel`, `session_top`, `resolve_state`, the thread-record reader
  - `owner_checkouts`, `archive_ignored`, the hook `advise`/`deny` writers
  - the path helpers above, and `run()`

  `archive_ignored` copies ignored files before a forced removal; `thread.sh close` depends on it.

  Check: the suite passes. On Windows, `same_path` makes `C:\x`, `C:/x` and an 8.3 spelling of an
  existing folder equal. `archive_ignored` keeps an ignored file's relative path.
- [x] 2. Hooks and their tests:
  - `skills/agent-orchestration/hooks/guard_bash.py`, `guard_writes.py`, and `guard_timestamps.py`
    (renamed from `guard-timestamps.py`)
  - `agents/orchestrator.md`, `agents/lane.md`
  - `skills/agent-orchestration/tests/test_hooks.py`

  Port the hook cases from `tests/run.sh`. Change, don't just copy:
  - The foreground-mail-wait matcher matches `python3 …/mail.py wait`.
  - The deny and advise messages name the `.py` scripts.
  - Add a case for a foreground `python3 …/mail.py wait`.
  - The inode warning uses `os.statvfs` and is skipped where that doesn't exist (Windows).

  Hook entries use the form step 0 chose: exec form,
  `command: python3` with `args: ["-c", "<runpy of os.path.expanduser('~/.claude/.../<hook>.py')>"]`, since exec
  form expands no `$HOME`. Exec-form hooks were confirmed to fire in an agent definition, and `test_hooks.py`
  AgentHooks runs every declared hook as Claude Code would and checks its guard answers. Delete `guard-bash.sh`, `guard-writes.sh` and
  `guard-timestamps.py`.

  Check: the suite passes with the hook assertion count of `tests/run.sh`, plus the new case. On
  Linux, each hook's median of 20 runs on a realistic payload is under 100 ms.
- [x] 3. `skills/agent-orchestration/scripts/state.py`, `decisions.py`, `meter.py`, `wake_at.py`,
  `skills/agent-orchestration/tests/test_state.py`. Port their cases from `tests/run.sh`, then delete
  the four `.sh` files. Check: the suite passes with the source count.
- [x] 4. `skills/agent-orchestration/scripts/mail.py` and
  `skills/agent-orchestration/tests/test_mail.py`: send, read and wait, plus `--home <path>` on
  every subcommand. A Codex lane's sandbox cannot see its pane's environment, so lane briefs pass
  `--home`, not an environment prefix.
  - Delivery stays an atomic rename (`os.replace`).
  - wait polls herdr through `run()`, with its clock and sleep injectable, so the 5-minute unread
    rule is tested without waiting.
  - The ten mailbox mutants in `docs/orchestration/herdr-rework/plan.md` step 2 become named cases.
  - Delete `mail.sh`.

  Check: the suite passes with the source count, and each of the ten mutants fails it.
- [x] 5. `skills/agent-orchestration/scripts/lane.py`, `finish_lane.py`, `land.py`, `land_local.py`,
  `watch_gates.py`, `skills/agent-orchestration/tests/test_lanes.py`.
  - finish-lane refuses while herdr reports an agent in the worktree, whether the path is spelled
    `D:\…`, `D:/…` or relative.
  - A Codex lane's brief gives `mail.py send --home <home>`.
  - land-local runs the check with `bash -c`:
    - On Windows, bash is Git Bash: `CLAUDE_CODE_GIT_BASH_PATH` when set, otherwise the
      `bin\bash.exe` of the Git for Windows install found from `git`. It is never a `bash` found
      by name on PATH, which from PowerShell is WSL's launcher.
    - On Linux, bash is `bash` from PATH.
    - With neither, it prints `STOPPED lane=<branch> no bash for the check command`.
  - Delete the `.sh` files.

  Check: the suite passes with the source count, including the no-bash case and a Windows case
  where a WSL `bash.exe` comes before Git's on PATH.
- [x] 6. `skills/orchestration-main/scripts/thread.py`, `skills/orchestration-main/tests/__init__.py`,
  `skills/orchestration-main/tests/test_thread.py`: launch, stop, rotate, list, check, close and
  integrate.
  - Records store realpath. Briefs get `as_posix` paths.
  - `--env ORCHESTRATION_HOME=<path>` is a native path.
  - Add a test for integrate's path comparison: the previous handoff found that reverting it failed
    nothing.
  - Delete `thread.sh` and `skills/agent-orchestration/scripts/lib.sh`.

  Check: both orchestration suites pass with the source count, and the integrate test fails
  against a mutant that compares unresolved paths.
- [x] 7. Callers:
  - `skills/agent-orchestration/SKILL.md`, `references/*.md`, and the agent-orchestration eval
    fixture prose and `evals/shared-benchmark.json`
  - `skills/orchestration-main/SKILL.md`, and its eval fixture prose and benchmark
  - `agents/*.md`, `instructions/CLAUDE.md`, `CONTRIBUTING.md`, `README.md`

  Each script reference becomes `python3 "$HOME/.claude/skills/<skill>/scripts/<name>.py"`.
  Delete `skills/agent-orchestration/tests/run.sh`.

  Check: `git grep -nE '\b(lib|state|decisions|meter|wake-at|mail|lane|finish-lane|land|land-local|watch-gates|thread|guard-bash|guard-writes)\.sh\b|guard-timestamps\.py|~/\.claude/skills/[a-z-]+/scripts/[a-z_]+\.py' -- <reference excludes>`
  prints nothing.
- [x] 8. `.github/workflows/validate.yml`:
  - `actions/setup-python` with `3.12` on both operating systems, plus a step that fails unless
    `python3 --version` prints `3.12`.
  - The "orchestration scripts and hooks" bash step becomes the two `unittest` commands.

  Check: CI is green on `ubuntu-latest` and `windows-latest`, and the version step shows 3.12 on
  both.
- [x] 9. `docs/tooling/python-migration/windows/smoke.py`, plus a section added to
  `docs/tooling/python-migration/windows/HANDOFF.md`. The script runs on Windows with the branch
  checked out in the main checkout, and uses a separate `ORCHESTRATION_HOME`. It covers:
  - a thread launch;
  - a Claude lane and a Codex lane, started from PowerShell, each mailing the thread;
  - both guards refusing a write into the checkout;
  - `finish_lane.py` while a lane runs and after it closes;
  - rotate, then close, with nothing left behind;
  - each hook's median of 20 runs as Claude Code invokes it.

  It prints one `SMOKE` line per item, and cleans up even when an item fails.

  Check: run on Linux first. On Windows, the owner's agent reports every item passing and each
  hook under 700 ms.

  Linux, 2026-10-13, on 8264100 with Claude Code 2.1.296: every item passed.
  - The thread's write and the Claude lane's write into the checkout were both refused.
  - Both lanes committed and mailed the thread; the Codex lane mailed through `--home` from its sandbox.
  - finish_lane refused a running lane given native, slashed and relative paths, and retired both lanes once
    their panes closed.
  - The thread rotated, and close left no agent, worktree, branch or registry row.
  - Hook medians, shell form through bash: guard_bash 31 ms, guard_writes 30 ms, guard_timestamps 31 ms.
  - The run needed the owner to answer two startup prompts: the thread's folder trust and the Codex lane's.

  Windows, 2026-10-13, at 0eb2f71 with `--skip-codex` (`windows/results/smoke.md`): every item passed.
  - The guards refused the thread's write and the lane's write into the checkout.
  - The Claude lane committed and mailed the thread.
  - finish_lane refused the running lane for each path spelling, then retired it.
  - Rotate, close and cleanup passed.
  - Exec-form hook medians, where the bash hooks took 2,853 and 1,560 ms: guard_bash 230 ms, guard_writes
    336 ms, guard_timestamps 284 ms.
  - Its two script bugs are fixed: a relative path across drives, and read-only git objects left behind.
- [x] 10. Evals: run `agent-orchestration` and `orchestration-main` against main's revision, as
  `docs/evaluating-skills.md` describes. Check: pass rates and trigger rates are no lower than the
  baseline's, or the owner accepts the difference. Then the owner merges the phase's pull request.

  2026-10-13, Opus at high effort, baseline main's revision (0ba7828). The baseline's objective score is low partly
  by construction, because the graders now expect `.py` names; the judge score is the fair comparison.

  | Skill | New: objective / judge | Baseline: objective / judge | No skill: objective / judge |
  |---|---|---|---|
  | agent-orchestration, 1 run per arm | 0.97 / 0.86 | 0.63 / 0.76 | 0.49 / 0.49 |
  | orchestration-main, 3 runs per arm | 0.97 / 0.74 | 0.75 / 0.67 | 0.35 / 0.27 |

  - orchestration-main's single run judged the new skill 0.68 against 0.83. The 3-run rerun shows that was noise.
  - Triggers: orchestration-main fired 9/9 and held back 9/9. agent-orchestration has no trigger cases, because
    the orchestrator agent loads it.

## Phase 2: model council (branch `py/council`)

- [ ] 11. Council scripts and their callers:
  - `skills/model-council/scripts/codex_member.py`, `tally.py`, `run.py` (the spawn helper)
  - `skills/model-council/tests/__init__.py`, `skills/model-council/tests/test_council.py`
  - `skills/model-council/SKILL.md`, the model-council eval fixture prose and benchmark
  - `.github/workflows/validate.yml`

  Port the cases from `tests/run.sh` (timeout, symlinked repository, stale answer, resume,
  malformed answer). Add a timeout case whose fake codex starts a grandchild that writes the answer
  file after the timeout; the stale answer must not be read. Delete the `.sh` files and
  `tests/run.sh`.

  Check: the suite passes with the source count of 46 assertions plus the new case, on both CI
  operating systems. `git grep -nE 'codex-member\.sh|tally\.sh' -- <reference excludes>` prints
  nothing. One real blind round runs from PowerShell on Windows.
- [ ] 12. Evals for `model-council` as in step 10. Then the owner merges the phase's pull request.

## Phase 3: status line and pull-request scripts (branch `py/statusline-pr`)

- [ ] 13. Status line and its setup:
  - `statusline/statusline.py`, `statusline/tests/__init__.py`, `statusline/tests/test_statusline.py`
  - `statusline/README.md`, `README.md`
  - `scripts/Setup.Common.psm1`: link `~/.claude/statusline.py`, and remove a `statusline.js` link
    that points into this checkout

  Render on EOF or at the deadline, whichever comes first, then flush and exit with `os._exit`, so
  a thread blocked on stdin can't hold the process. Delete `statusline.js`.

  Check: the suite passes, including a case where stdin never closes, which must exit within the
  deadline. Node's and Python's medians of 20 runs on both machines are recorded under this step.
  As the step's last action, the owner switches each machine's `statusLine` command.
- [ ] 14. Pull-request scripts and everything that names them:
  - `skills/pull-request/scripts/get_pr_feedback.py`, `resolve_pr_thread.py`, `run.py`
  - `skills/pull-request/tests/__init__.py`, `skills/pull-request/tests/test_pr_scripts.py`
  - `skills/pull-request/SKILL.md`
  - the graders in `skills/pull-request/evals/shared-benchmark.json`
  - `skills/pull-request/evals/planted/**`

  Port both `.Tests.ps1` suites one for one, including "never resolves after a failed reply". Use
  `--thread-id`, `--body` and `--pr`. Rewrite the graders' regexes for
  `resolve_pr_thread(\.py)? … --thread-id`. Delete both `.ps1` scripts and their tests.

  Check: the suite passes with the source count, and
  `git grep -nE 'Resolve-PrThread|Get-PrFeedback|-ThreadId' -- <reference excludes>` prints
  nothing.
- [ ] 15. Evals for `pull-request` as in step 10. Then the owner merges the phase's pull request.

## Phase 4: setup, MCP and eval tooling (branch `py/setup`)

- [ ] 16. Before porting anything, save `pwsh -NoProfile -File ./setup-skills-link.ps1 -WhatIf`
  output from this machine to the scratchpad.

  Port the setup scripts:
  - `scripts/setup_common.py`, `setup_skills_link.py` and `verify_setup.py` (both at the root, as
    today)
  - `tests/__init__.py`, `tests/test_setup.py`
  - `docs/agents-prompts-skills.md`, `README.md`, `instructions/CLAUDE.md`

  Port linking, `--what-if`, conflicts and backups, migration, and the Codex legacy cleanup.
  Verification runs `python3 --version` and `python3 -c "import sys; print(sys.version_info[:2])"`
  as subprocesses, and fails on a missing `python3`, the Store placeholder, or anything below
  3.12. Drop the stale Word COM message.

  Delete `setup-skills-link.ps1`, `verify-setup.ps1` and `tests/Setup.Tests.ps1`. Keep
  `scripts/Setup.Common.psm1` until step 17.

  Check: the suite passes with the source count. `python3 setup_skills_link.py --what-if` prints
  the same link set as the saved PowerShell preview. Verification fails when `PATH` points
  `python3` at a placeholder that exits 9009.
- [ ] 17. `mcp/bootstrap/mcp_common.py`, `install.py`, `verify.py`, `tests/test_mcp.py`,
  `mcp/README.md`. Port prerequisites, previews, native failures, client selection, config backups,
  the JSONC merge and timeout updates. Delete the MCP `.ps1` and `.psm1` files,
  `scripts/Setup.Common.psm1` and `tests/Mcp.Tests.ps1`. Check: the suite passes with the source
  count.
- [ ] 18. The eval tooling and its docs:
  - `scripts/run_skill_eval.py`, plus `scripts/agent_eval_backend.py`, `skill_usage.py` and
    `trigger_matrix_shim.py` renamed from kebab-case
  - `skills/pull-request/evals/stage_plugin_baseline.py`, `check_assertions.py`
  - `skills/pull-request/evals/README.md`, `README.md`, `docs/evaluating-skills.md`,
    `CONTRIBUTING.md` (`--baseline`), `.gitignore`

  Delete both `.ps1` files.

  Check: `python3 scripts/run_skill_eval.py --skill pull-request --trigger-only` completes, and so
  does one `--regrade` of an existing run.
- [ ] 19. `.github/workflows/validate.yml`, `CONTRIBUTING.md`, `README.md`:
  - CI runs every `unittest` suite on both operating systems under setup-python 3.12, and drops
    the pwsh steps, the node step and the PowerShell parse check.
  - CONTRIBUTING: "Scripts are Python 3.12+, standard library only, run as
    `python3 \"$HOME/...\"` or by a repository-relative path."

  Check: CI is green.
  `git ls-files ':!archive' ':!**/evals/fixtures/**' | grep -E '\.(sh|ps1|psm1|js)$'` prints
  nothing, and
  `git grep -nE '\b(pwsh|node) [^ ]*\.(ps1|js)\b' -- <reference excludes>` prints nothing.
- [ ] 20. Evals for each skill whose text changed in this phase, as in step 10. Then the owner merges the phase's
  pull request.

## Follow-ups

- **Codex lanes on Windows** don't run on the owner's machine in any language.
  - The elevated sandbox's setup fails with os error 32 (openai/codex#52488).
  - The unelevated sandbox can't launch the Store-packaged PowerShell 7 Codex picks.
  - If unelevated can't launch any Store-packaged program, `python3` would be blocked too: on that machine it is a
    Store App Execution Alias, while `python` is a python.org install. That is untested.
  - Paths to try:
    - a Codex fix;
    - an MSI install of PowerShell 7, with Codex pointed at it;
    - lanes on Windows invoking a non-Store Python.
  - The last one would revisit decision 1 for Windows Codex lanes only.
