"""A build's mailboxes, one maildir per box under <home>/mail, addressed <build>/<box>: main is what MAIN reads for
the build, thread is the thread's inbox.
  mail.py send <build>/<box> --from <build>/<box or lane> [--quiet] [<text> | --file <path>]   the body is stdin
                                                                         when neither; never empty
  mail.py read <build>/<box>
  mail.py wait <build>/<box> [--watch <agent>[=<build>/<box>],...] [--timeout <seconds>]
  Every subcommand takes --home <path>: <home> is that path, else $ORCHESTRATION_HOME, else ~/.orchestration.
  A Codex lane's sandbox can't see its pane's environment, so its brief passes --home.
send prints SENT <to> <file>. A quiet message wakes no wait; the next read prints it with the rest. read prints each
new message, oldest first, after a "=== <file>" line, and files it, or prints NO MAIL. wait checks every 2 s and
prints one line, then exits 0:
  MAIL <n>            the box holds n unread messages that are not quiet
  BLOCKED <agent>     a watched agent entered herdr's blocked state (a permission or question prompt); once per prompt
  GONE <agent>        a watched agent left herdr's agent list
  UNREAD <agent> <n>  a watched agent sits idle while its own box (after the =) holds n messages, not quiet, older
                      than 5 minutes, so it stopped waiting; once until it works again
  TIMEOUT             no news within --timeout; without it, within as long as the box has been quiet since its newest
                      message, read or not, at least an hour and at most 8, so an idle build wakes its waiter less
                      and less often
A message is written to tmp/ and renamed into new/, so a reader never sees half of one; read moves it to cur/.
A waiter keeps what it last saw of each watched agent in <box>/.watch/<agent>: "<herdr state> <unread reported>".
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lib

# Mail sits unread this long, in seconds, before an idle receiver counts as not waiting: longer than any turn spent
# between reading mail and starting the next wait.
UNREAD_AFTER = 5 * 60
POLL = 2
# A wait without --timeout lasts as long as its box has been quiet, between these bounds, in seconds.
WAIT_MIN = 3600
WAIT_MAX = 8 * 3600
# wait's clock and pause; tests replace them to pass time without waiting.
clock = time.time
sleep = time.sleep
# The nanosecond stamp of this process's last send.
last_sent = 0


def usage():
    lib.usage_from(__doc__, 3, 8)


def box_dir(root, address):
    """The folder of box <build>/<box> under root, created on first use; the names follow herdr's agent-name
    pattern, and Fail names any other address."""
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}/[a-z][a-z0-9_-]{0,31}", address):
        raise lib.Fail(f"not a <build>/<box> address: {address}")
    box = root / address
    for sub in ("tmp", "new", "cur", ".watch"):
        (box / sub).mkdir(parents=True, exist_ok=True)
    return box


def waking(box, before=None):
    """The unread messages in box that are not quiet; when before is given, only those last modified before that
    epoch second."""
    return sum(1 for p in (box / "new").iterdir()
               if not p.name.endswith(".quiet.md") and (before is None or older(p, before)))


def older(path, epoch):
    """True when path was last modified before epoch; False when it is gone, as a read may file a message between
    the listing and this look."""
    try:
        return path.stat().st_mtime < epoch
    except FileNotFoundError:
        return False


def quiet_for(box):
    """Seconds since the newest message in box, read or not, arrived; 0 when it holds none."""
    times = [p.stat().st_mtime for sub in ("new", "cur") for p in (box / sub).iterdir() if p.is_file()]
    return clock() - max(times) if times else 0


def send(root, args, opts):
    # One argument is the whole message: an unquoted one would arrive as several and is refused.
    if not 1 <= len(args) <= 2 or "--from" not in opts:
        usage()
    to = args[0]
    if "--file" in opts:
        try:
            body = Path(opts["--file"]).read_text(encoding="utf-8").rstrip("\n")
        except (OSError, UnicodeDecodeError) as e:
            raise lib.Fail(f"cannot read {opts['--file']} as UTF-8 text: {e}") from e
    elif len(args) == 2:
        body = args[1]
    else:
        body = sys.stdin.read().rstrip("\n")
    if not body.strip():
        raise lib.Fail(f"refusing an empty message to {to}")
    box = box_dir(root, to)
    # Nanoseconds keep same-second messages in the order they were sent. A coarse clock repeats a stamp (time_ns
    # ticks every 15.6 ms on Windows before Python 3.13), and the rename below would replace a message of the same
    # name, so a stamp is always past this process's last one; other processes differ by pid.
    global last_sent
    ns = last_sent = max(time.time_ns(), last_sent + 1)
    sent = datetime.fromtimestamp(ns // 10**9, timezone.utc)
    name = f"{sent:%Y%m%dT%H%M%S}.{ns % 10**9:09d}Z-{os.getpid()}{'.quiet' if '--quiet' in opts else ''}.md"
    tmp = box / "tmp" / name
    tmp.write_text(f"From: {opts['--from']}\nDate: {sent:%Y-%m-%dT%H:%M:%SZ}\n\n{body}\n", encoding="utf-8",
                   newline="\n")
    os.replace(tmp, box / "new" / name)
    print(f"SENT {to} {name}")
    return 0


def read(root, args, opts):
    if len(args) != 1:
        usage()
    box = box_dir(root, args[0])
    # The names start with the send time, so name order is send order for each sender; two senders inside one tick
    # of the clock order by pid.
    messages = sorted(p for p in (box / "new").iterdir() if p.is_file())
    if not messages:
        print("NO MAIL")
    for p in messages:
        print(f"=== {p.name}")
        sys.stdout.write(p.read_text(encoding="utf-8"))
        print()
        os.replace(p, box / "cur" / p.name)
    return 0


def watch_once(root, box, specs):
    """The first watched agent's news as wait's line, or None. Nothing is judged when herdr can't list its agents,
    so a herdr hiccup never reads as every agent gone."""
    r = lib.run(["herdr", "agent", "list"])
    try:
        agents = json.loads(r.stdout)["result"]["agents"] if r.returncode == 0 else None
    except (ValueError, KeyError, TypeError):
        agents = None
    if agents is None:
        return None
    # herdr's null status is the state "null", as jq printed it; only an agent missing from the list is gone.
    states = {a["name"]: a.get("agent_status") or "null" for a in agents if a.get("name")}
    for spec in filter(None, specs.split(",")):
        agent, _, inbox = spec.partition("=")
        state = states.get(agent) or "gone"
        seen = box / ".watch" / agent
        last, reported = last_seen(seen)
        if state == "working":
            reported = "0"
        unread = 0
        if inbox and reported == "0" and state in ("idle", "done"):
            unread = waking(box_dir(root, inbox), clock() - UNREAD_AFTER)
            if unread:
                reported = "1"
        seen.write_text(f"{state} {reported}\n", encoding="utf-8")
        if state == "blocked" and last != "blocked":
            return f"BLOCKED {agent}"
        if state == "gone" and last and last != "gone":
            return f"GONE {agent}"
        if unread:
            return f"UNREAD {agent} {unread}"
    return None


def last_seen(seen):
    """The "<herdr state> <unread reported>" a waiter last wrote, or ("", "0") for none or one it can't read."""
    fields = seen.read_text(encoding="utf-8").split() if seen.exists() else []
    return tuple(fields) if len(fields) == 2 else ("", "0")


