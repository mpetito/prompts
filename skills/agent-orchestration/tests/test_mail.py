"""mail.py: send, read and wait, with herdr faked and wait's clock and sleep replaced."""
import itertools
import os
import re
import subprocess
import sys
import time
import unittest.mock

from .support import OrchTest, ROOT, SCRIPTS, call, load

MAIL = SCRIPTS / "mail.py"


class MailTest(OrchTest):
    def setUp(self):
        super().setUp()
        self.mail = load(MAIL)
        self.box = self.tmp / "orch" / "mail"
        # Separate senders differ by pid; in one process, a strictly rising clock keeps names apart and in order
        # where time_ns is coarse (Windows before Python 3.13).
        ticks = itertools.count(time.time_ns(), 1_000_000)
        patcher = unittest.mock.patch.object(self.mail.time, "time_ns", lambda: next(ticks))
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_mail(self, *argv, stdin=""):
        return call(self.mail, *argv, stdin=stdin)

    def out(self, *argv, stdin=""):
        """stdout of a call that must succeed."""
        code, out, err = self.run_mail(*argv, stdin=stdin)
        self.assertEqual(code, 0, err)
        return out

    def refused(self, *argv, stdin=""):
        code, out, _ = self.run_mail(*argv, stdin=stdin)
        return code == 1 and out == ""

    def wait(self, *argv):
        return self.out("wait", *argv, "--timeout", "0").strip()

    def agents(self, *pairs):
        """The agents the fake herdr lists, as "name state" strings."""
        self.herdr.agents = [dict(zip(("name", "agent_status"), p.split())) for p in pairs]

    def age(self, address, seconds=600):
        """Backdate every unread message in a box, as touch -d '-10 minutes' did."""
        then = time.time() - seconds
        for p in (self.box / address / "new").iterdir():
            os.utime(p, (then, then))


class Send(MailTest):
    def test_send_reports_and_delivers_from_text_file_and_stdin(self):
        self.assertRegex(self.out("send", "b1/main", "--from", "b1/thread", "STATUS: working - one"),
                         r"^SENT b1/main \S+\.md\n$")
        m2 = self.tmp / "m2.md"
        m2.write_text("STATUS: done - two\n", encoding="utf-8")
        self.out("send", "b1/main", "--from", "b1/thread", "--file", m2)
        self.out("send", "b1/main", "--from", "b1/lane-a", stdin="STATUS: working - three\n")
        messages = sorted((self.box / "b1/main/new").iterdir())
        self.assertEqual(len(messages), 3)
        for p in messages:
            self.assertRegex(p.read_text(encoding="utf-8"),
                             r"^From: b1/\S+\nDate: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ\n\nSTATUS: [^\n]+\n$")
        self.assertEqual(list((self.box / "b1/main/tmp").iterdir()), [], "a half-written message was left in tmp/")

    def test_refusals(self):
        self.assertTrue(self.refused("send", "b1/main", "no sender"), "sent without --from")
        self.assertTrue(self.refused("send", "main", "--from", "b1/thread", "x"), "accepted an address without a build")
        self.assertTrue(self.refused("send", "b1/main", "--from", "b1/thread", "  "), "sent an empty message")
        self.assertTrue(self.refused("send", "b1/main", "--from", "b1/thread", stdin="\n"),
                        "sent an empty message from stdin")
        # A body on stdin too, so only the word count can refuse it.
        self.assertTrue(self.refused("send", "b1/main", "--from", "b1/thread", "STATUS:", "working", "-", "unquoted",
                                     stdin="STATUS: working - stdin\n"),
                        "sent an unquoted message, keeping only its last word")
        self.assertTrue(self.refused("send", "b1/main", "--from", "b1/thread", "--quite", "STATUS: done - typo"),
                        "accepted an unknown option")
        self.assertTrue(self.refused("send", "b1/main", "--from", "b1/thread", "--quite", stdin="STATUS: done - typo\n"),
                        "sent an unknown option as the message")
        self.assertFalse((self.box / "b1" / "main").exists(), "a refused send made a box")

    def test_delivery_is_a_rename_from_tmp_into_new(self):
        renames = []
        real = os.replace

        def logged(src, dst):
            renames.append((src, dst))
            real(src, dst)

        with unittest.mock.patch.object(self.mail.os, "replace", logged):
            self.out("send", "b9/main", "--from", "b9/thread", "STATUS: working - renamed")
        [(src, dst)] = renames
        self.assertEqual((src.parent, dst.parent), (self.box / "b9/main/tmp", self.box / "b9/main/new"))
        self.assertEqual(src.name, dst.name)

    def test_home_option_overrides_the_environment(self):
        other = self.tmp / "other"
        self.out("send", "b1/main", "--from", "b1/thread", "--home", other, "STATUS: working - elsewhere")
        self.assertEqual(len(list((other / "mail/b1/main/new").iterdir())), 1)
        self.assertFalse((self.box / "b1").exists())
        self.assertEqual(self.out("wait", "b1/main", "--home", other, "--timeout", "0"), "MAIL 1\n")
        self.assertIn("STATUS: working - elsewhere", self.out("read", "b1/main", "--home", other))

    def test_default_home_is_under_the_user_home(self):
        del os.environ["ORCHESTRATION_HOME"]
        self.out("send", "b1/main", "--from", "b1/thread", "x")
        self.assertEqual(len(list((self.home / ".orchestration/mail/b1/main/new").iterdir())), 1)


