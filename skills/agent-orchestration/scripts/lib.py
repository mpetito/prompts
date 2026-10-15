"""Shared helpers for the orchestration scripts and hooks. Imported, not run.

Times are UTC "YYYY-MM-DDTHH:MMZ". Paths are stored as os.path.realpath gives them, which on Windows also
expands 8.3 short names of existing paths; same_path compares two paths the way the OS does (case-insensitively on
Windows); native gives the form to write into a prompt or brief an agent reads, forward slashes, which bash and
native tools both open. External commands run only through run(), so tests replace that one function.
"""
import contextlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

if os.name == "nt":
    # shutil.which would otherwise look in the current directory first, where a worktree could hold a git.cmd.
    os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")


class Fail(Exception):
    """A refusal or usage error: the caller prints the message on stderr and exits 1."""


def utc_now():
    return fmt_utc(time.time())


def fmt_utc(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def to_epoch(value):
    """Epoch seconds for a UTC time (YYYY-MM-DDTHH:MM[:SS]Z) or +<N>m / +<N>h from now; Fail names a bad value."""
    if m := re.fullmatch(r"\+(\d+)([mh])", value):
        return int(time.time()) + int(m[1]) * (60 if m[2] == "m" else 3600)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?Z", value):
        fmt = "%Y-%m-%dT%H:%M:%SZ" if value.count(":") == 2 else "%Y-%m-%dT%H:%MZ"
        try:
            return int(datetime.strptime(value, fmt).replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            pass
    raise Fail(f"not a UTC time (YYYY-MM-DDTHH:MMZ) or +<N>m / +<N>h: {value}")


def take_options(args, spec):
    """Split args into (positionals, options) for spec {"--name": takes_value}. An option missing its value or not in
    spec raises Fail; a flag's value is True, a repeated option keeps its last value."""
    positionals, options, i = [], {}, 0
    while i < len(args):
        a = args[i]
        if a.startswith("--") and a != "--":
            if a not in spec:
                raise Fail(f"unknown option {a}")
            if spec[a]:
                if i + 1 >= len(args):
                    raise Fail(f"option {a} needs a value")
                options[a] = args[i + 1]
                i += 2
                continue
            options[a] = True
        else:
            positionals.append(a)
        i += 1
    return positionals, options


def only_options(args, spec, usage):
    """take_options for a command that takes no further positionals: any error, or a stray argument, raises Fail
    with usage appended."""
    try:
        rest, options = take_options(args, spec)
    except Fail as e:
        raise Fail(f"{e}; {usage}") from None
    if rest:
        raise Fail(f"unknown option {rest[0]}; {usage}")
    return options


def usage_from(doc, first, last):
    """Fail with lines first..last (1-based) of a script's docstring: its usage block."""
    raise Fail("\n".join(doc.splitlines()[first - 1:last]))


def read_lines(file):
    """The lines of a UTF-8 text file, without their line endings."""
    text = Path(file).read_text(encoding="utf-8")
    return text.removesuffix("\n").split("\n") if text else []


def replace_lines(file, lines):
    """Write lines to file through a temporary file beside it, so a reader never sees half a file."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(file) or ".", prefix=os.path.basename(file) + ".")
    with open(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write("".join(line + "\n" for line in lines))
    os.replace(tmp, file)


# --- paths -------------------------------------------------------------------------------------------------------

def from_msys(path):
    """A Git Bash drive path, /c/rest or /c, in Windows form, C:/rest or C:/; any other path unchanged. Only a
    single-letter first component is a drive: /tmp and //server/share are left as they are."""
    m = re.fullmatch(r"/([A-Za-z])(/.*)?", path, re.DOTALL)
    return f"{m[1].upper()}:{m[2] or '/'}" if m else path


def windows_form(path):
    """On Windows, path with a Git Bash drive spelling turned into a Windows one by from_msys; elsewhere path itself.
    Windows itself would read /c/Users/x as a folder c at the root of the current drive."""
    return from_msys(os.fspath(path)) if os.name == "nt" else path


def canon(path):
    """The absolute, resolved form every stored path uses."""
    return os.path.realpath(windows_form(path))


def canon_from(base, path):
    """canon of path, resolving a relative one against base instead of the current directory."""
    return canon(os.path.join(base, windows_form(path)))


def same_path(a, b):
    return os.path.normcase(canon(a)) == os.path.normcase(canon(b))


def native(path):
    return Path(path).as_posix()


def inside(path, root):
    """True when path is root or below it, compared the way same_path compares."""
    p, r = os.path.normcase(canon(path)), os.path.normcase(canon(root))
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


# --- processes ---------------------------------------------------------------------------------------------------

def run(args, *, input=None, cwd=None, timeout=None, env=None, log=None):
    """Run args (a list, no shell) and return a CompletedProcess with text stdout and stderr, decoded as UTF-8.

    args[0] is resolved on PATH (PATHEXT on Windows, so an npm .cmd shim is found); a command that isn't found
    returns code 127 with the reason on stderr, as a shell would. On timeout the whole process tree is killed and
    the result has code 124, as timeout(1) gives. With log, a file path, stdout and stderr both go into that file,
    replacing it, as the command writes them, so a command that hangs can be read meanwhile; the result's stdout and
    stderr are then empty."""
    exe = shutil.which(args[0], path=(env or os.environ).get("PATH"))
    if not exe:
        return subprocess.CompletedProcess(args, 127, "", f"{args[0]}: command not found\n")
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    with open(log, "wb") if log else contextlib.nullcontext() as sink, \
            subprocess.Popen([exe, *args[1:]], stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                             stdout=sink or subprocess.PIPE, stderr=subprocess.STDOUT if sink else subprocess.PIPE,
                             text=True, encoding="utf-8", errors="replace", cwd=cwd, env=env, **kw) as p:
        try:
            out, err = p.communicate(input, timeout=timeout)
            code = p.returncode
        except subprocess.TimeoutExpired:
            kill_tree(p)
            out, err = p.communicate()
            code = 124
    return subprocess.CompletedProcess(args, code, out or "", err or "")


def kill_tree(p):
    """Kill a process started by run() and everything it started: an npm shim's node child outlives its parent."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def git(cwd, *args):
    """git -C cwd args...: stdout stripped of its final newline, or None when git fails."""
    r = run(["git", "-C", str(cwd), *args])
    return r.stdout.rstrip("\n") if r.returncode == 0 else None


def check_state(repo, sha, name):
    """The state of the check named name on commit sha of repo (owner/name), from every run of it GitHub lists:
    "none" with no run or when gh fails, "running" while any run is not completed, "success" when every run completed
    with success, else the other conclusions, distinct, sorted and comma-joined ("cancelled,failure").

    A workflow on both push and pull_request gives one head two runs of the same name, so every run must pass; one
    failed or unfinished run of either event holds the head. Reads one page of up to 100 runs."""
    r = run(["gh", "api", "-X", "GET", f"repos/{repo}/commits/{sha}/check-runs", "-f", f"check_name={name}",
             "-f", "per_page=100"])
    runs = json.loads(r.stdout)["check_runs"] if r.returncode == 0 else []
    if not runs:
        return "none"
    if any(c["status"] != "completed" for c in runs):
        return "running"
    return ",".join(sorted({c["conclusion"] for c in runs} - {"success"})) or "success"


# --- the coordination worktree and its records --------------------------------------------------------------------

def toplevel(path):
    """The git worktree root holding path, in canon form, or None outside git."""
    top = git(path, "rev-parse", "--show-toplevel")
    return canon(top) if top else None


def resolve_state(path, var):
    """The state file: $ORCHESTRATION_STATE when set, else <git toplevel of path>/.orchestration/state.md. Fail
    names var when path is outside git."""
    if os.environ.get("ORCHESTRATION_STATE"):
        return os.environ["ORCHESTRATION_STATE"]
    top = toplevel(path)
    if not top:
        raise Fail(f"{path} is not inside a git worktree; run from the coordination worktree or set {var}")
    return os.path.join(top, ".orchestration", "state.md")


def record_value(file, key):
    """The value of the first "<key>: value" line of file, trimmed, or "" when there is none or no file.

    The thread record, .orchestration/thread.md in the coordination worktree, holds one such line per field, written
    by MAIN's thread.py launch: the build (BUILD), the owner's checkout (CHECKOUT), and the build's base and landing
    mode (BASE, BASE-REF, LANE-BASE, LANDING)."""
    try:
        with open(file, encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}:"):
                    return line[len(key) + 1:].strip()
    except FileNotFoundError:
        pass
    return ""


def thread_field(top, key):
    return record_value(os.path.join(top, ".orchestration", "thread.md"), key)


def session_top(cwd):
    """The coordination worktree of this session: the git root of the folder it started in ($CLAUDE_PROJECT_DIR,
    which a cd never moves), else of cwd."""
    return toplevel(os.environ.get("CLAUDE_PROJECT_DIR") or cwd)


def owner_checkouts(top):
    """The owner's checkouts, in canon form: the repository's main checkout (the folder holding the common git dir)
    and, when the owner works in a linked worktree, the record's CHECKOUT. Empty when git fails."""
    common = git(top, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not common:
        return []
    found = [os.path.dirname(canon(common))]
    checkout = thread_field(top, "CHECKOUT")
    if checkout and not any(same_path(checkout, f) for f in found):
        found.append(canon(checkout))
    return found


# Dependency and cache folders are rebuilt from the lockfiles, so archive_ignored leaves them behind.
REBUILT = re.compile(r"(^|/)(node_modules|\.venv|venv|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|"
                     r"\.terraform|cdk\.out[^/]*|\.next|\.turbo|\.cache|dist|build|target)/?$")


def archive_ignored(wt, dest, prefix):
    """Copy the files git ignores in worktree wt to dest/ignored/<path>, and return one "archived ignored <path> to
    <dest>/ignored" line for each. The caller archives the prefix itself, so it stays behind, as do REBUILT folders.

    git status leaves ignored files out and a forced worktree removal deletes them, so this raises Fail when git
    can't list them or a copy fails, and the caller must then remove nothing."""
    r = run(["git", "-C", str(wt), "status", "--porcelain=v1", "-z", "--ignored=matching"])
    if r.returncode:
        raise Fail(f"refusing: git status failed in {wt}, so its ignored files can't be archived; nothing was removed")
    lines = []
    for entry in r.stdout.split("\0"):
        if not entry.startswith("!! "):
            continue
        path = entry[3:]
        rel = path.rstrip("/")
        if rel == prefix or rel.startswith(prefix + "/") or REBUILT.search(path):
            continue
        src, dst = Path(wt, rel), Path(dest, "ignored", rel)
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir() and not src.is_symlink():
                shutil.copytree(src, dst, symlinks=True, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst, follow_symlinks=False)
        except OSError as e:
            raise Fail(f"copying {path} to {Path(dest, 'ignored')} failed: {e}") from e
        lines.append(f"archived ignored {path} to {native(Path(dest, 'ignored'))}")
    return lines


# --- hooks -------------------------------------------------------------------------------------------------------

def hook_input():
    """Claude Code's hook JSON from stdin, or {} when there is none or it doesn't parse."""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def advise(context):
    """Print a hook reply that adds a note beside the tool result and leaves the call, and its permission check, as
    they were. Returns the hook's exit code."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}))
    return 0


def deny(reason):
    """Print a hook reply that refuses the call with reason. Returns the hook's exit code."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason}}))
    return 0


def entry(main):
    """Run a script's main(argv) as a program: UTF-8 stdio, a Fail printed on stderr, its exit code."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    try:
        code = main(sys.argv[1:])
    except Fail as e:
        print(e, file=sys.stderr)
        code = 1
    sys.exit(code)
