"""lane.py, finish_lane.py, land.py, land_local.py and watch_gates.py: starting, retiring and landing a lane."""
import os
import re
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

from .support import SCRIPTS, OrchTest, call, check_run, lib, load, result


def git(cwd, *args):
    """Run git in cwd for a fixture; stdout stripped."""
    return subprocess.run(["git", "-C", str(cwd), *args], check=True, capture_output=True, text=True).stdout.strip()


# A matrix job's check name, as GitHub names it; a workflow on push and pull_request gives a head two runs of it.
MATRIX = "scripts (ubuntu-latest)"


def commit(cwd, files, message):
    for name, text in files.items():
        Path(cwd, name).write_text(text, encoding="utf-8")
    git(cwd, "add", ".")
    git(cwd, "commit", "-qm", message)


class Usage(unittest.TestCase):
    """Each entry point, run as a program with bad arguments, exits 1 with its usage on stderr."""

    def test_bad_arguments_exit_1_with_the_usage(self):
        for script in ("lane.py", "finish_lane.py", "land.py", "land_local.py", "watch_gates.py"):
            with self.subTest(script):
                r = subprocess.run([sys.executable, str(SCRIPTS / script)], capture_output=True, text=True)
                self.assertEqual(r.returncode, 1)
                self.assertIn(f"{script} <", r.stderr)


class Remote(OrchTest):
    """An origin with main (f.txt, g.txt), a seed clone that moves main, and a clone wt on branch feat, pushed."""

    def setUp(self):
        super().setUp()
        self.origin, self.seed, self.wt = self.tmp / "origin.git", self.tmp / "seed", self.tmp / "wt"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.seed)], check=True, capture_output=True)
        commit(self.seed, {"f.txt": "one\n", "g.txt": "base\n"}, "init")
        git(self.seed, "push", "-q", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.wt)], check=True, capture_output=True)
        git(self.wt, "checkout", "-qb", "feat")
        commit(self.wt, {"f.txt": "one\nfeat\n"}, "feat")
        git(self.wt, "push", "-q", "origin", "feat")
        self.gh.wt = self.wt
        self.slept = []

    def move_main(self, files, message):
        commit(self.seed, files, message)
        git(self.seed, "push", "-q", "origin", "main")


