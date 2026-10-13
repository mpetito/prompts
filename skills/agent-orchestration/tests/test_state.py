"""state.py, decisions.py, wake_at.py and meter.py: the thread's state file, its decision queue, its timer and its
budget meter."""
import json
import os
import re
import subprocess
import sys
import time
import unittest.mock

from .support import SCRIPTS, UTC, OrchTest, call, load

STATE = load(SCRIPTS / "state.py")
DECISIONS = load(SCRIPTS / "decisions.py")
WAKE = load(SCRIPTS / "wake_at.py")
METER = load(SCRIPTS / "meter.py")


def section(text, start, end):
    """The lines from the one starting with start through the next one starting with end, as sed -n '/a/,/b/p'."""
    lines = text.split("\n")
    first = next(i for i, line in enumerate(lines) if line.startswith(start))
    last = next(i for i in range(first + 1, len(lines)) if lines[i].startswith(end))
    return lines[first:last + 1]


class Resolution(OrchTest):
    def setUp(self):
        super().setUp()
        self.plain = self.tmp / "plain"
        self.plain.mkdir()
        self.coord = self.repo(self.tmp / "coord", commit=False)

    def test_outside_git_names_the_variable_to_set(self):
        code, _, err = call(STATE, "log", "x", cwd=self.plain)
        self.assertEqual(code, 1)
        self.assertRegex(err, "not inside a git worktree.*set ORCHESTRATION_STATE")
        code, _, err = call(DECISIONS, "list", cwd=self.plain)
        self.assertEqual(code, 1)
        self.assertIn("set ORCHESTRATION_DECISIONS", err)

    def test_resolves_the_worktree_root(self):
        code, _, err = call(STATE, "log", "x", cwd=self.coord)
        self.assertEqual(code, 1)
        self.assertIn(f"no state file at {os.path.join(self.coord, '.orchestration', 'state.md')}", err)

    def test_now_prints_a_utc_stamp(self):
        self.assertRegex(call(STATE, "now")[1], f"^{UTC}\n$")


class Thread(OrchTest):
    """init, thread, log and resume in a coordination worktree, run from a folder below its root."""

    def setUp(self):
        super().setUp()
        self.coord = self.repo(self.tmp / "coord", commit=False)
        (self.coord / "sub").mkdir()
        self.orch = self.coord / ".orchestration"
        self.file = self.orch / "state.md"
        self.assertEqual(self.state("init", "b1")[0], 0)

    def state(self, *argv, stdin=""):
        return call(STATE, *argv, stdin=stdin, cwd=self.coord / "sub")

    def text(self):
        return self.file.read_text(encoding="utf-8")

    def test_init_writes_the_skeleton_at_the_worktree_root(self):
        os.remove(self.file)
        code, out, _ = self.state("init", "b1")
        self.assertEqual(code, 0)
        self.assertRegex(out, f"^initialised {re.escape(str(self.file))} {UTC}\n$")
        self.assertTrue((self.orch / "briefs").is_dir() and (self.orch / "results").is_dir())
        heads = [line for line in self.text().split("\n") if line.startswith("#")]
        self.assertEqual(heads, ["# Orchestration thread: b1", "## Thread", "## RESUME", "## Lanes", "## Decisions",
                                 "## Log"])
        self.assertRegex(self.text(), f"(?m)^Record: thread.md.*\n^Started: {UTC}$(.|\n)*^Written: {UTC}$")
        self.assertNotRegex(self.text(), "(?m)^MAIN:")

    def test_init_refuses_an_existing_file_and_the_old_main_argument(self):
        before = self.text()
        self.assertEqual(self.state("init", "b1")[0], 1)
        self.assertEqual(self.state("init", "b1", "prompts-9d")[0], 1)
        self.assertEqual(self.text(), before)
        os.remove(self.file)
        self.assertEqual(self.state("init", "b1", "prompts-9d")[0], 1)
        self.assertFalse(self.file.exists())

    def test_thread_reads_a_record_field(self):
        (self.orch / "thread.md").write_text("# record\nBUILD: b1\nCHECKOUT: /x\nBASE: dev\n"
                                             "LANE-BASE: orchestration/b1\nLANDING: local\n", encoding="utf-8")
        self.assertEqual(self.state("thread", "LANE-BASE")[:2], (0, "orchestration/b1\n"))
        code, out, _ = self.state("thread", "NOPE")
        self.assertEqual((code, out), (1, ""))
        self.assertEqual(self.state("thread")[0], 1)
        self.assertEqual(self.state("main")[0], 1)

    def test_log_appends_to_the_log_section(self):
        code, out, _ = self.state("log", "lane A launched")
        self.assertEqual(code, 0)
        self.assertRegex(out, f"^logged {UTC}\n$")
        self.assertRegex(self.text().split("\n")[-2], f"^- {UTC} lane A launched$")

    def test_resume_replaces_the_body_with_one_stamp(self):
        code, out, _ = self.state("resume", "-", stdin="Lanes A, B done.\nWritten: 1999-01-01T00:00Z\nNext: lane C.\n")
        self.assertEqual(code, 0)
        self.assertRegex(out, "^resume written")
        resume = section(self.text(), "## RESUME", "## Lanes")
        self.assertTrue(any(re.fullmatch(f"Written: {UTC}", line) for line in resume))
        self.assertEqual(len(re.findall("(?m)^Written:", self.text())), 1)
        self.assertRegex(resume[2], "^Written:")
        self.assertIn("\nNext: lane C.\n", self.text())
        self.assertNotIn("(nothing yet)", self.text())
        self.assertRegex(self.text(), "(?m)^## Lanes$(.|\n)*^## Log$")
        self.assertTrue(list(self.orch.glob("state.*.md")))

    def test_resume_reads_a_file_and_refuses_an_empty_body(self):
        before = self.text()
        self.assertEqual(self.state("resume", "-", stdin="   \n")[0], 1)
        self.assertEqual(self.state("resume", str(self.tmp / "missing"))[0], 1)
        utf16 = self.tmp / "utf16.md"
        utf16.write_bytes("From PowerShell.\n".encode("utf-16"))
        self.assertEqual(self.state("resume", str(utf16))[0], 1)
        self.assertEqual(self.text(), before)
        body = self.tmp / "resume.md"
        body.write_text("From a file.\n", encoding="utf-8")
        self.assertEqual(self.state("resume", str(body))[0], 0)
        self.assertIn("\nFrom a file.\n", self.text())

    def test_decisions_live_beside_the_state_file(self):
        call(DECISIONS, "add", "Tea or coffee", "lane B", "lane B", "tea", "+2h", cwd=self.coord / "sub")
        self.assertTrue((self.orch / "decisions.md").is_file())


