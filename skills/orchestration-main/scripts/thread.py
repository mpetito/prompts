"""Launch, stop, rotate and list orchestration threads: herdr agents running the orchestrator agent, one per build,
each named after its build and started in the build's own herdr workspace from its coordination worktree,
../<repo>-orch-<build> beside the main checkout, on branch orchestration/<build>. The thread keeps its files in
that worktree's untracked .orchestration/ folder, and talks to MAIN through the build's mailboxes (mail.py).
  thread.py launch <build> <checkout> <brief file> [--base <branch>] [--landing pr|local]
  thread.py stop <build>
  thread.py rotate <build> [--force]
  thread.py check [--all]
  thread.py integrate <build>
  thread.py close <build> | --worktree <coordination worktree> [--base <branch>] [--force]
  thread.py list
  thread.py decisions
launch, stop, rotate and integrate print one line: LAUNCHED <build> base=<branch>@<sha> landing=<mode>,
BLOCKED <build> <reason> (launched, but waiting on a startup prompt the owner must answer), STOPPED <build>,
ROTATED <build>, INTEGRATED <build> <branch>@<sha> (fast-forward|merge), CLOSED <build> archive=<dir>, or
FAILED <reason> with exit 1. close ends a build: it refuses while the build branch holds work the base lacks,
archives .orchestration/ and the build's mail under $ORCHESTRATION_HOME/archive/<build>-<stamp>/ and the
worktree's other ignored files (not dependency or cache folders) under its ignored/, then removes the worktree and
branch and closes the build's workspace. check prints IDENTITY lines (a repository's local git config sets
user.name or user.email apart from the global one), or OK; list and decisions print one line per thread or item,
or NONE.
A build name is a herdr agent name, [a-z][a-z0-9_-]{0,31}, and a thread keeps it across rotations.
The base defaults to the checkout's current branch. Landing is pr when the base is on origin with nothing
unpushed, else local: lanes merge into orchestration/<build>, and integrate brings that branch into the base.
Each thread's .orchestration/thread.md records its build, the owner's checkout, the base and the landing mode.
MAIN's list of threads, across repositories, is $ORCHESTRATION_HOME/threads.tsv (default
~/.orchestration/threads.tsv), one tab-separated row per thread: build repo worktree workspace launched
"""
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "agent-orchestration" / "scripts"))
import lib  # noqa: E402

# ROTATE makes the thread rewrite RESUME just before it answers "STATUS: rotating"; an older stamp means it never
# answered, and its RESUME may miss recent work.
RESUME_MAX_AGE_MINUTES = 15
HEADER = "build\trepo\tworktree\tworkspace\tlaunched\n"


class Failed(Exception):
    """A refusal main prints on stdout as "FAILED <reason>", exiting 1."""


class HerdrError(Exception):
    """herdr failed; the message is "<code>: <message>" from its JSON error, or its raw output."""


def usage():
    raise lib.Fail(__doc__.rstrip())


def orchestration_home():
    return Path(os.environ.get("ORCHESTRATION_HOME") or Path.home() / ".orchestration")


def registry():
    return orchestration_home() / "threads.tsv"


def write(path, text):
    """Replace path's content with text atomically, with LF line ends on every OS."""
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    os.replace(tmp, path)


# --- the registry ------------------------------------------------------------------------------------------------

def rows():
    """The registry's rows, each a list of its five fields; empty when there is no registry."""
    try:
        lines = registry().read_text(encoding="utf-8").splitlines()[1:]
    except FileNotFoundError:
        return []
    return [(line.split("\t") + [""] * 5)[:5] for line in lines if line]


def row_by(build):
    return next((r for r in rows() if r[0] == build), None)


def put_rows(kept):
    orchestration_home().mkdir(parents=True, exist_ok=True)
    write(registry(), HEADER + "".join("\t".join(r) + "\n" for r in kept))


def delete_row(build):
    put_rows([r for r in rows() if r[0] != build])


