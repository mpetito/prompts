"""Test support for the orchestration suites: load a script, call its main() in-process, and fake the CLIs.

Every script spawns through lib.run, so a test replaces that one function: herdr and gh go to the fakes below, which
keep the behaviour the bash suite's mocks had (herdr refuses what 0.9.3 refuses); git, and anything else, runs for
real. Nothing reaches the owner's herdr session, GitHub or the network.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]           # skills/agent-orchestration
SCRIPTS = ROOT / "scripts"
HOOKS = ROOT / "hooks"
MAIN_SCRIPTS = ROOT.parent / "orchestration-main" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lib  # noqa: E402

REAL_RUN = lib.run
UTC = r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z"


def load(path):
    """Import the script at path as a fresh module, without running it."""
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call(module, *argv, stdin="", cwd=None):
    """Run module.main(argv) as lib.entry would, in cwd: returns (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    old = os.getcwd()
    try:
        if cwd:
            os.chdir(cwd)
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), \
                unittest.mock.patch("sys.stdin", io.StringIO(stdin)):
            try:
                code = module.main([str(a) for a in argv])
            except lib.Fail as e:
                print(e, file=sys.stderr)
                code = 1
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
    finally:
        os.chdir(old)
    return code, out.getvalue(), err.getvalue()


def result(args, code=0, out="", err=""):
    return subprocess.CompletedProcess(args, code, out, err)


class FakeHerdr:
    """A herdr that keeps its agents in memory. mode: down, garbled, notab, startfail, notready, busy, lost or
    closefail. busy and lost time out the start: busy leaves an unnamed agent working in the pane, lost none."""

    def __init__(self):
        self.agents, self.log, self.started, self.mode, self.n = [], [], {}, "", 0

    def __call__(self, args):
        self.log.append(" ".join(args))
        self.n += 1
        a = args + ["", ""]
        verb = f"{a[0]} {a[1]}"
        if verb == "agent list":
            if self.mode == "garbled":
                return result(args, out="herdr: not json\n")
            return result(args, 1) if self.mode == "down" else result(args, out=json.dumps(
                {"result": {"agents": self.agents}}))
        if verb == "agent get":
            for ag in self.agents:
                if a[2] in (ag["name"], ag.get("pane_id")):
                    return result(args, out=json.dumps({"result": {"agent": {
                        **ag, "workspace_id": (ag.get("pane_id") or "").split(":")[0]}}}))
            return self.err(args, "agent_not_found", f"agent target {a[2]} not found")
        if verb == "agent prompt":
            if any(ag["name"] == a[2] and ag.get("agent_status") == "blocked" for ag in self.agents):
                return self.err(args, "agent_blocked", f"agent {a[2]} is blocked")
            return result(args, out='{"result":{"type":"ok"}}')
        if verb == "workspace create":
            if "--cwd" not in args or "--no-focus" not in args:
                return self.err(args, "invalid", "the mock wants --cwd and --no-focus")
            return result(args, out=json.dumps({"result": {"workspace": {"workspace_id": f"w{self.n}"},
                                                           "root_pane": {"pane_id": f"w{self.n}:p1"}}}))
        if verb == "tab create":
            if self.mode == "notab":
                return self.err(args, "workspace_not_found", "no such workspace")
            if "--workspace" not in args:
                return self.err(args, "invalid", "the mock wants --workspace")
            ws = args[args.index("--workspace") + 1]
            return result(args, out=json.dumps({"result": {"tab": {"tab_id": f"{ws}:t{self.n}"},
                                                           "root_pane": {"pane_id": f"{ws}:p{self.n}"}}}))
        if verb == "agent start":
            return self.start(args)
        if verb == "agent rename":
            for ag in self.agents:
                if a[2] in (ag["name"], ag.get("pane_id")):
                    ag["name"] = args[3]
                    return result(args, out=json.dumps({"result": {"agent": ag}}))
            return self.err(args, "agent_not_found", f"agent target {a[2]} not found")
        if verb == "pane close":
            if self.mode == "closefail":
                return self.err(args, "pane_not_found", f"pane {a[2]} not found")
            self.agents = [ag for ag in self.agents if ag.get("pane_id") != a[2]]
            return result(args, out='{"result":{"type":"ok"}}')
        if verb == "workspace close":
            return result(args, out='{"result":{"type":"ok"}}')
        return self.err(args, "unknown", f"the mock has no {a[0]} {a[1]}")

    def start(self, args):
        name, rest, pane = args[2], args[3:], ""
        if "--" in rest:
            agent_args = rest[rest.index("--") + 1:]
            rest = rest[:rest.index("--")]
        else:
            agent_args = []
        if "--pane" in rest:
            pane = rest[rest.index("--pane") + 1]
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,31}", name):
            return self.err(args, "invalid_name", "agent names must match [a-z][a-z0-9_-]{0,31}")
        if not pane:
            return self.err(args, "invalid", "--pane is required")
        if any("\n" in x for x in agent_args):
            return self.err(args, "invalid_agent_argument",
                            "agent arguments cannot be encoded safely for the target shell")
        self.started[name] = agent_args
        if self.mode == "startfail":
            return self.err(args, "agent_start_failed", "the agent exited")
        if self.mode in ("busy", "lost", "renamed"):
            if self.mode != "lost":
                self.agents.append({"name": None, "agent": "claude", "agent_status": "working", "pane_id": pane})
            if self.mode == "renamed":
                return self.err(args, "agent_name_not_found", f"named agent {name} no longer owns the target terminal")
            return self.err(args, "timeout", "timed out waiting for agent startup")
        state = "blocked" if self.mode == "notready" else "idle"
        self.agents.append({"name": name, "agent_status": state, "pane_id": pane})
        if state != "idle":
            return self.err(args, "agent_not_ready", f"agent {name} is blocked")
        return result(args, out=json.dumps({"result": {"agent": {"name": name, "pane_id": pane}}}))

    @staticmethod
    def err(args, code, message):
        return result(args, 1, err=json.dumps({"error": {"code": code, "message": message}}) + "\n")


