"""The pull-request scripts' spawn helper and program entry. Imported, not run.

External commands (gh) run only through run(), so tests replace that one function.
"""
import argparse
import os
import shutil
import subprocess
import sys

if os.name == "nt":
    # shutil.which would otherwise look in the current directory first, where a checkout could hold a gh.cmd.
    os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")


class Fail(Exception):
    """A failure or usage error: entry prints the message on stderr and exits 1."""


class Parser(argparse.ArgumentParser):
    """argparse whose usage errors raise Fail (exit 1) instead of exiting 2."""

    def error(self, message):
        raise Fail(f"{self.format_usage().rstrip()}\n{self.prog}: error: {message}")


def run(args):
    """Run args (a list, no shell) and return a CompletedProcess with text stdout and stderr, decoded as UTF-8.

    args[0] is resolved on PATH (PATHEXT on Windows, so a .cmd shim is found); a command that isn't found returns
    code 127 with the reason on stderr, as a shell would. gh gets no timeout, as the PowerShell scripts gave it none."""
    exe = shutil.which(args[0])
    if not exe:
        return subprocess.CompletedProcess(args, 127, "", f"{args[0]}: command not found\n")
    r = subprocess.run([exe, *args[1:]], stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return subprocess.CompletedProcess(args, r.returncode, r.stdout, r.stderr)


def output(r):
    """A failed command's stdout and stderr, for an error message."""
    return (r.stdout + r.stderr).strip()


def entry(main):
    """Run a script's main(argv) as a program: UTF-8 stdio, a Fail printed on stderr, its exit code."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    try:
        code = main(sys.argv[1:])
    except Fail as e:
        print(e, file=sys.stderr)
        code = 1
    sys.exit(code)
