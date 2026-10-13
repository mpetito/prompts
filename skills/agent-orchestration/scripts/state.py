"""Edit the orchestration thread's state file without typing a timestamp by hand.
  state.py init <build>                       create .orchestration/ (briefs/, results/) and the skeleton
  state.py log "<event>"                      append "- <UTC now> <event>" to the "## Log" section
  state.py set <lane> <column> <value>        replace one cell of the "## Lanes" table
  state.py resume <file|->                    back up, then replace the RESUME body, stamped "Written: <UTC>"
  state.py backup                             copy the file to state.<UTC stamp>.md beside it
  state.py thread <key>                       print one field of the thread record (BUILD, BASE, LANE-BASE, ...)
  state.py now                                print the UTC stamp the other commands use
The file is $ORCHESTRATION_STATE when set, else .orchestration/state.md at the root of the git worktree that
holds the current directory: the build's coordination worktree, ../<repo>-orch-<build>. The build's name, the
base and the landing mode live in the thread record beside it, .orchestration/thread.md, which MAIN's
thread.py writes; read them with "thread".
"""
import os
import shutil
import sys
import time
from pathlib import Path

import lib

SKELETON = """# Orchestration thread: {build}

## Thread

Record: thread.md (MAIN, base, landing; written by MAIN)
Started: {now}

## RESUME

Written: {now}
(nothing yet)

## Lanes

| Lane | Agent | PR | Head SHA | Next action |
| --- | --- | --- | --- | --- |

## Decisions

## Log

- {now} thread started
"""


def usage():
    lib.usage_from(__doc__, 1, 12)


def resolve():
    return lib.resolve_state(os.getcwd(), "ORCHESTRATION_STATE")


def need_file():
    file = resolve()
    if not os.path.isfile(file):
        raise lib.Fail(f"no state file at {file}; start one with state.py init")
    return file


def backup(file):
    # Seconds in the stamp, so two backups in one minute (a resume right after a backup) both survive.
    dest = f"{file.removesuffix('.md')}.{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.md"
    shutil.copyfile(file, dest)
    return dest


def show_backup():
    file = need_file()
    print(f"backed up {file} to {backup(file)}")


def init(args, now):
    if len(args) != 1:
        raise lib.Fail("usage: state.py init <build>")
    file = resolve()
    if os.path.lexists(file):
        raise lib.Fail(f"refusing: {file} already exists")
    for sub in ("briefs", "results"):
        os.makedirs(os.path.join(os.path.dirname(file), sub), exist_ok=True)
    Path(file).write_text(SKELETON.format(build=args[0], now=now), encoding="utf-8", newline="\n")
    print(f"initialised {file} {now}")


def log(args, now):
    if len(args) != 1 or not args[0]:
        raise lib.Fail('usage: state.py log "<event>"')
    file = need_file()
    entry = f"- {now} {args[0]}"
    # Insert at the end of the Log section, before any later section and its blank lines, so the log stays one
    # block wherever the section sits.
    out, blanks, inlog, done = [], 0, False, False
    for line in lib.read_lines(file):
        if inlog and not line.strip():
            blanks += 1
            continue
        if line.startswith("## ") and inlog:
            out.append(entry)
            done, inlog = True, False
        out += [""] * blanks
        blanks = 0
        if line.startswith("## Log"):
            inlog = True
        out.append(line)
    if not done:
        if not inlog:
            out += ["", "## Log", ""]
        out.append(entry)
    lib.replace_lines(file, out)
    print(f"logged {now}")


def set_cell(args, now):
    if len(args) != 3:
        raise lib.Fail("usage: state.py set <lane> <column> <value>")
    lane, col, val = args
    file = need_file()
    out, inlanes, header, target, done = [], False, False, None, False
    for line in lib.read_lines(file):
        if line.startswith("## Lanes"):
            inlanes = True
        elif inlanes and line.startswith("## "):
            inlanes = False
        if inlanes and line.startswith("|"):
            # cells[0] is before the first "|" and cells[-1] after the last; the table's cells lie between.
            cells = line.split("|")
            if not header:
                header = True
                target = next((i for i in range(len(cells) - 2, 0, -1) if cells[i].strip() == col), None)
                if target is None:
                    raise lib.Fail(f"no column {col}")
            elif cells[1].strip() == lane:
                cells[target] = f" {val} "
                line = "|" + "|".join(cells[1:-1]) + "|"
                done = True
        out.append(line)
    if not done:
        raise lib.Fail(f"no lane {lane}")
    lib.replace_lines(file, out)
    print(f"set {lane}.{col} {now}")


def resume(args, now):
    if len(args) != 1:
        raise lib.Fail("usage: state.py resume <file|->")
    file = need_file()
    lines = lib.read_lines(file)
    if not any(line.startswith("## RESUME") for line in lines):
        raise lib.Fail(f"no ## RESUME section in {file}")
    if args[0] == "-":
        body = sys.stdin.read()
    elif os.path.isfile(args[0]):
        try:
            body = Path(args[0]).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            raise lib.Fail(f"cannot read {args[0]} as UTF-8 text: {e}") from e
    else:
        raise lib.Fail(f"no file {args[0]}")
    # A copied stamp would leave two; the helper writes the only one.
    body = "\n".join(line for line in body.rstrip("\n").split("\n") if not line.startswith("Written:")).rstrip("\n")
    if not body.strip():
        raise lib.Fail("refusing: empty RESUME")
    saved = backup(file)
    out, inres = [], False
    for line in lines:
        if line.startswith("## "):
            inres = False
            if line.startswith("## RESUME"):
                out += [line, "", f"Written: {now}", *body.split("\n"), ""]
                inres = True
                continue
        if not inres:
            out.append(line)
    lib.replace_lines(file, out)
    print(f"resume written {now} (previous copy {saved})")


def thread(args, now):
    if len(args) != 1:
        usage()
    top = os.path.dirname(os.path.dirname(need_file()))
    value = lib.thread_field(top, args[0])
    if not value:
        raise lib.Fail(f"no {args[0]} in {os.path.join(top, '.orchestration', 'thread.md')}")
    print(value)


COMMANDS = {
    "now": lambda args, now: print(now),
    "init": init,
    "backup": lambda args, now: show_backup(),
    "log": log,
    "set": set_cell,
    "resume": resume,
    "thread": thread,
}


def main(argv):
    now = lib.utc_now()
    if not argv or argv[0] not in COMMANDS:
        usage()
    COMMANDS[argv[0]](argv[1:], now)
    return 0


if __name__ == "__main__":
    lib.entry(main)
