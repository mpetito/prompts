"""PreToolUse hook for Edit and Write.

Advises when the orchestration thread writes a new clock time (``14:30Z``, ``07:3xZ``, ``T18:16Z``) by hand into a
file under ``.orchestration/`` at the root of its git worktree (the coordination worktree). Past builds logged
estimated times there for hours; the state helper stamps times itself. The write goes ahead: a time quoted from a log
or a message is legitimate. Times already in the file on disk, workers' writes (input with ``agent_id``) and sessions
outside git pass silently.

Usage: python3 guard_timestamps.py < hook JSON
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lib  # noqa: E402

USAGE = "usage: guard_timestamps.py < hook JSON"
CLOCK = re.compile(r"(?<![0-9])\d{1,2}:(?:\d{2}|\d?x{1,2})Z\b")


def main(argv):
    if argv:
        raise lib.Fail(USAGE)
    data = lib.hook_input()
    if data.get("agent_id"):
        return 0
    tool = data.get("tool_input") or {}
    cwd = data.get("cwd") or ""
    found = set(CLOCK.findall(tool.get("new_string") or tool.get("content") or ""))
    path = lib.canon_from(cwd, tool.get("file_path") or "")
    # The cheap tests first: git runs only for a clock time written under some .orchestration folder.
    if not found or not (os.environ.get("CLAUDE_PROJECT_DIR") or cwd) or ".orchestration" not in os.path.normcase(path):
        return 0
    top = lib.session_top(cwd)
    if not top or not lib.inside(path, os.path.join(top, ".orchestration")):
        return 0
    try:
        existing = set(CLOCK.findall(Path(path).read_text(encoding="utf-8")))
    except OSError:
        existing = set()
    new = sorted(found - existing)
    if not new:
        return 0
    return lib.advise(f"New clock times in an orchestration file: {', '.join(new)}. If you estimated them, replace "
                      "them: hand-typed times were estimates in past builds. Log events with python3 "
                      "\"$HOME/.claude/skills/agent-orchestration/scripts/state.py\" log \"<event>\", which stamps "
                      "them with the current UTC time. A time quoted from a log or a message is fine as it is.")


if __name__ == "__main__":
    lib.entry(main)
