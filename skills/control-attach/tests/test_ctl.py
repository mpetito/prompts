"""ctl.py's session side: attach, detach, authority, report and typed, against a fake herdr and a throwaway home."""
import contextlib
import importlib.util
import io
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

SUPPORT = Path(__file__).resolve().parents[2] / "agent-orchestration" / "tests" / "support.py"
_spec = importlib.util.spec_from_file_location("orchestration_support", SUPPORT)
support = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = support
_spec.loader.exec_module(support)
lib = support.lib

ctl = support.load(Path(__file__).resolve().parents[1] / "scripts" / "ctl.py")
mail = ctl.mail
UTC = support.UTC


class CtlCase(support.OrchTest):
    """A Claude agent, unnamed, in pane w1:p1, which is this process's pane."""

    def setUp(self):
        super().setUp()
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w1:p1",
                                  "agent_session": {"agent": "claude", "kind": "id", "value": "s1"}})
        os.environ["HERDR_PANE_ID"] = "w1:p1"
        self.owner_box = mail.box_dir(ctl.mail_root(), "owner/in")

    def c(self, *args, stdin=""):
        return support.call(ctl, *args, stdin=stdin)

    def down(self, name, text):
        """Mail text to name's inbox from the controller, as send would."""
        with contextlib.redirect_stdout(io.StringIO()):
            mail.send(ctl.mail_root(), [f"{name}/in", text], {"--from": "owner"})

    def record(self, name):
        return json.loads(ctl.record_path(name).read_text(encoding="utf-8"))

    def agent(self, pane):
        return next(a for a in self.herdr.agents if a["pane_id"] == pane)

    def name_of(self, pane):
        return self.agent(pane)["name"]

    def owner_mail(self):
        return sorted((self.owner_box / "new").iterdir())

    def refused(self, outcome):
        code, out, err = outcome
        self.assertEqual(code, 1, out + err)
        self.assertTrue(out.startswith("REFUSED "), out)


class Attach(CtlCase):
    def test_attach_names_the_agent_and_prints_a_wait_on_its_inbox(self):
        code, out, err = self.c("attach", "alpha")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, f"WAIT {ctl.wait_line('alpha')}\n")
        self.assertEqual(self.name_of("w1:p1"), "alpha")
        self.assertEqual(ctl.wait_command(), ctl.wait_line("alpha"))
        # The printed command, run for real, waits on the box the controller sends to.
        self.down("alpha", "OWNER: hello")
        waited = subprocess.run([*shlex.split(ctl.wait_line("alpha")), "--timeout", "0"], capture_output=True,
                                text=True, check=True)
        self.assertEqual(waited.stdout, "MAIL 1\n")

    def test_a_new_record_takes_the_default_authority_and_hold(self):
        self.c("attach", "alpha")
        self.assertEqual(self.record("alpha"), {"pane": "w1:p1", "session": "s1", "authority": "delegate", "hold": 10,
                                                "typed": "", "attached": True, "started": False})
        os.environ["HERDR_PANE_ID"] = "w1:p2"
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w1:p2"})
        self.c("attach", "beta", "--hold", "3")
        self.assertEqual(self.record("beta")["hold"], 3)

    def test_a_name_another_live_session_holds_is_refused(self):
        self.herdr.agents.append({"name": "alpha", "agent": "claude", "agent_status": "idle", "pane_id": "w1:p2"})
        self.refused(self.c("attach", "alpha"))
        self.assertIsNone(self.name_of("w1:p1"))
        self.assertIsNone(ctl.load("alpha"))

    def test_owner_and_names_outside_the_pattern_are_refused(self):
        for name in ("owner", "Alpha", "1x", "a" * 33):
            with self.subTest(name=name):
                self.refused(self.c("attach", name))
                self.assertIsNone(self.name_of("w1:p1"))
                self.assertEqual(ctl.records(), [])

    def test_outside_herdr_is_refused(self):
        del os.environ["HERDR_PANE_ID"]
        self.refused(self.c("attach", "alpha"))
        self.assertEqual(ctl.records(), [])

    def test_reattaching_keeps_the_record_and_the_unread_mail(self):
        self.c("attach", "alpha", "--hold", "4")
        self.c("authority", "relay")
        self.c("typed", stdin="carry on\n")
        self.down("alpha", "OWNER: hello")
        before = self.record("alpha")
        self.assertRegex(before["typed"], UTC)
        code, out, _ = self.c("attach", "alpha")
        self.assertEqual((code, out), (0, f"WAIT {ctl.wait_line('alpha')}\n"))
        self.assertEqual(self.record("alpha"), before)
        self.assertEqual(mail.waking(mail.box_dir(ctl.mail_root(), "alpha/in")), 1)

    def test_reattaching_after_a_clear_takes_the_new_session_id(self):
        self.c("attach", "alpha")
        self.c("authority", "relay")
        # A /clear keeps the pane and the herdr name and changes the session id.
        self.agent("w1:p1")["agent_session"]["value"] = "s2"
        self.c("attach", "alpha")
        self.assertEqual((self.record("alpha")["session"], self.record("alpha")["authority"]), ("s2", "relay"))

    def test_attaching_another_name_from_the_pane_unattaches_the_first(self):
        self.c("attach", "alpha")
        self.c("attach", "beta")
        self.assertFalse(self.record("alpha")["attached"])
        self.assertEqual(ctl.attached()[0], "beta")


