"""ctl.py, both sides, against a fake herdr and a throwaway home; and protocol.md against the lines ctl.py prints."""
import contextlib
import importlib.util
import io
import json
import os
import re
import shlex
import subprocess
import sys
import time
import unittest.mock
from pathlib import Path

SUPPORT = Path(__file__).resolve().parents[2] / "agent-orchestration" / "tests" / "support.py"
_spec = importlib.util.spec_from_file_location("orchestration_support", SUPPORT)
support = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = support
_spec.loader.exec_module(support)
lib = support.lib

SKILL = Path(__file__).resolve().parents[1]
ctl = support.load(SKILL / "scripts" / "ctl.py")
mail = ctl.mail
UTC = support.UTC

# Screens as herdr agent read --format ansi gives them: an empty Claude input line between its rules, under an
# earlier prompt that the transcript shows with the same mark.
RULE = "\x1b[0m\x1b[38;2;136;136;136m" + "\u2500" * 40 + "\x1b[0m"
CLAUDE_EMPTY = f"\u276f\u00a0an earlier prompt\n\u25cf Done.\n\n{RULE}\n\u276f\u00a0\n{RULE}\n  \x1b[38;5;6m~/dev\x1b[0m\n"
CODEX_EMPTY = ("\u2022 Done.\n\x1b[0m\x1b[1m\x1b[48;2;41;41;41m\u203a\x1b[0m\x1b[48;2;41;41;41m \x1b[0m"
               "\x1b[2m\x1b[48;2;41;41;41mAsk Codex to do anything\x1b[0m\n  ? for shortcuts\n")


def claude_screen(typed):
    """CLAUDE_EMPTY with typed (escape codes and all) on its input line."""
    return CLAUDE_EMPTY.replace("\u276f\u00a0\n", f"\u276f\u00a0{typed}\n")


class Herdr(support.FakeHerdr):
    """agent-orchestration's fake herdr, plus agent read: a pane's screen is screens[pane], CLAUDE_EMPTY unless set."""

    def __init__(self):
        super().__init__()
        self.screens, self.refuse_prompts = {}, False

    def __call__(self, args):
        if args[:2] == ["agent", "prompt"] and self.refuse_prompts:
            self.log.append(" ".join(args))
            return self.err(args, "agent_prompt_stalled", "no state change")
        if args[:2] != ["agent", "read"]:
            return super().__call__(args)
        self.log.append(" ".join(args))
        for ag in self.agents:
            if args[2] in (ag["name"], ag.get("pane_id")):
                return support.result(args, out=self.screens.get(ag["pane_id"], CLAUDE_EMPTY))
        return self.err(args, "agent_not_found", f"agent target {args[2]} not found")

    def prompts(self):
        return [line for line in self.log if line.startswith("agent prompt ")]


