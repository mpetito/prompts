"""thread.py: launch, stop, rotate, list, decisions, check, integrate and close, against real git and a fake herdr."""
import importlib.util
import os
import re
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

SUPPORT = Path(__file__).resolve().parents[2] / "agent-orchestration" / "tests" / "support.py"
_spec = importlib.util.spec_from_file_location("orchestration_support", SUPPORT)
support = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = support
_spec.loader.exec_module(support)
lib = support.lib

SCRIPT = support.MAIN_SCRIPTS / "thread.py"
thread = support.load(SCRIPT)
UTC = support.UTC
SHA = "[0-9a-f]{7}"


def git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


def commit(cwd, name, text, message):
    Path(cwd, name).write_text(text, encoding="utf-8")
    git(cwd, "add", name)
    git(cwd, "commit", "-qm", message)


class ThreadCase(support.OrchTest):
    """An origin with main and dev, the owner's clone of it at proj/app, a brief, and a folder outside git."""

    def setUp(self):
        super().setUp()
        origin = self.tmp / "app-origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
        self.seed = self.tmp / "app-seed"
        subprocess.run(["git", "clone", "-q", str(origin), str(self.seed)], check=True, capture_output=True)
        commit(self.seed, "README.md", "app\n", "init")
        git(self.seed, "push", "-q", "origin", "main")
        git(self.seed, "checkout", "-qb", "dev")
        commit(self.seed, "DEV.md", "dev\n", "dev")
        git(self.seed, "push", "-q", "origin", "dev")
        self.proj = self.tmp / "proj"
        self.proj.mkdir()
        subprocess.run(["git", "clone", "-q", str(origin), str(self.proj / "app")], check=True, capture_output=True)
        self.app = Path(lib.canon(self.proj / "app"))
        self.brief = self.tmp / "brief-a.md"
        self.brief.write_text("Build the signup slice.\n", encoding="utf-8")
        self.plain = self.tmp / "plain"
        self.plain.mkdir()
        self.orch = Path(os.environ["ORCHESTRATION_HOME"])

    def t(self, *args, cwd=None):
        return support.call(thread, *args, cwd=cwd)

    def out(self, *args, cwd=None):
        return self.t(*args, cwd=cwd)[1].rstrip("\n")

    def launch(self, build, checkout=None, *opts):
        out = self.out("launch", build, checkout or self.app, self.brief, *opts)
        self.assertRegex(out, f"^LAUNCHED {build} ")
        return self.proj / f"app-orch-{build}"

    def row_of(self, build):
        reg = self.orch / "threads.tsv"
        lines = reg.read_text(encoding="utf-8").splitlines()[1:] if reg.exists() else []
        found = [line.split("\t") for line in lines if line.split("\t")[0] == build]
        self.assertLessEqual(len(found), 1, f"two rows for {build}")
        return found[0] if found else None

    def pane_of(self, build):
        return next((a["pane_id"] for a in self.herdr.agents if a["name"] == build), None)

    def write_state(self, wt, written, later=""):
        """A state file as state.py init writes it, its RESUME stamped written, and later in its Log section."""
        Path(wt, ".orchestration", "state.md").write_text(
            f"# Orchestration thread: x\n\n## RESUME\n\n{written}\n(nothing yet)\n\n## Lanes\n\n## Log\n{later}", encoding="utf-8")

    def alias(self, path):
        """path spelled through a symlink to its parent, or, where symlinks need privileges, in native form."""
        link = self.tmp / f"alias-{len(list(self.tmp.glob('alias-*')))}"
        try:
            os.symlink(Path(path).parent, link, target_is_directory=True)
        except OSError:
            return lib.native(path)
        return str(link / Path(path).name)


