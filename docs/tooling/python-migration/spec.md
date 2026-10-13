# One scripting language: Python 3

## Why

The repository's tooling is written in four languages. Bash covers orchestration, the model
council and their hooks. PowerShell covers setup, MCP bootstrap, the pull-request scripts and the
eval runner. Python covers a hook and the eval helpers, and Node the status line. The owner works on
Linux and on native Windows, and wants one convention.

Bash on Windows works only under Git Bash, and only through shims the repository maintains itself:
- Paths come in three spellings that have to be reconciled before any comparison.
- Native tools write CRLF.
- Paths written into prompts have to be converted by hand.
- GitHub's Windows runners spell the temp folder in 8.3 short form.
- An agent whose shell is PowerShell, such as Codex on Windows, gets WSL's launcher when it runs
  `bash`, which fails on the owner's machine.

Before the Git Bash port, one of these gaps let a write into the owner's checkout past the write
guard.

The second problem is speed. On the owner's Windows machine (average of 20 runs, measured outside
Claude Code), the bash Bash-command hook takes 2,853 ms and the bash write hook 1,560 ms. Each
starts a dozen or more processes, and process start-up is slow on Windows. Orchestrator and lane
agents pay that before every command and every edit. By comparison:
- Python starts in 248 ms as `python` and in 387 ms as `python3`, which goes through an App
  Execution Alias.
- PowerShell 7 starts in 545 ms.

On Linux, Python starts in about 13 ms and PowerShell in about 150 ms.

On 2026-10-13 a two-member model council debated the choice (one Claude on Opus, one Codex on
GPT-6 Astra). It started split between Python and PowerShell. After one exchange both chose Python,
because of the hooks' start-up cost. The council's record was not kept in the repository.

## What changes

- **Every script outside the archive is Python 3:** orchestration scripts and hooks, the
  model-council scripts, the status line, the pull-request scripts, setup and verification, MCP
  bootstrap, the eval runner and helpers, and every test suite.
- **Each command keeps its behaviour.** Every script keeps its subcommands, its one-line results
  (MAIL, BLOCKED, LANDED, STOPPED, COUNCIL, MEMBER, GATES and the rest), its exit codes (1 for a
  usage error, as today) and its files. What changes:
  - Its file name.
  - How it is invoked.
  - Options on the former PowerShell scripts, which take the Python form (decision 4).
- **Invocation names the interpreter and a portable path.** Skills, agent hooks, briefs, CI and docs
  run every script as `python3` followed by a path that bash, PowerShell 7 and Windows
  PowerShell 5.1 all expand: under `$HOME`, never `~`, or an absolute path the thread wrote.
  - No script relies on a shebang, an executable bit, a file association or a shell-specific
    environment prefix.
  - Settings a sandboxed agent cannot inherit from its pane are passed as options.
  - cmd is not a supported shell.
- **Native paths, no translation layer.** Scripts store paths as the OS resolves them, which also
  turns 8.3 names into long ones. They compare paths case-insensitively where the OS does, and
  write a path into prose with forward slashes, which bash and native tools both open. The
  shims for Git Bash paths, CRLF and short names go away.
- **External tools are called directly, without a shell:** git, herdr, gh, codex, claude and docker
  get a list of arguments, so there is no quoting and no path rewriting.
  - A timeout stops the whole process tree, so an npm shim's child cannot finish after its
    timeout.
  - The one exception is a repository's own check command, which is shell text by nature
    (decision 5).
- **Each skill stays self-contained.** A skill is linked into a client on its own, so it cannot
  import another skill's code. The one exception exists today: orchestration-main uses
  agent-orchestration's helpers. Each component carries its own small spawn helper.
- **The standard library only,** except the eval helpers, which already import the eval harness.
  On the owner's Windows machine `python` and `python3` reach different installs, and a package
  installed into one is missing from the other.
- **One test framework:** the standard library's, on Linux and on Windows.
  - Tests call each script's entry point in-process, with the external CLIs faked at the spawn
    helper. git is real.
  - A few end-to-end cases run each script as a process.
  - Each existing assertion is ported one for one and counted against its source suite.
  - Every assertion is shown to fail against a planted mutant before it lands.
- **Faster hooks:** each hook is one Python process, and it spawns git only when its answer needs
  it.
- **Setup checks the interpreter it depends on.** Verification runs `python3` as a separate process
  and fails when it is missing, is the Microsoft Store placeholder, or is older than the minimum
  version.
