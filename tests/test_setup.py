"""setup_skills_link.py and verify_setup.py against a fixture checkout whose path has spaces and brackets, linking
into a throwaway home: selections, previews, reruns, relative and broken links, conflicts, backups, migration,
verification and its python3 checks."""
import contextlib
import ctypes
import io
import os
import re
import signal
import subprocess
import sys
import threading
import time
import unittest.mock
from pathlib import Path

from .support import ROOT, SetupTest, call, load, sc, symlink

SETUP = load(ROOT / "setup_skills_link.py")
VERIFY = load(ROOT / "verify_setup.py")
ALL = "codex,claude,opencode,copilot"


def files_below(folder):
    return sorted(str(p) for p in Path(folder).rglob("*"))


def tree(root):
    """Every entry below root with its kind and its link target or file bytes, links not followed: what a preview
    must leave exactly as it found it."""
    entries = {}
    for folder, dirs, files in os.walk(root):
        for name in dirs + files:
            path = os.path.join(folder, name)
            if sc.is_link(path):
                entries[path] = ("link", os.readlink(path))
            elif os.path.isdir(path):
                entries[path] = ("dir",)
            else:
                entries[path] = ("file", Path(path).read_bytes())
    return entries


class Linking(SetupTest):
    def setUp(self):
        super().setUp()
        self.repo = self.tmp / "repo with spaces [test]"
        for folder in ("skills", "agents", "instructions", "statusline"):
            (self.repo / folder).mkdir(parents=True)
        for name in ("example", "pr-scripts"):
            (self.repo / "skills" / name).mkdir()
            (self.repo / "skills" / name / "data.txt").write_text("source\n")
        (self.repo / "instructions" / "CLAUDE.md").write_text("instructions\n")
        (self.repo / "statusline" / "statusline.py").write_text("# script\n")
        for module in (SETUP, VERIFY):
            patcher = unittest.mock.patch.object(module, "REPO", str(self.repo))
            patcher.start()
            self.addCleanup(patcher.stop)
        self.dest = self.tmp / "user with spaces"
        self.paths = sc.setup_paths(str(self.dest))
        self.source = str(self.repo / "skills" / "example")
        self.link = os.path.join(self.paths.shared_skills, "example")
        self.legacy = Path(self.paths.codex_root) / "skills"

    def setup(self, *argv, home=None):
        return call(SETUP, "--home-directory", home or self.dest, *argv)

    def assert_incomplete(self, *argv):
        code, _, err = self.setup(*argv)
        self.assertEqual(code, 1)
        self.assertIn("incomplete", err)

    def test_what_if_creates_nothing_not_even_the_home(self):
        self.assertEqual(self.setup("--tools", ALL, "--what-if")[0], 0)
        self.assertFalse(self.dest.exists())

    def test_codex_uses_the_shared_skills_and_leaves_claude_alone(self):
        self.assertEqual(self.setup("--tools", "codex")[0], 0)
        self.assertTrue(sc.is_repo_link(self.link, self.source))
        self.assertFalse(os.path.exists(self.paths.claude_root))

    def test_rerun_adds_nothing_and_verification_passes(self):
        self.assertEqual(self.setup("--tools", ALL)[0], 0)
        code, _, err = call(VERIFY, "--tools", ALL, "--home-directory", self.dest)
        self.assertEqual(code, 0, err)
        before = files_below(self.dest)
        self.assertEqual(self.setup("--tools", ALL)[0], 0)
        self.assertEqual(files_below(self.dest), before)
        self.assertTrue(sc.is_repo_link(os.path.join(self.paths.shared_skills, "pr-scripts"),
                                        str(self.repo / "skills" / "pr-scripts")))
        for root in (os.path.join(self.paths.claude_root, "skills"), self.paths.copilot_skills):
            self.assertTrue(sc.is_repo_link(os.path.join(root, "example"), self.source), root)
        self.assertTrue(sc.is_repo_link(os.path.join(self.paths.claude_root, "CLAUDE.md"),
                                        str(self.repo / "instructions" / "CLAUDE.md")))
        self.assertTrue(sc.is_repo_link(os.path.join(self.paths.claude_root, "statusline.py"),
                                        str(self.repo / "statusline" / "statusline.py")))

    def test_setup_alone_removes_the_retired_status_line_link_and_only_when_it_is_ours(self):
        self.setup("--tools", "claude")
        retired = os.path.join(self.paths.claude_root, "statusline.js")
        symlink(str(self.repo / "statusline" / "statusline.js"), retired)
        call(VERIFY, "--tools", "claude", "--home-directory", self.dest)
        self.assertTrue(os.path.lexists(retired), "verification must never remove it")
        self.setup("--tools", "claude", "--what-if")
        self.assertTrue(os.path.lexists(retired), "a preview must not remove it")
        self.setup("--tools", "codex")
        self.assertTrue(os.path.lexists(retired), "setup without claude must not remove it")
        self.assertEqual(self.setup("--tools", "claude")[0], 0)
        self.assertFalse(os.path.lexists(retired), "setup must remove the link into this checkout")
        others = {"a real file": lambda: Path(retired).write_text("mine"),
                  "a link elsewhere": lambda: symlink(str(self.tmp / "other" / "statusline.js"), retired)}
        for kind, make in others.items():
            with self.subTest(kind=kind):
                make()
                self.setup("--tools", "claude")
                self.assertTrue(os.path.lexists(retired), f"a statusline.js that is {kind} must be left alone")
                os.unlink(retired)

    def test_a_valid_relative_link_stays_as_it_is(self):
        self.setup("--tools", "codex")
        os.unlink(self.link)
        relative = os.path.relpath(self.source, self.paths.shared_skills)
        symlink(relative, self.link)
        self.assertEqual(self.setup("--tools", "codex")[0], 0)
        self.assertEqual(os.readlink(self.link), relative)

    def test_only_an_owned_dangling_link_is_pruned(self):
        self.setup("--tools", "codex")
        foreign = os.path.join(self.paths.shared_skills, "foreign")
        stale = os.path.join(self.paths.shared_skills, "removed-skill")
        symlink(str(self.tmp / "missing-foreign"), foreign)
        symlink(os.path.relpath(self.repo / "skills" / "removed-skill", self.paths.shared_skills), stale)
        self.assertEqual(self.setup("--tools", "codex")[0], 0)
        self.assertFalse(os.path.lexists(stale))
        self.assertTrue(os.path.lexists(foreign))

    def test_a_conflict_is_kept_until_replaced_and_then_backed_up(self):
        self.setup("--tools", "codex")
        os.unlink(self.link)
        os.mkdir(self.link)
        Path(self.link, "personal.txt").write_text("keep me")
        self.assert_incomplete("--tools", "codex")
        self.assertEqual(Path(self.link, "personal.txt").read_text(), "keep me")
        self.assertEqual(self.setup("--tools", "codex", "--replace-conflicts", "--what-if")[0], 0)
        self.assertFalse(os.path.exists(self.paths.backup_root))
        self.assertEqual(self.setup("--tools", "codex", "--replace-conflicts")[0], 0)
        backups = [p for p in Path(self.paths.backup_root).rglob("*") if p.is_file()]
        self.assertEqual([p.read_text() for p in backups], ["keep me"])

    def test_replace_repairs_a_broken_conflicting_link(self):
        self.setup("--tools", "codex")
        os.unlink(self.link)
        symlink(str(self.tmp / "missing-other"), self.link)
        self.assert_incomplete("--tools", "codex")
        self.assertEqual(self.setup("--tools", "codex", "--replace-conflicts")[0], 0)
        self.assertTrue(sc.is_repo_link(self.link, self.source))

    def test_migration_removes_only_duplicated_legacy_links(self):
        self.setup("--tools", "codex")
        (self.legacy / ".system").mkdir(parents=True)
        (self.legacy / ".system" / "keep.txt").write_text("system")
        symlink(self.source, self.legacy / "example")
        symlink(str(self.tmp / "missing-other"), self.legacy / "other")
        self.assertEqual(self.setup("--tools", "codex")[0], 0)
        self.assertFalse(os.path.lexists(self.legacy / "example"))
        self.assertTrue((self.legacy / ".system" / "keep.txt").exists())
        self.assertTrue(os.path.lexists(self.legacy / "other"))

    def test_migration_leaves_a_linked_legacy_folder_alone(self):
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        symlink(self.source, elsewhere / "example")
        os.makedirs(self.paths.codex_root)
        symlink(str(elsewhere), self.legacy)
        self.assertEqual(self.setup("--tools", "codex")[0], 0)
        self.assertTrue(sc.is_repo_link(elsewhere / "example", self.source))

    def test_migration_keeps_the_legacy_link_when_its_replacement_failed(self):
        self.setup("--tools", "codex")
        os.unlink(self.link)
        os.mkdir(self.link)
        self.legacy.mkdir(parents=True)
        symlink(self.source, self.legacy / "example")
        self.assert_incomplete("--tools", "codex")
        self.assertTrue(sc.is_repo_link(self.legacy / "example", self.source))

    def test_whole_folder_links_become_real_folders(self):
        home = self.tmp / "whole-folder-user"
        paths = sc.setup_paths(str(home))
        os.makedirs(paths.codex_root)
        os.makedirs(os.path.dirname(paths.shared_skills))
        symlink(str(self.repo / "skills"), os.path.join(paths.codex_root, "skills"))
        symlink(str(self.repo / "skills"), paths.shared_skills)
        self.assertEqual(self.setup("--tools", "codex", home=home)[0], 0)
        self.assertFalse(sc.is_link(paths.shared_skills))
        self.assertTrue(os.path.isdir(paths.shared_skills))
        self.assertFalse(sc.is_link(os.path.join(paths.codex_root, "skills")))
        self.assertTrue(os.path.isdir(os.path.join(paths.codex_root, "skills")))
        self.assertTrue((self.repo / "skills" / "example" / "data.txt").exists())
        self.assertEqual(os.listdir(os.path.dirname(paths.shared_skills)), ["skills"])
        self.assertFalse(os.path.exists(paths.backup_root))

    def test_a_whole_folder_legacy_link_stays_until_every_replacement_exists(self):
        os.makedirs(self.paths.codex_root)
        symlink(str(self.repo / "skills"), self.legacy)
        os.makedirs(self.link)
        self.assert_incomplete("--tools", "codex")
        self.assertTrue(sc.is_repo_link(self.legacy, str(self.repo / "skills")))

    def test_a_conflicting_skills_root_is_kept_until_replaced(self):
        os.makedirs(os.path.dirname(self.paths.shared_skills))
        Path(self.paths.shared_skills).write_text("mine")
        self.assert_incomplete("--tools", "codex")
        self.assertEqual(Path(self.paths.shared_skills).read_text(), "mine")
        self.assertEqual(self.setup("--tools", "codex", "--replace-conflicts", "--what-if")[0], 0)
        self.assertEqual(Path(self.paths.shared_skills).read_text(), "mine")
        self.assertEqual(self.setup("--tools", "codex", "--replace-conflicts")[0], 0)
        self.assertTrue(sc.is_repo_link(self.link, self.source))
        backups = [p for p in Path(self.paths.backup_root).rglob("*") if p.is_file()]
        self.assertEqual([p.read_text() for p in backups], ["mine"])

    def test_a_preview_writes_nothing_and_exits_0_whatever_each_destination_holds(self):
        foreign = self.tmp / "foreign"
        (foreign / "inside").mkdir(parents=True)
        claude = {name: os.path.join(self.repo, *source.split("/")) for source, name in sc.CLAUDE_FILES}
        # Every destination setup touches, with the source an owned link to it would point at.
        skills = self.repo / "skills"
        destinations = [(self.paths.shared_skills, skills), (self.paths.copilot_skills, skills),
                        (os.path.join(self.paths.claude_root, "skills"), skills), (str(self.legacy), skills),
                        *((os.path.join(self.paths.claude_root, name), source) for name, source in claude.items()),
                        (os.path.join(self.paths.claude_root, "statusline.js"),
                         self.repo / "statusline" / "statusline.js")]

        def conflicting_folder(path, _):
            os.makedirs(os.path.join(path, "example"))
            Path(path, "example", "personal.txt").write_text("keep me")
            symlink(str(self.tmp / "missing"), os.path.join(path, "foreign"))
            symlink(str(self.repo / "skills" / "removed-skill"), os.path.join(path, "removed-skill"))
            symlink(str(self.repo / "skills" / "pr-scripts"), os.path.join(path, "pr-scripts"))

        states = {
            "missing": lambda path, source: None,
            "a file": lambda path, source: Path(path).write_text("mine"),
            "a folder of conflicts": conflicting_folder,
            "a link to its source": lambda path, source: symlink(str(source), path),
            "a link elsewhere": lambda path, source: symlink(str(foreign), path),
            "a dangling link": lambda path, source: symlink(str(self.tmp / "missing"), path),
        }
        for state, make in states.items():
            for replace in ((), ("--replace-conflicts",)):
                with self.subTest(state=state, replace=bool(replace)):
                    home = self.tmp / f"home-{state}-{bool(replace)}"
                    paths = sc.setup_paths(str(home))
                    for path, source in destinations:
                        path = os.path.join(home, os.path.relpath(path, self.dest))
                        os.makedirs(os.path.dirname(path), exist_ok=True)
                        make(path, source)
                    before, repo = tree(home), tree(self.repo)
                    code, _, err = self.setup("--tools", ALL, "--what-if", *replace, home=home)
                    self.assertEqual(code, 0, err)
                    self.assertEqual(tree(home), before)
                    self.assertEqual(tree(self.repo), repo)
                    self.assertFalse(os.path.exists(paths.backup_root))
        for parent in (".agents", ".copilot", ".claude", ".codex"):
            with self.subTest(state=f"{parent} is a file"):
                home = self.tmp / f"home-file-{parent}"
                home.mkdir()
                (home / parent).write_text("mine")
                before = tree(home)
                code, _, err = self.setup("--tools", ALL, "--what-if", "--replace-conflicts", home=home)
                self.assertEqual(code, 0, err)
                self.assertEqual(tree(home), before)

    @unittest.skipUnless(os.name == "nt", "junctions exist only on Windows")
    def test_a_junction_to_the_skills_folder_is_converted_and_the_checkout_kept(self):
        import _winapi
        for replace in ((), ("--replace-conflicts",)):
            with self.subTest(replace=bool(replace)):
                home = self.tmp / f"junction-{bool(replace)}"
                paths = sc.setup_paths(str(home))
                os.makedirs(os.path.dirname(paths.shared_skills))
                _winapi.CreateJunction(str(self.repo / "skills"), paths.shared_skills)
                before = tree(self.repo)
                code, _, err = self.setup("--tools", "codex", *replace, home=home)
                self.assertEqual(code, 0, err)
                self.assertEqual(tree(self.repo), before)
                self.assertFalse(os.path.exists(paths.backup_root))
                self.assertFalse(sc.is_link(paths.shared_skills))
                self.assertTrue(sc.is_repo_link(os.path.join(paths.shared_skills, "example"), self.source))

    def test_a_failed_link_puts_the_replaced_entry_back(self):
        self.setup("--tools", "codex")
        os.unlink(self.link)
        os.mkdir(self.link)
        Path(self.link, "personal.txt").write_text("keep me")
        with unittest.mock.patch.object(os, "symlink", side_effect=OSError("refused")):
            code, _, err = self.setup("--tools", "codex", "--replace-conflicts")
        self.assertEqual(code, 1)
        self.assertIn("refused", err)
        self.assertEqual(Path(self.link, "personal.txt").read_text(), "keep me")

    def test_codex_reading_the_shared_folder_keeps_its_links(self):
        os.environ["CODEX_HOME"] = str(self.home / ".agents")
        self.assertEqual(call(SETUP, "--tools", "codex")[0], 0)
        self.assertEqual(call(SETUP, "--tools", "codex")[0], 0)
        self.assertTrue(sc.is_repo_link(os.path.join(self.home, ".agents", "skills", "example"), self.source))

    @unittest.skipIf(os.name == "nt", "Windows compares paths case-insensitively")
    def test_unix_comparisons_are_case_sensitive(self):
        self.assertFalse(sc.same_path(self.tmp / "Case", self.tmp / "case"))

    def test_an_unknown_tool_is_refused(self):
        code, _, err = self.setup("--tools", "unknown")
        self.assertEqual(code, 1)
        self.assertIn("Unknown tool", err)

    def test_verification_fails_on_a_missing_link(self):
        self.setup("--tools", "codex")
        os.unlink(self.link)
        code, _, err = call(VERIFY, "--tools", "codex", "--home-directory", self.dest)
        self.assertEqual(code, 1)
        self.assertIn(self.link, err)

    def test_verification_fails_on_a_whole_folder_link(self):
        os.makedirs(os.path.dirname(self.paths.shared_skills))
        symlink(str(self.repo / "skills"), self.paths.shared_skills)
        code, _, err = call(VERIFY, "--tools", "codex", "--home-directory", self.dest)
        self.assertEqual(code, 1)
        self.assertRegex(err, f"(?m){re.escape(self.paths.shared_skills)}$")

    def test_without_tools_only_clients_on_path_are_set_up(self):
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        exe = bin_dir / ("codex.cmd" if os.name == "nt" else "codex")
        exe.write_text("exit 1\n")
        exe.chmod(0o755)
        with unittest.mock.patch.dict(os.environ, PATH=str(bin_dir)):
            code, out, _ = self.setup()
        self.assertEqual(code, 0)
        self.assertTrue(sc.is_repo_link(self.link, self.source))
        self.assertFalse(os.path.exists(self.paths.claude_root))
        self.assertEqual(out.count("[SKIPPED]"), 3)

    def test_default_destinations_are_in_the_test_home(self):
        self.assertEqual(Path.home(), self.home)
        paths = sc.setup_paths()
        for field in ("user_root", "codex_root", "claude_root", "claude_config", "opencode_config", "shared_skills",
                      "copilot_skills", "backup_root"):
            self.assertTrue(Path(getattr(paths, field)).is_relative_to(self.home), field)
        self.assertEqual(call(SETUP, "--tools", "codex")[0], 0)
        self.assertTrue(sc.is_repo_link(os.path.join(self.home, ".agents", "skills", "example"), self.source))

    def test_a_placeholder_first_on_path_fails_verification(self):
        bin_dir = self.tmp / "bin"
        bin_dir.mkdir()
        if os.name == "nt":
            (bin_dir / "python3.cmd").write_text(f"@exit /b {VERIFY.STORE_PLACEHOLDER}\r\n")
        else:
            # A POSIX exit status keeps only the low 8 bits, so 9009 itself can't be returned here.
            (bin_dir / "python3").write_text(f"#!/bin/sh\nexit {VERIFY.STORE_PLACEHOLDER}\n")
            (bin_dir / "python3").chmod(0o755)
        self.setup("--tools", "codex")
        with unittest.mock.patch.dict(os.environ, PATH=f"{bin_dir}{os.pathsep}{os.environ['PATH']}"):
            code, _, err = call(VERIFY, "--tools", "codex", "--home-directory", self.dest)
        self.assertEqual(code, 1)
        self.assertRegex(err, "Microsoft Store placeholder" if os.name == "nt" else r"python3 --version failed")
        self.assertRegex(err, r"\b1 setup check")