class Land(Remote):
    def setUp(self):
        super().setUp()
        self.land = load(SCRIPTS / "land.py")
        self.land.sleep = self.slept.append
        self.body = self.tmp / "body.md"
        self.body.write_text("body\n", encoding="utf-8")

    def run_land(self, *extra):
        return call(self.land, "7", self.wt, "--check", "ci", "--subject", "feat: x", "--body-file", self.body,
                    *extra)

    def test_refuses_bad_arguments(self):
        self.assertEqual(call(self.land)[0], 1)
        code, _, err = call(self.land, "7", self.wt, "--check")
        self.assertEqual(code, 1)
        self.assertIn("--check needs a value", err)
        self.assertEqual(self.run_land("--max-rounds", "0")[0], 1)
        code, _, err = call(self.land, "x", self.wt, "--check", "ci", "--subject", "s", "--body-file", self.body)
        self.assertEqual(code, 1)
        self.assertRegex(err, "^PR must be a number")
        code, _, err = self.run_land("extra")
        self.assertRegex(err, "^unknown option extra; usage: ")
        code, _, err = call(self.land, "7", self.wt, "--check", "ci", "--subject", "s", "--body-file", self.tmp / "no")
        self.assertRegex(err, "^usage: ")
        self.assertEqual(self.gh.log, [])

    def test_lands_a_clean_pr(self):
        code, out, _ = self.run_land()
        self.assertEqual(code, 0)
        self.assertRegex(out, r"^LANDED pr=7 head=[0-9a-f]{7}\n$")
        self.assertTrue(any(l.startswith(f"pr merge 7 --squash --match-head-commit {git(self.wt, 'rev-parse', 'HEAD')}")
                            for l in self.gh.log))
        self.assertFalse(any(l.startswith("pr comment") for l in self.gh.log))
        self.assertEqual(self.slept, [])

    def test_stops_on_a_failed_merge(self):
        self.gh.merge_fail = True
        self.assertRegex(self.run_land()[1], r"^STOPPED pr=7 merge failed")

    def test_stops_on_a_failed_check(self):
        self.gh.runs = [check_run("ci", "failure")]
        self.assertRegex(self.run_land()[1], r"^STOPPED pr=7 ci=failure")

    def test_lands_when_every_run_of_the_check_succeeds(self):
        self.gh.runs = [check_run(MATRIX, "success"), check_run(MATRIX, "success"),
                        check_run("scripts (windows-latest)", "failure")]
        self.assertRegex(self.run_land("--check", MATRIX)[1], r"^LANDED pr=7 ")

    def test_stops_on_one_failed_run_beside_a_passing_one(self):
        self.gh.runs = [check_run(MATRIX, "success"), check_run(MATRIX, "failure")]
        self.assertRegex(self.run_land("--check", MATRIX)[1], r"^STOPPED pr=7 scripts \(ubuntu-latest\)=failure on ")

    def test_stops_on_a_failed_run_listed_before_a_passing_one(self):
        self.gh.runs = [check_run(MATRIX, "failure"), check_run(MATRIX, "success")]
        self.assertRegex(self.run_land("--check", MATRIX)[1], r"^STOPPED pr=7 scripts \(ubuntu-latest\)=failure on ")

    def test_waits_while_the_check_has_no_run(self):
        self.gh.runs = [check_run("other", "success")]
        self.assertRegex(self.run_land("--check-minutes", "1")[1], r"^STOPPED pr=7 ci=none .* after up to 1 min")
        self.assertEqual(self.slept, [20] * 3)

    def test_waits_while_gh_cannot_read_the_check(self):
        self.gh.runs = None
        self.assertRegex(self.run_land("--check-minutes", "1")[1], r"^STOPPED pr=7 ci=none .* after up to 1 min")
        self.assertEqual(self.slept, [20] * 3)

    def test_merges_a_moved_base_and_records_the_proof(self):
        self.move_main({"g.txt": "base\nmore\n"}, "base2")
        self.assertRegex(self.run_land()[1], r"^LANDED pr=7")
        self.assertTrue(any(l.startswith("pr comment 7 ") for l in self.gh.log))
        self.assertEqual(git(self.wt, "rev-parse", "HEAD^2"), git(self.seed, "rev-parse", "HEAD"))
        self.assertEqual(git(self.origin, "rev-parse", "feat"), git(self.wt, "rev-parse", "HEAD"))

    def test_stops_on_a_conflicting_base(self):
        self.move_main({"f.txt": "one\nclash\n"}, "clash")
        self.assertRegex(self.run_land()[1], r"^STOPPED pr=7 merge of main conflicts in: f\.txt")
        self.assertEqual(git(self.wt, "status", "--porcelain"), "")

    def test_waits_for_a_running_check_up_to_its_minutes(self):
        self.gh.runs = [check_run("ci", None, "in_progress")]
        self.assertRegex(self.run_land("--check-minutes", "2")[1], r"^STOPPED pr=7 ci=running .* after up to 2 min")
        self.assertEqual(self.slept, [20] * 6)

    def test_waits_while_one_run_of_the_check_is_still_running(self):
        self.gh.runs = [check_run(MATRIX, "success"), check_run(MATRIX, None, "in_progress")]
        out = self.run_land("--check", MATRIX, "--check-minutes", "2")[1]
        self.assertRegex(out, r"^STOPPED pr=7 scripts \(ubuntu-latest\)=running .* after up to 2 min")
        self.assertEqual(self.slept, [20] * 6)

    def test_waits_while_a_run_listed_before_a_passing_one_is_running(self):
        self.gh.runs = [check_run(MATRIX, None, "in_progress"), check_run(MATRIX, "success")]
        out = self.run_land("--check", MATRIX, "--check-minutes", "1")[1]
        self.assertRegex(out, r"^STOPPED pr=7 scripts \(ubuntu-latest\)=running .* after up to 1 min")

    def test_waits_for_github_to_compute_the_merge_state(self):
        self.gh.merge_state = "UNKNOWN"
        self.assertRegex(self.run_land()[1], r"^STOPPED pr=7 unexpected state '[0-9a-f]{40} UNKNOWN'")
        self.assertEqual(self.slept, [10] * 12)

    def test_stops_on_a_blocked_state_and_after_its_rounds(self):
        self.gh.merge_state = "BLOCKED"
        self.assertRegex(self.run_land()[1], r"^STOPPED pr=7 state=BLOCKED on [0-9a-f]{7}; mergeState=BLOCKED")
        self.gh.merge_state = "BEHIND"
        code, out, err = self.run_land("--max-rounds", "2")
        self.assertRegex(out, r"^STOPPED pr=7 after 2 rounds; ")
        self.assertEqual(err.count("main moved"), 2)

    def land_with_git_answering(self, answer):
        """run_land after main moved, with each git call for which answer(args) returns a result answered by it. The
        STOPPED or LANDED line, and whether anything was pushed or posted."""
        self.move_main({"g.txt": "base\nmore\n"}, "base2")
        pushed, inner, calls = git(self.origin, "rev-parse", "feat"), lib.run, []

        def run(args, **kw):
            calls.append(args)
            return (answer(args[3:]) if args[0] == "git" else None) or inner(args, **kw)

        with unittest.mock.patch.object(lib, "run", run):
            out = self.run_land()[1]
        pushed = git(self.origin, "rev-parse", "feat") != pushed or any("push" in a for a in calls)
        posted = any(l.startswith(("pr comment", "pr merge")) for l in self.gh.log)
        return out, pushed or posted

    def test_stops_before_pushing_a_merge_off_the_previous_head(self):
        out, sent = self.land_with_git_answering(
            lambda a: result(a, out="0" * 40 + "\n") if a[0] == "rev-parse" and a[-1].endswith("^1") else None)
        self.assertRegex(out, r"^STOPPED pr=7 first parent of [0-9a-f]{7} is not the previous head")
        self.assertFalse(sent)

    def test_stops_before_pushing_a_second_parent_off_the_base(self):
        out, sent = self.land_with_git_answering(
            lambda a: result(a, 1) if a[:2] == ["merge-base", "--is-ancestor"] and a[2].endswith("^2") else None)
        self.assertRegex(out, r"^STOPPED pr=7 second parent of [0-9a-f]{7} is not on main")
        self.assertFalse(sent)

    def test_stops_before_pushing_a_merge_the_remerge_diff_finds_changed(self):
        out, sent = self.land_with_git_answering(
            lambda a: result(a, out="g.txt\nf.txt\ng.txt\n") if "--remerge-diff" in a else None)
        self.assertRegex(out, r"^STOPPED pr=7 remerge-diff touches: f\.txt g\.txt \(needs a delta review\)")
        self.assertFalse(sent)