def put_row(build, row):
    """Replace the row named build, or append row when there is none."""
    found, kept = False, []
    for r in rows():
        if r[0] == build:
            r, found = row, True
        kept.append(r)
    put_rows(kept if found else kept + [row])


def valid_name(build):
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", build):
        raise Failed(f"build name '{build}' must match [a-z][a-z0-9_-]{{0,31}}: it is the thread's herdr agent name")


# --- herdr -------------------------------------------------------------------------------------------------------

def herdr(*args):
    """herdr's JSON reply to args, parsed; HerdrError names herdr's reason when it fails, or carries its output when
    a reply isn't JSON."""
    r = lib.run(["herdr", *args])
    if r.returncode == 0:
        try:
            return json.loads(r.stdout or "{}")
        except ValueError:
            raise HerdrError(f"unexpected reply: {r.stdout.rstrip(chr(10))}") from None
    out = r.stdout + r.stderr
    try:
        err = json.loads(out)["error"]
        raise HerdrError(f"{err['code']}: {err['message']}")
    except (ValueError, KeyError, TypeError):
        raise HerdrError(out.rstrip("\n")) from None


def field(reply, *keys):
    """The value at keys in a herdr reply; HerdrError carrying the reply when it has another shape."""
    value = reply
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, IndexError, TypeError):
        raise HerdrError(f"unexpected reply: {json.dumps(reply)}") from None


def quietly(*args):
    """Run herdr args and ignore the outcome: a cleanup step that must not stop the one after it."""
    lib.run(["herdr", *args])


def agent(build):
    """herdr's record of the live agent named build, or {} when there is none."""
    try:
        return field(herdr("agent", "get", build), "result", "agent") or {}
    except HerdrError:
        return {}


def agent_pane(build):
    return agent(build).get("pane_id") or ""


def home_env():
    # The build's workspace doesn't inherit this process's environment, so a non-default home is passed on.
    home = os.environ.get("ORCHESTRATION_HOME")
    return ["--env", f"ORCHESTRATION_HOME={home}"] if home else []


def new_pane(build, wt, ws):
    """A fresh shell pane for the thread, in a new tab of workspace ws, or in a new workspace when ws is empty or
    gone: (pane, workspace). HerdrError when herdr can't make a workspace."""
    if ws:
        try:
            out = herdr("tab", "create", "--workspace", ws, "--cwd", str(wt), "--label", build, "--no-focus",
                        *home_env())
            return field(out, "result", "root_pane", "pane_id"), ws
        except HerdrError:
            pass
    out = herdr("workspace", "create", "--cwd", str(wt), "--label", build, "--no-focus", *home_env())
    return field(out, "result", "root_pane", "pane_id"), field(out, "result", "workspace", "workspace_id")


def start_thread(build, pane, brief):
    """Start the orchestrator agent on a one-line prompt naming the brief, since herdr refuses agent arguments it
    can't encode for the shell (a multi-line brief among them). Returns "" when it is ready, or a reason for the
    owner when it waits on a startup prompt (a folder trust question); HerdrError for any other failure."""
    try:
        herdr("agent", "start", build, "--kind", "claude", "--pane", pane, "--timeout", "120000", "--",
              "--agent", "orchestrator", f"Read {lib.native(brief)} and follow it.")
    except HerdrError as e:
        if str(e).startswith("agent_not_ready:"):
            return f"waiting on a startup prompt: answer it in workspace {build}"
        raise
    return ""


# --- git ---------------------------------------------------------------------------------------------------------

def common_dir(path):
    """The canon git common dir of the checkout at path, or None outside git."""
    common = lib.git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return lib.canon(common) if common else None


def branch_of(path):
    return lib.git(path, "symbolic-ref", "--quiet", "--short", "HEAD")