class Session(CtlCase):
    def setUp(self):
        super().setUp()
        self.c("attach", "alpha")

    def test_detach_keeps_authority_and_ends_the_attachment(self):
        self.c("authority", "observe")
        code, out, _ = self.c("detach")
        self.assertEqual((code, out.split()), (0, ["DETACHED", "alpha"]))
        self.assertEqual(self.record("alpha")["authority"], "observe")
        self.assertIsNone(ctl.wait_command())
        self.refused(self.c("detach"))
        self.refused(self.c("authority", "relay"))

    def test_authority_sets_the_level(self):
        code, out, _ = self.c("authority", "relay")
        self.assertEqual((code, out.split()), (0, ["AUTHORITY", "alpha", "relay"]))
        self.assertEqual(self.record("alpha")["authority"], "relay")

    def test_a_report_wakes_the_controller_only_when_it_needs_it(self):
        cases = {"STATUS: need-decision - D1 which": True, "STATUS: blocked - no access": True,
                 "STATUS: done - shipped": True, "STATUS: working - lane merged": False,
                 "STATUS: doneish - x": False, "no status line": False}
        for first, wakes in cases.items():
            with self.subTest(first=first):
                before = mail.waking(self.owner_box)
                self.assertEqual(self.c("report", stdin=f"{first}\nmore\n")[0], 0)
                self.assertEqual(mail.waking(self.owner_box) - before, int(wakes))
        self.assertEqual(len(self.owner_mail()), len(cases))

    def test_a_report_is_sent_from_the_sessions_own_name(self):
        self.c("report", stdin="STATUS: done - shipped\n")
        [sent] = self.owner_mail()
        self.assertEqual(lib.record_value(sent, "From"), "alpha")

    def test_an_empty_report_sends_nothing(self):
        self.assertEqual(self.c("report", stdin=" \n\n"), (0, "", ""))
        self.assertEqual(self.owner_mail(), [])

    def test_typed_records_the_owner_but_ignores_a_ring_line(self):
        self.assertEqual(self.c("typed", stdin="/control-attach alpha\n"), (0, "", ""))
        self.assertEqual(self.record("alpha")["typed"], "")
        self.assertEqual(self.c("typed", stdin="stop that\n"), (0, "", ""))
        self.assertRegex(self.record("alpha")["typed"], UTC)


class Unattached(CtlCase):
    """report and typed print nothing and change nothing for a pane that isn't attached."""

    def check_silent(self):
        for args, stdin in ((("report",), "STATUS: done - x\n"), (("typed",), "hello\n")):
            with self.subTest(args=args):
                self.assertEqual(self.c(*args, stdin=stdin), (0, "", ""))
        self.assertEqual(self.owner_mail(), [])

    def test_outside_herdr(self):
        del os.environ["HERDR_PANE_ID"]
        self.check_silent()

    def test_never_attached(self):
        self.check_silent()

    def test_detached(self):
        self.c("attach", "alpha")
        self.c("detach")
        before = self.record("alpha")
        self.check_silent()
        self.assertEqual(self.record("alpha"), before)

    def test_another_pane_attached(self):
        self.c("attach", "alpha")
        os.environ["HERDR_PANE_ID"] = "w1:p2"
        self.check_silent()
        self.assertEqual(self.record("alpha")["typed"], "")


class AttachedAs(CtlCase):
    """Whether an agent from herdr's list counts as attached, which sessions shows."""

    def setUp(self):
        super().setUp()
        self.c("attach", "alpha")
        self.me = self.agent("w1:p1")

    def test_the_attached_agent_with_its_session_id(self):
        self.assertEqual(ctl.attached_as(self.me), "alpha")

    def test_a_cleared_session_is_unattached(self):
        self.me["agent_session"]["value"] = "s2"
        self.assertIsNone(ctl.attached_as(self.me))

    def test_a_detached_or_unnamed_agent_is_unattached(self):
        self.assertIsNone(ctl.attached_as({**self.me, "name": None}))
        self.c("detach")
        self.assertIsNone(ctl.attached_as(self.me))
