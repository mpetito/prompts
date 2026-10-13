"""Claude Code status line. Reads the session JSON on stdin, prints one line, no newline, and exits 0.

Payload fields used here: cwd, workspace.*, model.*, effort.level, context_window.*, worktree.branch.
(The payload also carries session_name, vim, pr, cost, rate_limits -- vim and pr are native.)
Runs as `python3 <path to statusline.py>`; it takes no arguments.
"""
import json
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import threading

if os.name == "nt":
    # shutil.which would otherwise look in the current directory first, where a checkout could hold a git.cmd.
    os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")

# Claude Code spawns us with a stdin pipe, and also spawns MCP servers via cmd.exe that inherit open handles. A
# grandchild holding the write end means we never see EOF once Claude exits, so waiting for EOF alone leaks a wedged
# process per session. Render on whichever comes first -- EOF or the deadline -- and always exit with os._exit, which
# does not wait for the reader thread still blocked on stdin.
DEADLINE = 2.0      # seconds
GIT_TIMEOUT = 1.0   # seconds
DRAIN = 1.0         # seconds for the tree kill, and again to read a killed command's pipe

# Nerd Font glyphs -- these require a Nerd Font (Cascadia Code NF is installed and set as the Windows Terminal face).
# Written as escapes so this file stays pure ASCII. Every glyph below was checked against the font's cmap. U+2387 (the
# old branch mark), U+2717 and U+2718 (ballot X) are NOT in Cascadia Code NF -- do not reach for them.
ICON = {
    "dir":      "",      # fa folder-open
    "repo":     "",      # octicon repo
    "branch":   "",      # devicon git-branch
    "clean":    "✓",      # check -- working tree clean
    "dirty":    "●",      # filled circle -- uncommitted changes
    "conflict": "",      # fa warning -- unmerged paths
    "model":    "\U000F06A9",  # md robot
    "effort":   "",      # fa bolt
    "context":  "",      # octicon graph
    "sep":      "│",      # box-drawing vertical bar
}


def paint(code, s):
    return f"\x1b[{code}m{s}\x1b[0m"


# Envative branches are `users/<user>/<work-item>-<description>`, which runs to ~60 characters and wraps the status
# line. Drop the owner prefix -- it is always this user -- and cap what remains.
BRANCH_MAX = 32


def short_branch(b):
    s = re.sub(r"^users/[^/]+/", "", b)
    return s[:BRANCH_MAX - 1] + "…" if len(s) > BRANCH_MAX else s


def context_pct(pct):
    """Context usage as a bare percentage, clamped to 0-100 and rounded half up. The colour carries the urgency, so
    the ten-cell bar this replaces was costing width without adding information."""
    clamped = max(0, min(100, pct))
    colour = "31" if clamped >= 80 else "33" if clamped >= 60 else "32"  # red / yellow / green
    return paint(colour, f"{ICON['context']} {math.floor(clamped + 0.5)}%")


def run(args, timeout):
    """Run args (a list, no shell) and return a CompletedProcess with text stdout, decoded as UTF-8; stderr is
    dropped. A command not on PATH gives code 127. On timeout (seconds) the whole process tree is killed and the code
    is 124; draining the pipe afterwards is bounded by DRAIN seconds too, so a process that escaped the kill and still
    holds the pipe can't hold the status line (os._exit leaves it behind). The kill itself is bounded by DRAIN."""
    exe = shutil.which(args[0])
    if not exe:
        return subprocess.CompletedProcess(args, 127, "", "")
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    p = subprocess.Popen([exe, *args[1:]], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace", **kw)
    try:
        out, _ = p.communicate(timeout=timeout)
        return subprocess.CompletedProcess(args, p.returncode, out or "", "")
    except subprocess.TimeoutExpired:
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True, timeout=DRAIN)
            else:
                os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass
        try:
            p.communicate(timeout=DRAIN)
        except subprocess.TimeoutExpired:
            pass
        return subprocess.CompletedProcess(args, 124, "", "")


def parse_status(out):
    """{branch, changed, conflict} from `git status --porcelain=v1 --branch` output. branch is "" when detached."""
    lines = out.split("\n")

    # Header looks like "## main...origin/main [ahead 1]", "## main", or "## HEAD (no branch)" when detached. Branch
    # names may contain dots, so split on the literal "..." upstream separator rather than on any dot.
    branch = ""
    head = lines[0]
    if head.startswith("## ") and not head.startswith("## HEAD (no branch)"):
        branch = re.sub(r"\s+\[.*\]$", "", re.sub(r"^No commits yet on ", "", head[3:].split("...")[0])).strip()

    # One porcelain line is one file. Count lines, not index/worktree flags: a file that is staged and then modified
    # again reports "MM" and must still count once.
    changed = conflict = 0
    for line in lines[1:]:
        if not line:
            continue
        x, y = line[0], line[1:2]
        # Unmerged: either side U, or the AA / DD both-added / both-deleted pairs.
        if x == "U" or y == "U" or x + y in ("AA", "DD"):
            conflict += 1
        else:
            changed += 1  # includes "??" untracked, which is also one line per file
    return {"branch": branch, "changed": changed, "conflict": conflict}