class Launch(ThreadCase):
    def test_list_and_decisions_print_none_without_registry(self):
        self.assertEqual(self.out("list"), "NONE")
        self.assertEqual(self.out("decisions"), "NONE")

    def test_launch_makes_the_worktree_record_workspace_and_brief(self):
        out = self.out("launch", "t-a", self.app, self.brief)
        self.assertRegex(out, f"^LAUNCHED t-a base=main@{SHA} landing=pr$")
        wta = Path(lib.canon(self.proj / "app-orch-t-a"))
        self.assertEqual(git(wta, "rev-parse", "--abbrev-ref", "HEAD"), "orchestration/t-a")
        self.assertEqual(git(wta, "rev-parse", "HEAD"), git(self.app, "rev-parse", "origin/main"))
        rec = (wta / ".orchestration" / "thread.md").read_text(encoding="utf-8")
        fields = re.findall(r"(?m)^[A-Z-]+: (.*)$", rec)[:6]
        self.assertEqual(fields, ["t-a", str(self.app), "main", "origin/main", "origin/main", "pr"])
        self.assertNotRegex(rec, "(?m)^MAIN")
        self.assertNotIn("branch.orchestration/t-a.merge", git(wta, "config", "--list"))
        self.assertIn(".orchestration/", (self.app / ".git" / "info" / "exclude").read_text(encoding="utf-8").splitlines())
        # One workspace per build, opened at the coordination worktree without taking the owner's focus.
        self.assertIn(f"workspace create --cwd {wta} --label t-a --no-focus --env ORCHESTRATION_HOME={self.orch}",
                      self.herdr.log)
        row = self.row_of("t-a")
        self.assertEqual(row[:3], ["t-a", str(self.app), str(wta)])
        self.assertRegex(row[3], r"^w[0-9]+$")
        self.assertEqual(self.pane_of("t-a"), f"{row[3]}:p1")
        brief = wta / ".orchestration" / "launch-brief.md"
        self.assertEqual(self.herdr.started["t-a"],
                         ["--agent", "orchestrator", f"Read {lib.native(brief)} and follow it."])
        self.assertEqual(brief.read_text(encoding="utf-8").splitlines()[:3], [
            "BUILD: t-a", "MAIL: t-a/thread is yours; send MAIN t-a/main",
            f"STATE: {lib.native(wta / '.orchestration' / 'state.md')}"])
        self.assertIn("Build the signup slice.", brief.read_text(encoding="utf-8"))
        # The record reads from inside the new worktree, and .orchestration stays untracked.
        self.write_state(wta, f"Written: {lib.utc_now()}")
        self.assertEqual(lib.thread_field(lib.toplevel(wta), "BUILD"), "t-a")
        self.assertEqual(git(wta, "status", "--porcelain"), "")

    def test_launch_refuses_a_taken_name_a_foreign_path_and_bad_input(self):
        self.launch("t-a")
        self.assertRegex(self.out("launch", "t-a", self.app, self.brief),
                         "^FAILED a thread for build t-a is already registered")
        self.herdr.agents.append({"name": "held", "agent_status": "idle", "pane_id": "w0:p9"})
        self.assertRegex(self.out("launch", "held", self.app, self.brief),
                         "^FAILED a live herdr agent is already named held")
        (self.proj / "app-orch-x").mkdir()
        self.assertRegex(self.out("launch", "x", self.app, self.brief),
                         f"^FAILED {re.escape(lib.native(self.proj / 'app-orch-x'))} exists and is not the "
                         "coordination worktree")
        git(self.app, "worktree", "add", "-q", "-b", "other", str(self.proj / "app-orch-y"))
        self.assertRegex(self.out("launch", "y", self.app, self.brief), "^FAILED .*app-orch-y exists and is not the "
                                                                         "coordination worktree for build y")
        self.assertRegex(self.out("launch", "t-z", self.tmp / "nowhere", self.brief),
                         "^FAILED no repository checkout")
        self.assertRegex(self.out("launch", "t-z", self.plain, self.brief), "^FAILED .* is not a git checkout")
        for bad in ("bad name", "Upper", "1st", "a" * 33):
            self.assertRegex(self.out("launch", bad, self.app, self.brief), "^FAILED build name .* must match", bad)
        self.assertRegex(self.out("launch", "t-z", self.app, self.brief, "--base", "nope"),
                         "^FAILED no branch nope in .* or on origin")
        self.assertRegex(self.out("launch", "t-z", self.app, self.brief, "--landing", "push"),
                         "^FAILED --landing takes pr or local")

    def test_a_thread_at_a_startup_prompt_is_kept_and_a_failed_start_leaves_nothing(self):
        self.herdr.mode = "notready"
        self.assertEqual(self.out("launch", "t-u", self.app, self.brief),
                         "BLOCKED t-u waiting on a startup prompt: answer it in workspace t-u")
        self.assertIsNotNone(self.row_of("t-u"))
        self.herdr.mode = ""
        self.t("stop", "t-u")
        self.herdr.mode = "startfail"
        code, out, _ = self.t("launch", "t-f", self.app, self.brief)
        self.assertEqual((code, out), (1, "FAILED herdr agent start: agent_start_failed: the agent exited\n"))
        self.assertIsNone(self.row_of("t-f"))
        self.assertTrue(any(line.startswith("workspace close w") for line in self.herdr.log))

    def test_a_thread_still_on_its_first_turn_when_the_start_times_out_is_named_and_kept(self):
        self.herdr.mode = "busy"
        self.assertRegex(self.out("launch", "t-b", self.app, self.brief), "^LAUNCHED t-b ")
        self.assertIsNotNone(self.row_of("t-b"))
        self.herdr.mode = ""
        self.assertEqual(thread.agent("t-b")["agent_status"], "working")
        self.assertFalse(any(line.startswith("workspace close") for line in self.herdr.log))
        self.herdr.mode = "lost"
        code, out, _ = self.t("launch", "t-l", self.app, self.brief)
        self.assertEqual((code, out), (1, "FAILED herdr agent start: timeout: timed out waiting for agent startup\n"))
        self.assertIsNone(self.row_of("t-l"))
        self.assertTrue(any(line.startswith("workspace close w") for line in self.herdr.log))

    def test_a_brief_it_cannot_read_fails_before_anything_is_made(self):
        # PowerShell 5.1's > writes UTF-16LE with a byte order mark.
        self.brief.write_bytes("Build the signup slice.\n".encode("utf-16"))
        code, out, _ = self.t("launch", "t-u", self.app, self.brief)
        self.assertEqual(code, 1)
        self.assertRegex(out, f"^FAILED cannot read the brief {re.escape(str(self.brief))}")
        self.assertFalse((self.proj / "app-orch-t-u").exists())
        self.assertIsNone(self.row_of("t-u"))
        self.assertEqual(self.herdr.log, [])

    def test_a_linked_worktree_still_places_the_coordination_worktree_beside_the_main_checkout(self):
        git(self.app, "worktree", "add", "-q", str(self.proj / "app-wt-lane-b"), "-b", "lane-b")
        wtb = self.launch("signup", self.proj / "app-wt-lane-b", "--base", "dev")
        self.assertTrue((wtb / "DEV.md").is_file())
        self.assertIn(f"CHECKOUT: {lib.canon(self.proj / 'app-wt-lane-b')}",
                      (wtb / ".orchestration" / "thread.md").read_text(encoding="utf-8").splitlines())