class WatchGates(Remote):
    def setUp(self):
        super().setUp()
        self.watch = load(SCRIPTS / "watch_gates.py")
        self.watch.sleep = self.slept.append
        self.sha = git(self.wt, "rev-parse", "HEAD")
        self.reviewed, self.feedback_calls = {"copilot": True, "codex": True, "claude": False}, []

        self.feedback_head = self.sha

        def feedback(repo, pr):
            self.feedback_calls.append((repo, pr))
            return {"head": self.feedback_head, "threads": [{}, {}], "automatedReviewers": {
                n: {"seen": True, "reviewedHead": done} for n, done in self.reviewed.items()}}
        self.watch.feedback = feedback

    def test_refuses_bad_arguments(self):
        self.assertEqual(call(self.watch, "7", "abc1234")[0], 1)
        self.assertEqual(call(self.watch)[0], 1)
        self.assertEqual(call(self.watch, "7", self.sha, "--minutes", "0")[0], 1)
        self.assertRegex(call(self.watch, "x", self.sha)[2], "^PR must be a number")
        self.assertRegex(call(self.watch, "7", self.sha, "extra")[2], "^unknown option extra; usage: ")
        self.assertEqual(self.gh.log, [])
        self.assertRegex(call(self.watch, "7", self.sha, "--reviewers", "gemini")[2],
                         "^unknown reviewer gemini; known: copilot,codex,claude")

    def test_reports_passing_gates(self):
        code, out, _ = call(self.watch, "7", self.sha, "--check", "ci", "--reviewers", "copilot,codex",
                            "--minutes", "1")
        self.assertEqual(out, f"GATES pr=7 head={self.sha[:7]} check=success reviewers=copilot:reviewed,"
                              "codex:reviewed unresolved_threads=2\n")
        self.assertEqual(self.slept, [])
        self.assertEqual(self.feedback_calls[0], ("o/r", "7"))

    def test_reports_success_when_every_run_of_the_check_succeeds(self):
        self.gh.runs = [check_run(MATRIX, "success"), check_run(MATRIX, "success")]
        self.assertRegex(call(self.watch, "7", self.sha, "--check", MATRIX, "--minutes", "1")[1], r" check=success ")
        self.assertEqual(self.slept, [])

    def test_reports_one_failed_run_beside_a_passing_one(self):
        self.gh.runs = [check_run(MATRIX, "failure"), check_run(MATRIX, "success"), check_run(MATRIX, "failure")]
        self.assertRegex(call(self.watch, "7", self.sha, "--check", MATRIX, "--minutes", "1")[1], r" check=failure ")

    def test_names_each_other_conclusion_once_in_order(self):
        self.gh.runs = [check_run(MATRIX, "skipped"), check_run(MATRIX, "success"), check_run(MATRIX, "failure"),
                        check_run(MATRIX, "skipped")]
        self.assertRegex(call(self.watch, "7", self.sha, "--check", MATRIX, "--minutes", "1")[1],
                         r" check=failure,skipped ")

    def test_does_not_settle_while_one_run_of_the_check_is_still_running(self):
        self.gh.runs = [check_run(MATRIX, "success"), check_run(MATRIX, None, "queued")]
        self.assertRegex(call(self.watch, "7", self.sha, "--check", MATRIX, "--minutes", "1")[1], r" check=timeout ")
        self.assertEqual(self.slept, [15] * 4)

    def test_waits_for_each_named_reviewer(self):
        out = call(self.watch, "7", self.sha, "--reviewers", "copilot,claude", "--minutes", "1")[1]
        self.assertRegex(out, r" reviewers=copilot:reviewed,claude:timeout ")
        self.assertEqual(self.slept, [15] * 4)
        self.assertEqual(len(self.feedback_calls), 2, "reviewers once a minute, plus the final thread count")

    def test_reports_a_moved_head(self):
        self.gh.pr_head = "0123456789012345678901234567890123456789"
        out = call(self.watch, "7", self.sha, "--check", "ci", "--minutes", "1")[1]
        self.assertEqual(out, f"MOVED pr=7 head={self.sha[:7]} now=0123456\n")

    def test_times_out_after_four_polls_a_minute(self):
        self.gh.runs, self.reviewed["copilot"] = [check_run("ci", None, "in_progress")], False
        out = call(self.watch, "7", self.sha, "--check", "ci", "--reviewers", "copilot", "--minutes", "2")[1]
        self.assertRegex(out, r"check=timeout reviewers=copilot:timeout ")
        self.assertEqual(self.slept, [15] * 8)
        out = call(self.watch, "7", self.sha)[1]
        self.assertRegex(out, r"check=n/a reviewers=n/a unresolved_threads=2")

    def test_a_reviewer_finishing_in_the_last_minute_is_reviewed(self):
        real = self.watch.feedback
        reads = []

        def late(repo, pr):
            reads.append(pr)
            self.reviewed["claude"] = len(reads) > 1
            return real(repo, pr)
        self.watch.feedback = late
        out = call(self.watch, "7", self.sha, "--reviewers", "claude", "--minutes", "1")[1]
        self.assertRegex(out, r" reviewers=claude:reviewed ")

    def test_feedback_for_another_head_is_a_moved_head(self):
        self.feedback_head = "0123456789012345678901234567890123456789"
        out = call(self.watch, "7", self.sha, "--reviewers", "copilot", "--minutes", "1")[1]
        self.assertEqual(out, f"MOVED pr=7 head={self.sha[:7]} now=0123456\n")
        out = call(self.watch, "7", self.sha, "--minutes", "1")[1]
        self.assertEqual(out, f"MOVED pr=7 head={self.sha[:7]} now=0123456\n")

    def test_a_moved_head_in_the_loop_is_moved_even_when_the_last_read_fails(self):
        real, reads = self.watch.feedback, []
        self.feedback_head = "0123456789012345678901234567890123456789"

        def then_fail(repo, pr):
            reads.append(pr)
            return real(repo, pr) if len(reads) == 1 else None
        self.watch.feedback = then_fail
        out = call(self.watch, "7", self.sha, "--reviewers", "copilot", "--minutes", "1")[1]
        self.assertEqual(out, f"MOVED pr=7 head={self.sha[:7]} now=0123456\n")

    def test_reads_feedback_from_the_sibling_pull_request_skill(self):
        self.assertTrue(self.watch.FEEDBACK.is_file(), self.watch.FEEDBACK)

    def test_an_unreadable_feedback_is_an_unknown_thread_count(self):
        self.watch.feedback = lambda repo, pr: None
        self.assertRegex(call(self.watch, "7", self.sha, "--minutes", "1")[1], r"unresolved_threads=\?\n$")


