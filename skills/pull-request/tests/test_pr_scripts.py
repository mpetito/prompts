"""get_pr_feedback.py and resolve_pr_thread.py against a faked gh: no GitHub access.

Ports the two PowerShell suites these scripts replaced one for one. Each script's run() is replaced by a gh
that answers only the calls it recognises; any other call fails the test, so the network is never reached.
"""
import contextlib
import importlib.util
import io
import json
import re
import subprocess
import sys
import unittest
import unittest.mock
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import run  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FEEDBACK = load("get_pr_feedback")
HEAD = "abc1234567" + "0" * 30
RESOLVE = load("resolve_pr_thread")

SUPPRESSED_BODY = """## Review
<details>
<summary>Comments suppressed due to low confidence (1)</summary>
src/export.py:41 - `until` is exclusive here but inclusive in the CLI help.
</details>"""


def thread_page(nodes, more):
    return {"data": {"repository": {"pullRequest": {"reviewThreads": {
        "pageInfo": {"hasNextPage": more, "endCursor": "c1"}, "nodes": nodes}}}}}


def thread(id, resolved, outdated):
    return {"id": id, "isResolved": resolved, "isOutdated": outdated, "path": "src/a.py", "line": 3,
            "comments": {"nodes": [{"fullDatabaseId": "4197153031", "author": {"login": "copilot-pull-request-reviewer", "__typename": "Bot"},
                                    "body": "Check this.", "url": "u"}]}}


class FakeGh:
    """Stands in for gh; records each call as its arguments joined by spaces. scenario picks the call that fails or the data returned."""

    def __init__(self, scenario="", comments=(), check_runs=(), copilot_commit=HEAD, extra_reviews=()):
        self.scenario, self.calls = scenario, []
        self.comments, self.check_runs, self.copilot_commit = list(comments), list(check_runs), copilot_commit
        self.extra_reviews = list(extra_reviews)

    def __call__(self, args):
        if args[0] != "gh":
            raise AssertionError(f"unexpected command: {args}")
        call = " ".join(args[1:])
        self.calls.append(call)
        ok = lambda out: subprocess.CompletedProcess(args, 0, out, "")
        failed = subprocess.CompletedProcess(args, 1, "", "HTTP 502")
        if call == "repo view --json nameWithOwner -q .nameWithOwner":
            return subprocess.CompletedProcess(args, 1, "no git remotes", "") if self.scenario == "no-repo" \
                else ok("example/repo\n")
        if call == "pr view --json number -q .number":
            return ok("123\n")
        if re.match(r"api graphql -f query=mutation.*addPullRequestReviewThreadReply", call, re.S):
            return failed if self.scenario == "reply" else ok(
                '{"data":{"addPullRequestReviewThreadReply":{"comment":{"url":"https://example.test/c1"}}}}')
        if re.match(r"api graphql -f query=mutation.*resolveReviewThread", call, re.S):
            return failed if self.scenario == "resolve" else ok(
                '{"data":{"resolveReviewThread":{"thread":{"isResolved":true}}}}')
        if call.startswith("api graphql "):
            if self.scenario == "threads-fail":
                return failed
            if self.scenario == "body-only":
                return ok(json.dumps([thread_page([], False)]))
            return ok(json.dumps([thread_page([thread("PRRT_open", False, True), thread("PRRT_done", True, False)], True),
                                  thread_page([thread("PRRT_page2", False, False)], False)]))
        if call == "api repos/example/repo/pulls/123 -q .head.sha":
            return ok(HEAD + "\n")
        if call == "api repos/example/repo/issues/123/comments --paginate --slurp":
            return failed if self.scenario == "comments-fail" else ok(json.dumps([self.comments]))
        if call == f"api repos/example/repo/commits/{HEAD}/check-runs --paginate --slurp":
            return ok(json.dumps([{"total_count": len(self.check_runs), "check_runs": self.check_runs}]))
        if call.startswith("api repos/example/repo/pulls/123/reviews "):
            if self.scenario == "reviews-fail":
                return failed
            copilot = {"id": 100, "user": {"login": "copilot-pull-request-reviewer[bot]"}, "state": "COMMENTED",
                       "commit_id": self.copilot_commit, "html_url": "https://example.test/r100", "body": SUPPRESSED_BODY}
            human = {"id": 101, "user": {"login": "human"}, "state": "COMMENTED", "commit_id": "def456",
                     "html_url": "https://example.test/r101", "body": "Looks fine."}
            return ok(json.dumps([[copilot] if self.copilot_commit else [], [human, *self.extra_reviews]]))
        raise AssertionError(f"Unexpected gh call (network refused): {call}")


