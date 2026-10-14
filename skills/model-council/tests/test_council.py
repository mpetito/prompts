"""Tests for the council scripts. No model is called: codex_member.py spawns through run.run, which a test replaces
with a fake codex, a Python script started through the real run.run, so timeouts and tree kills are real.
Run: python3 -m unittest discover -s skills/model-council/tests -t skills/model-council
"""
import contextlib
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import codex_member  # noqa: E402
import run  # noqa: E402
import tally  # noqa: E402

REAL_RUN = run.run
ANSWER = "stance: initial\ndisposition: defect\naction: x\ndecisive: a.ts:1\n"
# MOCK_CODEX picks what the fake does; it writes the answer file named by --output-last-message, as codex does.
FAKE_CODEX = r"""
import os, subprocess, sys, time
args = sys.argv[1:]
out = args[args.index("--output-last-message") + 1]
mode = os.environ.get("MOCK_CODEX", "ok")
answer = %r
def write(text):
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
if mode == "ok":
    print('{"type":"thread.started","thread_id":"t-123"}')
    write("Reasoning here.\nstance: initial\ndisposition: defect\naction: add the tenant id to the cache key\n")
elif mode == "twothreads":
    print('{"type":"thread.started","thread_id":"t-123"}')
    print('{"type":"thread.started","thread_id":"t-456"}')
    write("Reasoning here.\nstance: initial\ndisposition: defect\naction: add the tenant id to the cache key\n")
elif mode == "quoted":
    write("stance: initial | agree | revise | hold\ndisposition: <one of>\n...\n"
          "stance: hold\ndisposition: false-positive\naction: no change\n")
elif mode == "prose":
    write("I think it is fine.\n")
elif mode == "fail":
    sys.exit(3)
elif mode == "signal":
    import signal
    os.kill(os.getpid(), signal.SIGTERM)
elif mode == "writefail":
    write(answer)
    sys.exit(3)
elif mode == "slow":
    write(answer)
    time.sleep(5)
elif mode == "grandchild":
    late = f"import time; time.sleep(3); open({out!r}, 'w').write({answer!r})"
    subprocess.Popen([sys.executable, "-c", late])
    time.sleep(30)
""" % ANSWER


