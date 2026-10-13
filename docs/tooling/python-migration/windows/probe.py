"""Probe what phase 1 of the Python migration assumes about Windows (plan.md step 0), before it lands.

    python3 probe.py <evidence dir> [--codex-model <id>] [--claude-model <id>] [--runs <n, default 20>]
                     [--codex-windows-sandbox elevated|unelevated] [--codex-python <command or path>]
                     [--codex-drop-path <text>] [--only codex]

Run it from PowerShell on the owner's Windows machine; it also runs on Linux, which checks the script itself.
Prints one line per check, then exits 1 if any check failed:

    PROBE <check> pass|fail <facts>

Checks:
  interpreters    which of python3, python and py resolve, to what, and whether each one runs (a Microsoft Store
                  placeholder resolves but does not)
  codex-sandbox   codex exec, given -c 'sandbox_mode="workspace-write"' (a quoted value, which an npm codex.cmd shim
                  passes through cmd.exe) and --add-dir on a folder outside its workdir and temp, reports that
                  sandbox and runs python3 inside it to write a file in that folder
  hook-fires      a claude -p run with one exec-form hook (command python3, args, no shell) and one shell-form hook
                  (python3 "<path>") on Bash shows which of the two Claude Code ran
  hook-cost       median milliseconds of <runs> spawns of an empty hook along each chain Claude Code uses: shell
                  form through bash -c (Git Bash on Windows), exec form spawned directly, for python3 and python

--codex-python picks the interpreter the sandboxed shell runs (default python3), and --codex-drop-path removes the
PATH entries containing its text from codex's environment: codex runs pwsh when PATH has it, and on the owner's
machine that is the Store build in WindowsApps, which the unelevated sandbox can't launch. --only codex runs that
check alone. --codex-windows-sandbox overrides the [windows] sandbox setting for the codex check alone, with a -c option, so a
mode can be tried without editing the owner's Codex config.

Each model call is one short, mechanically checked task. Evidence (command lines, outputs, the settings file) goes
to the evidence dir. The mail folder made under the home directory is removed at the end.
"""
import argparse
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOK = """import json, pathlib, sys, time
mode, marker = sys.argv[1], sys.argv[2]
payload = sys.stdin.read()
if mode != "time":
    tool = json.loads(payload or "{}").get("tool_name", "")
    with open(marker, "a", encoding="utf-8") as f:
        f.write(f"{mode} {tool} {time.time():.3f}\\n")
"""

failed = False


def report(check, ok, facts):
    global failed
    failed |= not ok
    print(f"PROBE {check} {'pass' if ok else 'fail'} {facts}", flush=True)