class Running(ThreadCase):
    """Two launched builds: t-a on main, signup on dev."""

    def setUp(self):
        super().setUp()
        self.wta = self.launch("t-a")
        self.wtb = self.launch("signup", None, "--base", "dev")
        self.wsa = self.row_of("t-a")[3]

    def test_list_reads_each_thread_status_from_herdr(self):
        next(a for a in self.herdr.agents if a["name"] == "t-a")["agent_status"] = "working"
        self.herdr(["pane", "close", self.pane_of("signup")])
        out = self.out("list").splitlines()
        self.assertTrue(any(line.startswith(f"t-a status=working workspace={self.wsa} worktree={lib.native(self.wta)} ")
                            for line in out), out)
        self.assertTrue(any(re.match(f"signup status=not-running workspace=w[0-9]+ worktree={re.escape(lib.native(self.wtb))} ", line)
                            for line in out), out)

    def add_decision(self, wt, what, default, when):
        """An open item as decisions.py add writes it."""
        file = Path(wt, ".orchestration", "decisions.md")
        text = file.read_text(encoding="utf-8") if file.exists() else "# Decisions\n\n## Open\n\n## Applied\n"
        n = text.count("\n- D") + 1
        tail = "owner-before: waits for the owner" if when == "owner-before" else \
            f"applies at {lib.fmt_utc(lib.to_epoch(when))} unless the owner objects"
        item = f"- D{n} ({lib.utc_now()}) {what} · why now: x · blocks: lane · default: {default} · {tail}\n\n"
        file.write_text(text.replace("## Applied", item + "## Applied"), encoding="utf-8")

    def test_decisions_put_owner_before_first_then_order_by_deadline(self):
        # The earlier deadline belongs to the thread whose name sorts last, so only the deadline orders them.
        self.add_decision(self.wta, "Tea or coffee", "tea", "+1h")
        self.add_decision(self.wtb, "Banner copy", "short copy", "+2h")
        self.add_decision(self.wtb, "Spend 40 USD", "none", "owner-before")
        applied = self.wta / ".orchestration" / "decisions.md"
        applied.write_text(applied.read_text(encoding="utf-8") + "- D9 (2000-01-01T00:00Z) Done · default: y · owner-before\n", encoding="utf-8")
        out = self.out("decisions").splitlines()
        self.assertEqual(len(out), 3, out)
        self.assertEqual(out[0], "signup D2 Spend 40 USD | default: none | owner-before")
        self.assertRegex(out[1], f"^t-a D1 Tea or coffee \\| default: tea \\| applies at {UTC}$")
        self.assertRegex(out[2], f"^signup D1 Banner copy \\| default: short copy \\| applies at {UTC}$")

    def test_rotate_needs_a_fresh_resume_stamp_unless_forced(self):
        self.write_state(self.wta, "Written: 2000-01-01T00:00Z")
        self.assertRegex(self.out("rotate", "t-a"), r"^FAILED RESUME in .* min ago \(limit 15\)")
        self.assertRegex(self.out("rotate", "signup"), "^FAILED no RESUME Written")
        # Only RESUME's own stamp counts, not one in a later section.
        self.write_state(self.wtb, "", f"Written: {lib.utc_now()}\n")
        self.assertRegex(self.out("rotate", "signup"), "^FAILED no RESUME Written")

    def test_rotate_replaces_the_thread_in_the_builds_workspace(self):
        self.write_state(self.wta, f"Written: {lib.utc_now()}")
        olda = self.pane_of("t-a")
        self.assertEqual(self.out("rotate", "t-a"), "ROTATED t-a")
        tab = f"tab create --workspace {self.wsa} --cwd {self.wta} --label t-a --no-focus " \
              f"--env ORCHESTRATION_HOME={self.orch}"
        self.assertIn(tab, self.herdr.log)
        newa = self.pane_of("t-a")
        self.assertIn(f"pane close {olda}", self.herdr.log)
        self.assertTrue(newa and newa != olda, (olda, newa))
        brief = self.wta / ".orchestration" / "rotate-brief.md"
        self.assertIn(f"Read {lib.native(brief)} and follow it.", self.herdr.started["t-a"])
        self.assertIn("Resume: read STATE first and continue from its RESUME section without redoing finished work.",
                      brief.read_text(encoding="utf-8").splitlines())
        self.assertEqual(self.row_of("t-a")[:4], ["t-a", str(self.app), str(self.wta), self.wsa])
        # The new pane opens before the old one closes, so the build's workspace is never left empty.
        self.assertLess(self.herdr.log.index(tab), self.herdr.log.index(f"pane close {olda}"))

    def test_rotate_reports_a_startup_prompt_a_failed_start_and_an_old_thread_that_stays(self):
        self.herdr.mode = "notready"
        self.assertEqual(self.out("rotate", "t-a", "--force"),
                         "BLOCKED t-a waiting on a startup prompt: answer it in workspace t-a")
        next(a for a in self.herdr.agents if a["name"] == "t-a")["agent_status"] = "idle"
        before = len(self.herdr.log)
        self.herdr.mode = "startfail"
        self.assertEqual(self.out("rotate", "t-a", "--force"),
                         "FAILED the new thread did not start: agent_start_failed: the agent exited; "
                         "the old one was closed; run thread.py rotate t-a --force")
        self.assertEqual(sum(line.startswith("pane close ") for line in self.herdr.log[before:]), 2)
        self.assertIsNone(self.pane_of("t-a"))
        self.herdr.mode = ""
        self.t("rotate", "t-a", "--force")
        keep = self.pane_of("t-a")
        self.herdr.mode = "closefail"
        self.assertEqual(self.out("rotate", "t-a", "--force"),
                         f"FAILED the old thread still runs in {keep}, so nothing was started; "
                         "close it, then rotate again")
        self.assertEqual(self.pane_of("t-a"), keep)
        self.assertRegex(self.herdr.log[-1], f"^pane close (?!{keep}$)", "rotate left the new pane open")

    def test_a_thread_whose_workspace_is_gone_restarts_in_a_new_one_and_stop_ends_it(self):
        self.herdr(["pane", "close", self.pane_of("signup")])
        old_ws = self.row_of("signup")[3]
        self.herdr.mode = "notab"
        self.assertEqual(self.out("rotate", "signup", "--force"), "ROTATED signup")
        self.assertIsNotNone(self.pane_of("signup"))
        self.assertNotEqual(self.row_of("signup")[3], old_ws)
        self.herdr.mode = ""
        self.assertTrue(any(re.match("signup status=idle workspace=w[0-9]+ ", line)
                            for line in self.out("list").splitlines()))
        self.herdr.mode = "closefail"
        self.assertRegex(self.out("stop", "signup"), "^FAILED herdr pane close .*: pane_not_found")
        self.assertIsNotNone(self.row_of("signup"))
        self.herdr.mode = ""
        self.assertEqual(self.out("stop", "signup"), "STOPPED signup")
        self.assertIsNone(self.row_of("signup"))
        self.assertIsNone(self.pane_of("signup"))
        self.assertTrue((self.wtb / ".git").exists())
        self.assertRegex(self.out("stop", "signup"), "^FAILED no thread for build signup")
        self.assertRegex(self.out("launch", "signup", self.app, self.brief), "^LAUNCHED signup ")


