"""Land an approved lane when the build lands locally (LANDING: local in .orchestration/thread.md): check the lane's
head is the approved commit, merge it --no-ff into orchestration/<build> in the coordination worktree, run the check
command there, and undo the merge if the check fails. MAIN later brings orchestration/<build> into the base with
thread.py integrate.
  land_local.py <lane branch> <approved sha> --check "<command>" [--subject "<text>"]
Run from the coordination worktree. Prints one final line: LANDED lane=<branch> head=<sha7> merge=<sha7>, or
STOPPED lane=<branch> <reason>. The check command is bash text, run with bash -c (Git Bash on Windows); its output
goes to .orchestration/results/land-<lane>.log as it runs.
"""
import os
import shutil
from pathlib import Path

import lib

USAGE = 'usage: land_local.py <lane branch> <approved sha> --check "<command>" [--subject "<text>"]'
OPTIONS = {"--check": True, "--subject": True}


class Stopped(Exception):
    """A STOPPED line's reason."""


def main(argv):
    if len(argv) < 2:
        raise lib.Fail(USAGE)
    lane, sha = argv[:2]
    opts = lib.only_options(argv[2:], OPTIONS, USAGE)
    if not opts.get("--check"):
        raise lib.Fail(USAGE)
    top = lib.toplevel(os.getcwd())
    if not top:
        raise lib.Fail("run land_local.py from the coordination worktree")
    try:
        print(land(top, lane, sha, opts["--check"], opts.get("--subject", "")))
    except Stopped as e:
        print(f"STOPPED lane={lane} {e}")
    return 0


def land(top, lane, sha, check, subject):
    """Merge lane's approved head into the coordination branch and keep it only if check passes. The LANDED line, or
    Stopped."""
    def git(*args):
        return lib.git(top, *args)

    if lib.thread_field(top, "LANDING") != "local":
        raise Stopped(f"LANDING is not local in {lib.native(Path(top, '.orchestration', 'thread.md'))}; "
                      "land pull requests with land.py")
    branch = git("symbolic-ref", "--quiet", "--short", "HEAD")
    if branch is None:
        raise Stopped("the coordination worktree has a detached HEAD")
    if not branch.startswith("orchestration/"):
        raise Stopped(f"the coordination worktree is on {branch}, not orchestration/<build>")
    if git("diff", "--quiet") is None or git("diff", "--cached", "--quiet") is None:
        raise Stopped(f"uncommitted changes to tracked files in {lib.native(top)}")
    head = git("rev-parse", "--verify", "-q", f"refs/heads/{lane}^{{commit}}")
    if head is None:
        raise Stopped(f"no branch {lane}")
    approved = git("rev-parse", "--verify", "-q", f"{sha}^{{commit}}")
    if approved is None:
        raise Stopped(f"no commit {sha}")
    if head != approved:
        raise Stopped(f"head is {head[:7]}, not the approved {approved[:7]}; send the new commits to the reviewer as "
                      "a delta")
    if git("merge-base", "--is-ancestor", head, "HEAD") is not None:
        raise Stopped(f"{head[:7]} is already on {branch}")
    bash = find_bash()
    if not bash:
        raise Stopped("no bash for the check command")
    before = git("rev-parse", "HEAD")
    message = f"Merge {lane}: {subject}" if subject else f"Merge {lane}"
    if git("-c", "core.editor=true", "merge", "-q", "--no-ff", "-m", message, head) is None:
        conflicted = lib.run(["git", "-C", top, "diff", "--name-only", "--diff-filter=U"]).stdout
        git("merge", "--abort")
        raise Stopped(f"merging into {branch} conflicts in: {conflicted.replace(chr(10), ' ')}(rebase the lane on "
                      f"{branch} and review the delta)")
    merge = git("rev-parse", "HEAD")
    log = Path(top, ".orchestration", "results", f"land-{lane.replace('/', '-')}.log")
    log.parent.mkdir(parents=True, exist_ok=True)
    if lib.run([bash, "-c", check], cwd=top, log=log).returncode:
        # The tree was clean before the merge, so resetting to it drops only this merge.
        git("reset", "-q", "--hard", before)
        raise Stopped(f"check failed on merge {merge[:7]}, merge undone; output in {lib.native(log)}")
    return f"LANDED lane={lane} head={head[:7]} merge={merge[:7]}"


def find_bash(os_name=os.name, env=None):
    """The bash that runs the check command, or None. On Windows it is Git Bash: $CLAUDE_CODE_GIT_BASH_PATH when it
    names a file, else the bin\\bash.exe of the Git for Windows install holding the git on PATH (git.exe sits in its
    cmd\\, bin\\ or mingw64\\bin\\). Never a bash found by name on PATH there: from PowerShell that is WSL's launcher,
    C:\\Windows\\System32\\bash.exe, which runs the check in a Linux distribution. Elsewhere it is bash on PATH."""
    env = os.environ if env is None else env
    path = env.get("PATH")
    if os_name != "nt":
        return shutil.which("bash", path=path)
    if os.path.isfile(env.get("CLAUDE_CODE_GIT_BASH_PATH", "")):
        return env["CLAUDE_CODE_GIT_BASH_PATH"]
    git = shutil.which("git", path=path)
    if not git:
        return None
    for folder in Path(git).resolve().parents:
        if (folder / "bin" / "bash.exe").is_file():
            return str(folder / "bin" / "bash.exe")
    return None


if __name__ == "__main__":
    lib.entry(main)
