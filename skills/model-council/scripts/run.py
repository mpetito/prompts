"""The council scripts' spawn helper. Imported, not run: every external command they start goes through run(), so a
test replaces that one function.
"""
import os
import shutil
import signal
import subprocess

if os.name == "nt":
    # shutil.which would otherwise look in the current directory first, where a repository could hold a codex.cmd.
    os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")


def run(args, *, cwd=None, stdin=None, stdout=None, stderr=None, timeout=None):
    """Run args (a list, no shell) in cwd and return its exit code.

    stdin is a file path to read, stdout and stderr file paths to write (replaced); each left None is the null device.
    args[0] is resolved on PATH (PATHEXT on Windows, so an npm .cmd shim is found); a command that isn't found returns
    127, as a shell would. timeout is in seconds: when it passes, the whole process tree is killed and the code is 124,
    as timeout(1) gives, so nothing the command started can write after the caller has moved on."""
    exe = shutil.which(args[0])
    if not exe:
        return 127
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    with open(stdin or os.devnull, "rb") as i, open(stdout or os.devnull, "wb") as o, \
            open(stderr or os.devnull, "wb") as e, \
            subprocess.Popen([exe, *args[1:]], stdin=i, stdout=o, stderr=e, cwd=cwd, **kw) as p:
        try:
            return p.wait(timeout)
        except subprocess.TimeoutExpired:
            kill_tree(p)
            p.wait()
            return 124


def kill_tree(p):
    """Kill a process started by run() and everything it started: an npm shim's node child outlives its parent."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
