"""The hooks: guard_bash.py, guard_writes.py and guard_timestamps.py."""
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path
from types import SimpleNamespace

from .support import HOOKS, SCRIPTS, OrchTest, call, lib, load

AGENTS = Path(__file__).resolve().parents[3] / "agents"

guard_bash = load(HOOKS / "guard_bash.py")
guard_writes = load(HOOKS / "guard_writes.py")
guard_timestamps = load(HOOKS / "guard_timestamps.py")
MAIL_PY = '"$HOME/.claude/skills/agent-orchestration/scripts/mail.py"'


def reply(out):
    """The hook's hookSpecificOutput, or None when it printed nothing."""
    return json.loads(out)["hookSpecificOutput"] if out.strip() else None


def inodes(files, free):
    return lambda fs: SimpleNamespace(f_files=files, f_ffree=free)


class HookTest(OrchTest):
    def hook(self, module, payload, *argv):
        code, out, err = call(module, *argv, stdin=json.dumps(payload))
        self.assertEqual((code, err), (0, ""))
        return reply(out)

    def assertDenied(self, r):
        self.assertIsNotNone(r)
        self.assertEqual(r.get("permissionDecision"), "deny")

    def assertAdvised(self, r, pattern):
        self.assertIsNotNone(r)
        self.assertNotIn("permissionDecision", r)
        self.assertRegex(r["additionalContext"], pattern)