class Read(MailTest):
    def setUp(self):
        super().setUp()
        self.out("send", "b1/main", "--from", "b1/thread", "STATUS: working - one")
        self.out("send", "b1/main", "--from", "b1/thread", "STATUS: done - two")
        self.out("send", "b1/main", "--from", "b1/lane-a", stdin="STATUS: working - three\n")

    def test_wait_counts_then_read_prints_oldest_first_and_files(self):
        self.assertEqual(self.wait("b1/main"), "MAIL 3")
        out = self.out("read", "b1/main")
        self.assertEqual([l for l in out.splitlines() if l.startswith("STATUS")],
                         ["STATUS: working - one", "STATUS: done - two", "STATUS: working - three"])
        self.assertIn("From: b1/lane-a", out.splitlines())
        self.assertEqual(len(re.findall(r"^=== \S+\.md$", out, re.M)), 3)
        self.assertEqual(len(list((self.box / "b1/main/cur").iterdir())), 3)
        self.assertEqual(list((self.box / "b1/main/new").iterdir()), [])
        self.assertEqual(self.out("read", "b1/main"), "NO MAIL\n", "read printed old mail again")
        self.assertEqual(self.wait("b1/main"), "TIMEOUT", "wait woke with no mail")

    def test_quiet_mail_wakes_no_wait_and_the_next_read_prints_it(self):
        self.out("read", "b1/main")
        self.out("send", "b1/main", "--from", "b1/thread", "--quiet", "STATUS: working - quiet")
        self.assertEqual(self.wait("b1/main"), "TIMEOUT", "wait woke for a quiet message")
        self.assertIn("STATUS: working - quiet", self.out("read", "b1/main").splitlines())


class Watch(MailTest):
    def test_a_prompt_is_reported_once_and_again_after_work(self):
        self.agents("b1 working", "b2 blocked")
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2"), "BLOCKED b2")
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2"), "TIMEOUT", "the same prompt was reported twice")
        self.agents("b1 working", "b2 working")
        self.wait("m/main", "--watch", "b1,b2")
        self.agents("b1 working", "b2 blocked")
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2"), "BLOCKED b2", "missed a second prompt")

    def test_herdr_down_judges_nothing_and_a_leaver_is_gone_once(self):
        self.agents("b1 working", "b2 blocked")
        self.wait("m/main", "--watch", "b1,b2")
        self.herdr.mode = "down"
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2"), "TIMEOUT", "judged agents while herdr was down")
        self.herdr.mode = "garbled"
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2"), "TIMEOUT", "judged agents from output it can't read")
        self.herdr.mode = ""
        self.agents("b2 blocked")
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2"), "GONE b1")
        self.assertEqual(self.wait("m/main", "--watch", "b1,b2,b9"), "TIMEOUT",
                         "reported GONE twice, or for an agent it never saw")

    def test_an_idle_thread_with_old_mail_is_unread_once_per_stretch(self):
        self.agents("b3 idle")
        self.out("send", "b3/thread", "--from", "b3/lane-a", "--quiet", "STATUS: working - old and quiet")
        self.age("b3/thread")
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "TIMEOUT", "called old quiet mail unread")
        self.out("send", "b3/thread", "--from", "b3/main", "STEER: fresh")
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "TIMEOUT", "called fresh mail unread")
        self.age("b3/thread")
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "UNREAD b3 1")
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "TIMEOUT",
                         "reported the same unread stretch twice")
        self.agents("b3 working")
        self.wait("b3/main", "--watch", "b3=b3/thread")
        self.agents("b3 done")
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "UNREAD b3 1",
                         "missed a second unread stretch")

    def test_unread_starts_after_five_minutes_on_the_clock(self):
        self.agents("b3 idle")
        self.out("send", "b3/thread", "--from", "b3/main", "STEER: one")
        sent = time.time()
        self.mail.clock = lambda: sent + 4 * 60
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "TIMEOUT")
        self.mail.clock = lambda: sent + 6 * 60
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "UNREAD b3 1")

    def test_a_working_or_blocked_receiver_is_not_unread(self):
        self.out("send", "b3/thread", "--from", "b3/main", "STEER: one")
        self.age("b3/thread")
        self.agents("b3 working")
        self.assertEqual(self.wait("b3/main", "--watch", "b3=b3/thread"), "TIMEOUT")


