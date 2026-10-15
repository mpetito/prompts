"""The control layer's script: a session attaches under a name and reports to the controller, and the controller
steers attached sessions through their mailboxes. references/protocol.md is the contract (Protocol version 1): every
subcommand's arguments, every line it prints, and the files under $ORCHESTRATION_HOME/control (default
~/.orchestration/control), which only this script writes.
  ctl.py attach <name> [--hold <minutes>]
  ctl.py detach
  ctl.py authority observe|relay|delegate
  ctl.py report      the report is stdin
  ctl.py typed       the prompt is stdin
  ctl.py sessions
  ctl.py send <name> OWNER|CONTROL|QUESTION <text>
  ctl.py send <name> DECISION <ref> <answer> [--owner]
  ctl.py read
  ctl.py wait [--timeout <seconds>]
  ctl.py ring <name|pane> <attach-name>
  ctl.py ring <name|pane> --brief <file>
  ctl.py start <name> <folder> <objective-file>
After a "--" argument, every later argument is text, never an option. A session's subcommands find its record by
HERDR_PANE_ID. A refusal prints REFUSED <reason> and exits 1.
"""
import contextlib
import io
import json
import os
import re
import sys
import time
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
    """The name an agent from herdr's list is attached under, or None: an attached record with the agent's herdr name
    and pane. Only a Claude agent attaches: a Codex session has no wait to wake it, so it is observed and rung."""
    record = load(agent["name"]) if agent.get("name") and agent.get("agent") == "claude" else None
    return agent["name"] if record and record["attached"] and record["pane"] == agent.get("pane_id") else None


def wait_command():
    """For the session's hooks: the command of this pane's WAIT line, or None when the pane isn't attached. Reads
    the records only, never herdr."""
    found = attached()
    return wait_line(found[0]) if found else None


# --- herdr -------------------------------------------------------------------------------------------------------

def herdr(*args, text=False):
    """The "result" object of herdr's JSON reply to args, or with text its stdout as printed (agent read prints the
    screen, not JSON). HerdrError when herdr fails, or replies with anything but JSON holding a result object, so no
    caller reads a reply herdr didn't give."""
    r = lib.run(["herdr", *args])
    if text and r.returncode == 0:
        return r.stdout
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


# --- controller subcommands --------------------------------------------------------------------------------------

# What each level lets the controller send: the message kind, and for a decision who made it.
PERMITS = {
    "observe": (),
    "relay": ("OWNER", "QUESTION", "DECISION owner"),
    "delegate": ("OWNER", "QUESTION", "DECISION owner", "CONTROL", "DECISION controller"),
}


def message_kind(text):
    """The PERMITS kind of a down message's text: OWNER, CONTROL, QUESTION, or DECISION and who made it from its
    second line. Text that opens with none of them is the controller's own direction, so it counts as CONTROL."""
    lines = text.split("\n")
    if m := re.match(r"(OWNER|CONTROL|QUESTION):", lines[0]):
        return m[1]
    if re.match(r"DECISION [^\s:]+:", lines[0]):
        return f"DECISION {'owner' if lines[1:2] == ['By: owner'] else 'controller'}"
    return "CONTROL"


# The input line's prompt mark: Claude Code's, then Codex's.
PROMPT_MARK = re.compile(r"\s*[❯›]")
CSI = re.compile(r"\x1b\[([0-9;?]*)([A-Za-z])")
# The rule under Claude's input box; Codex draws none.
RULE = re.compile(r"\s*\u2500")


def named(name):
    """The record of a would-be name, or None for a name outside the pattern (a pane id, say) or one never used."""
    return load(name) if NAME.fullmatch(name) else None


def records_of(agent):
    """The records agent is the session of, as [(name, record)]; or None for a named agent that isn't its name's
    record's session, such as orchestration's. A record's session is the agent in its pane: herdr names whatever
    agent asks next, so after a session exits its name alone says nothing about who holds it. A named agent has only
    its name's record. An unnamed one, whose name herdr cleared or never gave, has the attached record with its
    session id, which a resume keeps, so a session continued in another pane keeps its name's level; else its pane's
    attached record; else every record in its pane: one pane can hold a record for each name it was detached or
    started under. The session id comes first because a pane's attached record may be an exited session's."""
    if agent.get("name"):
        record = named(agent["name"])
        return [(agent["name"], record)] if record and record["pane"] == agent.get("pane_id") else None
    sid, every = session_id(agent), records()
    tied = [(n, r) for n, r in every if r["attached"] and sid and r.get("session") == sid]
    mine = [(n, r) for n, r in every if r["pane"] == agent.get("pane_id")]
    return tied[:1] or [m for m in mine if m[1]["attached"]][:1] or mine


def agents():
    """herdr's live agent list."""
    found = herdr("agent", "list").get("agents")
    if not isinstance(found, list):
        raise HerdrError("unexpected reply: no agent list")
    return found


def held_until(record):
    """The epoch second the hold window after the owner's last typed prompt ends, or None once it has passed."""
    if not record["typed"]:
        return None
    until = lib.to_epoch(record["typed"]) + record["hold"] * 60
    return until if time.time() < until else None