def wait(root, args, opts):
    if len(args) != 1:
        usage()
    box = box_dir(root, args[0])
    try:
        timeout = int(opts["--timeout"]) if "--timeout" in opts else min(WAIT_MAX, max(WAIT_MIN, quiet_for(box)))
    except ValueError:
        raise lib.Fail(f"not a number of seconds: {opts['--timeout']}") from None
    end = clock() + timeout
    while True:
        if n := waking(box):
            print(f"MAIL {n}")
            return 0
        if "--watch" in opts and (line := watch_once(root, box, opts["--watch"])):
            print(line)
            return 0
        if clock() >= end:
            print("TIMEOUT")
            return 0
        sleep(POLL)


# subcommand: (handler, its options beyond --home; True when the option takes a value)
COMMANDS = {
    "send": (send, {"--from": True, "--file": True, "--quiet": False}),
    "read": (read, {}),
    "wait": (wait, {"--watch": True, "--timeout": True}),
}


def main(argv):
    if len(argv) < 2 or argv[0] not in COMMANDS:
        usage()
    handler, spec = COMMANDS[argv[0]]
    args, opts = lib.take_options(argv[1:], {"--home": True, **spec})
    home = opts.get("--home") or os.environ.get("ORCHESTRATION_HOME") or Path.home() / ".orchestration"
    return handler(Path(home) / "mail", args, opts)


if __name__ == "__main__":
    lib.entry(main)