def identity_warnings(repo):
    """An IDENTITY line for each of user.name and user.email that the repository's local config (the common
    .git/config, shared by its linked worktrees) sets apart from the global value. A copied worktree's git config
    once wrote a test identity there, and commits on main took it."""
    lines = []
    for key in ("user.name", "user.email"):
        mine = lib.git(repo, "config", "--local", "--get", key) or ""
        g = lib.run(["git", "config", "--global", "--get", key])
        glob = g.stdout.rstrip("\n") if g.returncode == 0 else ""
        if mine and mine != glob:
            r = lib.native(repo)
            lines.append(f"IDENTITY {r} {key}={mine} (global {glob or 'none'}): a local git identity; remove it with "
                         f"git -C {r} config --unset {key} unless the owner set it")
    return lines


def brief_text(build, state, body):
    """The header lines, a blank line, then the body."""
    return (f"BUILD: {build}\nMAIL: {build}/thread is yours; send MAIN {build}/main\nSTATE: {lib.native(state)}\n\n"
            f"{body.rstrip(chr(10))}")


def write_record(wt, build, checkout, base, base_ref, lane_base, landing):
    folder = Path(wt, ".orchestration")
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / "thread.md", "\n".join([
        "# Thread record, written by MAIN's thread.py launch. The thread reads it and never edits it.",
        f"BUILD: {build}", f"CHECKOUT: {checkout}", f"BASE: {base}", f"BASE-REF: {base_ref}",
        f"LANE-BASE: {lane_base}", f"LANDING: {landing}", f"UPDATED: {lib.utc_now()}"]) + "\n")


def pick_base(main, base, want):
    """(base ref, landing): origin/<base> when the local branch has nothing unpushed (or is absent), else the local
    branch; landing follows, pr from origin and local otherwise, unless want asks for local."""
    if lib.git(main, "remote", "get-url", "origin") is not None and lib.git(main, "fetch", "-q", "origin") is None:
        print(f"warning: git fetch origin failed in {lib.native(main)}; using the refs already there", file=sys.stderr)
    local_ok = lib.git(main, "rev-parse", "--verify", "-q", f"refs/heads/{base}^{{commit}}") is not None
    remote_ok = lib.git(main, "rev-parse", "--verify", "-q", f"refs/remotes/origin/{base}^{{commit}}") is not None
    if not (local_ok or remote_ok):
        raise Failed(f"no branch {base} in {lib.native(main)} or on origin")
    if remote_ok and (not local_ok or lib.git(main, "merge-base", "--is-ancestor", f"refs/heads/{base}",
                                              f"refs/remotes/origin/{base}") is not None):
        base_ref, auto = f"origin/{base}", "pr"
    else:
        base_ref, auto = base, "local"
    if want == "pr" and auto != "pr":
        raise Failed(f"--landing pr needs {base} on origin with nothing unpushed; push it, or use --landing local")
    if want not in (None, "pr", "local"):
        raise Failed(f"--landing takes pr or local, got {want}")
    return base_ref, want or auto


def ensure_worktree(main, common, wt, build, base_ref):
    """Reuse the build's coordination worktree or create it from base_ref; Failed with a reason otherwise."""
    branch = f"orchestration/{build}"
    if os.path.exists(wt):
        its_common, its_top = common_dir(wt), lib.toplevel(wt)
        if its_common and its_top and lib.same_path(its_common, common) and lib.same_path(its_top, wt) \
                and lib.git(wt, "rev-parse", "--abbrev-ref", "HEAD") == branch:
            return
        raise Failed(f"{lib.native(wt)} exists and is not the coordination worktree for build {build} (branch {branch} "
                     f"of {lib.native(main)}); move it aside or pick another --build")
    if lib.git(main, "rev-parse", "--verify", "-q", f"refs/heads/{branch}") is not None:
        if lib.git(main, "worktree", "add", "-q", str(wt), branch) is None:
            raise Failed(f"git worktree add {lib.native(wt)} {branch} failed")
    # --no-track: the coordination branch must never push to, or pull from, the base by accident.
    elif lib.git(main, "worktree", "add", "-q", "--no-track", "-b", branch, str(wt), base_ref) is None:
        raise Failed(f"git worktree add {lib.native(wt)} from {base_ref} failed")


