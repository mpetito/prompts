"""The decision queue: one file, one line per open decision, each with a default and a deadline.
  decisions.py add "<what>" "<why now>" "<blocks>" "<default>" <UTC | +<N>m | +<N>h | owner-before>
  decisions.py list                      print open items, oldest first
  decisions.py due                       print open items whose deadline has passed
  decisions.py close <id> "<outcome>"    move an item to the Applied section
An owner-before item (spend, trust roots, production data, safety rules) never applies itself.
The file is $ORCHESTRATION_DECISIONS when set, else decisions.md beside the state file (state.py resolves it:
$ORCHESTRATION_STATE, or .orchestration/ at the root of the current git worktree).
"""
import os
import re
from pathlib import Path

import lib

HEADER = ("# Decisions\n\nOpen items apply their default at the deadline unless the owner objects. Owner-before items"
          " never apply themselves.\n\n## Open\n\n## Applied\n")


def ensure():
    """The decisions file, created with its two sections when missing."""
    file = os.environ.get("ORCHESTRATION_DECISIONS") or os.path.join(
        os.path.dirname(lib.resolve_state(os.getcwd(), "ORCHESTRATION_DECISIONS")), "decisions.md")
    if not os.path.isfile(file):
        os.makedirs(os.path.dirname(file) or ".", exist_ok=True)
        Path(file).write_text(HEADER, encoding="utf-8", newline="\n")
    return file


def open_items(file):
    """The lines between "## Open" and "## Applied"."""
    on = False
    for line in lib.read_lines(file):
        if line.startswith("## Open"):
            on = True
        elif line.startswith("## Applied"):
            on = False
        elif on:
            yield line


def add(args, now):
    if len(args) != 5:
        raise lib.Fail('usage: decisions.py add "<what>" "<why now>" "<blocks>" "<default>" '
                       '<UTC | +<N>m | +<N>h | owner-before>')
    what, why, blocks, default, deadline = args
    if deadline == "owner-before":
        when, said = "owner-before: waits for the owner", "owner-before (never applies itself)"
    else:
        at = lib.fmt_utc(lib.to_epoch(deadline))
        when, said = f"applies at {at} unless the owner objects", f"applies at {at}"
    file = ensure()
    lines = lib.read_lines(file)
    n = sum(1 for line in lines if re.match(r"- D[0-9]", line)) + 1
    entry = f"- D{n} ({now}) {what} · why now: {why} · blocks: {blocks} · default: {default} · {when}"
    at_applied = next((i for i, line in enumerate(lines) if line.startswith("## Applied")), None)
    if at_applied is not None:
        lines[at_applied:at_applied] = [entry, ""]
    lib.replace_lines(file, lines)
    print(f"D{n} {said}")


def list_open(args, now):
    if args:
        raise lib.Fail("usage: decisions.py list")
    for line in open_items(ensure()):
        if line.startswith("- D"):
            print(line)


def due(args, now):
    if args:
        raise lib.Fail("usage: decisions.py due")
    # The stamps share one fixed-width format, so a string comparison orders them in time.
    for line in open_items(ensure()):
        if line.startswith("- D") and (m := re.search(r"applies at ([0-9T:Z-]+)", line)) and m[1] <= now:
            print(line)


def close(args, now):
    if len(args) != 2:
        raise lib.Fail('usage: decisions.py close <id> "<outcome>"')
    item, outcome = args
    file = ensure()
    if not any(line.startswith(f"- {item} ") for line in open_items(file)):
        raise lib.Fail(f"no open item {item}")
    out, moved, on = [], None, False
    for line in lib.read_lines(file):
        if line.startswith("## Open"):
            on = True
        elif line.startswith("## Applied"):
            on = False
        if on and line.startswith(f"- {item} "):
            moved = f"{line} · closed {now}: {outcome}"
        else:
            out.append(line)
    lib.replace_lines(file, [*out, moved])
    print(f"closed {item} {now}")


COMMANDS = {"add": add, "list": list_open, "due": due, "close": close}


def main(argv):
    now = lib.utc_now()
    if not argv or argv[0] not in COMMANDS:
        lib.usage_from(__doc__, 1, 8)
    COMMANDS[argv[0]](argv[1:], now)
    return 0


if __name__ == "__main__":
    lib.entry(main)