class Python(SetupTest):
    """verify_setup.py's python3 check, which runs python3 as its own process."""

    def check(self, version=(0, "Python 3.12.3\n"), info=(0, "(3, 12)\n")):
        answers = {"--version": version, "-c": info}
        self.fake_run(lambda args, _: subprocess.CompletedProcess(args, *answers[args[1]], ""))
        return self.check_python()

    def check_python(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return VERIFY.check_python()

    def test_the_real_python3_passes(self):
        self.assertIsNone(self.check_python())

    def test_a_missing_python3_fails(self):
        self.assertRegex(self.check(version=(127, "")), "not on PATH")

    def test_the_store_placeholder_fails(self):
        self.assertRegex(self.check(version=(VERIFY.STORE_PLACEHOLDER, "")), "Store placeholder")

    def test_python_3_11_fails(self):
        self.assertRegex(self.check(version=(0, "Python 3.11.9\n"), info=(0, "(3, 11)\n")), "3.11.9")

    def test_a_version_query_that_fails_or_prints_nothing_fails(self):
        for info in ((1, ""), (0, ""), (1, "Traceback (most recent call last):\n")):
            with self.subTest(info=info):
                self.assertIsNotNone(self.check(info=info))

    def test_python_3_12_and_later_pass(self):
        self.assertIsNone(self.check())
        self.assertIsNone(self.check(info=(0, "(3, 14)\n")))
        self.assertIsNone(self.check(info=(0, "(4, 0)\n")))


class Run(SetupTest):
    """setup_common.run, the one place setup spawns a process."""

    def test_a_missing_command_returns_127(self):
        self.assertEqual(sc.run(["no-such-command-for-setup-tests"]).returncode, 127)

    def test_a_timeout_kills_the_whole_tree(self):
        # The grandchild holds the output pipe open; only killing the tree lets run() return before it exits.
        sleeper = "import subprocess, sys, time; subprocess.Popen([sys.executable, '-c', 'import time; " \
                  "time.sleep(30)']); time.sleep(30)"
        started = time.monotonic()
        self.assertEqual(sc.run([sys.executable, "-c", sleeper], timeout=1).returncode, 124)
        self.assertLess(time.monotonic() - started, 15)

    @unittest.skipUnless(os.name == "posix", "a Windows wait cannot be interrupted until the command exits")
    def test_an_interruption_kills_the_command_and_what_it_started(self):
        marker = self.tmp / "survived"
        grandchild = f"import time; time.sleep(2); open({str(marker)!r}, 'w')"
        child = f"import subprocess, sys; subprocess.run([sys.executable, '-c', {grandchild!r}])"
        # A real SIGINT, as Ctrl+C sends: it interrupts the wait, which interrupt_main does not.
        threading.Timer(0.5, os.kill, (os.getpid(), signal.SIGINT)).start()
        with self.assertRaises(KeyboardInterrupt):
            sc.run([sys.executable, "-c", child])
        time.sleep(3)
        self.assertFalse(marker.exists())

    def test_output_takes_both_streams(self):
        with open(self.tmp / "out.log", "w", encoding="utf-8") as log:
            r = sc.run([sys.executable, "-c", "import sys; print('out'); print('err', file=sys.stderr)"], output=log)
        self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
        self.assertEqual(sorted((self.tmp / "out.log").read_text(encoding="utf-8").split()), ["err", "out"])

    @unittest.skipUnless(os.name == "nt" and ctypes.windll.kernel32.GetConsoleWindow(), "needs a console to share")
    def test_a_parent_without_stdio_gives_its_children_no_console_window(self):
        probe = [sys.executable, "-c", "import ctypes; print(bool(ctypes.windll.kernel32.GetConsoleWindow()))"]
        self.assertEqual(sc.run(probe).stdout.strip(), "True")
        # pythonw's signature: no console, so a console child would otherwise open a window of its own.
        with unittest.mock.patch.object(sys, "__stdout__", None):
            self.assertEqual(sc.run(probe).stdout.strip(), "False")

    def test_entry_runs_without_stdio_as_under_pythonw(self):
        with unittest.mock.patch.multiple(sys, stdin=None, stdout=None, stderr=None), \
                self.assertRaises(SystemExit) as exit:
            sc.entry(lambda argv: 0)
        self.assertEqual(exit.exception.code, 0)


class LinkDestination(SetupTest):
    @unittest.skipUnless(os.name == "nt", "readlink gives \\\\?\\ substitute names only on Windows")
    def test_a_unc_substitute_name_reads_as_a_share_path(self):
        link = str(self.tmp / "link")
        with unittest.mock.patch.object(sc, "is_link", return_value=True), \
                unittest.mock.patch.object(os, "readlink", return_value="\\\\?\\UNC\\server\\share\\skills"):
            self.assertTrue(sc.same_path(sc.link_destination(link), "\\\\server\\share\\skills"))


class Usage(SetupTest):
    """Each script run as a program: a usage error exits 1."""

    def test_an_unknown_option_exits_1(self):
        for script in ("setup_skills_link.py", "verify_setup.py"):
            r = subprocess.run([sys.executable, str(ROOT / script), "--nope"], capture_output=True, text=True,
                               cwd=self.tmp)
            self.assertEqual(r.returncode, 1, script)
            self.assertIn("usage:", r.stderr, script)
