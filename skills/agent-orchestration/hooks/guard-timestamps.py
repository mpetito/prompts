#!/usr/bin/env python3
"""PreToolUse hook for Edit and Write.

Advises when the orchestration thread writes a new clock time (``14:30Z``, ``07:3xZ``, ``T18:16Z``) by hand into a
file under ``.orchestration/`` at the root of its git worktree (the coordination worktree). Past builds logged
estimated times there for hours; the state helper interpolates ``date -u`` itself. The write goes ahead: a time
quoted from a log or a message is legitimate. Times already in the file on disk, workers' writes (input with
``agent_id``) and sessions outside git pass silently.
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
    if data.get("agent_id"):
        return
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd") or ""
    # The folder the session started in identifies it; a cd never moves CLAUDE_PROJECT_DIR.
    build = orchestration_folder(os.environ.get("CLAUDE_PROJECT_DIR") or cwd)
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
    advice = (
        "New clock times in an orchestration file: "
        + ", ".join(new)
        + ". If you estimated them, replace them: hand-typed times were estimates in past builds. Log events with "
        "~/.claude/skills/agent-orchestration/scripts/state.sh log \"<event>\", which stamps them with date -u. "
        "A time quoted from a log or a message is fine as it is."
    )
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": advice}}))


if __name__ == "__main__":
    main()
