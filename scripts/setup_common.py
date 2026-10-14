"""Shared by the skill linker, its verification and the MCP installer. Importing it changes no files.

setup_paths gives every destination in one home. Linker makes a home's links to this checkout: it keeps a conflicting
entry unless told to replace it, backs up what it replaces outside every skill discovery folder, and with what_if
changes nothing and prints what it would do. External commands run only through run(), so tests replace that one
function.

A link belongs to this checkout only when it points, one hop, at the exact absolute repository path setup would make
it for. That is deliberately not realpath, unlike the plan's path convention: ownership decides what setup may
remove or replace, so it fails closed. A link spelled another way (an 8.3 name, a checkout reached through another
link) reads as a conflict and is kept, never taken for ours.
"""
import argparse
import os
import shutil
import signal
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

if os.name == "nt":
    # shutil.which would otherwise look in the current directory first, where a checkout could hold a git.cmd.
    os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")

CLIENTS = ("codex", "claude", "opencode", "copilot")

# The non-skill files Claude Code gets: repository source (forward slashes) -> name under the Claude config folder.
CLAUDE_FILES = (
    ("agents", "agents"),
    ("instructions/CLAUDE.md", "CLAUDE.md"),
    ("statusline/statusline.py", "statusline.py"),
)


class Fail(Exception):
    """A refusal or usage error: the caller prints the message on stderr and exits 1."""


class Parser(argparse.ArgumentParser):
    """argparse whose usage errors raise Fail, so they exit 1 as every other script's do, not argparse's 2."""

    def error(self, message):
        raise Fail(f"{self.format_usage()}{self.prog}: error: {message}")


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


def warn(message):
    print(f"WARNING: {message}", file=sys.stderr)


def should(what_if, target, action):
    """True when action on target may go ahead; with what_if, print what would be done instead and return False."""
    if what_if:
        print(f'What if: Performing the operation "{action}" on target "{target}".')
    return not what_if


# --- processes ---------------------------------------------------------------------------------------------------

def run(args, *, input=None, timeout=None, capture=True):
    """Run args (a list, no shell) and return a CompletedProcess, with text stdout and stderr decoded as UTF-8 when
    capture is set; without it the command writes straight to this process's console and both are empty.

    args[0] is resolved on PATH (PATHEXT on Windows, so an npm .cmd shim is found); a command that isn't found
    returns code 127 with the reason on stderr, as a shell would. On timeout, in seconds, the whole process tree is
    killed and the result has code 124, as timeout(1) gives."""
    exe = shutil.which(args[0])
    if not exe:
        return subprocess.CompletedProcess(args, 127, "", f"{args[0]}: command not found\n")
    pipe = subprocess.PIPE if capture else None
    kw = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    with subprocess.Popen([exe, *args[1:]], stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                          stdout=pipe, stderr=pipe, text=True, encoding="utf-8", errors="replace", **kw) as p:
        try:
            out, err = p.communicate(input, timeout=timeout)
            code = p.returncode
        except subprocess.TimeoutExpired:
            kill_tree(p)
            out, err = p.communicate()
            code = 124
    return subprocess.CompletedProcess(args, code, out or "", err or "")


