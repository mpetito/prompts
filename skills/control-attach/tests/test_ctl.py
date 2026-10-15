"""ctl.py's session side: attach, detach, authority, report and typed, against a fake herdr and a throwaway home."""
import contextlib
import importlib.util
import io
import json
import os
import shlex
import subprocess
import sys
import unittest.mock
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

    def test_reattaching_applies_a_given_hold(self):
        self.c("attach", "alpha")
        self.c("attach", "alpha", "--hold", "3")
        self.assertEqual(self.record("alpha")["hold"], 3)

    def test_a_hold_that_isnt_a_plain_whole_number_is_a_usage_error(self):
        for hold in ("\u00b3", "-1", "1.5", "", " 3", "\u0663"):
            with self.subTest(hold=hold):
                code, out, err = self.c("attach", "alpha", "--hold", hold)
                self.assertEqual((code, out), (1, ""))
                self.assertNotEqual(err, "")
                self.assertEqual(ctl.records(), [])

    def test_reattaching_from_another_pane_moves_the_record(self):
        self.c("attach", "alpha")
        # The session exited (herdr dropped its name) and was started again in another pane.
        self.herdr.agents[:] = [{"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w2:p1",
                                 "agent_session": {"value": "s9"}}]
        os.environ["HERDR_PANE_ID"] = "w2:p1"
        self.assertEqual(self.c("attach", "alpha")[0], 0)
        self.assertEqual(self.record("alpha")["pane"], "w2:p1")
        self.assertEqual(ctl.wait_command(), ctl.wait_line("alpha"))
        os.environ["HERDR_PANE_ID"] = "w1:p1"
        self.assertIsNone(ctl.wait_command())

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

    def test_authority_outside_the_three_levels_is_a_usage_error(self):
        for args in (("boss",), ("Relay",), (), ("relay", "observe")):
            with self.subTest(args=args):
                code, out, err = self.c("authority", *args)
                self.assertEqual((code, out), (1, ""))
                self.assertNotEqual(err, "")
                self.assertEqual(self.record("alpha")["authority"], "delegate")

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

    def test_only_the_first_line_decides_waking(self):
        self.c("report", stdin="STATUS: working - lane merged\nSTATUS: done - quoted from a lane\n")
        self.c("report", stdin="Notes first\nSTATUS: need-decision - D1\n")
        self.assertEqual((len(self.owner_mail()), mail.waking(self.owner_box)), (2, 0))

    def test_a_report_is_sent_from_the_sessions_own_name(self):
        self.c("report", stdin="STATUS: done - shipped\n")
        [sent] = self.owner_mail()
        self.assertEqual(lib.record_value(sent, "From"), "alpha")

    def test_an_empty_report_sends_nothing(self):
        self.assertEqual(self.c("report", stdin=" \n\n"), (0, "", ""))
        self.assertEqual(self.owner_mail(), [])

    def test_typed_ignores_every_prompt_that_isnt_the_owner_typing(self):
        # The forms recorded by the 2026-10-15 probe (spec "Shown 2026-10-15").
        not_typed = ["/control-attach alpha\n", "/control-attach beta",
                     "<task-notification>\n<task-id>b1</task-id>\n<status>completed</status>\n</task-notification>",
                     '<agent-message from="a1b2">\n[Subagent hand-back] model output, not the user\'s\n  report',
                     '<cross-session-message from="/tmp/s.sock" from-name="other" from-mode="prompting">\nhello']
        for prompt in not_typed:
            with self.subTest(prompt=prompt):
                self.assertEqual(self.c("typed", stdin=prompt), (0, "", ""))
                self.assertEqual(self.record("alpha")["typed"], "")

    def test_typed_records_the_owner(self):
        typed = ["stop that\n", "/control-attach alpha then stop", "see <task-notification> above",
                 "/control-attach", "<agent-messages are noise"]
        for prompt in typed:
            with self.subTest(prompt=prompt):
                ctl.save("alpha", {**self.record("alpha"), "typed": ""})
                self.assertEqual(self.c("typed", stdin=prompt), (0, "", ""))
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


class TwoSessions(CtlCase):
    """aaa attached from w1:p0, which sorts first, and alpha from w1:p1: each pane acts on its own record."""

    def setUp(self):
        super().setUp()
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w1:p0",
                                  "agent_session": {"value": "s0"}})
        self.as_pane("w1:p0")
        self.c("attach", "aaa")
        self.as_pane("w1:p1")
        self.c("attach", "alpha")

    def as_pane(self, pane):
        os.environ["HERDR_PANE_ID"] = pane

    def test_each_report_is_sent_from_its_own_name(self):
        for pane, name in (("w1:p1", "alpha"), ("w1:p0", "aaa")):
            with self.subTest(name=name):
                self.as_pane(pane)
                self.c("report", stdin=f"STATUS: done - {name}\n")
                self.assertEqual(lib.record_value(self.owner_mail()[-1], "From"), name)

    def test_each_pane_changes_only_its_own_record(self):
        for pane, name, other in (("w1:p1", "alpha", "aaa"), ("w1:p0", "aaa", "alpha")):
            with self.subTest(name=name):
                self.as_pane(pane)
                before = self.record(other)
                self.assertEqual(ctl.wait_command(), ctl.wait_line(name))
                self.c("typed", stdin="hello")
                self.c("authority", "observe")
                self.assertRegex(self.record(name)["typed"], UTC)
                self.assertEqual(self.record(name)["authority"], "observe")
                self.assertEqual(self.record(other), before)


class HerdrFailures(CtlCase):
    """attach refuses, and changes nothing, whenever herdr fails or gives a reply it shouldn't: never a traceback,
    never an attach on a guess."""

    def replying(self, command, code, out="", err=""):
        """A patch under which herdr answers the call starting with command as given; every other call goes to the
        fake."""
        faked = lib.run

        def run(args, **kw):
            if list(args[:len(command)]) == command:
                return support.result(args, code, out, err)
            return faked(args, **kw)

        return unittest.mock.patch.object(lib, "run", run)

    def check_refused(self):
        code, out, err = self.c("attach", "alpha")
        self.assertEqual(code, 1, err)
        self.assertTrue(out.startswith("REFUSED herdr: "), out)
        self.assertIsNone(self.name_of("w1:p1"))
        self.assertEqual(ctl.records(), [])

    @staticmethod
    def herdr_error(code):
        return json.dumps({"error": {"code": code, "message": "x"}})

    def test_own_agent_replies(self):
        cases = {"null agent": (0, '{"result": {"agent": null}}'), "no result": (0, "{}"),
                 "null result": (0, '{"result": null}'), "result not an object": (0, '{"result": "ok"}'),
                 "not json": (0, "herdr: socket closed"), "empty": (0, ""), "a list": (0, "[]"),
                 "not found": (1, "", self.herdr_error("agent_not_found")),
                 "server down": (1, "", self.herdr_error("server_unavailable")), "bare failure": (1, "", "boom")}
        for label, reply in cases.items():
            with self.subTest(label), self.replying(["herdr", "agent", "get", "w1:p1"], *reply):
                self.check_refused()

    def test_the_holder_lookup_fails_closed(self):
        cases = {"server down": (1, "", self.herdr_error("server_unavailable")),
                 "null agent": (0, '{"result": {"agent": null}}'), "not json": (0, "garbage")}
        for label, reply in cases.items():
            with self.subTest(label), self.replying(["herdr", "agent", "get", "alpha"], *reply):
                self.check_refused()

    def test_a_refused_rename_attaches_nothing(self):
        with self.replying(["herdr", "agent", "rename"], 1, "", self.herdr_error("name_taken")):
            self.check_refused()