def spawn(args, evidence, name, stdin="", cwd=None, timeout=300):
    """Run args without a shell, save the command line and output under evidence/<name>.*, return the result."""
    (evidence / f"{name}.cmd.txt").write_text(json.dumps(args, indent=1), encoding="utf-8")
    try:
        r = subprocess.run(args, input=stdin, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           cwd=cwd, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        (evidence / f"{name}.err.txt").write_text(repr(e), encoding="utf-8")
        return None
    (evidence / f"{name}.out.txt").write_text(r.stdout, encoding="utf-8")
    (evidence / f"{name}.err.txt").write_text(r.stderr, encoding="utf-8")
    return r


def git_bash():
    """The bash Claude Code's shell-form hooks run in: Git Bash on Windows, found as Claude Code finds it."""
    if os.name != "nt":
        return shutil.which("bash")
    if os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"):
        return os.environ["CLAUDE_CODE_GIT_BASH_PATH"]
    git = shutil.which("git")
    for d in Path(git).resolve().parents if git else []:
        if (d / "bin" / "bash.exe").is_file():
            return str(d / "bin" / "bash.exe")
    return None


def interpreters(evidence):
    found = {}
    for name in ("python3", "python", "py"):
        path = shutil.which(name)
        r = path and spawn([path, "-c", "import sys; print(sys.version.split()[0], sys.executable)"], evidence,
                           f"interp-{name}", timeout=60)
        runs = bool(r and r.returncode == 0 and r.stdout.strip())
        found[name] = path if runs else None
        report(f"interpreters:{name}", runs or name != "python3", f"path={path} runs={runs} "
               f"version={r.stdout.strip() if runs else (r.stderr.strip()[:80] if r else 'n/a')!r}")
    return found


def codex_sandbox(evidence, model, windows_sandbox=None, python="python3", drop_path=None):
    """Ask codex to run python inside its workspace-write sandbox and write sys.executable into an --add-dir folder.

    python is the command the sandboxed shell runs: a name on PATH, or a full path. drop_path removes every PATH
    entry containing that text (case-insensitive) from codex's environment, so a shell or interpreter found there,
    such as the Store's pwsh and python3 aliases in WindowsApps, is out of reach. Reports which shell codex launched
    and which interpreter wrote the file."""
    env = dict(os.environ)
    if drop_path:
        env["PATH"] = os.pathsep.join(d for d in env["PATH"].split(os.pathsep) if drop_path.lower() not in d.lower())
    codex = shutil.which("codex", path=env["PATH"])
    if not codex:
        return report("codex-sandbox", False, "codex is not on PATH")
    mail = Path.home() / f".orchestration-probe-{os.getpid()}" / "mail"
    mail.mkdir(parents=True)
    work = Path(tempfile.mkdtemp(prefix="probe-work-"))
    target = mail / "probe"
    # Codex's shell is PowerShell on Windows, where a quoted full path needs the call operator, and bash elsewhere.
    is_path = "/" in python or "\\" in python
    launch = (f"& '{python}'" if os.name == "nt" else f"'{python}'") if is_path else python
    command = (f"{launch} -c \"import pathlib,sys; pathlib.Path(sys.argv[1]).write_text(sys.executable)\" "
               f"{target.as_posix()}")
    try:
        # The owner's own config, as a lane runs: on Windows, workspace-write needs its [windows] sandbox setting, and
        # --ignore-user-config would drop it and fall back to read-only.
        override = ["-c", f'windows.sandbox="{windows_sandbox}"'] if windows_sandbox else []
        args = [codex, "exec", "--skip-git-repo-check", "-m", model, *override, "-c", 'sandbox_mode="workspace-write"',
                "--add-dir", str(mail), "-C", str(work),
                f"Run exactly this shell command once, then reply DONE: {command}"]
        (evidence / "codex-sandbox.cmd.txt").write_text(json.dumps(args, indent=1), encoding="utf-8")
        try:
            r = subprocess.run(args, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", cwd=work, env=env, timeout=300)
        except (OSError, subprocess.TimeoutExpired) as e:
            return report("codex-sandbox", False, f"codex did not run: {e!r}")
        (evidence / "codex-sandbox.out.txt").write_text(r.stdout, encoding="utf-8")
        (evidence / "codex-sandbox.err.txt").write_text(r.stderr, encoding="utf-8")
        lines = r.stderr.splitlines()
        header = next((l for l in lines if l.startswith("sandbox:")), "")
        # Codex logs each command as "exec", then the shell and its arguments on the next line.
        shell = next((re.match(r'\s*(?:"([^"]+)"|(\S+))', lines[i + 1]).group(1, 2) for i, l in enumerate(lines[:-1])
                      if l.strip() == "exec" and lines[i + 1].strip()), ("unknown", None))
        shell = shell[0] or shell[1]
        wrote = target.read_text(encoding="utf-8") if target.is_file() else ""
        report("codex-sandbox", "workspace-write" in header and bool(wrote),
               f"launcher={Path(codex).name} windows_sandbox={windows_sandbox or 'config'} python={python} "
               f"drop_path={drop_path or 'none'} shell={shell} exit={r.returncode} header={header!r} "
               f"wrote_by={wrote or 'nothing'}")
    finally:
        shutil.rmtree(mail.parent, ignore_errors=True)
        shutil.rmtree(work, ignore_errors=True)


def hook_fires(evidence, model, python3):
    claude = shutil.which("claude")
    if not (claude and python3):
        return report("hook-fires", False, f"claude={claude} python3={python3}")
    hook = evidence / "probe_hook.py"
    marker = evidence / "hook-fired.txt"
    marker.unlink(missing_ok=True)
    run_exec = f"import runpy,sys; sys.argv=['hook','exec',r'{marker}']; runpy.run_path(r'{hook}', run_name='__main__')"
    settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
        {"type": "command", "command": "python3", "args": ["-c", run_exec], "timeout": 30},
        {"type": "command", "command": f'python3 "{hook.as_posix()}" shell "{marker.as_posix()}"', "timeout": 30},
    ]}]}}
    path = evidence / "probe-settings.json"
    path.write_text(json.dumps(settings, indent=1), encoding="utf-8")
    r = spawn([claude, "-p", "Use the Bash tool exactly once to run: echo probe. Then reply DONE.", "--model", model,
               "--settings", str(path), "--allowedTools", "Bash(echo probe)", "--debug-file",
               str(evidence / "claude-debug.log")], evidence, "hook-fires")
    lines = marker.read_text(encoding="utf-8").splitlines() if marker.is_file() else []
    fired = sorted({l.split()[0] for l in lines})
    version = spawn([claude, "--version"], evidence, "claude-version", timeout=60)
    report("hook-fires", fired == ["exec", "shell"], f"fired={','.join(fired) or 'none'} exit="
           f"{r.returncode if r else 'none'} claude={version.stdout.strip() if version else '?'}")