class NoWorkspace(ThreadCase):
    def test_a_workspace_herdr_refuses_fails_launch_and_rotate(self):
        wta = self.launch("t-a")
        self.write_state(wta, f"Written: {lib.utc_now()}")
        call = support.FakeHerdr.__call__

        def refuse(fake, args):
            full = args[:2] in (["workspace", "create"], ["tab", "create"])
            return fake.err(args, "no_space", "full") if full else call(fake, args)

        with unittest.mock.patch.object(support.FakeHerdr, "__call__", refuse):
            self.assertEqual(self.out("launch", "t-b", self.app, self.brief),
                             "FAILED herdr workspace create: no_space: full")
            self.assertEqual(self.out("rotate", "t-a"), "FAILED no pane for the new thread: no_space: full")


class OddReplies(ThreadCase):
    """herdr succeeds but replies in another shape: a FAILED line carrying the reply, never a traceback."""

    def answering(self, verbs, reply):
        call = support.FakeHerdr.__call__

        def odd(fake, args):
            return support.result(args, out=reply + "\n") if args[:2] in verbs else call(fake, args)

        return unittest.mock.patch.object(support.FakeHerdr, "__call__", odd)

    def test_launch_fails_on_a_workspace_reply_it_cannot_read(self):
        for reply in ("not json", '{"result": {"workspace": {}}}',
                      '{"result": {"root_pane": {"pane_id": "w9:p1"}, "workspace": {}}}'):
            with self.subTest(reply=reply), self.answering([["workspace", "create"]], reply):
                code, out, _ = self.t("launch", "t-b", self.app, self.brief)
                self.assertEqual(code, 1)
                self.assertRegex(out, "^FAILED herdr workspace create: ")
                self.assertIn(reply, out)
                self.assertIsNone(self.row_of("t-b"))

    def test_rotate_falls_back_from_an_odd_tab_reply_and_fails_on_an_odd_workspace_reply(self):
        self.launch("t-a")
        reply = '{"result": {"tab": {}}}'
        with self.answering([["tab", "create"]], reply):
            self.assertEqual(self.out("rotate", "t-a", "--force"), "ROTATED t-a")
        with self.answering([["tab", "create"], ["workspace", "create"]], reply):
            out = self.out("rotate", "t-a", "--force")
        self.assertRegex(out, "^FAILED no pane for the new thread: ")
        self.assertIn(reply, out)

    def test_list_and_stop_read_an_odd_agent_reply_as_no_agent(self):
        self.launch("t-a")
        with self.answering([["agent", "list"], ["agent", "get"]], '{"result": []}'):
            self.assertRegex(self.out("list"), "^t-a status=unknown ")
            self.assertEqual(self.out("stop", "t-a"), "STOPPED t-a")


