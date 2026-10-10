#!/usr/bin/env python3
"""PreToolUse hook for Edit and Write.

Refuses a new clock time (``14:30Z``, ``07:3xZ``, ``T18:16Z``) written by hand into a file under
``.orchestration/`` at the root of the session's git worktree (the coordination worktree). Past builds logged
estimated times there for hours; the only accepted source is the state helper, which interpolates ``date -u``
itself. Times already present in the file on disk may be moved or quoted. Outside git the hook does nothing.
"""
import json
import os
import re
import subprocess
import sys

CLOCK = re.compile(r"(?<![0-9])\d{1,2}:(?:\d{2}|\d?x{1,2})Z\b")


def orchestration_folder(cwd: str) -> str | None:
    if not cwd:
        return None
    found = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if found.returncode != 0 or not found.stdout.strip():
        return None
    return os.path.join(os.path.realpath(found.stdout.strip()), ".orchestration")


def main() -> None:
    data = json.load(sys.stdin)
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or ""
    build = orchestration_folder(cwd)
    if not build:
        return
    path = tool_input.get("file_path") or ""
    path = os.path.realpath(os.path.join(cwd, path))
    if not path.startswith(build.rstrip("/") + "/"):
        return
    text = tool_input.get("new_string") or tool_input.get("content") or ""
    found = set(CLOCK.findall(text))
    if not found:
        return
    try:
        with open(path, encoding="utf-8") as fh:
            existing = set(CLOCK.findall(fh.read()))
    except OSError:
        existing = set()
    new = sorted(found - existing)
    if not new:
        return
    reason = (
        "New clock times written by hand into an orchestration file: "
        + ", ".join(new)
        + ". Hand-typed times were estimates in past builds. Log the event with "
        "~/.claude/skills/agent-orchestration/scripts/state.sh log \"<event>\", which stamps it with date -u, "
        "or append the line with a shell command that interpolates $(date -u +%Y-%m-%dT%H:%MZ)."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))


if __name__ == "__main__":
    main()