class CtlCase(support.OrchTest):
    """A Claude agent, unnamed, in pane w1:p1, which is this process's pane."""

    def setUp(self):
        super().setUp()
        self.herdr = Herdr()
        run_patch = unittest.mock.patch.object(lib, "run", lambda args, **kw: self.herdr(list(args[1:])) if args[
            0] == "herdr" else support.REAL_RUN(args, **kw))
        run_patch.start()
        self.addCleanup(run_patch.stop)
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w1:p1"})
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
        self.assertEqual(self.record("alpha"), {"pane": "w1:p1", "authority": "delegate", "hold": 10,
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
        self.herdr.agents[:] = [{"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w2:p1"}]
        os.environ["HERDR_PANE_ID"] = "w2:p1"
        self.assertEqual(self.c("attach", "alpha")[0], 0)
        self.assertEqual(self.record("alpha")["pane"], "w2:p1")
        self.assertEqual(ctl.wait_command(), ctl.wait_line("alpha"))
        os.environ["HERDR_PANE_ID"] = "w1:p1"
        self.assertIsNone(ctl.wait_command())

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

    def test_the_attached_agent_in_its_pane(self):
        self.assertEqual(ctl.attached_as(self.me), "alpha")

    def test_an_agent_under_the_name_in_another_pane_is_unattached(self):
        self.assertIsNone(ctl.attached_as({**self.me, "pane_id": "w9:p1"}))

    def test_a_detached_or_unnamed_agent_is_unattached(self):
        self.assertIsNone(ctl.attached_as({**self.me, "name": None}))
        self.c("detach")
        self.assertIsNone(ctl.attached_as(self.me))


class TwoSessions(CtlCase):
    """aaa attached from w1:p0, which sorts first, and alpha from w1:p1: each pane acts on its own record."""

    def setUp(self):
        super().setUp()
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w1:p0"})
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


# --- controller --------------------------------------------------------------------------------------------------

def body(path):
    """A message's text, without mail.py's From and Date lines."""
    return path.read_text(encoding="utf-8").split("\n\n", 1)[1].removesuffix("\n")


class ControllerCase(CtlCase):
    def as_pane(self, pane):
        os.environ["HERDR_PANE_ID"] = pane

    def attach_at(self, name, pane, kind="claude", **fields):
        """name attached from pane, which a new idle agent of kind holds; fields then overwrite the record."""
        self.herdr.agents.append({"name": None, "agent": kind, "agent_status": "idle", "pane_id": pane})
        self.as_pane(pane)
        self.assertEqual(self.c("attach", name)[0], 0)
        ctl.save(name, {**self.record(name), **fields})

    def inbox(self, name):
        return sorted((mail.box_dir(ctl.mail_root(), f"{name}/in") / "new").iterdir())

    def typed_ago(self, minutes):
        return lib.fmt_utc(time.time() - minutes * 60)


class Sessions(ControllerCase):
    def rows(self):
        code, out, err = self.c("sessions")
        self.assertEqual((code, err), (0, ""))
        return out.splitlines()

    def test_one_row_per_agent_then_one_per_gone_record(self):
        typed = self.typed_ago(1)
        self.attach_at("alpha", "w2:p1", typed=typed, hold=10)
        self.down("alpha", "OWNER: one")
        self.attach_at("beta", "w2:p2", authority="relay")
        # gamma detached and exited: a record that isn't attached is not gone, just unlisted.
        self.attach_at("gamma", "w2:p3")
        self.c("detach")
        self.herdr.agents[:] = [a for a in self.herdr.agents if a["name"] not in ("beta", "gamma")]
        self.herdr.agents += [{"name": "shop-web", "agent": "claude", "agent_status": "working", "pane_id": "w3:p1"},
                              {"name": None, "agent": "codex", "agent_status": "done", "pane_id": "w3:p2"},
                              {"name": None, "agent": None, "agent_status": None, "pane_id": "w3:p3"}]
        until = lib.fmt_utc(lib.to_epoch(typed) + 600)
        self.assertEqual(self.rows(), ["w1:p1 claude idle unattached - -", f"alpha claude idle delegate {until} 1",
                                       "shop-web claude working unattached - -", "w3:p2 codex done unattached - -",
                                       "w3:p3 null null unattached - -", "beta - gone relay - 0"])

    def test_a_gone_session_stays_gone_when_another_agent_takes_its_name(self):
        self.attach_at("alpha", "w2:p1")
        self.herdr.agents[:] = [{"name": "alpha", "agent": "claude", "agent_status": "idle", "pane_id": "w9:p1"}]
        self.assertEqual(self.rows(), ["alpha claude idle unattached - -", "alpha - gone delegate - 0"])

    def test_the_hold_shows_only_while_it_lasts(self):
        self.attach_at("alpha", "w2:p1", typed=self.typed_ago(11), hold=10)
        self.assertIn("alpha claude idle delegate - 0", self.rows())

    def test_a_codex_session_shows_unattached_even_with_a_matching_record(self):
        self.attach_at("cx", "w2:p1", kind="codex")
        self.assertIn("cx codex idle unattached - -", self.rows())

    def test_no_agents_and_no_records_prints_none(self):
        self.herdr.agents.clear()
        self.assertEqual(self.rows(), ["NONE"])

    def test_herdr_down_is_refused(self):
        self.herdr.mode = "down"
        code, out, _ = self.c("sessions")
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("REFUSED herdr: "), out)


class Send(ControllerCase):
    MESSAGES = {"OWNER": ("OWNER", "go"), "QUESTION": ("QUESTION", "status?"), "CONTROL": ("CONTROL", "rebase"),
                "DECISION owner": ("DECISION", "D3", "Stripe", "--owner"), "DECISION controller": ("DECISION", "D3",
                                                                                                   "Stripe")}

    def setUp(self):
        super().setUp()
        self.attach_at("alpha", "w2:p1")

    def test_each_message_is_sent_from_owner_in_its_form(self):
        expected = {"OWNER": "OWNER: go", "QUESTION": "QUESTION: status?", "CONTROL": "CONTROL: rebase",
                    "DECISION owner": "DECISION D3: Stripe\nBy: owner",
                    "DECISION controller": "DECISION D3: Stripe\nBy: controller"}
        for label, args in self.MESSAGES.items():
            with self.subTest(label):
                code, out, _ = self.c("send", "alpha", *args)
                sent = self.inbox("alpha")[-1]
                self.assertEqual((code, out), (0, f"SENT alpha/in {sent.name}\n"))
                self.assertEqual((lib.record_value(sent, "From"), body(sent)), ("owner", expected[label]))

    def test_each_level_permits_only_its_messages(self):
        permitted = {"observe": set(), "relay": {"OWNER", "QUESTION", "DECISION owner"}, "delegate": set(self.MESSAGES)}
        for level, allowed in permitted.items():
            ctl.save("alpha", {**self.record("alpha"), "authority": level})
            for label, args in self.MESSAGES.items():
                with self.subTest(level=level, message=label):
                    before = len(self.inbox("alpha"))
                    code, out, _ = self.c("send", "alpha", *args)
                    if label in allowed:
                        self.assertEqual(code, 0, out)
                    else:
                        self.refused((code, out, ""))
                        self.assertEqual(len(self.inbox("alpha")), before)

    def test_inside_the_hold_window_the_owners_relay_and_a_question_go(self):
        typed = self.typed_ago(1)
        ctl.save("alpha", {**self.record("alpha"), "typed": typed, "hold": 10})
        until = lib.fmt_utc(lib.to_epoch(typed) + 600)
        for label, args in self.MESSAGES.items():
            with self.subTest(label):
                code, out, _ = self.c("send", "alpha", *args)
                if label in ("OWNER", "QUESTION"):
                    self.assertEqual(code, 0, out)
                else:
                    self.assertEqual((code, out), (1, f"HELD {until}\n"))
        self.assertEqual([body(m) for m in self.inbox("alpha")], ["OWNER: go", "QUESTION: status?"])

    def test_the_hold_lasts_to_its_last_minute(self):
        # typed keeps the minute: typed at 00:00 with hold 10 holds until 00:10, here 30 s away.
        now = 1_800_000_030
        typed = lib.fmt_utc(now - 570)
        ctl.save("alpha", {**self.record("alpha"), "typed": typed, "hold": 10})
        with unittest.mock.patch.object(ctl.time, "time", return_value=now):
            self.assertEqual(self.c("send", "alpha", "CONTROL", "go"), (1, f"HELD {lib.fmt_utc(now + 30)}\n", ""))

    def test_after_the_hold_window_everything_goes(self):
        for typed, hold in ((self.typed_ago(11), 10), (self.typed_ago(0), 0)):
            with self.subTest(typed=typed, hold=hold):
                ctl.save("alpha", {**self.record("alpha"), "typed": typed, "hold": hold})
                self.assertEqual(self.c("send", "alpha", "CONTROL", "go")[0], 0)

    def test_only_an_attached_record_receives(self):
        self.c("detach")
        for name in ("alpha", "nobody", "../alpha", "owner"):
            with self.subTest(name=name):
                self.refused(self.c("send", name, "OWNER", "go"))
        self.assertEqual(self.inbox("alpha"), [])

    def test_wrong_arguments_are_usage_errors(self):
        for args in (("alpha", "STEER", "go"), ("alpha", "OWNER", "go", "--owner"), ("alpha", "OWNER"),
                     ("alpha", "OWNER", " \n"), ("alpha", "DECISION", "D3:", "x"), ("alpha", "DECISION", "D 3", "x"),
                     ("alpha", "DECISION", "D3"), ("alpha", "QUESTION", "a", "b")):
            with self.subTest(args=args):
                code, out, err = self.c("send", *args)
                self.assertEqual((code, out), (1, ""))
                self.assertNotEqual(err, "")
        self.assertEqual(self.inbox("alpha"), [])


class ReadAndWait(ControllerCase):
    def test_read_files_the_controllers_mail(self):
        self.attach_at("alpha", "w2:p1")
        self.c("report", stdin="STATUS: done - shipped\n")
        [sent] = self.owner_mail()
        code, out, _ = self.c("read")
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[0], f"=== {sent.name}")
        self.assertIn("STATUS: done - shipped", out)
        self.assertEqual(self.c("read")[1], "NO MAIL\n")

    def test_a_waking_report_ends_the_wait(self):
        self.attach_at("alpha", "w2:p1")
        self.c("report", stdin="STATUS: need-decision - D1\n")
        self.assertEqual(self.c("wait", "--timeout", "0"), (0, "MAIL 1\n", ""))

    def age(self, name):
        """Make name's unread mail six minutes old, past mail.py's UNREAD threshold."""
        old = time.time() - 6 * 60
        for m in self.inbox(name):
            os.utime(m, (old, old))

    def test_wait_watches_every_attached_session_with_its_inbox(self):
        for name, pane in (("alpha", "w2:p1"), ("beta", "w2:p2"), ("gamma", "w2:p3")):
            self.attach_at(name, pane)
        self.as_pane("w2:p3")
        self.c("detach")
        # The wait sees an agent's state from its second look on; --timeout 0 looks once.
        self.assertEqual(self.c("wait", "--timeout", "0")[1], "TIMEOUT\n")
        self.down("gamma", "OWNER: unwatched")
        self.age("gamma")
        self.assertEqual(self.c("wait", "--timeout", "0")[1], "TIMEOUT\n")
        self.down("beta", "OWNER: watched")
        self.age("beta")
        self.assertEqual(self.c("wait", "--timeout", "0")[1], "UNREAD beta 1\n")
        self.herdr.agents[:] = [a for a in self.herdr.agents if a["name"] != "alpha"]
        self.assertEqual(self.c("wait", "--timeout", "0")[1], "GONE alpha\n")