LEGACY = """# Orchestrator state: test

## Lanes

| Lane | Agent | PR | Head SHA | Next action |
| --- | --- | --- | --- | --- |
| alpha | codex | #1 | abc1234 | review |
| beta | opus | #2 | def5678 | land |
| scripts | - | - | - | brief |

## Log

- 2026-10-01T00:00Z started

## Notes

kept below the log
"""


class ExplicitFile(OrchTest):
    """$ORCHESTRATION_STATE names the file, outside any git worktree."""

    def setUp(self):
        super().setUp()
        (self.tmp / "legacy").mkdir()
        self.file = self.tmp / "legacy" / "state.md"
        self.file.write_text(LEGACY, encoding="utf-8")
        os.environ["ORCHESTRATION_STATE"] = str(self.file)

    def state(self, *argv):
        return call(STATE, *argv, cwd=self.tmp)

    def lines(self):
        return self.file.read_text(encoding="utf-8").split("\n")[:-1]

    def test_log_inserts_at_the_end_of_the_log_section(self):
        self.state("log", "merged #2")
        log = section("\n".join(self.lines()), "## Log", "## Notes")
        self.assertTrue(any(re.fullmatch(f"- {UTC} merged #2", line) for line in log))
        self.assertEqual(log.count(""), 2)
        # The entry joins the block: right after the last entry, with the blank line still before "## Notes".
        self.assertEqual(log[-4], "- 2026-10-01T00:00Z started")
        self.assertRegex(log[-3], f"^- {UTC} merged #2$")
        self.assertIn("kept below the log", self.lines()[-1])
        self.assertEqual(self.state("log")[0], 1)
        self.assertEqual(self.state("log", "")[0], 1)

    def test_log_adds_a_missing_log_section(self):
        self.file.write_text("# s\n\n## Lanes\n", encoding="utf-8")
        self.state("log", "first")
        self.assertEqual(self.lines()[:-1], ["# s", "", "## Lanes", "", "## Log", ""])
        self.assertRegex(self.lines()[-1], f"^- {UTC} first$")

    def test_set_replaces_one_cell(self):
        self.assertRegex(self.state("set", "beta", "Head SHA", "9999999")[1], f"^set beta.Head SHA {UTC}\n$")
        self.assertIn("| beta | opus | #2 | 9999999 | land |", self.lines())
        self.assertIn("| alpha | codex | #1 | abc1234 | review |", self.lines())
        # A lane not yet started has "-" cells; the separator row never matches a lane.
        self.assertEqual(self.state("set", "scripts", "Agent", "opus")[0], 0)
        self.assertIn("| scripts | opus | - | - | brief |", self.lines())
        self.assertIn("| --- | --- | --- | --- | --- |", self.lines())
        self.assertIn("| beta | opus | #2 | 9999999 | land |", self.lines())

    def test_set_refuses_an_unknown_lane_or_column(self):
        self.assertEqual(self.state("set", "gamma", "Head SHA", "1")[0], 1)
        self.assertEqual(self.state("set", "beta", "Nope", "1")[0], 1)
        self.assertEqual(self.file.read_text(encoding="utf-8"), LEGACY)

    def test_resume_needs_a_resume_section(self):
        self.assertEqual(call(STATE, "resume", "-", stdin="body\n", cwd=self.tmp)[0], 1)
        self.assertEqual(self.file.read_text(encoding="utf-8"), LEGACY)

    def test_backup_copies_the_file_beside_it(self):
        code, out, _ = self.state("backup")
        self.assertEqual(code, 0)
        copies = list(self.file.parent.glob("state.*.md"))
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies[0].read_text(encoding="utf-8"), LEGACY)