class Lane(OrchTest):
    def setUp(self):
        super().setUp()
        self.lane = load(SCRIPTS / "lane.py")
        self.wt = self.tmp / "lanewt"
        self.wt.mkdir()
        self.brief = self.tmp / "lane-brief.md"
        self.brief.write_text("Build the API.\n", encoding="utf-8")
        self.herdr.agents = [{"name": "lb", "agent_status": "idle", "pane_id": "w7:p1"}]

    def start(self, build, lane, *opts):
        return call(self.lane, build, lane, self.wt, self.brief, *opts)

    def test_starts_a_codex_lane_beside_its_thread(self):
        home = os.environ["ORCHESTRATION_HOME"]
        code, out, _ = self.start("lb", "api", "--kind", "codex", "--model", "m1")
        self.assertEqual(code, 0)
        self.assertRegex(out, r"^LANE lb-api pane=w7:p[0-9]+ kind=codex\n$")
        self.assertIn(f"tab create --workspace w7 --cwd {self.wt} --label api --no-focus "
                      f"--env ORCHESTRATION_HOME={home}", self.herdr.log)
        self.assertEqual(self.herdr.started["lb-api"],
                         ["--approve-for-me", "--add-dir", os.path.join(home, "mail", "lb"), "--model", "m1"])
        self.assertTrue(os.path.isdir(os.path.join(home, "mail", "lb")))
        self.assertIn(f"agent prompt lb-api Read {lib.native(self.brief)} and follow it.", self.herdr.log)

    def test_network_opens_codex_sandbox(self):
        self.start("lb", "net", "--kind", "codex", "--model", "m1", "--network")
        self.assertIn("sandbox_workspace_write.network_access=true", self.herdr.started["lb-net"])

    def test_starts_a_claude_lane(self):
        self.assertRegex(self.start("lb", "ui", "--kind", "claude", "--model", "opus")[1], r"^LANE lb-ui ")
        self.assertEqual(self.herdr.started["lb-ui"], ["--agent", "lane", "--model", "opus"])

    def test_a_claude_lane_gets_the_main_checkouts_local_settings(self):
        main = self.repo(self.tmp / "app")
        wt = self.tmp / "app-lane"
        subprocess.run(["git", "-C", str(main), "worktree", "add", "-q", "-b", "lane", str(wt)], check=True)
        self.wt = wt
        self.start("lb", "plain", "--kind", "claude", "--model", "opus")
        self.assertEqual(self.herdr.started["lb-plain"], ["--agent", "lane", "--model", "opus"])
        local = main / ".claude" / "settings.local.json"
        local.parent.mkdir()
        local.write_text('{"enabledMcpjsonServers": ["db"]}\n', encoding="utf-8")
        self.start("lb", "mcp", "--kind", "claude", "--model", "opus")
        self.assertEqual(self.herdr.started["lb-mcp"],
                         ["--agent", "lane", "--model", "opus", "--settings", lib.native(str(local))])

    def test_refusals_are_failed_lines(self):
        for opts, pattern in [(("lb", "x", "--kind", "claude"), r"^FAILED --model is required"),
                              (("lb", "x", "--kind", "gemini", "--model", "g"), r"^FAILED --kind takes claude or codex"),
                              (("lb", "x" * 30, "--kind", "claude", "--model", "opus"),
                               r"^FAILED lane agent name .* must match"),
                              (("nob", "x", "--kind", "claude", "--model", "opus"), r"^FAILED no live thread named nob")]:
            with self.subTest(pattern):
                code, out, _ = self.start(*opts)
                self.assertEqual(code, 1)
                self.assertRegex(out, pattern)

    def test_refuses_an_extra_argument(self):
        self.assertEqual(self.start("lb", "x", "extra", "--kind", "claude", "--model", "o")[0], 1)
        self.assertEqual(self.herdr.log, [])

    def test_needs_a_worktree_a_brief_and_a_tab(self):
        code, out, _ = call(self.lane, "lb", "x", self.tmp / "nowt", self.brief, "--kind", "claude", "--model", "o")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"^FAILED no lane worktree at ")
        (self.tmp / "empty.md").write_text("", encoding="utf-8")
        out = call(self.lane, "lb", "x", self.wt, self.tmp / "empty.md", "--kind", "claude", "--model", "o")[1]
        self.assertRegex(out, r"^FAILED no brief at ")
        self.herdr.mode = "notab"
        out = self.start("lb", "x", "--kind", "claude", "--model", "o")[1]
        self.assertEqual(out, "FAILED herdr tab create: workspace_not_found: no such workspace\n")

    def test_a_reply_of_another_shape_is_a_failed_line_with_the_reply(self):
        call_herdr = type(self.herdr).__call__
        for verb, reply in ((["agent", "get"], "not json"), (["agent", "get"], '{"result": {}}'),
                            (["tab", "create"], '{"result": {"tab": {}}}')):
            with self.subTest(verb=verb, reply=reply), unittest.mock.patch.object(
                    type(self.herdr), "__call__",
                    lambda fake, args: result(args, out=reply + "\n") if args[:2] == verb else call_herdr(fake, args)):
                code, out, _ = self.start("lb", "x", "--kind", "claude", "--model", "o")
                self.assertEqual(code, 1)
                self.assertRegex(out, "^FAILED ")
                self.assertIn(reply, out)

    def test_a_startup_prompt_blocks_without_a_pointer_prompt(self):
        self.herdr.mode = "notready"
        code, out, _ = self.start("lb", "tr", "--kind", "codex", "--model", "m1")
        self.assertEqual((code, out), (0, "BLOCKED lb-tr waiting on a startup prompt: answer it in workspace lb, tab tr\n"))
        self.assertFalse(any(l.startswith("agent prompt") for l in self.herdr.log))

    def test_a_failed_start_closes_its_tab(self):
        self.herdr.mode = "startfail"
        code, out, _ = self.start("lb", "sf", "--kind", "codex", "--model", "m1")
        self.assertEqual((code, out), (1, "FAILED herdr agent start: agent_start_failed: the agent exited\n"))
        self.assertTrue(any(re.fullmatch(r"pane close w7:p[0-9]+", l) for l in self.herdr.log))