def started(build, waiting, done):
    print(f"BLOCKED {build} {waiting}" if waiting else done)
    return 0


# --- subcommands ---------------------------------------------------------------------------------------------------

def launch(args):
    if len(args) < 3:
        usage()
    build, repo, brief = args[:3]
    extra, opts = lib.take_options(args[3:], {"--base": True, "--landing": True})
    if extra:
        usage()
    base, want = opts.get("--base"), opts.get("--landing")
    valid_name(build)
    if not os.path.isdir(repo):
        raise Failed(f"no repository checkout at {repo}")
    if not os.path.isfile(brief) or os.path.getsize(brief) == 0:
        raise Failed(f"no brief at {brief}")
    try:
        body = Path(brief).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Failed(f"cannot read the brief {brief} as UTF-8 text: {e}") from None
    common = common_dir(repo)
    if not common:
        raise Failed(f"{repo} is not a git checkout")
    checkout = lib.toplevel(repo)
    # The main checkout holds the common git dir, so a linked worktree passed here still names the main one.
    main = os.path.dirname(common)
    wt = os.path.join(os.path.dirname(main), f"{os.path.basename(main)}-orch-{build}")
    if not base:
        base = branch_of(repo)
        if not base:
            raise Failed(f"{repo} is on a detached HEAD; pass --base <branch>")
    if row_by(build):
        raise Failed(f"a thread for build {build} is already registered; stop or close it, or pick another build name")
    if agent_pane(build):
        raise Failed(f"a live herdr agent is already named {build}; pick another build name")
    base_ref, landing = pick_base(main, base, want)
    ensure_worktree(main, common, wt, build, base_ref)
    exclude = Path(common, "info", "exclude")
    exclude.parent.mkdir(parents=True, exist_ok=True)
    if ".orchestration/" not in (exclude.read_text(encoding="utf-8").splitlines() if exclude.exists() else []):
        with open(exclude, "a", encoding="utf-8", newline="\n") as f:
            f.write(".orchestration/\n")
    lane_base = base_ref if landing == "pr" else f"orchestration/{build}"
    write_record(wt, build, checkout, base, base_ref, lane_base, landing)
    try:
        pane, ws = new_pane(build, wt, "")
    except HerdrError as e:
        raise Failed(f"herdr workspace create: {e}") from None
    # The row exists before the agent starts, so a thread waiting on a startup prompt is still known by name.
    put_row(build, [build, main, wt, ws, lib.utc_now()])
    brief_file = os.path.join(wt, ".orchestration", "launch-brief.md")
    write(brief_file, brief_text(build, os.path.join(wt, ".orchestration", "state.md"), body))
    try:
        waiting = start_thread(build, pane, brief_file)
    except HerdrError as e:
        delete_row(build)
        quietly("workspace", "close", ws)
        raise Failed(f"herdr agent start: {e}") from None
    sha = lib.git(main, "rev-parse", "--short", base_ref)
    return started(build, waiting, f"LAUNCHED {build} base={base}@{sha} landing={landing}")


def need_row(build):
    found = row_by(build)
    if not found:
        raise Failed(f"no thread for build {build} in {lib.native(registry())}")
    return found


def stop(args):
    if len(args) != 1:
        usage()
    need_row(args[0])
    pane = agent_pane(args[0])
    if pane:
        try:
            herdr("pane", "close", pane)
        except HerdrError as e:
            raise Failed(f"herdr pane close {pane}: {e}") from None
    delete_row(args[0])
    print(f"STOPPED {args[0]}")
    return 0


def resume_written(state):
    """The RESUME section's "Written:" stamp in the state file, or "" when there is none."""
    try:
        lines = Path(state).read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return ""
    inside = False
    for line in lines:
        if line.startswith("## "):
            if inside:
                return ""
            inside = line.startswith("## RESUME")
        elif inside and line.startswith("Written:"):
            return line[len("Written:"):].lstrip(" \t")
    return ""