class FromABranch(ThreadCase):
    def test_an_unpushed_current_branch_lands_locally(self):
        git(self.app, "checkout", "-q", "-b", "feat-x")
        commit(self.app, "FEAT.md", "feat\n", "feat")
        self.assertRegex(self.out("launch", "c", self.app, self.brief), f"^LAUNCHED c base=feat-x@{SHA} landing=local$")
        wtc = self.proj / "app-orch-c"
        self.assertEqual(git(wtc, "rev-parse", "HEAD"), git(self.app, "rev-parse", "feat-x"))
        rec = (wtc / ".orchestration" / "thread.md").read_text(encoding="utf-8").splitlines()
        self.assertIn("LANE-BASE: orchestration/c", rec)
        self.assertIn("BASE-REF: feat-x", rec)
        self.assertRegex(self.out("launch", "d", self.app, self.brief, "--landing", "pr"),
                         "^FAILED --landing pr needs feat-x on origin with nothing unpushed")
        git(self.app, "checkout", "-q", "--detach")
        self.assertRegex(self.out("launch", "d", self.app, self.brief), "^FAILED .* is on a detached HEAD; pass --base")

    def test_a_branch_with_unpushed_commits_starts_from_the_local_branch(self):
        git(self.app, "checkout", "-q", "-b", "dev", "origin/dev")
        commit(self.app, "LOCAL.md", "local\n", "local")
        out = self.out("launch", "e", self.app, self.brief)
        self.assertRegex(out, f"base=dev@{SHA} landing=local$")
        self.assertTrue((self.proj / "app-orch-e" / "LOCAL.md").is_file())

    def test_a_local_branch_behind_origin_starts_from_origin(self):
        git(self.seed, "checkout", "-q", "main")
        commit(self.seed, "MORE.md", "more\n", "more")
        git(self.seed, "push", "-q", "origin", "main")
        self.assertTrue(self.out("launch", "d", self.app, self.brief).endswith("landing=pr"))
        self.assertTrue((self.proj / "app-orch-d" / "MORE.md").is_file())

    def test_no_origin_or_an_unreachable_one_lands_locally(self):
        solo = self.repo(self.proj / "solo", commit=False)
        git(solo, "checkout", "-q", "-b", "trunk")
        commit(solo, "s.txt", "s\n", "s")
        self.assertRegex(self.out("launch", "s1", solo, self.brief), f"base=trunk@{SHA} landing=local$")
        git(solo, "remote", "add", "origin", str(self.tmp / "no-such-origin.git"))
        _, out, err = self.t("launch", "s2", solo, self.brief)
        self.assertTrue(out.rstrip().endswith("landing=local"), out)
        self.assertIn("warning: git fetch origin failed", err)