class FinishLane(OrchTest):
    def setUp(self):
        super().setUp()
        self.finish = load(SCRIPTS / "finish_lane.py")
        self.seed = self.repo(self.tmp / "seed", commit=False)
        commit(self.seed, {"f.txt": "one\n", "g.txt": "base\n"}, "init")
        # Ignored output: eval runs are evidence, node_modules is not.
        with open(self.seed / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
            f.write(".eval-runs/\nnode_modules/\n")

    def worktree(self, name, branch):
        git(self.seed, "worktree", "add", "-q", str(self.tmp / name), "-b", branch)
        return self.tmp / name

    def test_refuses_without_arguments(self):
        self.assertEqual(call(self.finish)[0], 1)

    def test_archives_evidence_then_removes_the_worktree_and_branch(self):
        lane = self.worktree("lane", "lane-x")
        (lane / ".orchestration" / "tmp").mkdir(parents=True)
        (lane / ".orchestration" / "tmp" / "note.txt").write_text("evidence\n", encoding="utf-8")
        (lane / ".eval-runs" / "r1").mkdir(parents=True)
        (lane / ".eval-runs" / "r1" / "out.md").write_text("run\n", encoding="utf-8")
        (lane / "node_modules" / "x").mkdir(parents=True)
        (lane / "node_modules" / "x" / "i.js").write_text("dep\n", encoding="utf-8")
        archive = self.tmp / "archive"
        with open(lane / "g.txt", "a", encoding="utf-8") as f:
            f.write("dirty\n")
        code, _, err = call(self.finish, lane, archive)
        self.assertEqual(code, 1)
        self.assertTrue(lane.is_dir(), "removed a worktree with uncommitted changes")
        self.assertIn("g.txt", err)
        git(lane, "checkout", "-q", "g.txt")
        code, out, _ = call(self.finish, lane, archive)
        self.assertEqual(code, 0)
        self.assertTrue((archive / "note.txt").is_file())
        self.assertTrue((archive / "ignored" / ".eval-runs" / "r1" / "out.md").is_file())
        self.assertFalse((archive / "ignored" / "node_modules").exists())
        self.assertIn("archived ignored .eval-runs/", out)
        self.assertFalse(lane.exists())
        self.assertIn("deleted branch lane-x", out)

    def test_refuses_an_extra_argument(self):
        code, _, err = call(self.finish, self.tmp, self.tmp / "a", "extra")
        self.assertEqual(code, 1)
        self.assertRegex(err, "^unknown option extra; usage: ")

    def test_refuses_a_missing_worktree_and_a_folder_outside_git(self):
        code, _, err = call(self.finish, self.tmp / "nowt", self.tmp / "a")
        self.assertEqual(code, 1)
        self.assertRegex(err, "^no worktree at ")
        (self.tmp / "plain").mkdir()
        code, _, err = call(self.finish, self.tmp / "plain", self.tmp / "a")
        self.assertEqual(code, 1)
        self.assertRegex(err, "^not a git worktree: ")

    def test_keep_branch_and_a_custom_scratch(self):
        lane = self.worktree("lane2", "lane-y")
        (lane / "scratch").mkdir()
        (lane / "scratch" / "n.txt").write_text("n\n", encoding="utf-8")
        code, out, _ = call(self.finish, lane, self.tmp / "archive2", "--scratch", "scratch", "--keep-branch")
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "archive2" / "n.txt").is_file())
        self.assertFalse(lane.exists())
        self.assertNotIn("deleted branch", out)
        self.assertEqual(git(self.seed, "branch", "--list", "lane-y"), "lane-y")

    def test_refuses_while_an_agent_runs_in_a_lane_named_by_a_relative_path(self):
        lane = self.worktree("lane4", "lane-w")
        os.environ["HERDR_ENV"] = "1"
        self.herdr.agents = [{"name": "t-l4", "agent_status": "idle", "cwd": str(lane / "src")},
                             {"name": "t-l40", "agent_status": "idle", "cwd": str(self.tmp / "lane40")}]
        code, _, err = call(self.finish, "lane4", self.tmp / "archive4", cwd=self.tmp)
        self.assertEqual((code, err), (1, "refusing: agent(s) still run in lane4: t-l4\n"))
        self.herdr.agents = self.herdr.agents[1:]
        # From a deeper folder, so the relative path means nothing from the main checkout git runs in.
        (self.tmp / "x" / "y").mkdir(parents=True)
        self.assertEqual(call(self.finish, "../../lane4", self.tmp / "archive4", cwd=self.tmp / "x" / "y")[0], 0)
        self.assertFalse(lane.exists(), "took an agent in a sibling worktree for one in the lane")

    def test_refuses_an_agent_cwd_however_herdr_spells_it(self):
        lane = self.worktree("lane5", "lane-v")
        os.environ["HERDR_ENV"] = "1"
        spellings = {"native": str(lane), "forward slashes": lib.native(lane), "trailing separator": str(lane) + os.sep,
                     "relative": os.path.join("lane5", "src")}
        try:
            (self.tmp / "link").symlink_to(lane, target_is_directory=True)
            spellings["symlinked"] = str(self.tmp / "link" / "src")
        except OSError:
            pass  # Windows without the symlink privilege
        for how, cwd in spellings.items():
            with self.subTest(how):
                self.herdr.agents = [{"name": "t-l5", "agent_status": "idle", "cwd": cwd}]
                code, _, err = call(self.finish, lane, self.tmp / "archive5", cwd=self.tmp)
                self.assertEqual(code, 1)
                self.assertIn("t-l5", err)
        self.assertTrue(lane.is_dir())
        self.herdr.mode = "down"
        self.assertEqual(call(self.finish, lane, self.tmp / "archive5")[0], 0, "a herdr that can't list blocks nothing")

    def test_outside_herdr_nothing_is_asked(self):
        lane = self.worktree("lane6", "lane-u")
        self.herdr.agents = [{"name": "t-l6", "agent_status": "idle", "cwd": str(lane)}]
        self.assertEqual(call(self.finish, lane, self.tmp / "archive6")[0], 0)
        self.assertEqual(self.herdr.log, [])

    def test_removes_nothing_when_git_cannot_list_ignored_files(self):
        lane = self.worktree("lane3", "lane-z")
        index = Path(git(lane, "rev-parse", "--absolute-git-dir"), "index")
        index.write_text("corrupt", encoding="utf-8")
        code, _, err = call(self.finish, lane, self.tmp / "archive3")
        self.assertEqual(code, 1)
        self.assertRegex(err, r"git status failed in .*nothing was removed")
        self.assertTrue(lane.is_dir())