def kill_tree(p):
    """Kill a process started by run() and everything it started: an npm shim's node child outlives its parent."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_checked(args, *, show=True):
    """run args, with their output on the console when show is set, else captured and only stderr shown on failure.
    A nonzero exit raises Fail naming the command: a native failure must stop setup, not pass for success."""
    r = run(args, capture=not show)
    if r.returncode:
        sys.stderr.write(r.stderr)
        raise Fail(f"Command failed (exit {r.returncode}): {' '.join(args)}")
    return r


# --- paths -------------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Paths:
    user_root: str
    codex_root: str
    claude_root: str
    claude_config: str
    opencode_config: str
    shared_skills: str
    copilot_skills: str
    backup_root: str


def setup_paths(home=None):
    """Every destination setup and MCP registration write, as absolute paths. Without home they are under the user's
    home and honour CODEX_HOME, CLAUDE_CONFIG_DIR, XDG_CONFIG_HOME, OPENCODE_CONFIG_DIR and OPENCODE_CONFIG; an
    explicit home isolates every destination from those machine-specific overrides."""
    isolated = bool(home and home.strip())
    user_root = os.path.abspath(home if isolated else Path.home())
    env = {} if isolated else os.environ

    def override(name, default):
        return os.path.abspath(env[name]) if env.get(name) else default

    claude_root = override("CLAUDE_CONFIG_DIR", os.path.join(user_root, ".claude"))
    config_root = override("XDG_CONFIG_HOME", os.path.join(user_root, ".config"))
    opencode_root = override("OPENCODE_CONFIG_DIR", os.path.join(config_root, "opencode"))
    jsonc = os.path.join(opencode_root, "opencode.jsonc")
    opencode_default = jsonc if os.path.exists(jsonc) else os.path.join(opencode_root, "opencode.json")
    return Paths(
        user_root=user_root,
        codex_root=override("CODEX_HOME", os.path.join(user_root, ".codex")),
        claude_root=claude_root,
        claude_config=os.path.join(claude_root if env.get("CLAUDE_CONFIG_DIR") else user_root, ".claude.json"),
        opencode_config=override("OPENCODE_CONFIG", opencode_default),
        shared_skills=os.path.join(user_root, ".agents", "skills"),
        copilot_skills=os.path.join(user_root, ".copilot", "skills"),
        backup_root=os.path.join(user_root, ".prompts-backups"),
    )


def select_tools(tools, supported=CLIENTS):
    """The clients to set up: tools, a comma-separated list, lower-cased and without repeats; without tools, each
    supported client found on PATH. Fail names an unknown tool."""
    if not tools:
        found = []
        for tool in supported:
            if shutil.which(tool):
                found.append(tool)
            else:
                print(f"[SKIPPED] {tool} is not on PATH. Use --tools {tool} to prepare its files before installation.")
        return found
    selected = list(dict.fromkeys(t.strip().lower() for t in tools.split(",")))
    for tool in selected:
        if tool not in supported:
            raise Fail(f"Unknown tool '{tool}'. Choose: {', '.join(supported)}.")
    return selected


def same_path(a, b):
    """True when a and b name the same location once made absolute, without following links: case-insensitively
    where the OS compares that way (Windows), exactly elsewhere."""
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def is_link(path):
    """True for a symbolic link, dangling or not, or a Windows junction."""
    return os.path.islink(path) or os.path.isjunction(path)


def link_destination(path):
    """The absolute path the link at path points at, one hop, a relative target taken from the link's folder; None
    when path is not a link."""
    if not is_link(path):
        return None
    target = os.readlink(path)
    # On Windows readlink gives the substitute name, which spells an absolute target \\?\C:\... or \\?\UNC\server\...
    if target.startswith("\\\\?\\UNC\\"):
        target = "\\\\" + target[len("\\\\?\\UNC\\"):]
    target = target.removeprefix("\\\\?\\")
    return os.path.abspath(os.path.join(os.path.dirname(path), target))


def is_repo_link(path, source):
    destination = link_destination(path)
    return destination is not None and same_path(destination, source)


def skill_dirs(source):
    """(name, path) of each folder in source, by name."""
    return sorted((e.name, e.path) for e in os.scandir(source) if e.is_dir())


@dataclass(frozen=True)
class Target:
    source: str
    path: str
    children: bool    # link each folder of source into path, which stays a real folder, instead of path itself


def skill_targets(repo, paths, tools):
    """What setup links for tools: skills one by one into each client's skills folder (Codex and OpenCode share
    one), and Claude Code's CLAUDE_FILES."""
    skills = os.path.join(repo, "skills")
    roots = {"codex": paths.shared_skills, "opencode": paths.shared_skills, "copilot": paths.copilot_skills,
             "claude": os.path.join(paths.claude_root, "skills")}
    targets = [Target(skills, root, True) for root in dict.fromkeys(r for t, r in roots.items() if t in tools)]
    if "claude" in tools:
        targets += [Target(os.path.join(repo, *source.split("/")), os.path.join(paths.claude_root, name), False)
                    for source, name in CLAUDE_FILES]
    return targets


# --- linking -----------------------------------------------------------------------------------------------------