class Check(ThreadCase):
    def test_check_reports_local_git_identities(self):
        self.launch("t-a")
        solo = self.repo(self.proj / "solo")
        self.launch("s1", solo)
        self.assertEqual(self.out("check", "--all", cwd=self.plain), "OK")
        # A local git identity that differs from the global one is reported once per repository; an equal one is not.
        Path(os.environ["GIT_CONFIG_GLOBAL"]).write_text("[user]\n\temail = owner@example.com\n", encoding="utf-8")
        git(self.app, "config", "user.email", "test@example.com")
        out = self.out("check", "--all", cwd=self.plain).splitlines()
        self.assertEqual(len([line for line in out if line.startswith("IDENTITY ")]), 1, out)
        self.assertTrue(out[0].startswith(
            f"IDENTITY {lib.native(self.app)} user.email=test@example.com (global owner@example.com): "), out)
        self.assertTrue(self.out("check", cwd=self.app).startswith(f"IDENTITY {lib.native(self.app)} "))
        self.assertEqual(self.out("check", cwd=solo), "OK")
        git(self.app, "config", "user.name", "tester")
        self.assertIn(f"IDENTITY {lib.native(self.app)} user.name=tester (global none): ",
                      self.out("check", "--all", cwd=self.plain))
        git(self.app, "config", "--unset", "user.name")
        git(self.app, "config", "user.email", "owner@example.com")
        self.assertEqual(self.out("check", "--all", cwd=self.plain), "OK")


