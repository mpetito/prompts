"""The control-attach skill's Stop and UserPromptSubmit hooks, declared in its SKILL.md and run in every session that
has invoked the skill. references/protocol.md "What the hooks call" is the contract:

- Stop, in a pane with an attached record: when the record's wait command isn't among the running background tasks
  and no Stop hook has already continued this turn, block the stop with a reason naming the command, and send no
  report. Otherwise send the turn's final text to the controller with ctl.py report.
- UserPromptSubmit: every prompt goes to ctl.py typed, which alone decides whether it is the owner typing.

Input: Claude Code's hook JSON on stdin, whose hook_event_name picks the handler.
"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ctl  # noqa: E402

lib = ctl.lib


def run_ctl(subcommand, text):
    """ctl.py <subcommand> with text as its stdin, in this process; its exit code."""
    sys.stdin = io.StringIO(text)
    return ctl.main([subcommand])


def stop(data):
    command = ctl.wait_command()
    if command is None:
        return 0
    # A task with no command, such as a subagent, never matches.
    up = any(command in (task.get("command") or "") for task in data.get("background_tasks") or [])
    if up or data.get("stop_hook_active"):
        return run_ctl("report", data.get("last_assistant_message") or "")
    print(json.dumps({"decision": "block", "reason": (
        "The control wait isn't running. Start this exact command as a background task (run_in_background), "
        f"then end your turn: {command}")}))
    return 0


def prompt(data):
    return run_ctl("typed", data.get("prompt") or "")


# hook_event_name: its handler
EVENTS = {"Stop": stop, "UserPromptSubmit": prompt}


def main(argv):
    data = lib.hook_input()
    return EVENTS[data.get("hook_event_name")](data)


if __name__ == "__main__":
    lib.entry(main)