class Decisions(OrchTest):
    def setUp(self):
        super().setUp()
        self.file = self.tmp / "legacy" / "decisions.md"
        os.environ["ORCHESTRATION_DECISIONS"] = str(self.file)

    def decide(self, *argv):
        return call(DECISIONS, *argv, cwd=self.tmp)

    def test_add_list_due_close(self):
        code, out, _ = self.decide("add", "Ship the banner", "blocks the demo", "lane w3", "ship it", "+0m")
        self.assertEqual(code, 0)
        self.assertRegex(out, f"^D1 applies at {UTC}\n$")
        self.decide("add", "Rename the table", "nothing", "none", "keep the name", "+48h")
        self.assertRegex(self.decide("add", "Spend 40 USD", "quota", "lane w4", "none", "owner-before")[1],
                         "^D3 owner-before")
        self.assertEqual(len(self.decide("list")[1].splitlines()), 3)
        due = self.decide("due")[1]
        self.assertRegex(due, "(?m)^- D1 ")
        self.assertNotRegex(due, "(?m)^- D2 ")
        self.assertNotRegex(due, "(?m)^- D3 ")
        self.assertEqual(self.decide("close", "D1", "default applied")[0], 0)
        self.assertEqual(len(self.decide("list")[1].splitlines()), 2)
        closed = re.findall("(?m)^- D1 .*closed .*default applied$", self.file.read_text(encoding="utf-8"))
        self.assertEqual(len(closed), 1)
        self.assertEqual(self.decide("close", "D1", "again")[0], 1)

    def test_add_refuses_a_bad_deadline_or_argument_count(self):
        self.assertEqual(self.decide("add", "a", "b", "c", "d", "tomorrow")[0], 1)
        self.assertEqual(self.decide("add", "a", "b", "c", "+1h")[0], 1)
        self.assertEqual(self.decide("add", "a", "b", "c", "d", "+1h", "extra")[0], 1)
        self.assertFalse(self.file.exists())

    def test_due_and_close_read_only_open_items(self):
        self.file.parent.mkdir()
        item = "- D1 (x) new · applies at 2000-01-01T00:00Z unless the owner objects"
        self.file.write_text(f"# Decisions\n\n## Open\n\nnote: applies at 2000-01-01T00:00Z\n{item}\n\n## Applied\n"
                             "- D1 (x) old · closed x: kept\n", encoding="utf-8")
        self.assertEqual(self.decide("due")[1], item + "\n")
        self.decide("close", "D1", "done")
        self.assertIn("- D1 (x) old · closed x: kept", self.file.read_text(encoding="utf-8").split("\n"))


class WakeAt(OrchTest):
    def wake(self, *argv):
        with unittest.mock.patch.object(WAKE.time, "sleep") as sleep:
            return call(WAKE, *argv), sleep

    def test_prints_the_wake_line(self):
        (code, out, _), _ = self.wake("+0m", "lane-b")
        self.assertEqual(code, 0)
        self.assertRegex(out, f"^WAKE lane-b {UTC} \\(armed for {UTC}\\)\n$")

    def test_wakes_at_once_for_a_past_time(self):
        (code, out, _), sleep = self.wake("2000-01-01T00:00Z")
        self.assertRegex(out, "^WAKE timer ")
        sleep.assert_called_once_with(0)
        self.assertRegex(self.wake("+0m", "")[0][1], "^WAKE timer ")

    def test_sleeps_until_the_target(self):
        (code, out, _), sleep = self.wake("+2m")
        self.assertAlmostEqual(sleep.call_args.args[0], 120, delta=2)

    def test_refuses_a_bad_time_or_argument_count(self):
        for argv in (("soon",), ("+1m", "a", "b")):
            (code, _, _), sleep = self.wake(*argv)
            self.assertEqual(code, 1, argv)
            sleep.assert_not_called()


