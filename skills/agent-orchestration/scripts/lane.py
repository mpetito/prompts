"""Start one lane as a herdr agent, Claude or Codex, in a new tab of the build's workspace at the lane's worktree, and
hand it its brief with a one-line pointer prompt. The thread runs it from its own pane.
  lane.py <build> <lane> <lane worktree> <brief file> --kind claude|codex --model <id> [--network]
The agent is named <build>-<lane> and reports to the thread with
  mail.py send <build>/thread --from <build>/<lane> "<STATUS: ... line>"
Codex runs with --approve-for-me, so its automatic reviewer grants its approvals (commits in the worktree's protected
git directory among them), and --add-dir on the build's mail folder; --network lets its sandbox reach the network.
Claude runs the lane agent definition, which carries the guard hooks a subagent worker inherits, with --settings on
the main checkout's .claude/settings.local.json when it has one: on Windows Claude Code keeps that file per worktree,
so a new lane worktree has none, and the project's MCP approval dialog would swallow the pointer prompt.
A non-default ORCHESTRATION_HOME is passed to the lane's tab; Codex's sandbox doesn't see the pane's environment, so a
Codex lane's brief then gives its send command as mail.py send --home <home> ....
Prints one line: LANE <name> pane=<pane> kind=<kind>, BLOCKED <name> <reason> (started, but waiting on a startup
prompt the owner must answer; send the pointer prompt once it is idle), or FAILED <reason> with exit 1.
"""
import json
import os
import re
from pathlib import Path

import lib

OPTIONS = {"--kind": True, "--model": True, "--network": False}


class Failed(Exception):
    """A FAILED line's reason."""


def herdr(*args):
    """herdr args...: (ok, stdout), or on failure (False, herdr's "<code>: <message>"), so a FAILED line carries
    herdr's own reason."""
    r = lib.run(["herdr", *args])
    if r.returncode == 0:
        return True, r.stdout
    out = (r.stdout + r.stderr).strip()
    try:
        e = json.loads(out)["error"]
        return False, f"{e['code']}: {e['message']}"
    except (ValueError, KeyError, TypeError):
        return False, out


def field(out, *keys):
    """The value at keys in herdr's JSON reply out; Failed carrying the reply when it has another shape."""
    try:
        value = json.loads(out)
        for key in keys:
            value = value[key]
        return value
    except (ValueError, KeyError, IndexError, TypeError):
        raise Failed(f"unexpected herdr reply: {out.strip()}") from None


def main(argv):
    if len(argv) < 4:
        lib.usage_from(__doc__, 3, 3)
    build, lane, wt, brief = argv[:4]
    rest, opts = lib.take_options(argv[4:], OPTIONS)
    if rest:
        lib.usage_from(__doc__, 3, 3)
    try:
        print(start(build, lane, wt, brief, opts.get("--kind", ""), opts.get("--model", ""), "--network" in opts))
        return 0
    except Failed as e:
        print(f"FAILED {e}")
        return 1


def main_checkout_settings(wt):
    """["--settings", <file>] for the local settings of the main checkout holding worktree wt, which carry the
    owner's project MCP approvals; [] when it has none or wt is outside git."""
    common = lib.git(wt, "rev-parse", "--path-format=absolute", "--git-common-dir")
    local = os.path.join(os.path.dirname(lib.canon(common)), ".claude", "settings.local.json") if common else ""
    return ["--settings", lib.native(local)] if os.path.isfile(local) else []


def start(build, lane, wt, brief, kind, model, network):
    """The lane's one-line result, LANE or BLOCKED; Failed on anything else."""
    name = f"{build}-{lane}"
    if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name):
        raise Failed(f"lane agent name {name} must match [a-z][a-z0-9_-]{{0,31}}; shorten the lane name")
    if not model:
        raise Failed("--model is required: name the lane's model explicitly")
    if not os.path.isdir(wt):
        raise Failed(f"no lane worktree at {wt}")
    if not os.path.isfile(brief) or os.path.getsize(brief) == 0:
        raise Failed(f"no brief at {brief}")
    wt, brief = lib.canon(wt), lib.canon(brief)
    home = os.environ.get("ORCHESTRATION_HOME", "")
    mail = os.path.join(home or Path.home() / ".orchestration", "mail", build)
    if kind == "claude":
        args = ["--agent", "lane", "--model", model, *main_checkout_settings(wt)]
    elif kind == "codex":
        os.makedirs(mail, exist_ok=True)
        args = ["--approve-for-me", "--add-dir", mail, "--model", model]
        if network:
            args += ["-c", "sandbox_workspace_write.network_access=true"]
    else:
        raise Failed(f"--kind takes claude or codex, got {kind or 'nothing'}")

    ok, out = herdr("agent", "get", build)
    ws = field(out, "result", "agent", "workspace_id") if ok else None
    if not ws:
        raise Failed(f"no live thread named {build} to put the lane beside; run lane.py from the build's thread")
    env = ["--env", f"ORCHESTRATION_HOME={home}"] if home else []
    ok, out = herdr("tab", "create", "--workspace", ws, "--cwd", wt, "--label", lane, "--no-focus", *env)
    if not ok:
        raise Failed(f"herdr tab create: {out}")
    pane = field(out, "result", "root_pane", "pane_id")
    ok, out = herdr("agent", "start", name, "--kind", kind, "--pane", pane, "--timeout", "120000", "--", *args)
    if not ok:
        if out.startswith("agent_not_ready:"):
            return f"BLOCKED {name} waiting on a startup prompt: answer it in workspace {build}, tab {lane}"
        herdr("pane", "close", pane)
        raise Failed(f"herdr agent start: {out}")
    ok, out = herdr("agent", "prompt", name, f"Read {lib.native(brief)} and follow it.")
    if not ok:
        raise Failed(f"herdr agent prompt: {out}")
    return f"LANE {name} pane={pane} kind={kind}"


if __name__ == "__main__":
    lib.entry(main)