class Ring(ControllerCase):
    """The unnamed, idle Claude agent in w1:p1 with an empty input line is ringable."""

    def rung(self, *args, prompt):
        code, out, err = self.c("ring", *args)
        self.assertEqual((code, out, err), (0, f"RUNG {args[0]}\n", ""))
        self.assertEqual(self.herdr.prompts(), [f"agent prompt {prompt}"])

    def not_rung(self, *args):
        self.refused(self.c("ring", *args))
        self.assertEqual(self.herdr.prompts(), [])

    def test_rings_the_attach_line_into_an_unattached_claude_session(self):
        self.rung("w1:p1", "alpha", prompt="w1:p1 /control-attach alpha")

    def test_rings_a_brief_pointer_into_a_codex_session(self):
        self.herdr.agents.append({"name": None, "agent": "codex", "agent_status": "done", "pane_id": "w2:p1"})
        self.herdr.screens["w2:p1"] = CODEX_EMPTY
        brief = self.tmp / "brief.md"
        self.rung("w2:p1", "--brief", str(brief), prompt=f"w2:p1 Read {lib.native(brief)} and follow it.")

    def test_dim_text_on_the_input_line_is_not_typing(self):
        self.herdr.screens["w1:p1"] = claude_screen("\x1b[2mrun the tests\x1b[0m")
        self.rung("w1:p1", "alpha", prompt="w1:p1 /control-attach alpha")

    def test_an_input_line_holding_text_is_refused(self):
        for typed in ("half a thou", "\x1b[38;2;200;200;200mcoloured\x1b[0m", "\x1b[2mdim\x1b[22m then typed",
                      "\x1b[2mdim\x1b[0m then typed", "\n  a draft's second line", "\n\n  \x1b[2mdim\x1b[0m third"):
            with self.subTest(typed=typed):
                self.herdr.screens["w1:p1"] = claude_screen(typed)
                self.not_rung("w1:p1", "alpha")

    def test_a_screen_without_an_input_line_is_refused(self):
        self.herdr.screens["w1:p1"] = "Loading...\n"
        self.not_rung("w1:p1", "alpha")

    def test_only_an_idle_or_done_agent_is_rung(self):
        for state in ("working", "blocked", "unknown", None):
            with self.subTest(state=state):
                self.agent("w1:p1")["agent_status"] = state
                self.not_rung("w1:p1", "alpha")

    def test_a_session_at_observe_is_refused(self):
        self.attach_at("alpha", "w2:p1", authority="observe")
        self.not_rung("alpha", "alpha")
        self.not_rung("w2:p1", "alpha")

    def test_each_line_goes_only_into_its_kind(self):
        self.herdr.agents.append({"name": None, "agent": "codex", "agent_status": "idle", "pane_id": "w2:p1"})
        self.not_rung("w2:p1", "alpha")
        self.not_rung("w1:p1", "--brief", str(self.tmp / "brief.md"))

    def test_an_agent_with_a_name_no_record_has_is_refused(self):
        self.herdr.agents.append({"name": "shop-web", "agent": "claude", "agent_status": "idle", "pane_id": "w2:p1"})
        self.not_rung("shop-web", "alpha")
        self.not_rung("w2:p1", "alpha")

    def test_a_stale_records_name_taken_by_a_lane_is_refused(self):
        self.attach_at("alpha", "w2:p1")
        self.c("detach")
        self.herdr.agents[:] = [{"name": "alpha", "agent": "claude", "agent_status": "idle", "pane_id": "w9:p1"}]
        self.not_rung("alpha", "alpha")

    def test_a_gone_sessions_name_taken_by_a_thread_is_refused(self):
        # P1: the session exited (still attached, herdr dropped its name), and a build's thread took the name.
        self.attach_at("alpha", "w2:p1")
        self.herdr.agents[:] = [{"name": "alpha", "agent": "claude", "agent_status": "idle", "pane_id": "w9:p1"}]
        self.not_rung("alpha", "alpha")

    def test_a_started_records_name_taken_by_a_lane_is_refused(self):
        # P2: started never changes, so it can't vouch for a later agent with the name.
        ctl.save("alpha", {"pane": "w7:p1", "authority": "delegate", "hold": 10, "typed": "", "attached": False,
                           "started": True})
        self.herdr.agents.append({"name": "alpha", "agent": "claude", "agent_status": "idle", "pane_id": "w9:p1"})
        self.not_rung("alpha", "alpha")

    def test_a_session_whose_pane_moved_is_no_longer_its_records(self):
        # herdr gives a pane moved to another workspace a new id.
        self.attach_at("alpha", "w2:p1")
        self.agent("w2:p1")["pane_id"] = "w5:p3"
        self.not_rung("alpha", "alpha")
        self.c("detach")
        self.not_rung("alpha", "alpha")

    def test_a_record_in_another_pane_isnt_an_unnamed_agents(self):
        self.attach_at("alpha", "w2:p1", authority="observe")
        self.rung("w1:p1", "beta", prompt="w1:p1 /control-attach beta")

    def test_a_detached_session_in_its_own_pane_is_rung_back(self):
        self.attach_at("alpha", "w2:p1")
        self.c("detach")
        self.rung("alpha", "alpha", prompt="w2:p1 /control-attach alpha")

    def test_a_ring_never_attaches_a_session_under_another_name(self):
        # P5: alpha at relay, attached as beta, would take beta's level.
        self.attach_at("alpha", "w2:p1", authority="relay")
        self.not_rung("alpha", "beta")
        self.agent("w2:p1")["name"] = None
        self.not_rung("w2:p1", "beta")
        self.not_rung("alpha", "beta")
        self.rung("w2:p1", "alpha", prompt="w2:p1 /control-attach alpha")

    def test_observe_holds_by_pane_once_herdr_clears_the_name(self):
        self.attach_at("alpha", "w2:p1", authority="observe")
        self.agent("w2:p1")["name"] = None
        self.not_rung("w2:p1", "alpha")
        self.not_rung("alpha", "alpha")

    def test_a_started_record_reached_by_its_pane_keeps_its_level_and_name(self):
        ctl.save("alpha", {"pane": "w1:p1", "authority": "observe", "hold": 10, "typed": "", "attached": False,
                           "started": True})
        self.not_rung("alpha", "alpha")
        ctl.save("alpha", {**self.record("alpha"), "authority": "delegate"})
        self.not_rung("alpha", "beta")
        self.rung("alpha", "alpha", prompt="w1:p1 /control-attach alpha")

    def test_whose_a_session_is_decides_every_ring_path(self):
        # alpha's record from w2:p1, and the agent there named alpha or unnamed (herdr cleared the name on a resume).
        # A ring never attaches it as beta, whatever path reached it (Q1: detached at observe, unnamed, by pane;
        # Q2: started at observe, unnamed, by pane), and never anything at observe.
        states = {"attached": (True, False), "detached": (False, False), "started": (False, True)}
        for herdr_name in ("alpha", None):
            for state, (is_attached, started) in states.items():
                for level in ("observe", "delegate"):
                    with self.subTest(name=herdr_name, state=state, level=level):
                        for n, _ in ctl.records():
                            ctl.record_path(n).unlink()
                        ctl.save("alpha", {"pane": "w2:p1", "authority": level, "hold": 10, "typed": "",
                                           "attached": is_attached, "started": started})
                        self.herdr.agents[:] = [{"name": herdr_name, "agent": "claude", "agent_status": "idle",
                                                 "pane_id": "w2:p1"}]
                        for target, attach_name, rings in (
                                ("w2:p1", "beta", False), ("alpha", "beta", False),
                                ("w2:p1", "alpha", level != "observe"), ("alpha", "alpha", level != "observe")):
                            self.herdr.log.clear()
                            if rings:
                                self.rung(target, attach_name, prompt=f"w2:p1 /control-attach {attach_name}")
                            else:
                                self.not_rung(target, attach_name)

    def test_unattached_records_sharing_a_pane_each_give_their_name_and_any_observe_refuses(self):
        base = {"pane": "w2:p1", "hold": 10, "typed": ""}
        ctl.save("alpha", {**base, "authority": "delegate", "attached": False, "started": False})
        ctl.save("gamma", {**base, "authority": "delegate", "attached": False, "started": True})
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w2:p1"})
        for attach_name in ("alpha", "gamma"):
            self.herdr.log.clear()
            self.rung("w2:p1", attach_name, prompt=f"w2:p1 /control-attach {attach_name}")
        self.herdr.log.clear()
        self.not_rung("w2:p1", "beta")
        ctl.save("gamma", {**self.record("gamma"), "authority": "observe"})
        self.not_rung("w2:p1", "alpha")

    def test_an_attached_record_in_the_pane_comes_before_the_others(self):
        base = {"pane": "w2:p1", "hold": 10, "typed": "", "started": False}
        ctl.save("alpha", {**base, "authority": "delegate", "attached": True})
        ctl.save("gamma", {**base, "authority": "observe", "attached": False})
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w2:p1"})
        self.not_rung("w2:p1", "gamma")
        self.rung("w2:p1", "alpha", prompt="w2:p1 /control-attach alpha")

    def test_a_records_name_rings_its_pane_once_herdr_clears_the_name(self):
        self.attach_at("alpha", "w2:p1")
        # The session was resumed in its pane: herdr cleared its name.
        self.agent("w2:p1")["name"] = None
        for attached in (True, False):
            with self.subTest(attached=attached):
                self.herdr.log.clear()
                ctl.save("alpha", {**self.record("alpha"), "attached": attached})
                self.rung("alpha", "alpha", prompt="w2:p1 /control-attach alpha")

    def test_nothing_herdr_or_a_record_knows_is_refused(self):
        self.not_rung("ghost", "alpha")
        self.not_rung("w8:p8", "alpha")

    def test_an_attach_name_outside_the_pattern_or_owner_is_refused(self):
        for name in ("owner", "Alpha", "a b"):
            with self.subTest(name=name):
                self.not_rung("w1:p1", name)

    def test_wrong_arguments_are_usage_errors(self):
        for args in (("w1:p1",), ("w1:p1", "alpha", "--brief", "b.md"), ("w1:p1", "a", "b")):
            with self.subTest(args=args):
                code, out, err = self.c("ring", *args)
                self.assertEqual((code, out), (1, ""))
                self.assertNotEqual(err, "")