def git_info(cwd):
    """`git status --porcelain=v1 --branch` returns the branch and the working-tree state together, so the status
    indicator costs no extra subprocess over the `rev-parse` it replaces. None when git fails or times out."""
    try:
        r = run(["git", "-C", cwd, "status", "--porcelain=v1", "--branch"], GIT_TIMEOUT)
    except (OSError, ValueError):  # a path git can't be given, such as one with a NUL
        return None
    return parse_status(r.stdout) if r.returncode == 0 else None


def git_badge(g):
    """One glyph, coloured: red on conflicts, yellow with a count when there is anything uncommitted, green when the
    tree is clean."""
    if not g:
        return ""
    if g["conflict"]:
        return paint("31", f"{ICON['conflict']} {g['conflict']}")
    return paint("33", f"{ICON['dirty']} {g['changed']}") if g["changed"] else paint("32", ICON["clean"])


def field(d, *keys):
    """d[k1][k2]..., or None where a level is missing or is not an object."""
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def text(v):
    """v when it is a string, else None: a path or branch of another type is treated as absent."""
    return v if isinstance(v, str) else None


def process_dir():
    try:
        return os.getcwd()
    except OSError:  # the folder was removed under us
        return ""


def render(payload):
    """The status line for the payload; a payload that is not a JSON object, or nests too deep to parse, renders as
    {}. No payload makes it raise."""
    try:
        d = json.loads(payload)
    except (ValueError, RecursionError):
        d = {}
    if not isinstance(d, dict):
        d = {}

    cwd = text(field(d, "workspace", "current_dir")) or text(d.get("cwd")) or process_dir()

    home = os.path.expanduser("~")
    path = cwd
    if home and path.lower().startswith(home.lower()):
        path = "~" + path[len(home):]
    path = path.replace("\\", "/")

    # The payload carries repo identity (host/owner/name) but never the checked-out branch outside --worktree
    # sessions, so ask git directly.
    git = git_info(cwd) if cwd else None  # `git -C ""` would ask about whatever folder git starts in
    branch = text(field(d, "worktree", "branch")) or (git and git["branch"]) or ""

    # session_name is deliberately omitted -- the TUI already shows it by the input box. vim.mode and pr.number are
    # omitted too: Claude Code renders both natively (the built-in "-- INSERT --" text and the footer PR badge, which
    # pr.number mirrors).
    parts = [paint("36", f"{ICON['dir']} {path}")]                                       # cyan cwd

    repo = field(d, "workspace", "repo")
    if field(repo, "name"):
        parts.append(paint("34", f"{ICON['repo']} {repo.get('owner') or ''}/{repo['name']}"))  # blue repo

    if branch and branch != "HEAD":
        badge = git_badge(git)                                                           # magenta branch
        parts.append(paint("35", f"{ICON['branch']} {short_branch(branch)}") + (f" {badge}" if badge else ""))

    # Reasoning effort rides with the model rather than taking its own segment: it is a property of the model, and the
    # line is already wide. Absent when the model has no effort parameter; `xhigh` also covers Ultracode, which is not
    # a distinct level.
    model = field(d, "model", "display_name")
    effort = field(d, "effort", "level")
    if model or effort:
        head = paint("33", f"{ICON['model']} {model}") if model else ""                  # yellow model
        gap = " " if model and effort else ""
        tail = paint("90", f"{gap}{ICON['effort']} {effort}") if effort else ""         # dim effort
        parts.append(head + tail)

    pct = field(d, "context_window", "used_percentage")
    if isinstance(pct, (int, float)) and not isinstance(pct, bool):
        parts.append(context_pct(pct))

    return paint("90", f" {ICON['sep']} ").join(parts)


def read_payload(stream, deadline):
    """What stream (binary) gives until EOF, a read error, or deadline seconds, whichever comes first, decoded as
    UTF-8. At the deadline it returns the chunks read so far: the payload has usually arrived whole, and only the EOF
    is missing."""
    chunks, done = [], threading.Event()

    def reader():
        try:
            while chunk := stream.read1(65536):
                chunks.append(chunk)
        except (OSError, ValueError):
            pass
        done.set()

    threading.Thread(target=reader, daemon=True).start()
    done.wait(deadline)
    return b"".join(chunks).decode("utf-8", errors="replace")


def main(argv):
    sys.stdout.write(render(read_payload(sys.stdin.buffer, DEADLINE)))
    return 0


if __name__ == "__main__":
    # replace: a lone surrogate from the JSON, or a non-UTF-8 folder name, prints as "?" instead of failing.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    code = main(sys.argv[1:])
    sys.stdout.flush()
    os._exit(code)