class GuardBash(HookTest):
    def setUp(self):
        super().setUp()
        # The inode warning reads the real /tmp unless a test says otherwise; keep it quiet here.
        patcher = unittest.mock.patch.object(guard_bash, "statvfs", inodes(100, 90))
        patcher.start()
        self.addCleanup(patcher.stop)

    def bash(self, command, background=False, agent=None, lane=False, cwd="/tmp"):
        payload = {"cwd": cwd, "tool_input": {"command": command, "run_in_background": background}}
        if agent:
            payload["agent_id"] = agent
        return self.hook(guard_bash, payload, *(["--lane"] if lane else []))

    def test_denies_the_commands_that_destroyed_work(self):
        coord = self.tmp / "coord"
        for command in ("pkill -f vite", "git worktree remove ../wt --force", "git -C /repo worktree remove ../wt",
                        "rm -rf .orchestration/lanes/lane-b2", "rm -rf .orchestration/tmp",
                        "rm -rf ../app-orch-b1/.orchestration/results/lane-a.md",
                        f"rm -r {coord}/.orchestration/briefs", "cd /x && pkill node", "sh -c 'pkill -f node'",
                        "sudo killall node"):
            with self.subTest(command=command):
                self.assertDenied(self.bash(command, cwd=str(self.tmp)))

    def test_passes_the_same_words_out_of_command_position(self):
        coord = self.tmp / "coord"
        for command in (f"rm -r {coord}/.orchestration/plan.md", "kill 1234", "git worktree add ../wt -b x",
                        "echo pkill-safe-name", "printf '%s' 'pkill -f vite' | jq -Rs .",
                        "cat > doc.md <<EOF\n| hook | refuses `pkill` |\nEOF"):
            with self.subTest(command=command):
                self.assertIsNone(self.bash(command, cwd=str(self.tmp)))

    def test_advises_the_thread_on_a_long_foreground_sleep(self):
        self.assertAdvised(self.bash("sleep 45"), "sleeps 45 s in the foreground")
        self.assertAdvised(self.bash("sleep 2m && date"), "sleeps 120 s")
        self.assertIsNone(self.bash("sleep 45", background=True))
        self.assertIsNone(self.bash("sleep 5 && curl localhost:3000"))

    def test_advises_the_thread_on_a_foreground_wait_loop(self):
        self.assertAdvised(self.bash("until [ -f done.txt ]; do sleep 5; done"), "loops on sleep")
        self.assertAdvised(self.bash("while ! curl -s localhost; do sleep 2; done"), "loops on sleep")
        self.assertIsNone(self.bash("until [ -f done.txt ]; do sleep 5; done", background=True))
        self.assertIsNone(self.bash('while read -r l; do echo "$l"; done < f'))
        self.assertIsNone(self.bash('echo "until it sleeps"'))
        self.assertIsNone(self.bash('while read -r l; do echo no-sleep "$l"; done < f'))
        self.assertAdvised(self.bash("until [ -f done.txt ]; do sleep 60; done"), "loops on sleep")
        self.assertAdvised(self.bash(f"sleep 60; python3 {MAIL_PY} wait b1/thread"), "waits on mail")

    def test_leaves_workers_and_lanes_to_wait(self):
        self.assertIsNone(self.bash("sleep 45", agent="worker-1"))
        self.assertIsNone(self.bash("sleep 45", lane=True))
        self.assertIsNone(self.bash("until curl -s localhost; do sleep 2; done", agent="worker-1"))

    def test_advises_the_thread_on_a_foreground_mail_wait(self):
        self.assertAdvised(self.bash(f"python3 {MAIL_PY} wait b1/thread"), "waits on mail in the foreground")
        self.assertAdvised(self.bash("python3 $HOME/.claude/skills/agent-orchestration/scripts/mail.py wait b1/thread "
                                     "--timeout 600"), "waits on mail in the foreground")
        self.assertAdvised(self.bash("python '/c/Users/A B/.claude/skills/agent-orchestration/scripts/mail.py' wait "
                                     "b1/thread"), "waits on mail in the foreground")
        self.assertIsNone(self.bash(f"python3 {MAIL_PY} wait b1/thread", background=True))
        self.assertIsNone(self.bash(f"python3 {MAIL_PY} read b1/thread"))

    def test_denies_workers_too(self):
        self.assertDenied(self.bash("pkill -f vite", agent="worker-1"))
        r = self.bash("git worktree remove ../wt", agent="worker-1")
        self.assertIn("git clone --no-local", r["permissionDecisionReason"])

    def test_advises_when_the_input_has_no_cwd(self):
        self.assertAdvised(self.hook(guard_bash, {"tool_input": {"command": "sleep 45"}}), "sleeps 45 s")

    def test_warns_from_70_percent_of_inodes_rounded_up(self):
        for files, free, warns in ((100, 31, False), (100, 30, True), (1000, 305, True)):
            with self.subTest(files=files, free=free), \
                    unittest.mock.patch.object(guard_bash, "statvfs", inodes(files, free)):
                r = self.bash("ls")
                if warns:
                    self.assertAdvised(r, "^/tmp ")
                else:
                    self.assertIsNone(r)

    def test_checks_tmpdir_after_tmp(self):
        scratch = str(self.tmp / "scratch")
        os.environ["TMPDIR"] = scratch
        stat = lambda fs: SimpleNamespace(f_files=100, f_ffree=0 if fs == scratch else 90)  # noqa: E731
        with unittest.mock.patch.object(guard_bash, "statvfs", stat):
            self.assertIn(scratch, self.bash("ls")["additionalContext"])

    def test_skips_the_inode_warning_without_statvfs_or_an_inode_count(self):
        with unittest.mock.patch.object(guard_bash, "statvfs", None):
            self.assertIsNone(self.bash("ls"))
        with unittest.mock.patch.object(guard_bash, "statvfs", inodes(0, 0)):
            self.assertIsNone(self.bash("ls"))

    def test_joins_a_wait_and_an_inode_warning(self):
        with unittest.mock.patch.object(guard_bash, "statvfs", inodes(100, 0)):
            context = self.bash("sleep 45")["additionalContext"]
        self.assertRegex(context, "sleeps 45 s(.|\n)*\n/tmp ")


