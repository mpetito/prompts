"""statusline.py: each behaviour of the Node status line it replaces, case by case, plus the stdin deadline.

Expected text is built from the script's own ICON and paint, so a case checks which segments appear, in what order,
with what colour and content, and never restates a glyph. git is real; run() is faked only where git must fail.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "statusline.py"
spec = importlib.util.spec_from_file_location("statusline", SCRIPT)
sl = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sl)
ICON, paint = sl.ICON, sl.paint
SEP = paint("90", f" {ICON['sep']} ")


def git(cwd, *args):
    subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True)


class StatusLineTest(unittest.TestCase):
    """A throwaway home holding a plain folder and a git repository on main with one commit."""

    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="statusline-test-")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        self.plain = self.home / "plain"
        self.plain.mkdir(parents=True)
        env = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home), GIT_AUTHOR_NAME="t",
                   GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
                   GIT_CONFIG_GLOBAL=str(self.home / ".gitconfig"), GIT_CONFIG_NOSYSTEM="1")
        patcher = unittest.mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.home / "repo"
        git(self.tmp, "init", "-q", "-b", "main", str(self.repo))
        (self.repo / "a.txt").write_text("a\n")
        git(self.repo, "add", "a.txt")
        git(self.repo, "commit", "-q", "-m", "init")

    def render(self, **payload):
        return sl.render(json.dumps(payload))

    def dir_part(self, path):
        return paint("36", f"{ICON['dir']} ~/{Path(path).relative_to(self.home).as_posix()}")

    def branch_part(self, name, badge):
        return paint("35", f"{ICON['branch']} {name}") + f" {badge}"

    def clean(self):
        return paint("32", ICON["clean"])


class Directory(StatusLineTest):
    def test_outside_git_shows_only_the_folder(self):
        self.assertEqual(self.render(cwd=str(self.plain)), self.dir_part(self.plain))

    def test_workspace_current_dir_wins_over_cwd(self):
        out = self.render(cwd=str(self.repo), workspace={"current_dir": str(self.plain)})
        self.assertEqual(out, self.dir_part(self.plain))

    def test_cwd_is_used_without_workspace_current_dir(self):
        self.assertEqual(self.render(cwd=str(self.plain), workspace={}), self.dir_part(self.plain))

    def test_bad_json_renders_the_process_folder(self):
        with unittest.mock.patch.object(sl.os, "getcwd", return_value=str(self.plain)):
            self.assertEqual(sl.render("{not json"), self.dir_part(self.plain))
            self.assertEqual(sl.render(""), self.dir_part(self.plain))

    def test_a_payload_that_is_not_an_object_renders_as_empty(self):
        with unittest.mock.patch.object(sl.os, "getcwd", return_value=str(self.plain)):
            self.assertEqual(sl.render("[1, 2]"), self.dir_part(self.plain))

    def test_home_collapses_to_tilde_case_insensitively(self):
        with unittest.mock.patch.object(sl, "git_info", return_value=None):
            out = self.render(cwd=str(self.home).upper() + os.sep + self.plain.name)
        self.assertEqual(out, self.dir_part(self.plain))

    def test_a_folder_outside_home_keeps_its_full_path(self):
        out = self.render(cwd=str(self.tmp))
        self.assertEqual(out, paint("36", f"{ICON['dir']} {self.tmp.as_posix()}"))

    def test_backslashes_become_forward_slashes(self):
        with unittest.mock.patch.object(sl, "git_info", return_value=None):
            out = self.render(cwd="D:\\work\\x")
        self.assertEqual(out, paint("36", f"{ICON['dir']} D:/work/x"))


class Repo(StatusLineTest):
    def test_repo_shows_owner_and_name(self):
        out = self.render(cwd=str(self.plain), workspace={"current_dir": str(self.plain),
                                                          "repo": {"owner": "acme", "name": "web"}})
        self.assertEqual(out, self.dir_part(self.plain) + SEP + paint("34", f"{ICON['repo']} acme/web"))

    def test_repo_without_a_name_is_omitted(self):
        out = self.render(workspace={"current_dir": str(self.plain), "repo": {"owner": "acme"}})
        self.assertEqual(out, self.dir_part(self.plain))


class Branch(StatusLineTest):
    def test_branch_comes_from_git_with_a_clean_badge(self):
        self.assertEqual(self.render(cwd=str(self.repo)),
                         self.dir_part(self.repo) + SEP + self.branch_part("main", self.clean()))

    def test_worktree_branch_wins_over_git(self):
        out = self.render(cwd=str(self.repo), worktree={"branch": "feature"})
        self.assertEqual(out, self.dir_part(self.repo) + SEP + self.branch_part("feature", self.clean()))

    def test_a_branch_named_head_is_omitted(self):
        self.assertEqual(self.render(cwd=str(self.repo), worktree={"branch": "HEAD"}), self.dir_part(self.repo))

    def test_detached_head_shows_no_branch(self):
        git(self.repo, "checkout", "-q", "--detach")
        self.assertEqual(self.render(cwd=str(self.repo)), self.dir_part(self.repo))

    def test_users_prefix_is_dropped(self):
        git(self.repo, "checkout", "-q", "-b", "users/someone/123-fix")
        self.assertEqual(self.render(cwd=str(self.repo)),
                         self.dir_part(self.repo) + SEP + self.branch_part("123-fix", self.clean()))

    def test_a_long_branch_is_capped_with_an_ellipsis(self):
        exact, long = "b" * sl.BRANCH_MAX, "c" * (sl.BRANCH_MAX + 1)
        self.assertEqual(sl.short_branch(exact), exact)
        self.assertEqual(sl.short_branch(long), "c" * (sl.BRANCH_MAX - 1) + "\u2026")
        self.assertEqual(sl.short_branch(f"users/x/{exact}"), exact)

    def test_a_git_failure_keeps_the_payload_branch_without_a_badge(self):
        failed = subprocess.CompletedProcess([], 128, "", "")
        with unittest.mock.patch.object(sl, "run", return_value=failed):
            out = self.render(cwd=str(self.repo), worktree={"branch": "feature"})
        self.assertEqual(out, self.dir_part(self.repo) + SEP + paint("35", f"{ICON['branch']} feature"))

    def test_git_runs_with_a_timeout(self):
        calls = []
        with unittest.mock.patch.object(sl, "run", lambda args, timeout: calls.append((args, timeout))
                                        or subprocess.CompletedProcess(args, 124, "", "")):
            self.render(cwd=str(self.repo))
        self.assertEqual(calls, [(["git", "-C", str(self.repo), "status", "--porcelain=v1", "--branch"],
                                  sl.GIT_TIMEOUT)])


class Porcelain(unittest.TestCase):
    """parse_status on the header and entry forms of `git status --porcelain=v1 --branch`."""

    def test_header_drops_the_upstream_and_tracking_note(self):
        self.assertEqual(sl.parse_status("## main...origin/main [ahead 1]\n")["branch"], "main")
        self.assertEqual(sl.parse_status("## main [gone]\n")["branch"], "main")

    def test_a_dotted_branch_survives_the_upstream_split(self):
        self.assertEqual(sl.parse_status("## release/1.2.0...origin/release/1.2.0\n")["branch"], "release/1.2.0")

    def test_no_commits_yet_names_the_branch(self):
        self.assertEqual(sl.parse_status("## No commits yet on main\n")["branch"], "main")

    def test_detached_head_has_no_branch(self):
        self.assertEqual(sl.parse_status("## HEAD (no branch)\n")["branch"], "")

    def test_each_line_counts_once(self):
        g = sl.parse_status("## main\nMM a\n?? b\n D c\nR  d -> e\n")
        self.assertEqual((g["changed"], g["conflict"]), (4, 0))

    def test_unmerged_pairs_count_as_conflicts(self):
        g = sl.parse_status("## main\nUU a\nAU b\nUD c\nAA d\nDD e\nM  f\n")
        self.assertEqual((g["changed"], g["conflict"]), (1, 5))


class Badge(StatusLineTest):
    def test_dirty_tree_shows_the_count_in_yellow(self):
        (self.repo / "a.txt").write_text("changed\n")
        git(self.repo, "add", "a.txt")
        (self.repo / "a.txt").write_text("changed again\n")
        (self.repo / "new.txt").write_text("n\n")
        self.assertEqual(self.render(cwd=str(self.repo)),
                         self.dir_part(self.repo) + SEP + self.branch_part("main", paint("33", f"{ICON['dirty']} 2")))

    def test_conflicts_show_in_red_over_the_dirty_count(self):
        git(self.repo, "checkout", "-q", "-b", "other")
        (self.repo / "a.txt").write_text("other\n")
        git(self.repo, "commit", "-q", "-am", "other")
        git(self.repo, "checkout", "-q", "main")
        (self.repo / "a.txt").write_text("main\n")
        git(self.repo, "commit", "-q", "-am", "main")
        subprocess.run(["git", "-C", str(self.repo), "merge", "-q", "other"], capture_output=True)
        (self.repo / "new.txt").write_text("n\n")
        self.assertEqual(self.render(cwd=str(self.repo)),
                         self.dir_part(self.repo) + SEP + self.branch_part("main",
                                                                           paint("31", f"{ICON['conflict']} 1")))

    def test_badges(self):
        self.assertEqual(sl.git_badge(None), "")
        self.assertEqual(sl.git_badge({"changed": 0, "conflict": 0}), self.clean())


class ModelAndContext(StatusLineTest):
    def line(self, **payload):
        return sl.render(json.dumps({"cwd": str(self.plain), **payload}))[len(self.dir_part(self.plain) + SEP):]

    def test_model_and_effort_share_a_segment(self):
        self.assertEqual(self.line(model={"display_name": "Opus 5"}, effort={"level": "high"}),
                         paint("33", f"{ICON['model']} Opus 5") + paint("90", f" {ICON['effort']} high"))

    def test_model_alone(self):
        self.assertEqual(self.line(model={"display_name": "Opus 5"}), paint("33", f"{ICON['model']} Opus 5"))

    def test_effort_alone_has_no_leading_gap(self):
        self.assertEqual(self.line(effort={"level": "xhigh"}), paint("90", f"{ICON['effort']} xhigh"))

    def test_context_colour_follows_the_thresholds(self):
        for pct, colour, shown in ((59.9, "32", 60), (60, "33", 60), (79.9, "33", 80), (80, "31", 80)):
            with self.subTest(pct=pct):
                self.assertEqual(self.line(context_window={"used_percentage": pct}),
                                 paint(colour, f"{ICON['context']} {shown}%"))

    def test_context_is_clamped(self):
        self.assertEqual(self.line(context_window={"used_percentage": -5}), paint("32", f"{ICON['context']} 0%"))
        self.assertEqual(self.line(context_window={"used_percentage": 150}), paint("31", f"{ICON['context']} 100%"))

    def test_context_rounds_half_up(self):
        self.assertEqual(self.line(context_window={"used_percentage": 42.5}), paint("32", f"{ICON['context']} 43%"))
        self.assertEqual(self.line(context_window={"used_percentage": 41.5}), paint("32", f"{ICON['context']} 42%"))

    def test_a_context_that_is_not_a_number_is_omitted(self):
        for value in ("43", None, True):
            with self.subTest(value=value):
                out = sl.render(json.dumps({"cwd": str(self.plain), "context_window": {"used_percentage": value}}))
                self.assertEqual(out, self.dir_part(self.plain))

    def test_segments_keep_their_order_and_unused_fields_are_ignored(self):
        out = self.render(workspace={"current_dir": str(self.repo), "repo": {"owner": "acme", "name": "web"}},
                          model={"display_name": "M"}, context_window={"used_percentage": 10},
                          session_name="s", vim={"mode": "INSERT"}, pr={"number": 7}, cost={"total_cost_usd": 1})
        self.assertEqual(out, SEP.join([self.dir_part(self.repo), paint("34", f"{ICON['repo']} acme/web"),
                                        self.branch_part("main", self.clean()), paint("33", f"{ICON['model']} M"),
                                        paint("32", f"{ICON['context']} 10%")]))


class Stdin(unittest.TestCase):
    """The deadline: render on EOF or after DEADLINE seconds, whichever comes first."""

    def pipe(self):
        r, w = os.pipe()
        reader = os.fdopen(r, "rb")
        self.addCleanup(reader.close)
        return reader, w

    def test_eof_returns_at_once(self):
        reader, w = self.pipe()
        os.write(w, b'{"cwd": "x"}')
        os.close(w)
        start = time.monotonic()
        self.assertEqual(sl.read_payload(reader, 5), '{"cwd": "x"}')
        self.assertLess(time.monotonic() - start, 1)

    def test_an_open_pipe_returns_what_arrived_at_the_deadline(self):
        reader, w = self.pipe()
        # Closed after 5 s at the latest, so a reader that waits for EOF fails this case instead of hanging the suite.
        # The reader's thread holds the read end's lock until EOF, so the write end closes before the read end.
        closed = []

        def close():
            if not closed:
                closed.append(True)
                os.close(w)

        closer = threading.Timer(5, close)
        closer.start()
        self.addCleanup(close)
        self.addCleanup(closer.cancel)
        os.write(w, b'{"cwd": "x"}')
        start = time.monotonic()
        self.assertEqual(sl.read_payload(reader, 0.3), '{"cwd": "x"}')
        self.assertLess(time.monotonic() - start, 1.5)

    def test_a_stdin_that_never_closes_exits_within_the_deadline(self):
        folder = os.path.realpath(tempfile.mkdtemp(prefix="statusline-test-"))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        p = subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.addCleanup(p.stdin.close)
        p.stdin.write(json.dumps({"cwd": folder}).encode())
        p.stdin.flush()
        start = time.monotonic()
        try:
            # wait, not communicate: communicate would close stdin, which is the EOF this case withholds.
            code = p.wait(timeout=sl.DEADLINE + 3)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            self.fail("the status line waited for EOF past its deadline")
        finally:
            out = p.stdout.read()
            p.stdout.close()
        self.assertGreaterEqual(time.monotonic() - start, sl.DEADLINE - 0.5)
        self.assertEqual(code, 0)
        self.assertEqual(out.decode("utf-8"), sl.render(json.dumps({"cwd": folder})))

    def test_the_line_has_no_trailing_newline_and_exits_zero(self):
        r = subprocess.run([sys.executable, str(SCRIPT)], input=b"{}", capture_output=True, timeout=10)
        self.assertEqual(r.returncode, 0)
        self.assertFalse(r.stdout.endswith(b"\n"))
        self.assertTrue(r.stdout.decode("utf-8").startswith(paint("36", ICON["dir"]).removesuffix("\x1b[0m")))


if __name__ == "__main__":
    unittest.main()