class Waiting(MailTest):
    """wait polls every 2 s until its timeout, on a clock the test moves."""

    def setUp(self):
        super().setUp()
        self.now, self.pauses = 1_000_000.0, []
        self.mail.clock = lambda: self.now
        self.mail.sleep = self.pause
        self.on_pause = lambda: None

    def pause(self, seconds):
        self.pauses.append(seconds)
        self.now += seconds
        self.on_pause()

    def test_times_out_after_its_timeout(self):
        self.assertEqual(self.out("wait", "b1/main", "--timeout", "10"), "TIMEOUT\n")
        self.assertEqual(self.pauses, [2] * 5)

    def test_default_timeout_is_an_hour(self):
        self.assertEqual(self.out("wait", "b1/main"), "TIMEOUT\n")
        self.assertEqual(sum(self.pauses), 3600)

    def test_wakes_when_mail_arrives(self):
        self.on_pause = lambda: len(self.pauses) == 3 and self.out("send", "b1/main", "--from", "b1/thread", "hi")
        self.assertEqual(self.out("wait", "b1/main", "--timeout", "60"), "MAIL 1\n")
        self.assertEqual(len(self.pauses), 3)

    def test_wakes_when_a_watched_agent_blocks(self):
        self.agents("b1 working")
        self.on_pause = lambda: len(self.pauses) == 2 and self.agents("b1 blocked")
        self.assertEqual(self.out("wait", "m/main", "--watch", "b1", "--timeout", "60"), "BLOCKED b1\n")

    def test_refuses_a_bad_timeout(self):
        self.assertTrue(self.refused("wait", "b1/main", "--timeout", "soon"))


class Usage(MailTest):
    def test_bad_arguments(self):
        for argv in (["send"], ["read", "a/b", "c/d"], ["wait"], ["list", "b1/main"], ["read", "--home", "x"]):
            self.assertTrue(self.refused(*argv), argv)

    def test_command_line_usage_error(self):
        r = subprocess.run([sys.executable, str(MAIL), "nope", "b1/main"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        for line in self.mail.__doc__.splitlines()[2:8]:
            self.assertIn(line, r.stderr)


class Docs(unittest.TestCase):
    def test_protocol_names_the_wait_lines_mail_documents_and_prints(self):
        protocol = (ROOT / "references" / "protocol.md").read_text(encoding="utf-8")
        waking = protocol[protocol.index("## Waking"):protocol.index("## Messages")]
        doc_lines = set(re.findall(r"^\| `([A-Z]+)", waking, re.M))
        mail = load(MAIL)
        head_lines = set(re.findall(r"^  ([A-Z]{4,})(?: |$)", mail.__doc__, re.M))
        self.assertTrue(doc_lines)
        self.assertEqual(doc_lines, head_lines, "protocol.md's wait lines differ from mail.py's header")
        source = MAIL.read_text(encoding="utf-8")
        for token in doc_lines:
            self.assertRegex(source, rf'f?"{token}[ "]', f"protocol.md names {token}, which mail.py never prints")


if __name__ == "__main__":
    unittest.main()
