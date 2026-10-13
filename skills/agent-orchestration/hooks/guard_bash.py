"""PreToolUse hook for Bash, in the orchestration thread and the workers it starts. Denies, for both, the commands
that destroyed work in past builds. Advises the thread when it waits in the foreground (workers may: their waits
deafen no one), and warns when the scratch filesystem is nearly out of inodes. Input: Claude Code's hook JSON on stdin;
a subagent worker's carries agent_id, and a lane session's hook runs with --lane.

A command is matched only in command position (start of a line, after ; & | ( or $( , or after `sh -c '`), so the
same words inside a quoted string, a backtick span or a comment pass. The matching is textual, so it catches the
commands past builds ran by mistake, not every way to run them; the thread is trusted, and this only reminds it.

Usage: python3 guard_bash.py [--lane] < hook JSON
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lib  # noqa: E402

USAGE = "usage: guard_bash.py [--lane] < hook JSON"
SCRIPTS = "$HOME/.claude/skills/agent-orchestration/scripts"
# A foreground wait shorter than this (a retry backoff, letting a port bind) costs less than a message arriving late;
# anything longer leaves messages from MAIN and lane hand-backs unread while it runs.
FOREGROUND_SLEEP_LIMIT = 30
# Lanes fail in confusing ways once /tmp runs out of inodes; 70% leaves room to clean up first.
INODE_WARN_PERCENT = 70
# None where the OS has no statvfs (Windows): the inode warning is then skipped.
statvfs = getattr(os, "statvfs", None)

# Command position. Patterns are searched one line at a time, so \s never crosses a line and ^ is a line's start.
AT = r"(?:^|[;&|(]|\$\(|-c\s+[\"'])\s*(?:sudo\s+)?"
DENIALS = [
    (re.compile(AT + r"(?:pkill|killall)(?:\s|$)"),
     "pkill and killall match by pattern or name across every lane on this machine, and have killed the caller's own "
     "shell and another lane's server. Stop a process by PID: find it with 'ss -ltnp' or 'pgrep -a', read its command "
     "line, then 'kill <pid>'."),
    (re.compile(AT + r"git(?:\s+-C\s+\S+)?\s+worktree\s+remove"),
     f"Raw worktree removal has deleted lane evidence before it was archived. Use python3 \"{SCRIPTS}/finish_lane.py\" "
     "../<repo>-wt-<lane> <archive dir>, which archives the scratch directory and ignored files such as .eval-runs, "
     "refuses while an agent runs there, then removes the worktree. For a throwaway copy, use `git clone --no-local` "
     "or `git archive`, never `cp -a` of a worktree."),
    # Lane evidence lives in the coordination worktree's .orchestration/briefs and results, a lane worktree keeps its
    # scratch in .orchestration/tmp until finish_lane.py archives it, and .orchestration/lanes holds evidence from
    # earlier builds.
    (re.compile(AT + r"rm\s+(?:-[a-zA-Z]+\s+)*\S*\.orchestration/(?:briefs|results|lanes|tmp)(?:[/\s]|$)"),
     "Deleting .orchestration/briefs, results, lanes or tmp removes lane evidence. Archive a lane worktree "
     "(../<repo>-wt-<lane>) with finish_lane.py, or move files aside instead."),
]
SLEEP = re.compile(AT + r"sleep\s+(\d+)(?:\.\d+)?([smhd]?)")
SECONDS = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}
LOOP = re.compile(AT + r"(?:until|while)(?:\s|$)")
ANY_SLEEP = re.compile(r"(?:^|[^\w-])sleep\s")
MAIL_WAIT = re.compile(AT + r"(?:python3?\s+)?(?:\"[^\"]*|'[^']*|\S*)mail\.py[\"']?\s+wait(?:\s|$)")


def main(argv):
    if argv not in ([], ["--lane"]):
        raise lib.Fail(USAGE)
    data = lib.hook_input()
    tool = data.get("tool_input") or {}
    lines = (tool.get("command") or "").split("\n")
    for pattern, reason in DENIALS:
        if any(pattern.search(line) for line in lines):
            return lib.deny(reason)
    notes = []
    if tool.get("run_in_background") is not True and not data.get("agent_id") and not argv:
        reason = wait_reason(lines)
        if reason:
            notes.append(f"This call {reason}: until it ends, messages from MAIN and lane hand-backs queue unread. "
                         f"Next time, arm a background timer: python3 \"{SCRIPTS}/wake_at.py\" <UTC|+<N>m> <label> "
                         "with run_in_background, or watch the condition with Monitor.")
    note = inode_note()
    if note:
        notes.append(note)
    return lib.advise("\n".join(notes)) if notes else 0


def wait_reason(lines):
    """Why the command keeps the thread waiting in the foreground, or "". A mail wait outranks a sleep loop, which
    outranks a long sleep."""
    if any(MAIL_WAIT.search(line) for line in lines):
        return "waits on mail in the foreground"
    if any(LOOP.search(line) for line in lines) and any(ANY_SLEEP.search(line) for line in lines):
        return "loops on sleep in the foreground"
    reason = ""
    for m in (m for line in lines for m in SLEEP.finditer(line)):
        secs = int(m[1]) * SECONDS[m[2]]
        if secs >= FOREGROUND_SLEEP_LIMIT:
            reason = f"sleeps {secs} s in the foreground"
    return reason


def inode_note():
    """The warning for the first scratch filesystem (/tmp, then $TMPDIR) at INODE_WARN_PERCENT of its inodes or more,
    or None. A filesystem that reports no inode count, as df shows "-" for, is skipped."""
    if not statvfs:
        return None
    for fs in dict.fromkeys(("/tmp", os.environ.get("TMPDIR") or "/tmp")):
        try:
            st = statvfs(fs)
        except OSError:
            continue
        if not st.f_files:
            continue
        use = -(-(st.f_files - st.f_ffree) * 100 // st.f_files)  # rounded up, as df -i rounds
        if use >= INODE_WARN_PERCENT:
            return (f"{fs} is at {use}% of its inodes; clean cdk.out* and scratch copies or move TMPDIR to disk before "
                    "launching more lanes.")
    return None


if __name__ == "__main__":
    lib.entry(main)
