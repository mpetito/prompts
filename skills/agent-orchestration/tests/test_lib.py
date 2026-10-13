"""lib.py: times, paths, the spawn helper, the thread record, the owner's checkouts and the ignored-file archive."""
import os
import re
import subprocess
import sys
import time
import unittest

from .support import OrchTest, REAL_RUN, UTC, lib


class Times(unittest.TestCase):
    def test_utc_now_is_minutes(self):
        self.assertRegex(lib.utc_now(), f"^{UTC}$")

    def test_to_epoch_reads_utc_and_offsets(self):
        self.assertEqual(lib.to_epoch("2026-10-13T14:30Z"), 1791901800)
        self.assertEqual(lib.to_epoch("2026-10-13T14:30:15Z"), 1791901815)
        self.assertAlmostEqual(lib.to_epoch("+2m"), time.time() + 120, delta=2)
        self.assertAlmostEqual(lib.to_epoch("+1h"), time.time() + 3600, delta=2)
        self.assertEqual(lib.fmt_utc(1791901800), "2026-10-13T14:30Z")

    def test_to_epoch_names_a_bad_value(self):
        for bad in ("14:30Z", "+5", "2026-13-40T99:99Z", "tomorrow"):
            with self.assertRaisesRegex(lib.Fail, f"not a UTC time.*{re.escape(bad)}"):
                lib.to_epoch(bad)


class Options(unittest.TestCase):
    def test_splits_positionals_values_and_flags(self):
        pos, opts = lib.take_options(["a", "--kind", "codex", "b", "--network"], {"--kind": True, "--network": False})
        self.assertEqual((pos, opts), (["a", "b"], {"--kind": "codex", "--network": True}))

    def test_refuses_an_unknown_option_and_a_missing_value(self):
        with self.assertRaisesRegex(lib.Fail, "unknown option --nope"):
            lib.take_options(["--nope"], {})
        with self.assertRaisesRegex(lib.Fail, "option --kind needs a value"):
            lib.take_options(["--kind"], {"--kind": True})


class Paths(OrchTest):
    def test_same_path_ignores_spelling(self):
        d = self.tmp / "a"
        d.mkdir()
        self.assertTrue(lib.same_path(str(d), str(d) + os.sep))
        self.assertTrue(lib.same_path(str(d), str(self.tmp / "a" / ".." / "a")))
        self.assertFalse(lib.same_path(str(d), str(self.tmp)))
        if os.name == "nt":
            self.assertTrue(lib.same_path(str(d), str(d).upper()))
            self.assertTrue(lib.same_path(str(d), str(d).replace("\\", "/")))

    @unittest.skipUnless(os.name == "nt", "8.3 names exist only on Windows")
    def test_same_path_expands_a_short_name(self):
        import ctypes
        d = self.tmp / "a long folder name"
        d.mkdir()
        buf = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetShortPathNameW(str(d), buf, 1024)
        if buf.value == str(d):
            self.skipTest("8.3 names are off on this volume")
        self.assertTrue(lib.same_path(buf.value, str(d)))

    def test_inside_needs_a_whole_component(self):
        (self.tmp / "repo").mkdir()
        (self.tmp / "repo-wt").mkdir()
        self.assertTrue(lib.inside(self.tmp / "repo" / "x", self.tmp / "repo"))
        self.assertTrue(lib.inside(self.tmp / "repo", self.tmp / "repo"))
        self.assertFalse(lib.inside(self.tmp / "repo-wt" / "x", self.tmp / "repo"))

    def test_canon_from_resolves_against_a_base(self):
        self.assertEqual(lib.canon_from(str(self.tmp), "x/../y"), lib.canon(self.tmp / "y"))
        self.assertEqual(lib.canon_from("/elsewhere", str(self.tmp)), lib.canon(self.tmp))

    def test_native_uses_forward_slashes(self):
        self.assertNotIn("\\", lib.native(self.tmp / "a" / "b"))


class Run(OrchTest):
    def test_a_missing_command_is_127(self):
        r = REAL_RUN(["no-such-command-anywhere"])
        self.assertEqual(r.returncode, 127)
        self.assertIn("not found", r.stderr)

    def test_passes_arguments_without_a_shell(self):
        arg = 'a b "c" $HOME; echo x'
        r = REAL_RUN([sys.executable, "-c", "import sys; print(sys.argv[1])", arg])
        self.assertEqual((r.returncode, r.stdout), (0, arg + "\n"))

    def test_a_timeout_kills_the_tree(self):
        # The child starts a grandchild that writes a file after the timeout: killing only the child would let it.
        late = self.tmp / "late"
        grandchild = f"import time, pathlib; time.sleep(3); pathlib.Path({str(late)!r}).write_text('late')"
        child = (f"import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', {grandchild!r}]); "
                 "time.sleep(30)")
        r = REAL_RUN([sys.executable, "-c", child], timeout=1)
        self.assertEqual(r.returncode, 124)
        time.sleep(4)
        self.assertFalse(late.exists(), "the grandchild outlived the timeout")