def sessions(args, opts):
    if args:
        usage()
    listed = agents()
    rows = []  # (target, kind, state, the attached name or None)
    for agent in listed:
        name = attached_as(agent)
        rows.append((name or agent.get("name") or agent.get("pane_id"), agent.get("agent") or "null",
                     agent.get("agent_status") or "null", name))
    rows += [(n, "-", "gone", n) for n, r in records()
             if r["attached"] and not any(a.get("name") == n and a.get("pane_id") == r["pane"] for a in listed)]
    for target, kind, state, name in rows:
        record = load(name) if name else None
        until = held_until(record) if record else None
        unread = mail.waking(mail.box_dir(mail_root(), f"{name}/in")) if name else "-"
        print(" ".join((target, kind, state, record["authority"] if record else "unattached",
                        lib.fmt_utc(until) if until else "-", str(unread))))
    if not rows:
        print("NONE")
    return 0


def send(args, opts):
    if len(args) == 3 and args[1] in ("OWNER", "CONTROL", "QUESTION") and "--owner" not in opts:
        name, kind, text = args
        body = f"{kind}: {text}"
    elif len(args) == 4 and args[1] == "DECISION" and re.fullmatch(r"[^\s:]+", args[2]):
        name, by = args[0], "owner" if "--owner" in opts else "controller"
        kind, text = f"DECISION {by}", args[3]
        body = f"DECISION {args[2]}: {text}\nBy: {by}"
    else:
        usage()
    if not text.strip():
        usage()
    record = named(name)
    if not (record and record["attached"]):
        raise Refused(f"{name} is not attached")
    if kind not in PERMITS[record["authority"]]:
        raise Refused(f"{name} is at {record['authority']}")
    # The owner's newest words win, typed or relayed, so only the controller's own direction waits for the owner.
    until = held_until(record)
    if until and kind not in ("OWNER", "QUESTION"):
        print(f"HELD {lib.fmt_utc(until)}")
        return 1
    return mail.send(mail_root(), [f"{name}/in", body], {"--from": OWNER})


def read(args, opts):
    if args:
        usage()
    return mail.read(mail_root(), [f"{OWNER}/in"], {})


def wait(args, opts):
    if args:
        usage()
    watch = ",".join(f"{n}={n}/in" for n, r in records() if r["attached"])
    return mail.wait(mail_root(), [f"{OWNER}/in"], {**opts, **({"--watch": watch} if watch else {})})


def visible(line):
    """line as the screen shows it, without escape codes and without its dim text: the dim text on an input line is
    a placeholder or a suggested prompt, never typing."""
    shown, dim, at = [], False, 0
    for m in CSI.finditer(line):
        if not dim:
            shown.append(line[at:m.start()])
        at = m.end()
        if m[2] == "m":
            dim = sgr_dim(m[1], dim)
    if not dim:
        shown.append(line[at:])
    return "".join(shown)


def sgr_dim(params, dim):
    """Whether text is dim after an SGR sequence with these parameters, given whether it was before."""
    codes = [int(p) if p.isdigit() else 0 for p in params.split(";")]
    i = 0
    while i < len(codes):
        if codes[i] in (38, 48, 58):
            # A colour's own parameters follow it: 5;<n>, or 2;<r>;<g>;<b>. A 2 among them isn't dim.
            i += 3 if codes[i + 1:i + 2] == [5] else 5
            continue
        if codes[i] == 2:
            dim = True
        elif codes[i] in (0, 22):
            dim = False
        i += 1
    return dim


def input_line_empty(screen):
    """True when the last input line on the screen (the last line opening with a prompt mark) holds no typing, nor
    does any line between it and the rule closing Claude's input box, where a draft's later lines go. A screen with
    no input line isn't known to be empty, so it is not."""
    lines = screen.splitlines()
    marks = [i for i, line in enumerate(lines) if PROMPT_MARK.match(CSI.sub("", line))]
    if not marks:
        return False
    draft = [PROMPT_MARK.sub("", visible(lines[marks[-1]]), count=1)]
    rule = next((i for i in range(marks[-1] + 1, len(lines)) if RULE.match(CSI.sub("", lines[i]))), None)
    if rule is not None:
        draft += [visible(line) for line in lines[marks[-1] + 1:rule]]
    return not "".join(draft).strip()