class Start(ControllerCase):
    def setUp(self):
        super().setUp()
        self.work = self.tmp / "work"
        self.folder = self.work / "proj"
        self.folder.mkdir(parents=True)
        (self.tmp / "work2").mkdir()
        self.folders = ctl.control() / "folders"
        self.folders.parent.mkdir(parents=True, exist_ok=True)
        self.folders.write_text(f"\n{self.work}\n\n", encoding="utf-8")
        self.objective = self.tmp / "objective.md"
        self.objective.write_text("OWNER: investigate the flaky test\nThe owner said so on the phone.\n",
                                  encoding="utf-8")

    def start(self, name="alpha", folder=None, objective=None):
        return self.c("start", name, folder or self.folder, objective or self.objective)

    def started_nothing(self, outcome):
        self.refused(outcome)
        self.assertFalse(any(line.startswith("workspace create") for line in self.herdr.log))
        self.assertIsNone(ctl.load("alpha"))

    def test_start_opens_a_session_on_the_attach_line_with_the_objective_in_its_inbox(self):
        code, out, err = self.start()
        pane = self.record("alpha")["pane"]
        self.assertEqual((code, out, err), (0, f"STARTED alpha {pane}\n", ""))
        self.assertEqual(self.record("alpha"), {"pane": pane, "authority": "delegate", "hold": 10, "typed": "",
                                                "attached": False, "started": True})
        [objective] = self.inbox("alpha")
        self.assertEqual((lib.record_value(objective, "From"), body(objective)),
                         ("owner", self.objective.read_text(encoding="utf-8").rstrip("\n")))
        self.assertEqual(self.herdr.prompts(), ["agent prompt alpha /control-attach alpha"])
        [create] = [line for line in self.herdr.log if line.startswith("workspace create")]
        self.assertIn(f"--cwd {self.folder} ", create)
        self.assertIn(f"--env ORCHESTRATION_HOME={os.environ['ORCHESTRATION_HOME']}", create)

    def test_attaching_a_started_session_keeps_started(self):
        self.start()
        self.as_pane(self.record("alpha")["pane"])
        self.assertEqual(self.c("attach", "alpha")[0], 0)
        self.assertEqual((self.record("alpha")["attached"], self.record("alpha")["started"]), (True, True))
        self.c("detach")
        self.c("attach", "alpha")
        self.assertTrue(self.record("alpha")["started"])

    def test_a_startup_dialog_starts_it_blocked_without_the_attach_line(self):
        self.herdr.mode = "notready"
        self.assertEqual(self.start(), (0, "BLOCKED alpha waiting on a startup prompt\n", ""))
        self.assertTrue(self.record("alpha")["started"])
        self.assertEqual(len(self.inbox("alpha")), 1)
        self.assertEqual(self.herdr.prompts(), [])

    def test_a_refused_first_prompt_starts_it_blocked(self):
        self.herdr.refuse_prompts = True
        self.assertEqual(self.start(), (0, "BLOCKED alpha waiting on a startup prompt\n", ""))
        self.assertTrue(self.record("alpha")["started"])
        self.assertEqual(len(self.inbox("alpha")), 1)

    def test_starting_under_a_name_keeps_its_level_and_hold(self):
        # P3: the owner set alpha to relay; the address outlives the session that exited.
        ctl.save("alpha", {"pane": "w7:p1", "authority": "relay", "hold": 3, "typed": "2026-10-01T10:00Z",
                           "attached": True, "started": False})
        self.assertEqual(self.start()[0], 0)
        record = self.record("alpha")
        self.assertEqual((record["authority"], record["hold"], record["attached"], record["started"]),
                         ("relay", 3, False, True))

    def test_the_objective_must_be_a_message_the_kept_level_permits(self):
        # Q3 (CONTROL at relay) and Q4 (anything at observe): refused before anything is made or mailed.
        objectives = {"OWNER: go": {"relay", "delegate"}, "QUESTION: which?": {"relay", "delegate"},
                      "DECISION D1: Stripe\nBy: owner": {"relay", "delegate"},
                      "CONTROL: force-push main": {"delegate"}, "DECISION D1: Stripe\nBy: controller": {"delegate"},
                      "no kind on the first line": {"delegate"}}
        for level in ("observe", "relay", "delegate"):
            for text, permitted in objectives.items():
                with self.subTest(level=level, objective=text):
                    for n, _ in ctl.records():
                        ctl.record_path(n).unlink()
                    ctl.save("alpha", {"pane": "w7:p1", "authority": level, "hold": 10, "typed": "",
                                       "attached": False, "started": False})
                    self.herdr.log.clear()
                    self.herdr.agents[:] = [a for a in self.herdr.agents if a["name"] != "alpha"]
                    for m in self.inbox("alpha"):
                        m.unlink()
                    self.objective.write_text(text + "\n", encoding="utf-8")
                    code, out, _ = self.start()
                    if level in permitted:
                        self.assertEqual(code, 0, out)
                        continue
                    self.refused((code, out, ""))
                    self.assertFalse(any(line.startswith("workspace create") for line in self.herdr.log))
                    self.assertEqual(self.inbox("alpha"), [])
                    self.assertFalse(self.record("alpha")["started"])

    def test_a_path_outside_the_list_never_says_whether_it_exists(self):
        outside = [self.tmp / "missing", self.tmp / "work2"]
        lines = {self.c("start", "alpha", f, self.objective)[1].replace(str(f), "<folder>") for f in outside}
        self.assertEqual(len(lines), 1, lines)

    def test_a_folder_that_isnt_a_directory_is_refused(self):
        (self.folder / "file").write_text("x", encoding="utf-8")
        for folder in (self.folder / "file", self.folder / "missing"):
            with self.subTest(folder=folder):
                self.started_nothing(self.start(folder=folder))

    def test_a_failed_agent_start_is_refused_and_records_nothing(self):
        self.herdr.mode = "startfail"
        code, out, _ = self.start()
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("REFUSED herdr: "), out)
        self.assertIsNone(ctl.load("alpha"))

    def test_only_a_listed_folder_or_one_inside_it(self):
        self.assertEqual(self.start(folder=self.work)[0], 0)
        for folder in (self.tmp, self.tmp / "work2"):
            with self.subTest(folder=folder):
                self.herdr.log.clear()
                self.refused(self.start("beta", folder=folder))
                self.assertIsNone(ctl.load("beta"))
                self.assertFalse(any(line.startswith("workspace create") for line in self.herdr.log))

    def test_without_the_folders_file_nothing_starts(self):
        self.folders.unlink()
        self.started_nothing(self.start())

    def test_an_objective_that_cant_be_read_is_refused(self):
        bad = self.tmp / "bad.md"
        for content in (None, b"", b" \n", b"\xff\xfe"):
            with self.subTest(content=content):
                bad.unlink(missing_ok=True)
                if content is not None:
                    bad.write_bytes(content)
                self.started_nothing(self.start(objective=bad))

    def test_a_fourth_running_started_session_is_refused(self):
        for i, name in enumerate(("aa", "bb", "cc")):
            ctl.save(name, {"pane": f"w7:p{i}", "authority": "delegate", "hold": 10, "typed": "", "attached": False,
                            "started": True})
        # aa runs under its name, bb in its pane after herdr cleared its name, cc no longer runs.
        self.herdr.agents += [{"name": "aa", "agent": "claude", "agent_status": "idle", "pane_id": "w7:p0"},
                              {"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w7:p1"}]
        self.assertEqual(self.start()[0], 0)
        self.herdr.log.clear()
        ctl.save("alpha", {**self.record("alpha"), "started": False})
        self.herdr.agents.append({"name": None, "agent": "claude", "agent_status": "idle", "pane_id": "w7:p2"})
        self.refused(self.start("beta"))
        self.assertIsNone(ctl.load("beta"))
        self.assertFalse(any(line.startswith("workspace create") for line in self.herdr.log))

    def test_a_name_a_live_agent_holds_is_refused(self):
        self.herdr.agents.append({"name": "alpha", "agent": "claude", "agent_status": "idle", "pane_id": "w2:p1"})
        self.started_nothing(self.start())

    def test_owner_and_names_outside_the_pattern_are_refused(self):
        for name in ("owner", "Alpha", "a" * 33):
            with self.subTest(name=name):
                self.refused(self.start(name))
        self.assertFalse(any(line.startswith("workspace create") for line in self.herdr.log))

    def test_wrong_arguments_are_usage_errors(self):
        code, out, err = self.c("start", "alpha", self.folder)
        self.assertEqual((code, out), (1, ""))
        self.assertNotEqual(err, "")