class LandLocal(OrchTest):
    """A repository app, its coordination worktree on orchestration/c landing locally, a pull-request build's
    coordination worktree on orchestration/a, and a lane lane/l1 off orchestration/c with one commit."""

    def setUp(self):
        super().setUp()
        self.ll = load(SCRIPTS / "land_local.py")
        app = self.repo(self.tmp / "app")
        commit(app, {"README.md": "app\n"}, "readme")
        with open(app / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
            f.write(".orchestration/\n")
        self.wtc, self.wta = self.tmp / "app-orch-c", self.tmp / "app-orch-a"
        for wt, branch, landing in ((self.wtc, "orchestration/c", "local"), (self.wta, "orchestration/a", "pr")):
            git(app, "worktree", "add", "-q", str(wt), "-b", branch)
            (wt / ".orchestration").mkdir()
            (wt / ".orchestration" / "thread.md").write_text(f"BUILD: x\nLANDING: {landing}\n", encoding="utf-8")
        lane = self.tmp / "app-wt-l1"
        git(app, "worktree", "add", "-q", str(lane), "-b", "lane/l1", "orchestration/c")
        commit(lane, {"L1.md": "l1\n"}, "l1")
        self.l1 = git(app, "rev-parse", "lane/l1")

    def land(self, *argv, cwd=None):
        return call(self.ll, *argv, cwd=cwd or self.wtc)

    def test_refuses_an_unapproved_head(self):
        self.assertRegex(self.land("lane/l1", "HEAD~1", "--check", "true")[1],
                         f"^STOPPED lane=lane/l1 head is {self.l1[:7]}, not the approved")

    def test_undoes_a_merge_whose_check_fails(self):
        before = git(self.wtc, "rev-parse", "HEAD")
        out = self.land("lane/l1", self.l1, "--check", "echo err >&2; echo out; exit 3")[1]
        self.assertRegex(out, r"^STOPPED lane=lane/l1 check failed on merge .*, merge undone")
        self.assertEqual(git(self.wtc, "rev-parse", "HEAD"), before)
        log = self.wtc / ".orchestration" / "results" / "land-lane-l1.log"
        self.assertEqual(log.read_text(encoding="utf-8"), "err\nout\n")

    def test_the_log_fills_while_the_check_runs(self):
        check = "echo started; grep -q started .orchestration/results/land-lane-l1.log"
        self.assertRegex(self.land("lane/l1", self.l1, "--check", check)[1], r"^LANDED lane=lane/l1 ")

    def test_lands_the_approved_head_with_a_no_ff_merge(self):
        # From a folder below the worktree's root: the check still runs at the root.
        code, out, _ = self.land("lane/l1", self.l1, "--check", "test -f L1.md", "--subject", "feat: l1",
                                 cwd=self.wtc / ".orchestration")
        self.assertEqual(code, 0)
        self.assertRegex(out, rf"^LANDED lane=lane/l1 head={self.l1[:7]} merge=[0-9a-f]{{7}}\n$")
        self.assertEqual(git(self.wtc, "rev-parse", "HEAD^2"), self.l1)
        self.assertEqual(git(self.wtc, "log", "-1", "--format=%s"), "Merge lane/l1: feat: l1")
        self.assertIn("is already on orchestration/c", self.land("lane/l1", self.l1, "--check", "true")[1])

    def test_refuses_a_missing_branch_a_pr_build_and_a_missing_check(self):
        self.assertRegex(self.land("lane/none", "abc", "--check", "true")[1], r"^STOPPED lane=lane/none no branch")
        self.assertIn("LANDING is not local", self.land("lane/l1", self.l1, "--check", "true", cwd=self.wta)[1])
        self.assertEqual(self.land("lane/l1", self.l1)[0], 1)
        self.assertRegex(self.land("lane/l1", self.l1, "x", "--check", "true")[2], "^unknown option x; usage: ")
        code, _, err = self.land("lane/l1", self.l1, "--check", "true", cwd=self.tmp)
        self.assertEqual(code, 1)
        self.assertIn("from the coordination worktree", err)

    def test_refuses_an_unready_coordination_worktree(self):
        self.assertRegex(self.land("lane/l1", "nope", "--check", "true")[1], r"^STOPPED lane=lane/l1 no commit nope")
        (self.wtc / "README.md").write_text("edit\n", encoding="utf-8")
        self.assertRegex(self.land("lane/l1", self.l1, "--check", "true")[1], r"^STOPPED lane=lane/l1 uncommitted ")
        git(self.wtc, "checkout", "-q", "README.md")
        git(self.wtc, "checkout", "-q", "-b", "other")
        self.assertRegex(self.land("lane/l1", self.l1, "--check", "true")[1], r"is on other, not orchestration/")
        git(self.wtc, "checkout", "-q", "--detach")
        self.assertRegex(self.land("lane/l1", self.l1, "--check", "true")[1], r"has a detached HEAD")
        self.assertEqual(git(self.wtc, "rev-parse", "HEAD"), git(self.wtc, "rev-parse", "orchestration/c"))

    def test_stops_on_a_conflict_and_aborts_the_merge(self):
        commit(self.tmp / "app-wt-l1", {"README.md": "lane\n"}, "lane readme")
        commit(self.wtc, {"README.md": "coord\n"}, "coord readme")
        l1 = git(self.wtc, "rev-parse", "lane/l1")
        out = self.land("lane/l1", l1, "--check", "true")[1]
        self.assertRegex(out, r"^STOPPED lane=lane/l1 merging into orchestration/c conflicts in: README\.md \(rebase")
        self.assertEqual(git(self.wtc, "status", "--porcelain", "--untracked-files=no"), "")

    def test_stops_before_merging_without_a_bash(self):
        before = git(self.wtc, "rev-parse", "HEAD")
        self.ll.find_bash = lambda: None
        code, out, _ = self.land("lane/l1", self.l1, "--check", "true")
        self.assertEqual((code, out), (0, "STOPPED lane=lane/l1 no bash for the check command\n"))
        self.assertEqual(git(self.wtc, "rev-parse", "HEAD"), before)


class FindBash(OrchTest):
    """Which bash runs land_local.py's check, on Windows and elsewhere, from a fake install tree."""

    def setUp(self):
        super().setUp()
        self.find = load(SCRIPTS / "land_local.py").find_bash
        self.git_cmd = self.tmp / "Git" / "cmd"
        self.git_bash = self.tmp / "Git" / "bin" / "bash.exe"
        self.wsl = self.tmp / "System32"
        for exe in (self.git_cmd / "git", self.git_cmd / "git.exe", self.git_bash,
                    self.wsl / "bash", self.wsl / "bash.exe"):
            exe.parent.mkdir(parents=True, exist_ok=True)
            exe.write_text("", encoding="utf-8")
            exe.chmod(0o755)

    def path(self, *folders):
        return os.pathsep.join(str(f) for f in folders)

    def test_the_variable_wins_on_windows_when_it_names_a_file(self):
        other = self.tmp / "Other" / "bash.exe"
        other.parent.mkdir()
        other.write_text("", encoding="utf-8")
        env = {"CLAUDE_CODE_GIT_BASH_PATH": str(other), "PATH": self.path(self.wsl, self.git_cmd)}
        self.assertEqual(self.find("nt", env), str(other))
        for stale in (str(self.tmp / "Gone" / "bash.exe"), str(other.parent)):
            env["CLAUDE_CODE_GIT_BASH_PATH"] = stale
            self.assertEqual(self.find("nt", env), str(self.git_bash))

    def test_windows_finds_git_bash_beside_git_and_skips_wsl_on_path(self):
        self.assertEqual(self.find("nt", {"PATH": self.path(self.git_cmd)}), str(self.git_bash))
        self.assertEqual(self.find("nt", {"PATH": self.path(self.wsl, self.git_cmd)}), str(self.git_bash))

    def test_windows_without_git_bash_finds_none(self):
        self.assertIsNone(self.find("nt", {"PATH": self.path(self.wsl)}))
        self.git_bash.unlink()
        self.assertIsNone(self.find("nt", {"PATH": self.path(self.wsl, self.git_cmd)}))

    @unittest.skipIf(os.name == "nt", "a bash on PATH is refused on Windows")
    def test_elsewhere_bash_is_on_path(self):
        self.assertEqual(self.find("posix", {"PATH": self.path(self.wsl)}), str(self.wsl / "bash"))
        self.assertIsNone(self.find("posix", {"PATH": self.path(self.git_cmd)}))


if __name__ == "__main__":
    unittest.main()