def rotate(args):
    if not args:
        usage()
    build, rest = args[0], args[1:]
    if any(a != "--force" for a in rest):
        usage()
    _, main, wt, ws, _ = need_row(build)
    state = os.path.join(wt, ".orchestration", "state.md")
    if not rest:
        written = resume_written(state)
        if not written:
            raise Failed(f"no RESUME Written: stamp in {lib.native(state)}; send ROTATE and wait for "
                         "'STATUS: rotating', or pass --force")
        age = int((int(time.time()) - lib.to_epoch(written)) / 60)
        if age > RESUME_MAX_AGE_MINUTES:
            raise Failed(f"RESUME in {lib.native(state)} was written {age} min ago (limit {RESUME_MAX_AGE_MINUTES}); "
                         "send ROTATE and wait for 'STATUS: rotating', or pass --force")
    old = agent_pane(build)
    # The new pane opens first, so closing the old one never leaves the build's workspace empty.
    try:
        pane, ws = new_pane(build, wt, ws)
    except HerdrError as e:
        raise Failed(f"no pane for the new thread: {e}") from None
    if old:
        quietly("pane", "close", old)
        if agent_pane(build):
            quietly("pane", "close", pane)
            raise Failed(f"the old thread still runs in {old}, so nothing was started; close it, then rotate again")
    put_row(build, [build, main, wt, ws, lib.utc_now()])
    brief_file = os.path.join(wt, ".orchestration", "rotate-brief.md")
    write(brief_file, brief_text(build, state, "Resume: read STATE first and continue from its RESUME section without "
                                               "redoing finished work."))
    try:
        waiting = start_thread(build, pane, brief_file)
    except HerdrError as e:
        quietly("pane", "close", pane)
        closed = "the old one was closed; " if old else ""
        raise Failed(f"the new thread did not start: {e}; {closed}run thread.py rotate {build} --force") from None
    return started(build, waiting, f"ROTATED {build}")


def check(args):
    every = args[:1] == ["--all"]
    if args[1 if every else 0:]:
        usage()
    found = rows()
    if not found:
        print("NONE")
        return 0
    # Only this repository's threads, unless --all or outside git: other main sessions own the rest.
    here = None if every else common_dir(os.getcwd())
    here = here and os.path.dirname(here)
    repos = sorted({r[1] for r in found if r[1] and (not here or lib.same_path(r[1], here))})
    lines = [line for repo in repos for line in identity_warnings(repo)]
    print("\n".join(lines) or "OK")
    return 0


def integrate(args):
    if len(args) != 1:
        usage()
    build, repo, wt, _, _ = need_row(args[0])
    landing, base, checkout = (lib.thread_field(wt, k) for k in ("LANDING", "BASE", "CHECKOUT"))
    if landing != "local":
        raise Failed(f"{build} lands by pull request (LANDING: {landing or 'unknown'}), so its base moves on origin; "
                     "pull it instead")
    if not base or not os.path.isdir(checkout):
        raise Failed(f"no BASE or CHECKOUT in {lib.native(os.path.join(wt, '.orchestration', 'thread.md'))}")
    # The registry's repo is the main checkout, which holds the common git dir of every checkout of it.
    common = common_dir(checkout)
    if not common or not lib.same_path(os.path.dirname(common), repo):
        raise Failed(f"{checkout} is not a checkout of {lib.native(repo)}")
    cur = branch_of(checkout) or "a detached HEAD"
    if cur != base:
        raise Failed(f"{checkout} is on {cur}, not {base}; check out {base} there first")
    if lib.git(checkout, "diff", "--quiet") is None or lib.git(checkout, "diff", "--cached", "--quiet") is None:
        raise Failed(f"{checkout} has uncommitted changes to tracked files; commit or stash them first")
    src = f"orchestration/{build}"
    if lib.git(checkout, "merge", "-q", "--ff-only", src) is not None:
        how = "fast-forward"
    elif lib.git(checkout, "-c", "core.editor=true", "merge", "-q", "--no-ff", "--no-edit", src) is not None:
        how = "merge"
    else:
        conflicted = (lib.git(checkout, "diff", "--name-only", "--diff-filter=U") or "").split("\n")
        lib.git(checkout, "merge", "--abort")
        raise Failed(f"merging {src} into {base} conflicts in: {' '.join(conflicted)}")
    print(f"INTEGRATED {build} {base}@{lib.git(checkout, 'rev-parse', '--short', 'HEAD')} ({how})")
    return 0