class LocalBuild(ThreadCase):
    """Build c on the unpushed branch feat-x, lands locally, with lane l1 merged into orchestration/c; build d on main
    lands by pull request. The owner's checkout is back on main."""

    def setUp(self):
        super().setUp()
        git(self.app, "checkout", "-q", "-b", "feat-x")
        commit(self.app, "FEAT.md", "feat\n", "feat")
        self.wtc = self.launch("c")
        git(self.app, "checkout", "-q", "main")
        self.wtd = self.launch("d")
        self.l1 = self.proj / "app-wt-l1"
        git(self.app, "worktree", "add", "-q", str(self.l1), "-b", "lane/l1", "orchestration/c")
        commit(self.l1, "L1.md", "l1\n", "l1")
        git(self.wtc, "merge", "-q", "--no-ff", "-m", "Merge lane/l1", "lane/l1")

    def test_integrate(self):
        self.assertRegex(self.out("integrate", "c"), "^FAILED .* is on main, not feat-x")
        git(self.app, "checkout", "-q", "feat-x")
        self.assertRegex(self.out("integrate", "c"), f"^INTEGRATED c feat-x@{SHA} \\(fast-forward\\)$")
        self.assertTrue((self.app / "L1.md").is_file())
        commit(self.app, "OWNER.md", "owner\n", "owner")
        commit(self.wtc, "C2.md", "c2\n", "c2")
        self.assertTrue(self.out("integrate", "c").endswith("(merge)"))
        self.assertTrue((self.app / "C2.md").is_file() and (self.app / "OWNER.md").is_file())
        commit(self.app, "CLASH.md", "a\n", "a")
        commit(self.wtc, "CLASH.md", "b\n", "b")
        self.assertRegex(self.out("integrate", "c"),
                         "^FAILED merging orchestration/c into feat-x conflicts in: CLASH.md")
        self.assertEqual(git(self.app, "status", "--porcelain", "--untracked-files=no"), "")
        with open(self.app / "FEAT.md", "a") as f:
            f.write("dirty\n")
        self.assertRegex(self.out("integrate", "c"), "^FAILED .* has uncommitted changes")
        git(self.app, "checkout", "-q", "FEAT.md")
        self.assertRegex(self.out("integrate", "d"), "^FAILED d lands by pull request")
        solo = self.repo(self.proj / "solo")
        rec = self.wtc / ".orchestration" / "thread.md"
        rec.write_text(re.sub(r"(?m)^CHECKOUT: .*$", lambda _: f"CHECKOUT: {solo}", rec.read_text(encoding="utf-8")), encoding="utf-8")
        self.assertRegex(self.out("integrate", "c"),
                         f"^FAILED {re.escape(str(solo))} is not a checkout of {re.escape(lib.native(self.app))}")

    def test_integrate_compares_the_checkout_with_the_registry_in_canon_form(self):
        """The registry's repo and the record's CHECKOUT in another spelling of the same folders, a symlink here, as
        C:/x and C:\\x differ on Windows, still name one repository."""
        git(self.app, "checkout", "-q", "feat-x")
        rec = self.wtc / ".orchestration" / "thread.md"
        rec.write_text(re.sub(r"(?m)^CHECKOUT: .*$", lambda _: f"CHECKOUT: {self.alias(self.app)}", rec.read_text(encoding="utf-8")), encoding="utf-8")
        reg = self.orch / "threads.tsv"
        reg.write_text(reg.read_text(encoding="utf-8").replace(f"c\t{self.app}\t", f"c\t{self.alias(self.app)}\t"), encoding="utf-8")
        self.assertRegex(self.out("integrate", "c"), f"^INTEGRATED c feat-x@{SHA} \\(fast-forward\\)$")

    def test_close(self):
        git(self.app, "checkout", "-q", "feat-x")
        self.t("integrate", "c")
        commit(self.wtc, "CLASH.md", "b\n", "b")
        # c's branch holds a commit feat-x lacks, so close refuses.
        self.assertRegex(self.out("close", "c"), "^FAILED orchestration/c holds work that feat-x lacks in: CLASH.md")
        self.assertTrue(self.wtc.is_dir())
        # Files git ignores in the coordination worktree are evidence too, except dependency folders.
        with open(self.app / ".git" / "info" / "exclude", "a") as f:
            f.write(".eval-runs/\n.claude/agent-memory/\nnode_modules/\n")
        for rel, text in ((".eval-runs/r1/out.md", "run\n"), (".claude/agent-memory/x.md", "memory\n"),
                          ("node_modules/x/i.js", "dep\n")):
            (self.wtc / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.wtc / rel).write_text(text, encoding="utf-8")
        mail = self.orch / "mail" / "c" / "main" / "new"
        mail.mkdir(parents=True)
        (mail / "1-msg").write_text("From: c/thread\n\nSTATUS: done - c\n", encoding="utf-8")
        panec, wsc = self.pane_of("c"), self.row_of("c")[3]
        git(self.app, "worktree", "add", "-q", "-b", "far", str(self.tmp / "far" / "app-wt-far"))
        out = self.out("close", "c", "--force")
        self.assertNotIn("app-wt-far", out, "close listed a worktree that is not beside the checkout as a lane")
        self.assertRegex(out, f"^CLOSED c archive={re.escape(lib.native(self.orch))}/archive/c-[0-9T]+Z "
                              "lanes still present: .*app-wt-l1")
        arch = Path(out.split("archive=")[1].split(" ")[0])
        self.assertTrue((arch / "thread.md").is_file())
        self.assertTrue(list((arch / "mail" / "main" / "new").iterdir()))
        self.assertFalse((self.orch / "mail" / "c").exists())
        self.assertTrue((arch / "ignored/.eval-runs/r1/out.md").is_file())
        self.assertTrue((arch / "ignored/.claude/agent-memory/x.md").is_file())
        self.assertFalse((arch / "ignored/node_modules").exists())
        self.assertFalse((arch / "ignored/.orchestration").exists())
        self.assertFalse(self.wtc.exists())
        self.assertNotIn("orchestration/c", git(self.app, "branch", "--list", "orchestration/c"))
        self.assertIsNone(self.row_of("c"))
        self.assertIn(f"pane close {panec}", self.herdr.log)
        self.assertIn(f"workspace close {wsc}", self.herdr.log)

    def test_close_recognises_squash_landed_work(self):
        (self.wtd / "README.md").write_text("dirty\n", encoding="utf-8")
        self.assertRegex(self.out("close", "d"), "^FAILED .* has uncommitted changes to tracked files")
        git(self.wtd, "checkout", "-q", "README.md")
        commit(self.wtd, "PLAN.md", "plan\n", "plan")
        self.assertRegex(self.out("close", "d"),
                         "^FAILED orchestration/d holds work that origin/main lacks in: PLAN.md")
        git(self.seed, "checkout", "-q", "main")
        git(self.seed, "pull", "-q", "origin", "main")
        commit(self.seed, "PLAN.md", "plan\n", "plan (#9)")
        git(self.seed, "push", "-q", "origin", "main")
        self.assertRegex(self.out("close", "d"), "^CLOSED d ")

    def test_close_by_worktree(self):
        wtz = self.proj / "app-orch-z"
        git(self.app, "worktree", "add", "-q", "-b", "orchestration/z", str(wtz), "main")
        self.assertRegex(self.out("close", "--worktree", wtz), "^FAILED no record of .* base; pass --base")
        # When git can't list the ignored files, close keeps the worktree.
        index = Path(git(wtz, "rev-parse", "--absolute-git-dir"), "index")
        saved = index.read_bytes()
        index.write_text("corrupt", encoding="utf-8")
        out = self.out("close", "--worktree", wtz, "--base", "main", "--force")
        self.assertRegex(out, r"^FAILED refusing: git status failed in .*app-orch-z.*nothing was removed "
                              r"\(archive at [^\n]*\)$")
        self.assertTrue(wtz.is_dir())
        index.write_bytes(saved)
        self.herdr.agents.append({"name": "z", "agent_status": "idle", "pane_id": "w88:p1"})
        # Given in another spelling of the same folder, the worktree is still found beside its checkout.
        self.assertRegex(self.out("close", "--worktree", self.alias(wtz), "--base", "main"), "^CLOSED z ")
        self.assertFalse(wtz.exists())
        self.assertIn("workspace close w88", self.herdr.log)
        self.assertRegex(self.out("close", "--worktree", self.app), "is on .*, not orchestration/<build>")
        self.assertRegex(self.out("close", "t-nope"), "^FAILED no thread for build t-nope")


class Usage(unittest.TestCase):
    def test_bad_arguments_print_the_usage_and_exit_1(self):
        for args in ([], ["frobnicate"], ["stop"], ["rotate", "x", "y"], ["close", "a", "b"]):
            r = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual((r.returncode, r.stdout, r.stderr), (1, "", thread.__doc__.rstrip() + "\n"), args)


if __name__ == "__main__":
    unittest.main()