class Protocol(unittest.TestCase):
    """protocol.md's printed lines and ctl.py's, compared by shape: each <placeholder> or {expression} is one *."""

    @staticmethod
    def shape(line):
        return re.sub(r"<[^>]+>|\{[^}]+\}", "*", line)

    def test_protocol_names_every_line_ctl_prints_and_no_other(self):
        doc = (SKILL / "references" / "protocol.md").read_text(encoding="utf-8")
        subcommands = doc[doc.index("## Session subcommands"):doc.index("## What the hooks call")]
        # Every "| `<line>` | <exit> |" row; wait's lines are mail.py's own, which test_mail.py checks.
        documented = {self.shape(m) for m in re.findall(r"^\| `([^`]+)` \| \d \|", subcommands, re.M)}
        documented |= set(re.findall(r"\bit prints `([^`]+)`", subcommands))
        source = (SKILL / "scripts" / "ctl.py").read_text(encoding="utf-8")
        printed = {self.shape(m) for m in re.findall(r'\bprint\(f?"([^"]+)"\)', source)}
        printed |= {self.shape(f"REFUSED {m}") for m in
                    re.findall(r'\b(?:Refused|super\(\)\.__init__)\(f?"([^"]+)"\)', source)}
        # main prints each refusal as REFUSED <reason>; the reasons are collected above.
        printed.discard("REFUSED *")
        self.assertTrue(documented)
        # SENT is mail.py's send line, which ctl.py prints through mail.send.
        self.assertIn("mail.send(", source)
        self.assertEqual({d for d in documented if not d.startswith("SENT ")}, printed)
