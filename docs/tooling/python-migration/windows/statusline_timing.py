"""Times the Node status line against the Python one on this machine (plan.md step 13, spec decision 6).

    python3 statusline_timing.py [--runs <n, default 20>] [--node-ref <git ref>] [--out <file>]

Run it from the checkout that holds this script. It takes statusline.js from --node-ref (default: the last revision
of HEAD's history that has it) and statusline.py from this checkout. It feeds each the same realistic payload on
stdin, closed, with this checkout as the working folder, and prints one line per measurement:

    TIMING <interpreter> <shell|direct> median=<ms> min=<ms> max=<ms> runs=<n>

shell is how Claude Code runs a statusLine command, through a shell: Git Bash on Windows (CLAUDE_CODE_GIT_BASH_PATH,
else the bin/bash.exe of the Git install that holds git), bash on Linux. direct starts the interpreter with no shell.
The interpreters are node and python3, and python too when it is on PATH and is not python3. An interpreter that is
missing prints `TIMING <interpreter> missing`. Then one line says whether every interpreter printed the same status
line:

    OUTPUT same|differs

It saves those lines, the versions and both outputs to --out (default results/statusline-timing.md beside this
script), and exits 1 if the outputs differ or a measurement failed. The saved text is for a public repository: the
home folder is written as %USERPROFILE% on Windows and <home> elsewhere, and if the home folder, the user name or an
8.3 short path (which carries the start of the user name) still appears after that, the script saves nothing and
exits 1 with a LEAK line.
"""
import argparse
import getpass
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
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[3]
PYTHON_SCRIPT = CHECKOUT / "statusline" / "statusline.py"


def git_bash():
    """The bash Claude Code runs commands in, or None."""
    if os.name != "nt":
        return shutil.which("bash")
    if os.environ.get("CLAUDE_CODE_GIT_BASH_PATH"):
        return os.environ["CLAUDE_CODE_GIT_BASH_PATH"]
    git = shutil.which("git")
    if not git:
        return None
    # git.exe lives in <install>\cmd or <install>\mingw64\bin; bash.exe in <install>\bin.
    for up in Path(git).resolve().parents:
        if (up / "bin" / "bash.exe").is_file():
            return str(up / "bin" / "bash.exe")
    return None


def home_pattern():
    """The home folder as a regex matching either slash, and doubled backslashes as repr() writes them."""
    home = str(Path.home())
    parts = [re.escape(part) for part in re.split(r"[\\/]+", home) if part]
    lead = r"[\\/]+" if home[:1] in "/\\" else ""
    return re.compile(lead + r"[\\/]+".join(parts) + r"(?![\w.-])", re.I if os.name == "nt" else 0)


def mask(text):
    return home_pattern().sub("%USERPROFILE%" if os.name == "nt" else "<home>", text)


def leak(text):
    """What private name is left in text, or None."""
    if home_pattern().search(text):
        return "the home folder"
    user = getpass.getuser()
    if re.search(rf"(?<![\w-]){re.escape(user)}(?![\w-])", text, re.I):
        return f"the user name ({len(user)} characters)"
    # An 8.3 short name such as ABCDEF~1 carries the start of the user name, and the home mask can't see it.
    if re.search(r"(?<![^\\/\s'\"])[^\\/\s'\"~]{1,6}~\d+(?:\.[^\\/\s'\"]{1,3})?(?=[\\/\s'\"]|$)", text):
        return "an 8.3 short path"
    return None


def timed(args, payload, runs):
    """(median, min, max) ms of runs starts of args with payload on stdin, and the last stdout; None on a failure."""
    times, out = [], b""
    for _ in range(runs):
        start = time.perf_counter()
        r = subprocess.run(args, input=payload, capture_output=True, cwd=CHECKOUT, timeout=30)
        times.append((time.perf_counter() - start) * 1000)
        if r.returncode != 0:
            return None, r.stderr.decode("utf-8", "replace")
        out = r.stdout
    return (statistics.median(times), min(times), max(times)), out


def version(args):
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return (r.stdout or r.stderr).strip().splitlines()[0]
    except (OSError, IndexError, subprocess.TimeoutExpired):
        return "unknown"


