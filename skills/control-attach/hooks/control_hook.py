"""The control-attach skill's Stop and UserPromptSubmit hooks, declared in its SKILL.md and run in every session that
has invoked the skill. references/protocol.md "What the hooks call" is the contract:

- Stop, in a pane with an attached record: send the turn's final text to the controller with ctl.py report, on every
  stop. Then, when the record's wait command isn't among the running background tasks and no Stop hook has already
  continued this turn, block the stop with a reason naming the command.
- UserPromptSubmit: every prompt goes to ctl.py typed, which alone decides whether it is the owner typing.

Input: Claude Code's hook JSON on stdin, whose hook_event_name picks the handler. Exits 0 and prints nothing but a
block decision, whatever fails: these hooks run on every prompt and every turn end of the owner's session, and any
other output or exit code would reach the owner as a hook error.
"""
import contextlib
import io
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def run_ctl(ctl, subcommand, text):
    """ctl.py <subcommand> with text as its stdin, in this process, its output discarded: only the hook's own decision
    may reach stdout, where Claude Code reads it as JSON."""
    sys.stdin = io.StringIO(text)
    with contextlib.redirect_stdout(io.StringIO()):
        ctl.main([subcommand])


def stop(ctl, data):
    command = ctl.wait_command()
    if command is None:
        return
    # A report that fails must not keep the stop from checking the wait.
    with contextlib.suppress(Exception):
        run_ctl(ctl, "report", data.get("last_assistant_message") or "")
    # A task with no command, such as a subagent, never matches.
    up = any(command in (task.get("command") or "") for task in data.get("background_tasks") or [])
    if not up and not data.get("stop_hook_active"):
        print(json.dumps({"decision": "block", "reason": (
            "The control wait isn't running. Start this exact command as a background task (run_in_background):\n"
            f"{command}\nThen end your turn with one short line and no STATUS line: this turn's report is already "
            "sent.")}))


def prompt(ctl, data):
    run_ctl(ctl, "typed", data.get("prompt") or "")


# hook_event_name: its handler
EVENTS = {"Stop": stop, "UserPromptSubmit": prompt}


def main():
    try:
        data = json.loads(sys.stdin.read())
        sys.path.insert(0, str(SCRIPTS))
        import ctl
        EVENTS[data["hook_event_name"]](ctl, data)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.exit(main())