def hook_cost(evidence, runs, found):
    hook = evidence / "probe_hook.py"
    bash = git_bash()
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "echo probe"}})
    chains = {}
    for name in ("python3", "python"):
        exe = found.get(name)
        if not exe:
            continue
        chains[f"exec:{name}"] = [exe, str(hook), "time", "-"]
        if bash:
            chains[f"shell:{name}"] = [bash, "-c", f'{name} "{hook.as_posix()}" time -']
    for label, args in chains.items():
        times = []
        for _ in range(runs):
            start = time.perf_counter()
            r = subprocess.run(args, input=payload, capture_output=True, text=True)
            times.append((time.perf_counter() - start) * 1000)
            if r.returncode:
                break
        ok = r.returncode == 0
        report(f"hook-cost:{label}", ok,
               f"median_ms={statistics.median(times):.0f} runs={len(times)}" if ok else f"exit={r.returncode} "
               f"stderr={r.stderr.strip()[:120]!r}")
    if not bash:
        report("hook-cost:shell", False, "no bash found for the shell-form chain")


def main(argv):
    p = argparse.ArgumentParser(prog="probe.py")
    p.add_argument("evidence")
    p.add_argument("--codex-model", default="gpt-6.1-sol")
    p.add_argument("--claude-model", default="opus")
    p.add_argument("--runs", type=int, default=20)
    p.add_argument("--codex-windows-sandbox", choices=("elevated", "unelevated"))
    p.add_argument("--codex-python", default="python3")
    p.add_argument("--codex-drop-path")
    p.add_argument("--only", choices=("codex",), help="run only this check")
    a = p.parse_args(argv)
    evidence = Path(a.evidence).resolve()
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "probe_hook.py").write_text(HOOK, encoding="utf-8")
    print(f"PROBE host {platform.platform()} python={sys.version.split()[0]} evidence={evidence.as_posix()}")
    if a.only == "codex":
        codex_sandbox(evidence, a.codex_model, a.codex_windows_sandbox, a.codex_python, a.codex_drop_path)
        return 1 if failed else 0
    found = interpreters(evidence)
    codex_sandbox(evidence, a.codex_model, a.codex_windows_sandbox, a.codex_python, a.codex_drop_path)
    hook_fires(evidence, a.claude_model, found.get("python3"))
    hook_cost(evidence, a.runs, found)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