class Meter(OrchTest):
    def setUp(self):
        super().setUp()
        self.sessions = self.tmp / "sessions"
        self.sessions.mkdir()
        os.environ["CODEX_SESSIONS"] = str(self.sessions)

    def log(self, primary, root=None):
        (root or self.sessions).joinpath("s.jsonl").write_text(
            json.dumps({"payload": {"rate_limits": primary}}) + "\n", encoding="utf-8")

    def meter(self, *argv):
        return call(METER, *argv)[1]

    def test_unknown_without_logs(self):
        self.assertRegex(self.meter(), "^codex=unknown .*verdict=unknown")

    def test_verdicts(self):
        self.log({"primary": {"used_percent": 50, "resets_at": 1791600000}})
        self.assertIn("verdict=normal", self.meter())
        self.log({"primary": {"used_percent": 75, "resets_at": 1791600000}})
        self.assertEqual(len(re.findall("(?m)verdict=rotate|^rule: ask MAIN to rotate", self.meter())), 2)
        self.log({"primary": {"used_percent": 100, "resets_at": 1791600000}})
        self.assertIn("verdict=stop", self.meter())

    def test_unknown_without_a_primary_meter(self):
        self.log({"secondary": {"used_percent": 5}})
        self.assertRegex(self.meter(), "^codex=unknown .*no primary meter")

    def test_reads_the_last_meter_line(self):
        line = json.dumps({"payload": {"rate_limits": {"primary": {"used_percent": 90, "resets_at": 1791600000}}}})
        (self.sessions / "s.jsonl").write_text(line + "\n" + line.replace("90", "20") + "\n", encoding="utf-8")
        self.assertRegex(self.meter(), "^codex=20% ")

    def test_unknown_for_a_reading_that_is_not_a_number(self):
        for primary in ({"used_percent": "n/a", "resets_at": 1791600000}, {"used_percent": 50}):
            self.log({"primary": primary})
            self.assertRegex(self.meter(), "^codex=unknown .*no primary meter", primary)

    def test_refuses_a_bad_switch(self):
        self.assertEqual(call(METER, "--switch", "abc")[0], 1)

    def test_reads_the_newest_log_with_a_meter(self):
        old, new, empty = (self.sessions / d for d in ("2026/10/01", "2026/10/02", "2026/10/03"))
        for d in (old, new, empty):
            d.mkdir(parents=True)
        self.log({"primary": {"used_percent": 90, "resets_at": 1791600000}}, old)
        self.log({"primary": {"used_percent": 10, "resets_at": 1791600000}}, new)
        (empty / "s.jsonl").write_text('{"payload":{}}\n', encoding="utf-8")
        for i, d in enumerate((old, new, empty)):
            os.utime(d / "s.jsonl", (time.time() + i, time.time() + i))
        self.assertRegex(self.meter(), "^codex=10% .*verdict=normal")

    def test_defaults_to_the_home_folder(self):
        del os.environ["CODEX_SESSIONS"]
        home = self.home / ".codex" / "sessions"
        home.mkdir(parents=True)
        self.log({"primary": {"used_percent": 0, "resets_at": 1791600000}}, home)
        self.assertRegex(self.meter(), "^codex=0% resets=2026-10-10T.*verdict=normal")


class Usage(OrchTest):
    """Each script run as a program: a usage error exits 1 with the usage on stderr."""

    def run_script(self, name, *argv):
        return subprocess.run([sys.executable, str(SCRIPTS / name), *argv], capture_output=True, text=True,
                              cwd=self.tmp)

    def test_state_and_decisions_print_their_header(self):
        for name, module in (("state.py", STATE), ("decisions.py", DECISIONS)):
            r = self.run_script(name, "nope")
            self.assertEqual(r.returncode, 1, name)
            self.assertEqual(r.stderr.strip(), module.__doc__.strip(), name)

    def test_wake_at_and_meter_print_their_usage(self):
        for name, argv in (("wake_at.py", ()), ("meter.py", ("--nope",))):
            r = self.run_script(name, *argv)
            self.assertEqual(r.returncode, 1, name)
            self.assertRegex(r.stderr, f"^usage: {re.escape(name)} ", name)