- **References follow the scripts.** Any prose that tells an agent or a person how to run a
  migrated script is updated: skills, agents, references, live docs, eval fixtures and benchmark
  expectations. Fixture code (sample projects in other languages) is not updated. Neither are
  dated or finished records: spikes, retrospectives, audits, finished specs and plans, and the
  skill-audit candidates ledger.
- **Delivered in four phases:**
  1. Orchestration and its hooks: the speed win and the Codex-on-Windows fix.
  2. The model council.
  3. The status line and the pull-request scripts.
  4. Setup, MCP and the eval tooling.

  A phase deletes what it replaces when it lands: no shims, and no old names kept alive. Each
  phase that changes a skill runs that skill's evals against the previous revision, as
  CONTRIBUTING requires.
- **CI** runs the Python suites on Ubuntu and Windows at the minimum Python version. Steps for a
  language with no scripts left are removed. CONTRIBUTING names Python, its minimum version and
  the invocation rule as the convention.

## Out of scope

- Guarding PowerShell-tool commands. The Bash-command guard still reads Bash tool input; covering
  the PowerShell tool is a separate decision.
- Archived skills, fixture code, and dated or finished records. They keep the names they had.
- A packaged install: pip, a virtual environment or a lock file.

## Constraints

- **No live orchestration build across phase 1 landing,** and the migration itself does not run as
  an orchestration build. Threads, lanes, their registry rows, briefs and mail were written by the
  bash scripts.
- **Phase 1 needs a Windows probe before any code is ported:**
  - A Codex lane started from PowerShell runs `python3` inside its sandbox and writes its mail
    folder.
  - Hook timing is measured the way Claude Code invokes a hook.

  The probe is a script the owner runs on Windows. Porting may start before its results arrive,
  but if it fails, phase 1 stops for the owner before anything lands.
- **Skills are linked into each client from the main checkout,** so a phase takes effect when it
  lands on main and the checkout is pulled. Work happens on a branch in a separate worktree, and
  the branch is pushed so CI runs on it. A Windows test that needs the real hooks means checking
  the branch out in the Windows main checkout, which makes it live in every session there.
- **The status line command lives in each machine's own Claude Code settings,** not in the
  repository. When phase 3 lands, setup removes the old link, and the owner changes each machine's
  setting.

## Decisions

The owner answered the open questions on 2026-10-13.

1. **Interpreter command:** `python3` everywhere. Setup verification rejects the Store placeholder.
   `python3` is guaranteed on Linux and resolves on the owner's Windows machine, through an alias
   that costs about 140 ms more than `python`.
2. **Minimum version:** Python 3.12. It matches Ubuntu 24.04 and GitHub's Ubuntu runner. From 3.12,
   Windows executable lookup also honours PATHEXT for names that include a directory or an
   extension.
3. **Hooks:** exec form if the phase 1 probe shows it works through the App Execution Alias,
   otherwise shell form. Shell form runs through Git Bash on Windows, so bash start-up (222 ms)
   comes before Python's. Each hook's median over 20 runs, measured as Claude Code invokes it, is
   under 700 ms on the owner's Windows machine (today 1,560 and 2,853 ms) and under 100 ms on
   Linux.
4. **Options on the former PowerShell scripts** take Python's form (`--thread-id`, `--what-if`).
   The pull-request benchmark's graders, the eval docs and CONTRIBUTING change in the same phase.
5. **A lane's check command, when a build lands locally,** is shell text the thread writes, such
   as `npm test && pytest`, so a shell has to run it. It runs in bash, never in a bash found by
   name on Windows PATH: from PowerShell that is WSL's launcher.
   - On Windows it runs in Git Bash, found the way Claude Code finds it: `CLAUDE_CODE_GIT_BASH_PATH`
     when set, otherwise the `bin\bash.exe` of the Git for Windows install that holds `git`.
   - On Linux it runs in `bash` from PATH.
   - With neither, the landing stops and says so.

   (The owner's answer to the first default, "bash on PATH", was that it might fail on Windows;
   this form is the fix.)
6. **The status line moves to Python too.** Node and Python are measured on both machines, and the
   numbers are reported before the owner switches each machine's setting.
7. **Each phase lands through its own pull request.** CONTRIBUTING's rule against pull requests is
   meant for small skill updates, not a change of this size.
8. **Phase 1 gets a live Windows smoke test before it lands,** written as a script the owner runs
   on Windows. It is committed to the phase branch with a short handoff for the Windows agent, and
   covers a thread, a Claude lane, a Codex lane started from PowerShell, guards, finish-lane,
   rotation, close, cleanup and hook timings.
9. **Each changed skill's evals run before its phase lands:** the trigger-only suite and one
   behaviour run against the previous revision.
