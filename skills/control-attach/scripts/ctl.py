"""The control layer's script: a session attaches under a name and reports to the controller, and the controller
steers attached sessions through their mailboxes. references/protocol.md is the contract (Protocol version 1): every
subcommand's arguments, every line it prints, and the files under $ORCHESTRATION_HOME/control (default
~/.orchestration/control), which only this script writes.
  ctl.py attach <name> [--hold <minutes>]
  ctl.py detach
  ctl.py authority observe|relay|delegate
  ctl.py report      the report is stdin
  ctl.py typed       the prompt is stdin
A session's subcommands find its record by HERDR_PANE_ID. A refusal prints REFUSED <reason> and exits 1.
"""
import json
import os
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "agent-orchestration" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import lib  # noqa: E402
import mail  # noqa: E402

# herdr's agent-name pattern, which mail.py's boxes share.
NAME = re.compile(r"[a-z][a-z0-9_-]{0,31}")
OWNER = "owner"
LEVELS = ("observe", "relay", "delegate")
# Spec questions 1 and 3. The default authority is fixed: the owner changes one session's level, never the default.
DEFAULT_AUTHORITY = "delegate"
DEFAULT_HOLD = 10
# A report wakes the controller only when it needs the controller or the owner.
WAKING = re.compile(r"STATUS: (need-decision|blocked|done)( |$)")
# The one ring line typed into a Claude session; typed ignores it, so a ring never holds the controller.
RING = re.compile(rf"/control-attach {NAME.pattern}")
# How the prompts that aren't the owner typing begin (spec "Shown 2026-10-15"): a background task's wake, a
# subagent's report, another session's message.
NOT_TYPED = ("<task-notification>", "<agent-message ", "<cross-session-message ")


class Refused(Exception):
    """A refusal main prints on stdout as "REFUSED <reason>", exiting 1."""


class HerdrError(Refused):
    """herdr failed, printed as "REFUSED herdr: <reason>"; code is herdr's error code, or "" when it gave none."""

    def __init__(self, reason, code=""):
        super().__init__(f"herdr: {reason}")
        self.code = code


def usage():
    raise lib.Fail(__doc__.rstrip())


def control():
    return Path(os.environ.get("ORCHESTRATION_HOME") or Path.home() / ".orchestration") / "control"


def mail_root():
    return control() / "mail"


def wait_line(name):
    """The wait command attach prints for name: mail.py's wait on <name>/in, with absolute paths."""
    return f'python3 "{lib.native(SCRIPTS / "mail.py")}" wait {name}/in --home "{lib.native(lib.canon(control()))}"'


# --- records -----------------------------------------------------------------------------------------------------

def record_path(name):
    return control() / "sessions" / f"{name}.json"


