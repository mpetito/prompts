# Performance: why Python, and what the migration bought

Measurements behind [spec.md](spec.md)'s choice of Python and its hook decisions, collected on 2026-10-13. Linux is
the owner's Linux machine (Python 3.14.4, bash 5.3). Windows is the owner's Windows 11 machine (Git Bash 5.2,
Python 3.14). CI is GitHub's `ubuntu-latest` and `windows-latest` runners.

## Interpreter start-up

These figures are start-up only, with no script work.

| Command | Linux | Windows |
| --- | ---: | ---: |
| `bash -c true` | 2 ms | 222 ms (Git Bash) |
| `python3` | 11–13 ms | 387 ms (Store App Execution Alias) |
| `python` (python.org) | not installed | 248 ms |
| `node -e 0` | 19–21 ms | not measured |
| `powershell` 5.1 | n/a | 340 ms |
| `pwsh -NoProfile` (7) | 131–155 ms | 545 ms |

- **Linux:** median of 5–9 runs, taken by both council members and by the coordinator. The ranges cover their three
  measurements.
- **Windows:** average of 20 runs on an idle machine, measured by the owner's Windows agent.
- **Every process start costs about 200 ms or more on Windows,** whatever the language. On Linux the same starts take
  2–20 ms, except PowerShell.
- **The model council chose Python over PowerShell on start-up cost.** Python starts about 10 times faster on Linux
  and 1.4 times faster on Windows, and orchestrator and lane agents start a hook on every tool call.

## The guard hooks, before and after

| Hook | Bash, Linux | Bash, Windows | Python, Linux | Python, Windows |
| --- | ---: | ---: | ---: | ---: |
| guard_bash | 27–47 ms | 2,853 ms | 26–31 ms | 209–230 ms |
| guard_writes | 33 ms | 1,560 ms | 28–30 ms | 298–336 ms |
| guard_timestamps | 21 ms | 220–386 ms | 26–31 ms | 247–284 ms |

- **The bash hooks.**
  - Windows figures are averages of 20, measured outside Claude Code. guard_timestamps was already Python: 220 ms
    as `python`, 386 ms as `python3`.
  - Linux figures are medians of 20 process runs.
- **The Python hooks.**
  - Linux figures are medians of 20, as a process and as the smoke test starts them.
  - Windows figures are medians of 20 in the smoke test, across its two runs, started as Claude Code starts the
    agents' exec-form hooks: `python3 -c` with runpy, no shell.
- **On Windows, each bash hook started a dozen or more processes** (jq, git, cygpath, realpath, grep, awk), and each
  paid Windows' start-up cost. Each Python hook is one process, and it starts git only when its answer needs it.
  Bash commands got about 12–14 times faster and edits about 4.6–5.2 times faster.
- **guard_writes is the slowest Python hook** because it runs two git commands.
- **On Linux, both versions take about the same time,** because process start-up is cheap there.

## How Claude Code starts a hook

These are medians of 20 runs of an empty hook on Windows, from the step 0 probe, across three runs.

| Interpreter | Exec form, no shell | Shell form, through Git Bash |
| --- | ---: | ---: |
| `python3` (Store alias) | 226–233 ms | 340–364 ms |
| `python` (python.org) | 52–57 ms | 162–181 ms |

- **Exec form saves about 110–130 ms per hook.** Shell form runs every hook through Git Bash first. The agents' hooks
  now use exec form. Exec form expands no `$HOME`, so each hook runs its script through
  `runpy.run_path(os.path.expanduser(...))`.
- **The Store alias adds about 175 ms on top of the interpreter.** It turns `python3` into a roughly 230 ms start,
  where python.org's `python` starts in roughly 55 ms. Decision 1 keeps `python3`, because it is the one name every
  Linux machine has. Hooks run as `python` on Windows would drop to roughly 60–170 ms; that is an open option, not
  a decision.
- **On Linux, both forms take 17 ms** for an empty hook.

## The status line, Node and Python

These are medians of 20 runs of `statusline/statusline.js` (Node) and `statusline/statusline.py` (Python), measured
with `windows/statusline_timing.py`. Each run gets the same payload on stdin, with the repository as its working
folder, so each includes one `git status`. Both scripts printed the same line.

| Command | Linux, through bash | Linux, direct | Windows, through Git Bash | Windows, direct |
| --- | ---: | ---: | ---: | ---: |
| `node statusline.js` | 32 ms | 33 ms | pending | pending |
| `python3 statusline.py` | 28 ms | 26 ms | pending | pending |

- **Linux** is Python 3.14.4 and Node 24.21.0, on 2026-10-13.
- **Windows** is pending: the owner's Windows agent runs the script (HANDOFF.md, step 13).
- **How Claude Code runs it.** Claude Code's statusline docs say only that the command "runs in a shell". On Windows
  the script assumes Git Bash, the shell Claude Code runs commands in.
- **Who switches.** Each machine's `statusLine` command is in its own settings, so the owner switches it once these
  numbers are reported.

## Test suites

| Suite | Linux | Windows |
| --- | ---: | ---: |
| Bash orchestration suite | not timed | 5–10 min under Git Bash (owner's machine) |
| Python orchestration suites, 160 + 27 tests | 8 s + 3 s | 66–80 s + 55–57 s (CI runner) |
| Whole CI job, all steps | 25–39 s | 3 min 11–19 s with the bash suites; 1 min 55 s – 2 min 50 s with the Python suites |

## Options evaluated

| Option | Outcome |
| --- | --- |
| Stay on bash | Rejected. It needed shims for Windows paths, CRLF and 8.3 short names, and had the slowest hooks on Windows. A Codex agent whose shell is PowerShell gets WSL's launcher when it runs `bash`. |
| PowerShell 7 | Runner-up. It needed the smallest port, but it starts slowest: 545 ms on Windows and 131–155 ms on Linux, on every hook call. |
| Node | Not chosen. It starts close to Python on Linux. Neither council member chose it. |
| Python 3.12+, standard library only | Chosen. It starts fastest of the scripting languages, has argument lists with no shell quoting, has JSON built in, and resolves native paths. |
| Hook shell form or exec form | Exec form. Both fire, and exec form is 110–130 ms faster per hook on Windows. |
| `python3` or `python` on Windows | `python3` everywhere. `python` is about 175 ms faster per start on the owner's machine. Codex lanes don't need it: the Store `python3` alias runs inside the unelevated sandbox. |

## Not measured

- Node on Windows, until the status line timings arrive.
- The bash orchestration suite's runtime on Linux.
- Hook latency as Claude Code reports it end to end. Every figure here is the hook's own process, from start to exit.