class Records(OrchTest):
    def test_record_value_is_the_first_trimmed_match(self):
        f = self.tmp / "thread.md"
        f.write_text("BUILD:  b1 \nBASE-REF: x\nBASE: main\nBASE: other\n", encoding="utf-8")
        self.assertEqual(lib.record_value(f, "BUILD"), "b1")
        self.assertEqual(lib.record_value(f, "BASE"), "main")
        self.assertEqual(lib.record_value(f, "LANDING"), "")
        self.assertEqual(lib.record_value(self.tmp / "missing.md", "BUILD"), "")

    def test_resolve_state_prefers_the_variable_then_the_worktree(self):
        repo = self.repo(self.tmp / "coord")
        (repo / "sub").mkdir()
        self.assertEqual(lib.resolve_state(str(repo / "sub"), "X"), os.path.join(repo, ".orchestration", "state.md"))
        with self.assertRaisesRegex(lib.Fail, "not inside a git worktree.*set X"):
            lib.resolve_state(str(self.tmp), "X")
        os.environ["ORCHESTRATION_STATE"] = "/explicit/state.md"
        self.assertEqual(lib.resolve_state(str(self.tmp), "X"), "/explicit/state.md")

    def test_session_top_prefers_the_project_dir(self):
        a, b = self.repo(self.tmp / "a"), self.repo(self.tmp / "b")
        self.assertEqual(lib.session_top(str(a)), str(a))
        os.environ["CLAUDE_PROJECT_DIR"] = str(b)
        self.assertEqual(lib.session_top(str(a)), str(b))

    def test_owner_checkouts_are_the_main_checkout_and_the_record(self):
        main = self.repo(self.tmp / "repo")
        coord = self.tmp / "repo-orch-b1"
        subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", "-b", "orchestration/b1", str(coord)],
                       check=True)
        self.assertEqual(lib.owner_checkouts(str(coord)), [str(main)])
        mine = self.tmp / "mine"
        mine.mkdir()
        (coord / ".orchestration").mkdir()
        (coord / ".orchestration" / "thread.md").write_text(f"CHECKOUT: {mine}\n", encoding="utf-8")
        self.assertEqual(lib.owner_checkouts(str(coord)), [str(main), lib.canon(mine)])
        (coord / ".orchestration" / "thread.md").write_text(f"CHECKOUT: {main}\n", encoding="utf-8")
        self.assertEqual(lib.owner_checkouts(str(coord)), [str(main)])
        self.assertEqual(lib.owner_checkouts(str(self.tmp)), [])


class ArchiveIgnored(OrchTest):
    def setUp(self):
        super().setUp()
        self.wt = self.repo(self.tmp / "wt")
        (self.wt / ".gitignore").write_text("*.log\nruns/\nnode_modules/\n.orchestration/\n", encoding="utf-8")
        (self.wt / "a.log").write_text("a", encoding="utf-8")
        (self.wt / "runs" / "r1").mkdir(parents=True)
        (self.wt / "runs" / "r1" / "out.txt").write_text("r", encoding="utf-8")
        (self.wt / "node_modules" / "x").mkdir(parents=True)
        (self.wt / ".orchestration" / "tmp").mkdir(parents=True)
        (self.wt / ".orchestration" / "tmp" / "s").write_text("s", encoding="utf-8")
        self.dest = self.tmp / "archive"

    def test_copies_ignored_files_at_their_paths_and_leaves_rebuilt_and_prefix(self):
        lines = lib.archive_ignored(self.wt, self.dest, ".orchestration")
        self.assertEqual((self.dest / "ignored" / "a.log").read_text(), "a")
        self.assertEqual((self.dest / "ignored" / "runs" / "r1" / "out.txt").read_text(), "r")
        self.assertFalse((self.dest / "ignored" / "node_modules").exists())
        self.assertFalse((self.dest / "ignored" / ".orchestration").exists())
        self.assertEqual(len(lines), 2)
        self.assertTrue(all(l.startswith("archived ignored ") for l in lines))

    def test_refuses_when_git_cannot_list(self):
        with self.assertRaisesRegex(lib.Fail, "git status failed.*nothing was removed"):
            lib.archive_ignored(self.tmp / "not-a-repo", self.dest, ".orchestration")

    def test_fails_when_a_copy_fails(self):
        self.dest.mkdir()
        (self.dest / "ignored").write_text("a file where the folder should be", encoding="utf-8")
        with self.assertRaisesRegex(lib.Fail, "copying .* failed"):
            lib.archive_ignored(self.wt, self.dest, ".orchestration")


class Hooks(unittest.TestCase):
    def test_replies_are_the_pretooluse_shapes(self):
        import io, json, contextlib
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(lib.advise("note"), 0)
            self.assertEqual(lib.deny("no"), 0)
        advise, deny = (json.loads(l)["hookSpecificOutput"] for l in out.getvalue().splitlines())
        self.assertEqual(advise, {"hookEventName": "PreToolUse", "additionalContext": "note"})
        self.assertEqual(deny, {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                "permissionDecisionReason": "no"})


if __name__ == "__main__":
    unittest.main()
