"""Retire a lane's worktree without losing its evidence: archive its scratch directory and its ignored files (eval runs,
logs; not dependency or cache folders) first, refuse while an agent still runs there, then remove the worktree and
delete the local branch. Ignored files land under <archive dir>/ignored/ at their own paths.
  finish_lane.py <lane worktree, e.g. ../<repo>-wt-<lane>> <archive dir> [--scratch <relative path, default .orchestration/tmp>] [--keep-branch]
Prints one line per step done; refusals go to stderr with exit 1.
"""
import json
import os
import shutil

import lib

USAGE = "usage: finish_lane.py <worktree> <archive dir> [--scratch <relative path>] [--keep-branch]"
OPTIONS = {"--scratch": True, "--keep-branch": False}


def main(argv):
    if len(argv) < 2:
        raise lib.Fail(USAGE)
    wt, archive = argv[:2]
    opts = lib.only_options(argv[2:], OPTIONS, USAGE)
    scratch = opts.get("--scratch", ".orchestration/tmp")
    if not os.path.isdir(wt):
        raise lib.Fail(f"no worktree at {wt}")
    archive = lib.canon(archive)
    if lib.git(wt, "rev-parse", "--is-inside-work-tree") is None:
        raise lib.Fail(f"not a git worktree: {wt}")
    live = agents_in(wt)
    if live:
        raise lib.Fail(f"refusing: agent(s) still run in {wt}: " + "\n".join(live))

    if os.path.isdir(os.path.join(wt, scratch)):
        shutil.copytree(os.path.join(wt, scratch), archive, symlinks=True, dirs_exist_ok=True)
        print(f"archived {lib.native(os.path.join(wt, scratch))} to {lib.native(archive)}")
    # A failed listing would archive nothing and still remove the worktree, so it stops everything.
    for line in lib.archive_ignored(wt, archive, scratch):
        print(line)
    # Untracked output names the first unignored ancestor, so ".orchestration/" may stand for the scratch dir.
    leftover = [line for line in (lib.git(wt, "status", "--porcelain") or "").splitlines()
                if not (f"{scratch}/".startswith(line[3:]) or line[3:].startswith(scratch))]
    if leftover:
        raise lib.Fail(f"refusing: uncommitted changes in {wt}:\n" + "\n".join(leftover))
    branch = lib.git(wt, "rev-parse", "--abbrev-ref", "HEAD")
    # --show-toplevel would name the worktree itself; the common git dir sits under the main checkout.
    main_checkout = os.path.dirname(lib.git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    # --force only skips git's own untracked-file check; the leftover check above already proved that nothing but
    # the archived scratch directory is untracked and nothing is modified.
    r = lib.run(["git", "-C", main_checkout, "worktree", "remove", "--force", lib.canon(wt)])
    if r.returncode:
        raise lib.Fail(r.stderr.strip())
    print(f"removed worktree {wt}")
    if "--keep-branch" not in opts and branch != "HEAD" \
            and lib.git(main_checkout, "branch", "-D", branch) is not None:
        print(f"deleted branch {branch}")
    return 0


def agents_in(wt):
    """Names of the herdr agents whose working directory is wt or below it. Only inside herdr can a peer agent be
    running there; elsewhere, or when herdr can't list its agents, there is nothing to ask. herdr reports a cwd in
    its own platform's spelling (D:\\x on Windows), and a lane's sibling may share its name as a prefix, so the
    comparison is lib.inside's."""
    if os.environ.get("HERDR_ENV") != "1":
        return []
    r = lib.run(["herdr", "agent", "list"])
    try:
        agents = json.loads(r.stdout)["result"]["agents"] if r.returncode == 0 else []
    except (ValueError, KeyError, TypeError):
        return []
    return [a.get("name") or a.get("pane_id") for a in agents if a.get("cwd") and lib.inside(a["cwd"], wt)]


if __name__ == "__main__":
    lib.entry(main)