def short(ref):
    return version(["git", "-C", str(CHECKOUT), "rev-parse", "--short", ref])


def main(argv):
    parser = argparse.ArgumentParser(prog="statusline_timing.py")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--node-ref")
    parser.add_argument("--out", type=Path, default=HERE / "results" / "statusline-timing.md")
    args = parser.parse_args(argv)

    if not args.node_ref:
        # The commit that last touched statusline.js: it has the file, unless it is the one that deleted it.
        last = subprocess.run(["git", "-C", str(CHECKOUT), "rev-list", "-1", "HEAD", "--", "statusline/statusline.js"],
                              capture_output=True, text=True).stdout.strip()
        exists = subprocess.run(["git", "-C", str(CHECKOUT), "cat-file", "-e", f"{last}:statusline/statusline.js"],
                                capture_output=True).returncode == 0
        args.node_ref = last if exists else f"{last}^"
    node_source = subprocess.run(["git", "-C", str(CHECKOUT), "show", f"{args.node_ref}:statusline/statusline.js"],
                                 capture_output=True)
    if node_source.returncode != 0:
        print(f"no statusline/statusline.js at {args.node_ref}: {node_source.stderr.decode().strip()}")
        return 1
    # realpath: TEMP can be spelled in 8.3 form (C:\Users\ABCDEF~1\...), which the home mask would not match.
    tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="statusline-timing-")))
    node_script = tmp / "statusline.js"
    node_script.write_bytes(node_source.stdout)

    payload = json.dumps({
        "cwd": str(CHECKOUT), "session_name": "timing",
        "workspace": {"current_dir": str(CHECKOUT),
                      "repo": {"host": "github.com", "owner": "example", "name": "prompts"}},
        "model": {"id": "claude-opus-5-5", "display_name": "Opus 5.5"}, "effort": {"level": "high"},
        "context_window": {"used_percentage": 43.4}}).encode()

    interpreters = [("node", node_script), ("python3", PYTHON_SCRIPT)]
    python, python3 = shutil.which("python"), shutil.which("python3")
    if python and (not python3 or os.path.realpath(python) != os.path.realpath(python3)):
        interpreters.append(("python", PYTHON_SCRIPT))
    bash = git_bash()

    lines, outputs, ok = [], {}, True
    for name, script in interpreters:
        exe = shutil.which(name)
        if not exe:
            lines.append(f"TIMING {name} missing")
            print(lines[-1], flush=True)
            continue
        forms = [("direct", [exe, str(script)])]
        if bash:
            forms.insert(0, ("shell", [bash, "-c", f'{name} "{script.as_posix()}"']))
        for form, command in forms:
            stats, out = timed(command, payload, args.runs)
            if stats is None:
                lines.append(f"TIMING {name} {form} failed {out.strip()[:200]}")
                ok = False
            else:
                lines.append(f"TIMING {name} {form} median={stats[0]:.0f} min={stats[1]:.0f} max={stats[2]:.0f} "
                             f"runs={args.runs}")
                outputs[name] = out
            print(lines[-1], flush=True)
    same = len(set(outputs.values())) <= 1
    ok &= same
    lines.append(f"OUTPUT {'same' if same else 'differs'}")
    print(lines[-1], flush=True)

    versions = [f"- {platform.platform()}", f"- node {version(['node', '--version'])}",
                f"- python3 {version(['python3', '--version'])}", f"- bash {bash or 'none'}",
                f"- statusline.js from {args.node_ref} ({short(args.node_ref)})",
                f"- statusline.py from {short('HEAD')}"]
    shown = [f"- {name}: `{out.decode('utf-8', 'replace')!r}`" for name, out in outputs.items()]
    saved = mask("\n".join([f"# Status line timing, {date.today().isoformat()}", "", "```", *lines, "```", "",
                             "Versions:", *versions, "", "Outputs:", *shown, ""]))
    if found := leak(saved):
        print(f"LEAK {found} is still in the results after masking; nothing saved")
        shutil.rmtree(tmp, ignore_errors=True)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(saved, encoding="utf-8")
    print(f"saved {args.out}")
    shutil.rmtree(tmp, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