def unlanded(repo, branch, ref):
    """The files branch changed since it forked from ref that ref doesn't hold as branch does. Landed means an
    ancestor of ref, or, after a squash merge, every file the branch changed as it is on ref."""
    if lib.git(repo, "merge-base", "--is-ancestor", branch, ref) is not None:
        return []
    fork = lib.git(repo, "merge-base", branch, ref)
    names = (lib.git(repo, "diff", "-z", "--name-only", fork, branch) or "").split("\0")
    return [f for f in names if f and (lib.git(repo, "rev-parse", "-q", "--verify", f"{branch}:{f}") or "none")
            != (lib.git(repo, "rev-parse", "-q", "--verify", f"{ref}:{f}") or "none")]


def close(args):
    names, opts = lib.take_options(args, {"--worktree": True, "--base": True, "--force": False})
    if len(names) > 1 or any(n.startswith("-") for n in names) or not (names or opts.get("--worktree")):
        usage()
    name, wt, base, ws = (names or [""])[0], opts.get("--worktree", ""), opts.get("--base", ""), ""
    if name:
        found = row_by(name)
        if not found:
            raise Failed(f"no thread for build {name} in {lib.native(registry())}; for a build the registry no longer "
                         "lists, pass --worktree <coordination worktree>")
        _, _, wt, ws, _ = found
    if not os.path.isdir(wt):
        raise Failed(f"no coordination worktree at {lib.native(wt)}")
    branch = branch_of(wt)
    if not branch:
        raise Failed(f"{lib.native(wt)} has a detached HEAD; it is not a coordination worktree")
    if not branch.startswith("orchestration/"):
        raise Failed(f"{lib.native(wt)} is on {branch}, not orchestration/<build>; it is not a coordination worktree")
    build = branch[len("orchestration/"):]
    repo = os.path.dirname(common_dir(wt))
    if not lib.same_path(wt, os.path.join(os.path.dirname(repo), f"{os.path.basename(repo)}-orch-{build}")):
        raise Failed(f"{lib.native(wt)} is not {os.path.basename(repo)}-orch-{build} beside {lib.native(repo)}")
    base = base or lib.thread_field(wt, "BASE")
    landing = lib.thread_field(wt, "LANDING")
    if not opts.get("--force"):
        if lib.git(wt, "status", "--porcelain", "--untracked-files=no"):
            raise Failed(f"{lib.native(wt)} has uncommitted changes to tracked files; land them, or pass --force")
        if not base:
            raise Failed(f"no record of {lib.native(wt)}'s base; pass --base <branch>, or --force")
        ref = f"refs/heads/{base}"
        if landing == "pr" or lib.git(repo, "rev-parse", "--verify", "-q", ref) is None:
            lib.git(repo, "fetch", "-q", "origin")
            ref = f"refs/remotes/origin/{base}"
        if lib.git(repo, "rev-parse", "--verify", "-q", ref) is None:
            raise Failed(f"no branch {base} to compare {branch} with; pass --base <branch>, or --force")
        files = unlanded(repo, branch, ref)
        if files:
            raise Failed(f"{branch} holds work that {ref.split('/', 2)[2]} lacks in: {' '.join(files)} "
                         "(integrate or land it, or pass --force)")
    ws = ws or agent(build).get("workspace_id") or ""
    # Closing the workspace ends the thread and any lane still in it, so none sends mail after the archive.
    if ws:
        quietly("workspace", "close", ws)
    pane = agent_pane(build)
    if pane:
        quietly("pane", "close", pane)
    home = orchestration_home()
    archive = home / "archive" / f"{build}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}"
    archive.mkdir(parents=True, exist_ok=True)
    if os.path.isdir(os.path.join(wt, ".orchestration")):
        shutil.copytree(os.path.join(wt, ".orchestration"), archive, symlinks=True, dirs_exist_ok=True)
    if (home / "mail" / build).is_dir():
        shutil.move(home / "mail" / build, archive / "mail")
    # The forced removal deletes what git ignores (eval runs, agent memory), so archive it first. stdout carries
    # only the CLOSED or FAILED line, so the per-file lines are dropped.
    try:
        lib.archive_ignored(wt, archive, ".orchestration")
    except lib.Fail as e:
        raise Failed(f"{e} (archive at {lib.native(archive)})") from None
    r = lib.run(["git", "-C", repo, "worktree", "remove", "--force", wt])
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise Failed(f"git worktree remove {lib.native(wt)} failed; the archive is at {lib.native(archive)}")
    lib.git(repo, "branch", "-D", branch)
    if name:
        delete_row(name)
    # Lane worktrees are <repo>-wt-<name> beside the main checkout.
    prefix = os.path.normcase(f"{os.path.basename(repo)}-wt-")
    listed = re.findall(r"(?m)^worktree (.*)$", lib.git(repo, "worktree", "list", "--porcelain") or "")
    lanes = [lib.native(p) for p in listed if lib.same_path(os.path.dirname(p), os.path.dirname(repo))
             and os.path.normcase(os.path.basename(p)).startswith(prefix)]
    present = f" lanes still present: {' '.join(lanes)}" if lanes else ""
    print(f"CLOSED {build} archive={lib.native(archive)}{present}")
    return 0