def call(module, gh, *argv):
    """module.main(argv) as run.entry runs it, with gh faked: (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with unittest.mock.patch.object(module, "run", gh), contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        try:
            code = module.main(list(argv))
        except run.Fail as e:
            print(e, file=sys.stderr)
            code = 1
    return code, out.getvalue(), err.getvalue()


class GetPrFeedback(unittest.TestCase):
    """The feedback suite: paginated threads and reviews, suppressed bodies, body-only feedback, defaults, three
    failure paths."""

    @classmethod
    def setUpClass(cls):
        cls.gh = FakeGh("populated")
        code, out, err = call(FEEDBACK, cls.gh, "--pr", "123", "--repo", "example/repo")
        assert code == 0, err
        cls.result = json.loads(out)
        cls.thread_call = next(c for c in cls.gh.calls if c.startswith("api graphql "))

    def test_keeps_unresolved_threads_from_every_page_and_drops_resolved_ones(self):
        self.assertEqual([t["threadId"] for t in self.result["threads"]], ["PRRT_open", "PRRT_page2"])

    def test_names_the_repository_and_pull_request(self):
        self.assertEqual((self.result["repo"], self.result["pr"]), ("example/repo", 123))
        self.assertFalse([c for c in self.gh.calls if c.startswith(("pr view", "repo view"))],
                         "--pr and --repo must be used as given, not looked up")

    def test_carries_is_outdated_path_and_line(self):
        t = self.result["threads"][0]
        self.assertEqual((t["isOutdated"], t["path"], t["line"]), (True, "src/a.py", 3))

    def test_carries_the_comment_full_database_id_as_a_string_for_rest_replies(self):
        self.assertEqual(self.result["threads"][0]["comments"][0]["id"], "4197153031")

    def test_carries_each_comment(self):
        c = self.result["threads"][0]["comments"][0]
        self.assertEqual((c["author"], c["body"], c["url"]), ("copilot-pull-request-reviewer[bot]", "Check this.", "u"))

    def test_keeps_reviews_from_every_page(self):
        self.assertEqual(len(self.result["reviews"]), 2)

    def test_keeps_the_suppressed_section_verbatim(self):
        self.assertEqual(self.result["reviews"][0]["body"], SUPPRESSED_BODY)

    def test_keeps_review_id_author_and_state(self):
        r = self.result["reviews"][0]
        self.assertEqual((r["id"], r["author"], r["state"]), (100, "copilot-pull-request-reviewer[bot]", "COMMENTED"))

    def test_keeps_review_provenance(self):
        r = self.result["reviews"][0]
        self.assertEqual((r["commitId"], r["url"]), (HEAD, "https://example.test/r100"))

    def test_the_thread_query_is_pageable(self):
        for pattern in (r"\$endCursor: String", r"after: \$endCursor", r"pageInfo \{ hasNextPage endCursor \}"):
            self.assertRegex(self.thread_call, pattern)

    def test_the_thread_query_requests_each_field(self):
        for field in ("isResolved", "isOutdated", "path", "line", "fullDatabaseId", "author { login __typename }", "body", "url"):
            with self.subTest(field=field):
                self.assertRegex(self.thread_call, rf"[{{\s]{re.escape(field)}[\s}}]")

    def test_the_thread_query_names_the_repository_and_pull_request(self):
        for pattern in (r"owner=example(\s|$)", r"name=repo(\s|$)", r"pr=123(\s|$)"):
            self.assertRegex(self.thread_call, pattern)

    def test_threads_are_fetched_with_paginate_slurp(self):
        self.assertEqual(len([c for c in self.gh.calls if c.startswith("api graphql --paginate --slurp ")]), 1)

    def test_reviews_are_fetched_with_paginate_slurp(self):
        self.assertEqual(len([c for c in self.gh.calls if re.search(r"/reviews --paginate --slurp$", c)]), 1)

    def test_no_threads_serialize_as_an_empty_array_and_body_only_feedback_stays_visible(self):
        code, out, _ = call(FEEDBACK, FakeGh("body-only"), "--pr", "123", "--repo", "example/repo")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["threads"], [], "No threads must serialize as an empty array.")
        self.assertEqual(len(json.loads(out)["reviews"]), 2, "Body-only feedback must stay visible with zero threads.")

    def expect_failure(self, scenario, pattern, *argv):
        code, out, err = call(FEEDBACK, FakeGh(scenario), *argv)
        self.assertEqual((code, out), (1, ""), f"Scenario {scenario} must fail, not report no feedback.")
        self.assertIn(pattern, err)

    def test_a_failed_thread_fetch_fails(self):
        self.expect_failure("threads-fail", "Could not collect review threads", "--pr", "123", "--repo", "example/repo")

    def test_a_failed_review_fetch_fails(self):
        self.expect_failure("reviews-fail", "Could not collect review bodies", "--pr", "123", "--repo", "example/repo")

    def test_a_failed_comment_fetch_fails(self):
        self.expect_failure("comments-fail", "Could not collect comments", "--pr", "123", "--repo", "example/repo")

    def test_an_unresolvable_repository_fails(self):
        self.expect_failure("no-repo", "Could not resolve the repository")

    def test_defaults_to_the_current_repository_and_branch_pull_request(self):
        gh = FakeGh("populated")
        code, out, _ = call(FEEDBACK, gh)
        self.assertEqual(code, 0)
        self.assertIn("pr view --json number -q .number", gh.calls)
        result = json.loads(out)
        self.assertEqual((result["repo"], result["pr"], len(result["threads"])), ("example/repo", 123, 2))


def comment(author, body):
    return {"id": 7, "user": {"login": author}, "created_at": "2026-10-15T17:00:00Z",
            "html_url": "https://example.test/c7", "body": body}


def codex_summary(head, status, author="chatgpt-codex-connector[bot]"):
    state = {"headSha": head, "status": status, "mergeGateEnabled": False}
    return comment(author, f"<!-- codex-pull-request-review-summary -->\n<!-- codex-security-review:v1 "
                           f"{json.dumps(state)} -->\n## Codex Review Summary")


def claude_run(status, text):
    return {"name": "Claude Code Review", "status": status, "app": {"slug": "claude"}, "output": {"text": text}}


class AutomatedReviewers(unittest.TestCase):
    """Whether Copilot, Codex and Claude each reviewed the head, from a review on it or their own clean signal."""

    def reviewers(self, **gh):
        code, out, err = call(FEEDBACK, FakeGh("populated", **gh), "--pr", "123", "--repo", "example/repo")
        self.assertEqual(code, 0, err)
        return json.loads(out)["automatedReviewers"]

    def test_a_review_on_the_head_is_a_reviewed_head(self):
        self.assertEqual(self.reviewers()["copilot"], {"seen": True, "reviewedHead": True})

    def test_a_review_on_an_earlier_commit_is_seen_but_not_the_head(self):
        self.assertEqual(self.reviewers(copilot_commit="def456")["copilot"], {"seen": True, "reviewedHead": False})

    def test_codex_reports_the_head_in_its_summary_header(self):
        self.assertEqual(self.reviewers(comments=[codex_summary(HEAD, "completed")])["codex"],
                         {"seen": True, "reviewedHead": True})

    def test_a_running_codex_review_overrides_its_review_on_the_head(self):
        codex = {"id": 102, "user": {"login": "chatgpt-codex-connector[bot]"}, "state": "COMMENTED",
                 "commit_id": HEAD, "html_url": "u", "body": "**Reviewed commit:** `abc1234567`"}
        self.assertEqual(self.reviewers(comments=[codex_summary(HEAD, "running")], extra_reviews=[codex])["codex"],
                         {"seen": True, "reviewedHead": False})
        self.assertEqual(self.reviewers(extra_reviews=[codex])["codex"], {"seen": True, "reviewedHead": True})

    def test_a_codex_summary_of_another_commit_is_not_the_head(self):
        self.assertEqual(self.reviewers(comments=[codex_summary("def4567890", "completed")])["codex"],
                         {"seen": True, "reviewedHead": False})

    def test_only_codex_can_report_a_head_in_a_summary(self):
        quoted = codex_summary(HEAD, "completed", author="human")
        self.assertEqual(self.reviewers(comments=[quoted])["codex"], {"seen": False, "reviewedHead": False})

    def test_a_comment_without_an_author_is_skipped(self):
        ghost = dict(codex_summary(HEAD, "completed"), user=None)
        self.assertEqual(self.reviewers(comments=[ghost])["codex"], {"seen": False, "reviewedHead": False})

    def test_claude_reports_a_head_with_its_finished_check_run(self):
        done = claude_run("completed", 'Found 1 issue.\n<!-- bughunter-severity: {"normal":1,"nit":0} -->')
        self.assertEqual(self.reviewers(check_runs=[done])["claude"], {"seen": True, "reviewedHead": True})

    def test_a_running_or_failed_claude_check_is_seen_but_not_reviewed(self):
        for run in (claude_run("in_progress", ""), claude_run("completed", "Code review timed out.")):
            with self.subTest(run=run):
                self.assertEqual(self.reviewers(check_runs=[run])["claude"], {"seen": True, "reviewedHead": False})

    def test_only_the_claude_apps_check_run_counts(self):
        marker = '<!-- bughunter-severity: {"normal":0} -->'
        for run in (dict(claude_run("completed", marker), name="ci"),
                    dict(claude_run("completed", marker), app={"slug": "github-actions"})):
            with self.subTest(run=run):
                self.assertEqual(self.reviewers(check_runs=[run])["claude"], {"seen": False, "reviewedHead": False})

    def test_a_person_named_like_a_reviewer_is_not_that_reviewer(self):
        spoof = codex_summary(HEAD, "completed", author="chatgpt-codex-connector")
        self.assertEqual(self.reviewers(comments=[spoof, comment("claude", "LGTM")]),
                         {"copilot": {"seen": True, "reviewedHead": True},
                          "codex": {"seen": False, "reviewedHead": False},
                          "claude": {"seen": False, "reviewedHead": False}})

    def test_a_thread_comment_alone_makes_a_reviewer_seen(self):
        self.assertEqual(self.reviewers(copilot_commit=None)["copilot"], {"seen": True, "reviewedHead": False})
        self.assertEqual(self.reviewers()["claude"], {"seen": False, "reviewedHead": False})


class ResolvePrThread(unittest.TestCase):
    """The thread suite: reply then resolve, one output line, no resolve after a failed reply."""

    def resolve(self, scenario=""):
        self.gh = FakeGh(scenario)
        return call(RESOLVE, self.gh, "--thread-id", "PRRT_x", "--body", "Fixed in 4be91c2.")

    def test_prints_one_line_after_two_calls_reply_first(self):
        code, out, _ = self.resolve()
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ["resolved PRRT_x https://example.test/c1"],
                         "Must print exactly one fixed-format line.")
        self.assertEqual(len(self.gh.calls), 2, "Must make exactly two calls.")
        reply, resolve = self.gh.calls
        for pattern in ("addPullRequestReviewThreadReply", "id=PRRT_x", r"body=Fixed in 4be91c2\."):
            self.assertRegex(reply, pattern, "Must reply first, on the thread, with the body.")
        for pattern in ("resolveReviewThread", "id=PRRT_x"):
            self.assertRegex(resolve, pattern, "Must resolve second.")
        self.assertRegex(reply, r"addPullRequestReviewThreadReply\(input: \{pullRequestReviewThreadId: \$id, "
                                r"body: \$body\}\)", "The reply must pass the thread id and body as its input.")
        self.assertRegex(resolve, r"resolveReviewThread\(input: \{threadId: \$id\}\)",
                         "The resolve must pass the thread id as its input.")

    def test_never_resolves_after_a_failed_reply(self):
        code, _, err = self.resolve("reply")
        self.assertEqual(code, 1)
        self.assertIn("left open", err, "A failed reply must fail.")
        self.assertEqual(len(self.gh.calls), 1, "A failed reply must never be followed by a resolve.")

    def test_a_failed_resolve_fails_and_names_the_posted_reply(self):
        code, _, err = self.resolve("resolve")
        self.assertEqual(code, 1)
        self.assertIn("resolving it failed", err)
        self.assertIn("example.test/c1", err)


class Abbreviations(unittest.TestCase):
    """An abbreviated option is a usage error, so a transcript the graders read names every option in full."""

    def test_an_abbreviated_option_is_refused_before_any_call(self):
        for module, argv in ((RESOLVE, ["--thread", "PRRT_x", "--body", "b"]),
                             (FEEDBACK, ["--p", "123", "--repo", "example/repo"])):
            with self.subTest(argv=argv):
                gh = FakeGh()
                code, _, _ = call(module, gh, *argv)
                self.assertEqual((code, gh.calls), (1, []))


class Usage(unittest.TestCase):
    """Each entry point run as a process: a usage error exits 1."""

    def test_usage_errors_exit_1(self):
        for script, argv in (("resolve_pr_thread.py", ["--thread-id", "PRRT_x"]),
                             ("get_pr_feedback.py", ["--pr", "not-a-number"])):
            with self.subTest(script=script, argv=argv):
                r = subprocess.run([sys.executable, str(SCRIPTS / script), *argv], capture_output=True, text=True,
                                   timeout=30)
                self.assertEqual(r.returncode, 1)
                self.assertIn("usage:", r.stderr)


if __name__ == "__main__":
    unittest.main()