class HooksFixture(HookTest):
    """The owner's checkout, a coordination worktree, a lane worktree and a nested worktree, under the test home."""

    def setUp(self):
        super().setUp()
        self.app = self.repo(self.home / "gw" / "app", commit=False)
        (self.app / "a.txt").write_text("x\n", encoding="utf-8")
        self.git(self.app, "add", ".")
        self.git(self.app, "commit", "-qm", "init")
        with open(self.app / ".git" / "info" / "exclude", "a") as f:
            f.write(".orchestration/\n")
        self.git(self.app, "worktree", "add", "-q", str(self.home / "gw" / "app-orch-b"), "-b", "orchestration/b")
        self.git(self.app, "worktree", "add", "-q", str(self.home / "gw" / "app-wt-lane-a"), "-b", "lane-a")
        self.git(self.app, "worktree", "add", "-q", str(self.app / ".claude" / "worktrees" / "agent-x"), "-b", "agent-x")
        self.coord = Path(lib.canon(self.home / "gw" / "app-orch-b"))
        self.lane = Path(lib.canon(self.home / "gw" / "app-wt-lane-a"))
        (self.coord / ".orchestration").mkdir()
        (self.coord / "sub").mkdir()
        (self.coord / ".orchestration" / "state.md").write_text("# state\n", encoding="utf-8")
        self.record(f"CHECKOUT: {self.app}")
        self.plain = self.tmp / "plain"
        self.plain.mkdir()
        self.repo(self.tmp / "nostate", commit=False)

    @staticmethod
    def git(path, *args):
        subprocess.run(["git", "-C", str(path), *args], check=True)

    def record(self, *lines):
        (self.coord / ".orchestration" / "thread.md").write_text("\n".join(["# record", "BUILD: b1", *lines]) + "\n", encoding="utf-8")


