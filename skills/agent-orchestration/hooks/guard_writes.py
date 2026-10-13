"""PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit in an orchestration thread and the workers it starts (a
subagent worker's input carries agent_id; a lane session's hook runs with --lane). A reminder, not a boundary: the
thread is trusted, and could write any file through Bash anyway. It refuses the one write a reminder would come too
late for, into the owner's checkout, which may hold their uncommitted work; and it advises the thread when it writes
outside its coordination worktree, where a change usually belongs to a worker. A session that is neither a lane nor
started where a thread record or state file is, is not a thread: silent.

Usage: python3 guard_writes.py [--lane] < hook JSON
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import lib  # noqa: E402

USAGE = "usage: guard_writes.py [--lane] < hook JSON"


def main(argv):
    if argv not in ([], ["--lane"]):
        raise lib.Fail(USAGE)
    lane = bool(argv)
    data = lib.hook_input()
    tool = data.get("tool_input") or {}
    cwd = data.get("cwd") or ""
    path = tool.get("file_path") or tool.get("notebook_path") or ""
    worker = lane or bool(data.get("agent_id"))
    if not (path and cwd):
        return 0
    # A lane session starts in its own worktree, which holds no thread files; its owner's checkout is the
    # repository's. A thread's files sit at its git root, an ancestor of where it started, so a session with none
    # above it is no thread, and git need not run.
    start = Path(lib.canon(os.environ.get("CLAUDE_PROJECT_DIR") or cwd))
    if not lane and not any(thread_files(d) for d in (start, *start.parents)):
        return 0
    top = lib.session_top(cwd)
    if not top or not (lane or thread_files(top)):
        return 0
    target = lib.canon_from(cwd, path)
    for owner in lib.owner_checkouts(top):
        if lib.same_path(owner, top) or not lib.inside(target, owner):
            continue
        refused = (f"{lib.native(target)} is in the owner's checkout, {lib.native(owner)}, which may hold their "
                   "uncommitted work.")
        if worker:
            return lib.deny(f"{refused} Make the change in your own lane worktree.")
        return lib.deny(f"{refused} Brief a worker to make the change in a lane worktree, or send MAIN the diff for "
                        "the owner.")
    if worker or lib.inside(target, top):
        return 0
    return lib.advise(f"You wrote {lib.native(target)}, outside your coordination worktree, {lib.native(top)}. Code "
                      "belongs to the lane workers: a change in a lane's worktree usually goes to its worker as a "
                      "ruling, so it lands with their tests and review. A deliberate small fix is fine; record it with "
                      "state.py log.")


def thread_files(folder):
    return any(os.path.isfile(os.path.join(folder, ".orchestration", f)) for f in ("thread.md", "state.md"))


if __name__ == "__main__":
    lib.entry(main)