def check_run(name, conclusion, status="completed"):
    """One check run as GitHub's check-runs endpoint lists it, with the fields lib.check_state reads."""
    return {"name": name, "status": status, "conclusion": conclusion}


class FakeGh:
    """A gh answering the queries land.py and watch_gates.py make, from the head of the worktree wt. runs are the
    head's check runs, or None for a gh that fails to read them. A check-runs call with check_name=<name> gets those of
    that name, as GitHub filters them, only as a GET with per_page=100; any other shape fails as GitHub would answer
    the POST that gh sends without -X GET."""

    def __init__(self):
        self.log, self.wt, self.merge_state, self.merge_fail = [], None, "CLEAN", False
        self.runs, self.pr_head = [check_run("ci", "success")], None

    def __call__(self, args):
        joined = " ".join(args)
        self.log.append(joined)
        head = (lib.git(self.wt, "rev-parse", "HEAD") if self.wt else None) or "none"
        verb = " ".join(args[:2])
        if verb == "repo view":
            return result(args, out="o/r\n")
        if verb == "pr view":
            if "headRefOid,mergeStateStatus" in joined:
                return result(args, out=f"{head} {self.merge_state}\n")
            if "mergeStateStatus,reviewDecision" in joined:
                return result(args, out=f"mergeState={self.merge_state} review=APPROVED\n")
            return result(args, out=f"{self.pr_head or head}\n")
        if verb == "pr merge":
            return result(args, 1) if self.merge_fail else result(args, out="merged\n")
        if verb == "pr comment":
            return result(args, out="commented\n")
        if verb == "api graphql":
            return result(args, out="unresolved_threads=0\n" if "unresolved_threads=" in joined else "0\n")
        if "/check-runs" in joined and (names := [a[11:] for a in args if a.startswith("check_name=")]):
            get = any(args[i:i + 2] in (["-X", "GET"], ["--method", "GET"]) for i in range(len(args)))
            if self.runs is None or not get or "per_page=100" not in args:
                return result(args, 1, err="gh: Not Found (HTTP 404)\n")
            return result(args, out=json.dumps({"check_runs": [c for c in self.runs if c["name"] == names[0]]}))
        return result(args)


class OrchTest(unittest.TestCase):
    """A throwaway home, orchestration home and mail root per test, with herdr and gh faked and HERDR_* unset."""

    def setUp(self):
        self.tmp = Path(lib.canon(tempfile.mkdtemp(prefix="orch-test-")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.home.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("HERDR_")}
        for k in ("ORCHESTRATION_STATE", "ORCHESTRATION_DECISIONS", "CLAUDE_CODE_MESSAGING_SOCKET",
                  "CLAUDE_PROJECT_DIR"):
            env.pop(k, None)
        env.update(HOME=str(self.home), USERPROFILE=str(self.home), ORCHESTRATION_HOME=str(self.tmp / "orch"),
                   GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
                   GIT_CONFIG_GLOBAL=str(self.home / ".gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        patcher = unittest.mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.herdr, self.gh = FakeHerdr(), FakeGh()
        fakes = {"herdr": self.herdr, "gh": self.gh}

        def fake_run(args, **kw):
            return fakes[args[0]](list(args[1:])) if args[0] in fakes else REAL_RUN(args, **kw)

        run_patch = unittest.mock.patch.object(lib, "run", fake_run)
        run_patch.start()
        self.addCleanup(run_patch.stop)

    def repo(self, path, commit=True):
        """git init path (made if missing) on branch main, with one empty commit unless commit is False."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(path)], check=True)
        if commit:
            subprocess.run(["git", "-C", str(path), "commit", "-q", "--allow-empty", "-m", "init"], check=True)
        return Path(lib.canon(path))