class Linker:
    """Makes links to this checkout. A conflicting entry is kept, and its link reported incomplete, unless replace
    is set; then it moves to a unique folder under backup_root, outside every skill discovery folder, so a backed-up
    skill is never published twice. With what_if nothing changes, not even the home folder."""

    def __init__(self, backup_root, replace=False, what_if=False):
        self.backup_root, self.replace, self.what_if = backup_root, replace, what_if

    def link(self, source, path):
        """Link path to source. True when the link is in place; False when a conflict was kept or what_if held back
        the change.
        Fail when source is missing or the link can't be made, with the replaced entry put back."""
        if not os.path.exists(source):
            raise Fail(f"Repository source is missing: {source}")
        if is_repo_link(path, source):
            print(f"[LINKED] {path}")
            return True
        existing = os.path.lexists(path)
        if existing and not self.replace:
            warn(f"Conflict preserved: {path}. Use --replace-conflicts to back it up and replace it.")
            return False
        action = f"Back up existing entry and link to {source}" if existing else f"Link to {source}"
        if not should(self.what_if, path, action):
            return False
        backup = self.move_conflict(path) if existing else None
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            os.symlink(source, path, target_is_directory=os.path.isdir(source))
        except OSError as e:
            if backup:
                shutil.move(backup, path)
            hint = " Windows symlinks require Developer Mode or an elevated session." if os.name == "nt" else ""
            raise Fail(f"Cannot link {path} to {source}: {e}.{hint}") from None
        print(f"[LINKED] {path} -> {source}")
        return True

    def link_children(self, source, path):
        """Link each skill folder of source into path, made a real folder first: a whole-folder link to source is
        converted, any other link or file there is a conflict. Then remove links in path to skills source no longer
        has. True when every child is linked."""
        if os.path.lexists(path) and (is_link(path) or not os.path.isdir(path)):
            owned = is_repo_link(path, source)
            if not owned and not self.replace:
                warn(f"Skills root conflict preserved: {path}. Use --replace-conflicts to back it up and replace it.")
                return False
            if should(self.what_if, path, "Replace whole-folder link or conflicting file with a real skills directory"):
                if owned:
                    os.unlink(path)
                    warn(f"Converted whole-folder link: {path}. Tool-managed entries previously written into {source}"
                         " must be moved out manually.")
                else:
                    self.move_conflict(path)
        if not os.path.exists(path) and should(self.what_if, path, "Create skills directory"):
            os.makedirs(path)
        complete = True
        for name, child in skill_dirs(source):
            if not self.link(child, os.path.join(path, name)):
                complete = False
        # Under what_if a conflicting root is still there, and may be a file.
        if os.path.isdir(path):
            for name in sorted(os.listdir(path)):
                self.remove_stale(os.path.join(path, name), os.path.join(source, name))
        return complete

    def remove_stale(self, path, source, action="Remove stale repository skill link"):
        """Remove the link at path when it points exactly at source and source is gone from the repository. Any
        other entry, a dangling link elsewhere included, is left alone. action names the removal in a preview."""
        if not os.path.exists(source) and is_repo_link(path, source) and should(self.what_if, path, action):
            os.unlink(path)

    def remove_legacy_codex_links(self, repo, paths):
        """Retire the links Codex once read from its own skills folder, now that Codex reads the shared one. A
        whole-folder link to skills/ goes only once every skill is linked in the shared folder; a per-skill link
        only once its replacement exists or its skill is gone. Codex's .system and anything not ours stay."""
        source = os.path.join(repo, "skills")
        legacy = os.path.join(paths.codex_root, "skills")
        if same_path(legacy, paths.shared_skills):
            return
        if is_repo_link(legacy, source):
            missing = [name for name, child in skill_dirs(source)
                       if not is_repo_link(os.path.join(paths.shared_skills, name), child)]
            if not missing and should(self.what_if, legacy,
                                      "Remove legacy whole-folder link and retain a real Codex skills directory"):
                os.unlink(legacy)
                os.mkdir(legacy)
                warn(f"Removed legacy whole-folder link. Tool-managed entries in {source} must be moved into {legacy}"
                     " manually.")
            return
        if is_link(legacy) or not os.path.isdir(legacy):
            return
        for name in sorted(os.listdir(legacy)):
            child, expected = os.path.join(legacy, name), os.path.join(source, name)
            if not is_repo_link(child, expected):
                continue
            if os.path.exists(expected) and not is_repo_link(os.path.join(paths.shared_skills, name), expected):
                continue
            if should(self.what_if, child, "Remove migrated legacy Codex skill link"):
                os.unlink(child)

    def move_conflict(self, path):
        backup_dir = os.path.join(self.backup_root, f"{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex}")
        os.makedirs(backup_dir)
        backup = os.path.join(backup_dir, os.path.basename(path))
        shutil.move(path, backup)
        print(f"[BACKUP] {path} -> {backup}")
        return backup