class GuardWrites(HooksFixture):
    def writes(self, cwd, path, key="file_path", agent=None, lane=False):
        payload = {"cwd": str(cwd), "tool_input": {key: str(path)}}
        if agent:
            payload["agent_id"] = agent
        return self.hook(guard_writes, payload, *(["--lane"] if lane else []))

    def test_passes_writes_inside_the_coordination_worktree(self):
        self.assertIsNone(self.writes(self.coord, self.coord / ".orchestration" / "plan.md"))
        self.assertIsNone(self.writes(self.coord / "sub", self.coord / "src" / "app.ts"))
        self.assertIsNone(self.writes(self.coord / "sub", "../notes.md"))

    def test_refuses_the_owners_checkout(self):
        self.assertDenied(self.writes(self.coord, self.app / "a.txt"))
        self.assertDenied(self.writes(self.coord, self.app / "new" / "dir" / "b.txt"))
        self.assertDenied(self.writes(self.coord, "../app/a.txt"))
        reason = self.writes(self.coord, self.app / "a.txt")["permissionDecisionReason"]
        self.assertIn(f"owner's checkout, {lib.native(self.app)}, ", reason)

    def test_advises_the_thread_elsewhere(self):
        self.assertAdvised(self.writes(self.coord, self.lane / "src" / "app.ts"), "outside your coordination worktree")
        self.assertAdvised(self.writes(self.coord, "/etc/hosts", key="notebook_path"),
                           "outside your coordination worktree")
        self.assertAdvised(self.writes(self.coord, f"{self.coord}/../app-orch-b-evil/x"),
                           "outside your coordination worktree")
        self.assertAdvised(self.writes(self.coord / "sub", self.lane / "src" / "app.ts"),
                           "outside your coordination worktree")

    def test_either_thread_file_makes_a_thread(self):
        orch = self.coord / ".orchestration"
        for gone in ("thread.md", "state.md"):
            with self.subTest(gone=gone):
                saved = (orch / gone).read_text(encoding="utf-8")
                (orch / gone).unlink()
                self.assertAdvised(self.writes(self.coord, self.lane / "src" / "app.ts"),
                                   "outside your coordination worktree")
                (orch / gone).write_text(saved, encoding="utf-8")

    def test_a_thread_in_the_main_checkout_may_write_it(self):
        (self.app / ".orchestration").mkdir()
        (self.app / ".orchestration" / "state.md").write_text("# state\n", encoding="utf-8")
        self.assertIsNone(self.writes(self.app, self.app / "a.txt"))

    def test_leaves_workers_alone_outside_the_owners_checkout(self):
        self.assertIsNone(self.writes(self.coord, self.lane / "src" / "app.ts", agent="w1"))
        self.assertIsNone(self.writes(self.coord, self.home / "notes.md", agent="w1"))

    def test_guards_a_lane_session_by_its_flag(self):
        self.assertIsNone(self.writes(self.lane, self.app / "a.txt"))
        r = self.writes(self.lane, self.app / "a.txt", lane=True)
        self.assertIn("Make the change in your own lane worktree", r["permissionDecisionReason"])
        self.assertIsNone(self.writes(self.lane, self.lane / "src" / "app.ts", lane=True))
        self.assertIsNone(self.writes(self.lane, self.home / "notes.md", lane=True))

    def test_refuses_a_worker_with_the_workers_reason(self):
        self.assertDenied(self.writes(self.coord, self.app / "a.txt", agent="w1"))
        r = self.writes(self.coord, self.app / "a.txt", agent="w1")
        self.assertIn("Make the change in your own lane worktree", r["permissionDecisionReason"])

    def test_the_session_is_where_it_started(self):
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.coord)
        self.assertDenied(self.writes(self.app, self.app / "a.txt"))

    def test_guards_the_records_checkout_and_the_main_checkout(self):
        self.record(f"CHECKOUT: {lib.native(self.lane)}")
        self.assertDenied(self.writes(self.coord, self.lane / "src" / "app.ts"))
        self.assertDenied(self.writes(self.coord, self.app / "a.txt"))
        self.record()
        self.assertDenied(self.writes(self.coord, self.app / "a.txt"))

    def test_is_silent_outside_a_thread(self):
        self.assertIsNone(self.writes(self.plain, self.app / "a.txt"))
        self.assertIsNone(self.writes(self.tmp / "nostate", self.app / "a.txt"))
        (self.tmp / "nostate" / ".orchestration" / "state.md").mkdir(parents=True)
        self.assertIsNone(self.writes(self.tmp / "nostate", self.app / "a.txt"))
        inner = self.repo(self.coord / "inner")
        self.assertIsNone(self.writes(inner, self.app / "a.txt"))

    def test_is_silent_without_a_cwd_or_a_path(self):
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.coord)
        self.assertIsNone(self.hook(guard_writes, {"tool_input": {"file_path": str(self.app / "a.txt")}}))
        self.assertIsNone(self.hook(guard_writes, {"cwd": str(self.coord), "tool_input": {}}))

    def test_runs_no_git_outside_a_thread(self):
        spawned = []
        with unittest.mock.patch.object(lib, "run", lambda args, **kw: spawned.append(args)):
            self.assertIsNone(self.writes(self.lane, self.app / "a.txt"))
        self.assertEqual(spawned, [])

    @unittest.skipUnless(os.name == "nt", "Claude Code sends native paths only on Windows")
    def test_reads_native_paths_with_either_separator(self):
        for form in (str, lambda p: Path(p).as_posix()):
            with self.subTest(form=form):
                self.assertDenied(self.writes(form(self.coord), form(self.app / "a.txt")))
                self.assertDenied(self.writes(form(self.coord), "..\\app\\a.txt"))
                self.assertIsNone(self.writes(form(self.coord / "sub"), form(self.coord / "src" / "app.ts")))

    @unittest.skipUnless(os.name == "nt", "Git Bash drive paths exist only on Windows")
    def test_reads_a_git_bash_drive_path(self):
        target = str(self.app / "a.txt")
        self.assertDenied(self.writes(self.coord, "/" + target[0].lower() + target[2:].replace("\\", "/")))