def load(name):
    """name's record, or None when it has none."""
    try:
        return json.loads(record_path(name).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def save(name, record):
    path = record_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.replace_lines(path, [json.dumps(record)])


def records():
    """Every record, as (name, record) in name order."""
    folder = control() / "sessions"
    return [(p.stem, load(p.stem)) for p in sorted(folder.glob("*.json"))] if folder.is_dir() else []


def attached():
    """(name, record) of the record attached from this process's herdr pane, or None outside herdr or unattached.
    attach keeps at most one record attached per pane."""
    pane = os.environ.get("HERDR_PANE_ID")
    return next(((n, r) for n, r in records() if r["attached"] and r["pane"] == pane), None) if pane else None


def session_id(agent):
    """herdr's session id for an agent record, or "" when herdr gives none."""
    return (agent.get("agent_session") or {}).get("value", "")


def attached_as(agent):
    """The name an agent from herdr's list is attached under, or None. An attached record must have the agent's
    herdr name and the session id herdr gives it now: a /clear keeps the pane and the name but changes the id and
    drops the session's hooks, so a cleared session is unattached until it attaches again."""
    record = load(agent["name"]) if agent.get("name") else None
    return agent["name"] if record and record["attached"] and record["session"] == session_id(agent) else None


def wait_command():
    """For the session's hooks: the command of this pane's WAIT line, or None when the pane isn't attached. Reads
    the records only, never herdr."""
    found = attached()
    return wait_line(found[0]) if found else None


# --- herdr -------------------------------------------------------------------------------------------------------

def herdr(*args):
    """The "result" object of herdr's JSON reply to args. HerdrError when herdr fails, or replies with anything but
    JSON holding a result object, so no caller reads a reply herdr didn't give."""
    r = lib.run(["herdr", *args])
    out = (r.stdout if r.returncode == 0 else r.stdout + r.stderr).strip()
    try:
        reply = json.loads(out)
    except ValueError:
        reply = None
    if not isinstance(reply, dict):
        raise HerdrError(f"unexpected reply: {out}")
    if r.returncode == 0 and isinstance(reply.get("result"), dict):
        return reply["result"]
    err = reply.get("error")
    if r.returncode and isinstance(err, dict):
        raise HerdrError(f"{err.get('code')}: {err.get('message')}", err.get("code"))
    raise HerdrError(f"unexpected reply: {out}")


def live_agent(target):
    """herdr's record of the live agent at target, a name or a pane, or None when herdr says there is none
    (agent_not_found). HerdrError for any other failure, so a herdr that can't answer never reads as no agent."""
    try:
        agent = herdr("agent", "get", target).get("agent")
    except HerdrError as e:
        if e.code == "agent_not_found":
            return None
        raise
    if not isinstance(agent, dict):
        raise HerdrError(f"unexpected reply for {target}: no agent record")
    return agent


# --- session subcommands -----------------------------------------------------------------------------------------

def check_name(name):
    if not NAME.fullmatch(name):
        raise Refused(f"not a name: {name}")
    if name == OWNER:
        raise Refused("owner is the controller's address")


def attach(args, opts):
    if len(args) != 1:
        usage()
    name = args[0]
    check_name(name)
    hold = opts.get("--hold")
    # str.isdigit accepts digits int() can't read, such as "³".
    if hold is not None and not re.fullmatch(r"[0-9]+", hold):
        usage()
    pane = os.environ.get("HERDR_PANE_ID")
    if not pane:
        raise Refused("not in a herdr pane")
    me = live_agent(pane)
    if me is None:
        raise HerdrError(f"no agent in pane {pane}")
    # attach names the agent, so herdr's names are the live holders of the addresses.
    holder = (live_agent(name) or {}).get("pane_id")
    if holder and holder != pane:
        raise Refused(f"{name} is held by pane {holder}")
    if me.get("name") != name:
        herdr("agent", "rename", pane, name)
    for other, record in records():
        if other != name and record["attached"] and record["pane"] == pane:
            save(other, {**record, "attached": False})
    old = load(name) or {}
    save(name, {"pane": pane, "session": session_id(me), "authority": old.get("authority", DEFAULT_AUTHORITY),
                "hold": int(hold) if hold is not None else old.get("hold", DEFAULT_HOLD),
                "typed": old.get("typed", ""), "attached": True, "started": old.get("started", False)})
    print(f"WAIT {wait_line(name)}")
    return 0


def own_record():
    found = attached()
    if not found:
        raise Refused("not attached")
    return found


def detach(args, opts):
    if args:
        usage()
    name, record = own_record()
    save(name, {**record, "attached": False})
    print(f"DETACHED {name}")
    return 0


def authority(args, opts):
    if len(args) != 1 or args[0] not in LEVELS:
        usage()
    name, record = own_record()
    save(name, {**record, "authority": args[0]})
    print(f"AUTHORITY {name} {args[0]}")
    return 0


def report(args, opts):
    if args:
        usage()
    text = sys.stdin.read().rstrip("\n")
    found = attached()
    if not found or not text.strip():
        return 0
    quiet = {} if WAKING.match(text.split("\n", 1)[0]) else {"--quiet": True}
    return mail.send(mail_root(), [f"{OWNER}/in", text], {"--from": found[0], **quiet})


def typed(args, opts):
    if args:
        usage()
    prompt = sys.stdin.read().strip()
    found = attached()
    if found and not RING.fullmatch(prompt) and not prompt.startswith(NOT_TYPED):
        save(found[0], {**found[1], "typed": lib.utc_now()})
    return 0


# subcommand: (handler, its options; True when the option takes a value)
COMMANDS = {
    "attach": (attach, {"--hold": True}),
    "detach": (detach, {}),
    "authority": (authority, {}),
    "report": (report, {}),
    "typed": (typed, {}),
}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        usage()
    handler, spec = COMMANDS[argv[0]]
    args, opts = lib.take_options(argv[1:], spec)
    try:
        return handler(args, opts)
    except Refused as e:
        print(f"REFUSED {e}")
        return 1


if __name__ == "__main__":
    lib.entry(main)