def output(main, argv):
    """Call a script's main(argv) in-process: (exit code, stdout, stderr), each stream without its final newline."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(a) for a in argv])
    return code, out.getvalue().removesuffix("\n"), err.getvalue().removesuffix("\n")


def pair(argv, a, b):
    """True when b directly follows a somewhere in argv."""
    return any(argv[i:i + 2] == [a, b] for i in range(len(argv) - 1))


class CouncilTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="council-test-")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        for d in ("bin", "repo", "out"):
            (self.tmp / d).mkdir()
        (self.tmp / "prompt.md").write_text("packet\n", encoding="utf-8")
        fake = self.tmp / "fake_codex.py"
        fake.write_text(FAKE_CODEX, encoding="utf-8")
        # A codex on PATH for the script's own check; run.run is faked, so it never runs.
        stub = self.tmp / "bin" / ("codex.cmd" if os.name == "nt" else "codex")
        stub.write_text("exit 9\n")
        stub.chmod(0o755)
        env = unittest.mock.patch.dict(os.environ, {"PATH": f"{self.tmp / 'bin'}{os.pathsep}{os.environ['PATH']}"})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("MOCK_CODEX", None)
        self.argv, self.cwd, self.timeout_s = [], None, None
        self.out, self.log = self.tmp / "out" / "a.md", self.tmp / "out" / "a.log"

        def fake_run(args, **kw):
            self.assertEqual(args[0], "codex")
            self.argv, self.cwd, self.timeout_s = list(args[1:]), kw["cwd"], kw["timeout"]
            return REAL_RUN([sys.executable, str(fake), *args[1:]], **kw)

        patch = unittest.mock.patch.object(run, "run", fake_run)
        patch.start()
        self.addCleanup(patch.stop)

    def member(self, *args, mode="ok", out=None):
        os.environ["MOCK_CODEX"] = mode
        return output(codex_member.main, [self.tmp / "repo", self.tmp / "prompt.md", out or self.tmp / "out" / "a.md",
                                          *args])

    def line(self, *args, mode="ok"):
        return self.member(*args, mode=mode)[1]

    def done(self, session, stance, disposition):
        """The MEMBER done line for model m1 writing the default answer file."""
        return (f"MEMBER done member=codex model=m1 session={session} stance={stance} disposition={disposition} "
                f"out={self.out}")

    def timeout(self, after):
        return f"MEMBER timeout member=codex model=m1 session=none after {after}; log {self.log}"

    def failed(self, code):
        return f"MEMBER failed member=codex model=m1 session=none exit={code}; log {self.log}"

    def malformed(self):
        return f"MEMBER malformed member=codex model=m1 session=none out={self.out} (no answer block)"


class MemberCommand(CouncilTest):
    def test_a_fresh_run_is_read_only_inside_the_repository(self):
        line = self.line("--model", "m1", "--effort", "high")
        self.assertEqual(line, self.done("t-123", "initial", "defect"))
        self.assertTrue(pair(self.argv, "--sandbox", "read-only"), "fresh run lacks --sandbox read-only")
        self.assertTrue(pair(self.argv, "-c", 'sandbox_mode="read-only"'), "fresh run lacks the read-only override")
        self.assertTrue(pair(self.argv, "-c", 'model_reasoning_effort="high"'), "fresh run dropped the effort")
        self.assertIn("--ignore-user-config", self.argv, "fresh run loaded the user's Codex config")
        self.assertEqual(self.cwd, str(self.tmp / "repo"), "fresh run did not start inside the repository")

    def test_a_resumed_run_is_read_only_inside_the_repository(self):
        line = self.line("--model", "m1", "--resume", "r-999")
        self.assertEqual(self.argv[:3], ["exec", "resume", "r-999"], "resume did not call codex exec resume <id>")
        self.assertTrue(pair(self.argv, "-c", 'sandbox_mode="read-only"'), "resume dropped the read-only sandbox")
        self.assertTrue(pair(self.argv, "--model", "m1"), "resume dropped the model")
        self.line("--model", "m1", "--resume", "r-999", "--effort", "high")
        self.assertTrue(pair(self.argv, "-c", 'model_reasoning_effort="high"'), "resume dropped the effort")
        self.line("--model", "m1", "--resume", "r-999")
        self.assertIn("--ignore-user-config", self.argv, "resume loaded the user's Codex config")
        self.assertEqual(self.cwd, str(self.tmp / "repo"), "resume did not run inside the repository")
        self.assertEqual(line, self.done("r-999", "initial", "defect"), "resume line did not report the resumed session")

    def test_no_run_widens_the_sandbox(self):
        for kind, args in (("fresh", ()), ("resume", ("--resume", "t-123"))):
            self.line("--model", "m1", *args)
            with self.subTest(kind):
                self.assertNotRegex(" ".join(self.argv),
                                    "workspace-write|danger-full-access|dangerously|--ephemeral|network_access")

    def test_the_windows_sandbox_mode_is_passed_on_windows_only(self):
        for windows in (True, False):
            for args in ((), ("--resume", "t-123")):
                with unittest.mock.patch.object(codex_member, "WINDOWS", windows), self.subTest(windows, args=args):
                    self.line("--model", "m1", *args)
                    self.assertEqual(pair(self.argv, "-c", 'windows.sandbox="unelevated"'), windows)


class MemberOutcomes(CouncilTest):
    def test_reads_the_last_answer_block(self):
        self.assertEqual(self.line("--model", "m1", mode="quoted"), self.done("none", "hold", "false-positive"))

    def test_an_answer_without_a_block_is_malformed(self):
        self.assertEqual(self.line("--model", "m1", mode="prose"), self.malformed())

    def test_a_failing_codex_is_reported(self):
        self.assertEqual(self.line("--model", "m1", mode="fail"), self.failed(3))

    def test_a_slow_codex_is_a_timeout(self):
        self.assertEqual(self.line("--model", "m1", "--timeout", "1s", mode="slow"), self.timeout("1s"))

    def test_needs_a_codex_model(self):
        self.assertEqual(self.member()[0], 1, "ran without --model")
        for m in ("opus", "Sonnet", "haiku", "fable", "claude-x1"):
            with self.subTest(m):
                self.assertEqual(self.member("--model", m)[0], 1, f"accepted the Anthropic model {m} for Codex")

    def test_no_answer_file_survives_a_failure_or_a_timeout(self):
        self.assertEqual(self.line("--model", "m1", mode="writefail"), self.failed(3))
        self.assertFalse(self.out.exists(), "a failed run left its answer file")
        self.assertEqual(self.line("--model", "m1", "--timeout", "1s", mode="slow"), self.timeout("1s"))
        self.assertFalse(self.out.exists(), "a timed-out run left an answer file")

    def test_a_stale_answer_is_never_read(self):
        self.out.write_text(ANSWER, encoding="utf-8")
        self.assertEqual(self.line("--model", "m1", mode="silent"), self.malformed(),
                         "a stale answer file was read as this run's answer")
        self.assertFalse(self.out.exists(), "a stale answer file survived the run")

    def test_a_timeout_kills_what_codex_started(self):
        # The fake starts a grandchild that writes the answer after the timeout: killing only codex would let it.
        # The fake itself sleeps 30 s, so a kill that misses it shows as a run that outlasts its timeout.
        start = time.monotonic()
        line = self.line("--model", "m1", "--timeout", "1s", mode="grandchild")
        self.assertLess(time.monotonic() - start, 10, "the timeout did not kill codex at once")
        self.assertEqual(line, self.timeout("1s"))
        time.sleep(4)
        self.assertFalse(self.out.exists(), "a grandchild wrote the answer after the timeout")

    def test_the_session_is_the_first_thread(self):
        self.assertEqual(self.line("--model", "m1", mode="twothreads"), self.done("t-123", "initial", "defect"))

    def test_a_codex_killed_by_a_signal_reports_128_plus_n(self):
        if os.name == "nt":
            self.skipTest("Windows has no signals: TerminateProcess gives a positive exit code")
        self.assertEqual(self.line("--model", "m1", mode="signal"), self.failed(128 + 15))

    def test_the_timeout_takes_timeout1_durations(self):
        for duration, secs in (("90", 90), ("90s", 90), ("2m", 120), ("1h", 3600), ("1d", 86400), ("1.5m", 90)):
            with self.subTest(duration):
                self.assertEqual(codex_member.seconds(duration), secs)
        self.line("--model", "m1")
        self.assertEqual(self.timeout_s, 1200, "the default timeout is not 20m")
        self.assertEqual(self.line("--model", "m1", "--timeout", "0"), self.done("t-123", "initial", "defect"))
        self.assertIsNone(self.timeout_s, "--timeout 0 is not 'no limit', as it is for timeout(1)")
        for bad in ("soon", "5x", "-1m", ""):
            with self.subTest(bad=bad):
                self.assertEqual(self.member("--model", "m1", "--timeout", bad),
                                 (1, "", f"--timeout takes a duration such as 90s, 20m or 1h; {codex_member.USAGE}"))

    def test_a_line_ends_only_at_a_newline(self):
        # grep splits at \n alone; a form feed or a Unicode line separator inside a value is not a new line.
        self.out.write_text("stance: initial\fdisposition: hold\ndisposition: defect\u2028stance: x\n",
                            encoding="utf-8")
        self.assertEqual((codex_member.field("stance", str(self.out)), codex_member.field("disposition", str(self.out))),
                         ("initial\fdisposition: hold", "defect\u2028stance: x"))

    def test_a_symlinked_path_is_refused(self):
        # Its target is neither removed nor written beside. On Windows a symlink needs Developer Mode or elevation.
        keep, links = self.tmp / "keep", self.tmp / "links"
        keep.mkdir()
        links.mkdir()
        for suffix in ("md", "log", "jsonl"):
            target = keep / f"target.{suffix}"
            target.write_text("keep\n", encoding="utf-8")
            for f in links.iterdir():
                f.unlink()
            os.symlink(target, links / f"a.{suffix}")
            with self.subTest(suffix):
                code = self.member("--model", "m1", mode="fail", out=links / "a.md")[0]
                self.assertEqual(code, 1, f"a symlinked .{suffix} path was not refused")
                self.assertEqual(target.read_text(encoding="utf-8"), "keep\n",
                                 f"the target of a symlinked .{suffix} path was changed or removed")
        self.assertEqual(sorted(f.name for f in keep.iterdir()), ["target.jsonl", "target.log", "target.md"],
                         "files were written beside a symlink target")


class Tally(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="council-tally-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def ans(self, name, stance, disposition, action):
        (self.tmp / name).write_text(f"Some reasoning.\nstance: {stance}\ndisposition: {disposition}\n"
                                     f"action: {action}\ndecisive: src/a.ts:1\ncrux: x\n", encoding="utf-8")

    def tally(self, k):
        return output(tally.main, [self.tmp / "a", self.tmp / "b", "--exchange", k])[1]

    @staticmethod
    def exchange(k, cap=2):
        return f"COUNCIL exchange next={k + 1} of {cap}; send each member the other's answer, unattributed"

    @staticmethod
    def consensus(k, disposition):
        return (f"COUNCIL consensus after-exchange={k} disposition={disposition}; "
                "verify the decisive citations before reporting it")

    @staticmethod
    def no_consensus(reason, k):
        return f"COUNCIL no-consensus reason={reason} after-exchange={k}; report each final position and its crux"

    def incomplete(self, member, reason):
        return f"COUNCIL incomplete member={self.tmp / member} reason={reason}"

    def test_blind_disagreement_goes_to_an_exchange(self):
        self.ans("a", "initial", "defect", "add the tenant id to the cache key")
        self.ans("b", "initial", "false-positive", "no change")
        self.assertEqual(self.tally(0), self.exchange(0))
        self.ans("b", "initial", "defect", "partition the cache per tenant")
        self.assertEqual(self.tally(0), self.exchange(0), "same disposition, different action")

    def test_the_council_stops(self):
        self.ans("a", "hold", "defect", "add the tenant id to the cache key")
        self.ans("b", "revise", "defect", "partition the cache per tenant")
        self.assertEqual(self.tally(2), self.no_consensus("round-cap", "2 of 2"))
        self.ans("a", "hold", "defect", "x")
        self.ans("b", "hold", "false-positive", "no change")
        self.assertEqual(self.tally(1), self.no_consensus("both-hold", 1))

    def test_identical_positions_are_consensus(self):
        self.ans("a", "agree", "defect", "add the tenant id  to the cache key")
        self.ans("b", "hold", "defect", "add the tenant id to the cache key")
        self.assertEqual(self.tally(1), self.consensus(1, "defect"))
        self.ans("a", "initial", "defect", "no change")
        self.ans("b", "initial", "defect", "no change")
        self.assertEqual(self.tally(0), self.consensus(0, "defect"), "identical blind positions")
        self.ans("a", "initial", "Defect", "x")
        self.ans("b", "initial", "defect", "x")
        self.assertEqual(self.tally(0), self.consensus(0, "defect"), "dispositions compared case-sensitively")

    def test_crossed_agreement_is_not_consensus(self):
        self.ans("a", "agree", "false-positive", "no change")
        self.ans("b", "agree", "defect", "add the tenant id to the cache key")
        self.assertEqual(self.tally(1), self.exchange(1))

    def test_an_answer_that_cannot_be_tallied_is_incomplete(self):
        self.ans("a", "initial", "defect", "x")
        (self.tmp / "b").write_text("", encoding="utf-8")
        self.assertEqual(self.tally(0), self.incomplete("b", "no-answer"))
        self.ans("b", "initial", "maybe", "x")
        self.assertEqual(self.tally(0), self.incomplete("b", "disposition 'maybe'"))
        (self.tmp / "b").write_text("stance: initial\ndisposition: defect\ndecisive: a.ts:1\n", encoding="utf-8")
        self.assertEqual(self.tally(0), self.incomplete("b", "no-action"))
        (self.tmp / "b").write_text("stance: initial\ndisposition: defect\naction: no change\ncrux: x\n",
                                    encoding="utf-8")
        self.assertEqual(self.tally(0), self.incomplete("b", "no-decisive-citation"))

    def test_a_disposition_is_one_word(self):
        # bash's word list accepted "defect improvement"; the disposition is exactly one of the listed values.
        self.ans("a", "initial", "defect", "x")
        self.ans("b", "initial", "defect improvement", "x")
        self.assertEqual(self.tally(0), self.incomplete("b", "disposition 'defect improvement'"))

    def test_a_line_ends_only_at_a_newline(self):
        self.assertEqual(tally.field("disposition", "disposition: defect\naction: x\u2028disposition: maybe\n"),
                         "defect")

    def test_a_stance_must_fit_the_round(self):
        self.ans("a", "agree", "defect", "x")
        self.ans("b", "agree", "defect", "x")
        self.assertEqual(self.tally(0), self.incomplete("a", "stance 'agree' in the blind round"),
                         "an exchange stance in the blind round")
        self.ans("a", "initial", "defect", "x")
        self.ans("b", "initial", "false-positive", "y")
        self.assertEqual(self.tally(1), self.incomplete("a", "stance 'initial'"), "a blind stance in an exchange")

    def test_the_same_action_needs_the_same_disposition(self):
        self.ans("a", "hold", "defect", "no change")
        self.ans("b", "hold", "false-positive", "no change")
        self.assertEqual(self.tally(1), self.no_consensus("both-hold", 1))
        self.ans("a", "revise", "defect", "no change")
        self.ans("b", "revise", "false-positive", "no change")
        self.assertEqual(self.tally(1), self.exchange(1))

    def test_a_members_own_block_decides_over_one_it_quotes(self):
        self.ans("a", "hold", "defect", "add the tenant id")
        self.ans("x", "revise", "false-positive", "no change")
        quoted, own = (self.tmp / "a").read_text(encoding="utf-8"), (self.tmp / "x").read_text(encoding="utf-8")
        (self.tmp / "b").write_text(f"They wrote:\n{quoted}\nMine:\n{own}", encoding="utf-8")
        self.ans("a", "revise", "false-positive", "no change")
        self.assertEqual(self.tally(1), self.consensus(1, "false-positive"), "the member's own block did not decide")
        self.ans("a", "hold", "defect", "add the tenant id")
        self.assertEqual(self.tally(1), self.exchange(1), "a quoted block was read instead")

    def test_the_round_cap_is_the_one_named_constant(self):
        self.assertEqual(tally.MAX_EXCHANGE_ROUNDS, 2)
        self.ans("a", "hold", "defect", "x")
        self.ans("b", "revise", "defect", "y")
        with unittest.mock.patch.object(tally, "MAX_EXCHANGE_ROUNDS", 3):
            self.assertEqual(self.tally(2), self.exchange(2, cap=3))


class Usage(unittest.TestCase):
    def test_a_usage_error_exits_1(self):
        cases = ((codex_member, ["repo"], codex_member.USAGE),
                 (tally, ["a", "b"], tally.USAGE),
                 (tally, ["a", "b", "--exchange", "one"], f"--exchange takes a round number; {tally.USAGE}"),
                 (tally, ["a", "b", "--exchange", "-1"], f"--exchange takes a round number; {tally.USAGE}"))
        for module, argv, message in cases:
            with self.subTest(module.__name__, argv=argv):
                r = subprocess.run([sys.executable, module.__file__, *argv], capture_output=True, text=True)
                self.assertEqual((r.returncode, r.stdout, r.stderr), (1, "", message + "\n"))


if __name__ == "__main__":
    unittest.main()