class GuardTimestamps(HooksFixture):
    def setUp(self):
        super().setUp()
        self.notes = self.coord / ".orchestration" / "notes.md"
        self.notes.write_text("state at 10:00Z\n", encoding="utf-8")

    def edit(self, text, cwd=None, path=None, agent=None):
        payload = {"cwd": lib.native(cwd or self.coord),
                   "tool_input": {"file_path": lib.native(path or self.notes), "new_string": text}}
        if agent:
            payload["agent_id"] = agent
        return self.hook(guard_timestamps, payload)

    def test_advises_on_a_new_clock_time(self):
        self.assertAdvised(self.edit("approved at 14:30Z"), "14:30Z")
        self.assertAdvised(self.edit("stopped 07:3xZ"), "07:3xZ")
        self.assertAdvised(self.edit("resumed 2026-10-05T18:16Z"), "18:16Z")
        self.assertAdvised(self.edit("approved at 14:30Z", path=".orchestration/notes.md"), "14:30Z")

    def test_passes_a_time_already_in_the_file(self):
        self.assertIsNone(self.edit("see 10:00Z above"))

    def test_passes_outside_orchestration_and_outside_git(self):
        self.assertIsNone(self.edit("at 14:30Z", self.coord, self.coord / "docs" / "plan.md"))
        self.assertIsNone(self.edit("at 14:30Z", self.coord, self.lane / ".orchestration" / "x.md"))
        self.assertIsNone(self.edit("at 14:30Z", self.plain, self.plain / ".orchestration" / "x.md"))

    def test_passes_a_worker(self):
        self.assertIsNone(self.edit("approved at 14:30Z", agent="w1"))

    def test_the_session_is_where_it_started(self):
        os.environ["CLAUDE_PROJECT_DIR"] = str(self.coord)
        self.assertAdvised(self.edit("approved at 14:30Z", self.plain), "14:30Z")

    def test_runs_no_git_without_a_clock_time_under_orchestration(self):
        spawned = []
        with unittest.mock.patch.object(lib, "run", lambda args, **kw: spawned.append(args)):
            self.assertIsNone(self.edit("approved at noon"))
            self.assertIsNone(self.edit("at 14:30Z", self.coord, self.coord / "docs" / "plan.md"))
        self.assertEqual(spawned, [])


class AgentHooks(HooksFixture):
    """Every hook agents/*.md declares runs the way Claude Code starts an exec-form hook (its command and args, no
    shell) and reaches its guard. A broken entry fails as a non-blocking hook error, or runs nothing, so its guard
    would silently stop guarding."""

    def declared(self):
        for agent in sorted(AGENTS.glob("*.md")):
            lines = agent.read_text(encoding="utf-8").split("---")[1].splitlines()
            for i, line in enumerate(lines):
                if line.strip() == "command: python3":
                    yield agent.stem, json.loads(lines[i + 1].strip().removeprefix("args: "))

    def test_each_declared_hook_runs_its_guard(self):
        skill = self.home / ".claude" / "skills" / "agent-orchestration"
        shutil.copytree(HOOKS, skill / "hooks")
        shutil.copytree(SCRIPTS, skill / "scripts")
        hooks = list(self.declared())
        self.assertEqual(sorted(a for a, _ in hooks), ["lane", "lane", "orchestrator", "orchestrator", "orchestrator"])
        for agent, args in hooks:
            name = re.search(r"hooks/(\w+)\.py", args[1])[1]
            # Each payload is one the guard answers, as the agent that declares it: a lane's hooks run from its
            # worktree with --lane, the thread's from the coordination worktree.
            cwd = self.lane if agent == "lane" else self.coord
            payload, decision = {
                "guard_bash": ({"tool_name": "Bash", "tool_input": {"command": "pkill node"}}, "deny"),
                "guard_writes": ({"tool_name": "Write", "tool_input": {"file_path": str(self.app / "a.txt")}}, "deny"),
                "guard_timestamps": ({"tool_name": "Edit", "tool_input": {
                    "file_path": str(self.coord / ".orchestration" / "notes.md"), "new_string": "approved at 14:30Z"}},
                    None),
            }[name]
            r = subprocess.run([sys.executable, *args], input=json.dumps({**payload, "cwd": str(cwd)}),
                               capture_output=True, text=True, encoding="utf-8", cwd=cwd)
            with self.subTest(agent=agent, hook=name):
                self.assertEqual((r.returncode, r.stderr), (0, ""))
                answer = reply(r.stdout)
                self.assertIsNotNone(answer, "the hook answered nothing")
                self.assertEqual(answer.get("permissionDecision"), decision)


class Processes(unittest.TestCase):
    def test_each_hook_refuses_an_unknown_argument(self):
        for module in (guard_bash, guard_writes, guard_timestamps):
            with self.subTest(hook=module.__name__):
                r = subprocess.run([sys.executable, module.__file__, "--bogus"], input="{}", capture_output=True,
                                   text=True)
                self.assertEqual(r.returncode, 1)
                self.assertIn(module.USAGE, r.stderr)


if __name__ == "__main__":
    unittest.main()