def ring(args, opts):
    if len(args) == 2 and "--brief" not in opts:
        target, attach_name, kind = args[0], args[1], "claude"
        check_name(attach_name)
        line = f"/control-attach {attach_name}"
    elif len(args) == 1 and "--brief" in opts:
        target, attach_name, kind = args[0], None, "codex"
        line = f"Read {lib.native(lib.canon(opts['--brief']))} and follow it."
    else:
        usage()
    agent = live_agent(target)
    if agent is None:
        # herdr cleared the name when the session exited or a /clear replaced it; the session is back in the
        # record's pane at once after a /clear, or once resumed there.
        record = named(target)
        if record:
            agent = live_agent(record["pane"])
    if agent is None:
        raise Refused(f"no agent at {target}")
    pane = agent.get("pane_id")
    mine = records_of(agent)
    if mine is None:
        raise Refused(f"{target} is named {agent.get('name')}")
    if any(r["authority"] == "observe" for _, r in mine):
        raise Refused(f"{target} is at observe")
    # Attaching under another name would give the session that name's level, which only the owner sets.
    if mine and attach_name and attach_name not in [n for n, _ in mine]:
        raise Refused(f"{target} is attached as {mine[0][0]}")
    if agent.get("agent") != kind:
        raise Refused(f"{target} is {agent.get('agent') or 'null'}")
    state = agent.get("agent_status") or "null"
    if state not in ("idle", "done"):
        raise Refused(f"{target} is {state}")
    if not input_line_empty(herdr("agent", "read", pane, "--source", "visible", "--format", "ansi", text=True)):
        raise Refused(f"{target}'s input line is not empty")
    herdr("agent", "prompt", pane, line)
    print(f"RUNG {target}")
    return 0


def start(args, opts):
    if len(args) != 3:
        usage()
    name, folder, objective = args
    check_name(name)
    listing = control() / "folders"
    try:
        allowed = [f.strip() for f in lib.read_lines(listing) if f.strip()]
    except FileNotFoundError:
        raise Refused(f"no folders file at {lib.native(listing)}") from None
    # The list first, so a refusal never says whether a path outside it exists.
    if not any(lib.inside(folder, f) for f in allowed):
        raise Refused(f"{folder} is not a listed folder")
    if not os.path.isdir(folder):
        raise Refused(f"{folder} is not a folder")
    try:
        text = Path(objective).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        text = ""
    if not text.strip():
        raise Refused(f"cannot read {objective}")
    # A name's level and hold outlive its sessions, as on attach: only the owner changes a level. The objective is
    # a down message, so the kept level must permit it, as send checks.
    old = load(name) or {}
    level = old.get("authority", DEFAULT_AUTHORITY)
    if message_kind(text) not in PERMITS[level]:
        raise Refused(f"{name} is at {level}")
    listed = agents()
    panes = {a.get("pane_id") for a in listed}
    # Spec question 4. A started session counts while herdr lists its pane.
    if sum(1 for _, r in records() if r["started"] and r["pane"] in panes) >= 3:
        raise Refused("3 started sessions are running")
    holder = next((a.get("pane_id") for a in listed if a.get("name") == name), None)
    if holder:
        raise Refused(f"{name} is held by pane {holder}")
    # The new workspace doesn't inherit this process's environment, so a non-default home is passed on.
    home = os.environ.get("ORCHESTRATION_HOME")
    made = herdr("workspace", "create", "--cwd", lib.canon(folder), "--label", name, "--no-focus",
                 *(["--env", f"ORCHESTRATION_HOME={home}"] if home else []))
    pane = (made.get("root_pane") or {}).get("pane_id")
    if not isinstance(pane, str) or not pane:
        raise HerdrError("unexpected reply: no root pane")
    try:
        herdr("agent", "start", name, "--kind", "claude", "--pane", pane, "--timeout", "120000")
        ready = True
    except HerdrError as e:
        if e.code != "agent_not_ready":
            raise
        ready = False
    save(name, {"pane": pane, "authority": level,
                "hold": old.get("hold", DEFAULT_HOLD), "typed": "", "attached": False, "started": True})
    with contextlib.redirect_stdout(io.StringIO()):
        mail.send(mail_root(), [f"{name}/in", text.rstrip("\n")], {"--from": OWNER})
    if ready:
        try:
            herdr("agent", "prompt", name, f"/control-attach {name}")
        except HerdrError:
            # The session runs either way, and the remedy is the same: ring it once it is idle.
            ready = False
    if not ready:
        print(f"BLOCKED {name} waiting on a startup prompt")
        return 0
    print(f"STARTED {name} {pane}")
    return 0


# subcommand: (handler, its options; True when the option takes a value)
COMMANDS = {
    "attach": (attach, {"--hold": True}),
    "detach": (detach, {}),
    "authority": (authority, {}),
    "report": (report, {}),
    "typed": (typed, {}),
    "sessions": (sessions, {}),
    "send": (send, {"--owner": False}),
    "read": (read, {}),
    "wait": (wait, {"--timeout": True}),
    "ring": (ring, {"--brief": True}),
    "start": (start, {}),
}


def main(argv):
    if not argv or argv[0] not in COMMANDS:
        usage()
    handler, spec = COMMANDS[argv[0]]
    # Text after "--" is never an option, so an answer of "--owner" can't make a decision the owner's.
    rest = argv[1:]
    cut = rest.index("--") if "--" in rest else len(rest)
    args, opts = lib.take_options(rest[:cut], spec)
    args += rest[cut + 1:]
    try:
        return handler(args, opts)
    except Refused as e:
        print(f"REFUSED {e}")
        return 1


if __name__ == "__main__":
    lib.entry(main)