def list_threads(args):
    if args:
        usage()
    found = rows()
    if not found:
        print("NONE")
        return 0
    try:
        agents = field(herdr("agent", "list"), "result", "agents")
    except HerdrError:
        agents = None
    for build, _, wt, ws, launched in found:
        status = "unknown"
        if agents is not None:
            status = next((a.get("agent_status") for a in agents if a.get("name") == build), None) or "not-running"
        print(f"{build} status={status} workspace={ws} worktree={lib.native(wt)} launched={launched}")
    return 0


OPEN_ITEM = re.compile(r"- (D\d+) \([^)]*\) ")


def open_items(build, file):
    """(sort key, line) for each open item in a decisions file: key 0 for owner-before items, 1<deadline> for the
    rest, so owner-before comes first."""
    items, on = [], False
    for line in Path(file).read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            on = line.startswith("## Open")
            continue
        m = on and OPEN_ITEM.match(line)
        if not m:
            continue
        rest = line[m.end():]
        what = rest.split(" · why now: ")[0]
        default = rest.partition(" · default: ")[2].split(" · ")[0]
        if when := re.search(r"applies at ([0-9T:Z-]+)", rest):
            key, tail = "1" + when[1], f"applies at {when[1]}"
        else:
            key, tail = "0", "owner-before"
        items.append((key, f"{build} {m[1]} {what} | default: {default} | {tail}"))
    return items


def decisions(args):
    if args:
        usage()
    items = []
    for build, _, wt, _, _ in rows():
        file = os.path.join(wt, ".orchestration", "decisions.md")
        if build and os.path.isfile(file):
            items += open_items(build, file)
    print("\n".join(line for _, line in sorted(items)) or "NONE")
    return 0


COMMANDS = {"launch": launch, "stop": stop, "rotate": rotate, "check": check, "integrate": integrate,
            "close": close, "list": list_threads, "decisions": decisions}


def main(argv):
    command = COMMANDS.get(argv[0]) if argv else None
    if not command:
        usage()
    try:
        return command(argv[1:])
    except Failed as e:
        print(f"FAILED {e}")
        return 1


if __name__ == "__main__":
    lib.entry(main)
