"""run_skill_eval.py in-process, with uv, skill-benchmark and the trigger shim faked at its run(). The suites it
reads are the repository's own (skill-authoring, pull-request, the verifier agent); every run directory goes under
a temporary --out-root, and a regrade gets a run directory built here."""
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import run_skill_eval as rse

ROWS = 5  # tasks a faked prepare writes


def option(args, name):
    return args[args.index(name) + 1]


def variants_of(args):
    return [args[i + 1] for i, a in enumerate(args) if a == "--variant"]


class FakeRun:
    """Stands in for rse.run: records every command, and writes the files each harness verb would write. fail
    holds the verbs (or "uv", "shim") that exit 1 instead; a verb in missing exits 127, as for a command not on
    PATH."""

    def __init__(self, tool_dir, benchmark):
        self.tool_dir, self.benchmark = tool_dir, benchmark
        self.calls, self.fail, self.missing = [], set(), set()

    def __call__(self, args, log=None):
        self.calls.append(list(args))
        if log:
            Path(log).write_text("log\n", encoding="utf-8")
        if args[:3] == ["uv", "tool", "dir"]:
            return subprocess.CompletedProcess(args, 1 if "uv" in self.fail else 0, f"{self.tool_dir}\n", "")
        if args[0] == "skill-benchmark":
            verb = args[1]
            if verb in self.missing:
                return subprocess.CompletedProcess(args, 127, "", "skill-benchmark: command not found\n")
            if verb in self.fail:
                return subprocess.CompletedProcess(args, 1, "", "boom\n")
            if verb == "prepare":
                rows = "".join(json.dumps({"task": i}) + "\n" for i in range(ROWS))
                Path(option(args, "--out")).write_text(rows, encoding="utf-8")
            elif verb == "judge":
                Path(option(args, "--out")).write_text(json.dumps({"judged": option(args, "--variant")}) + "\n",
                                                       encoding="utf-8")
            elif verb == "benchmark":
                Path(option(args, "--out")).write_text(json.dumps(self.benchmark), encoding="utf-8")
            return subprocess.CompletedProcess(args, 0, f"{verb} ok\n", "")
        if args[3].endswith("trigger_matrix_shim.py"):
            if "shim" not in self.fail:
                Path(option(args, "--out")).write_text(json.dumps(TRIGGER), encoding="utf-8")
            return subprocess.CompletedProcess(args, 1 if "shim" in self.fail else 0, "", "")
        raise AssertionError(f"unexpected command {args}")

    def verbs(self, verb):
        return [c for c in self.calls if c[:2] == ["skill-benchmark", verb]]

    def shims(self):
        return [c for c in self.calls if len(c) > 3 and c[3].endswith("trigger_matrix_shim.py")]


BENCHMARK = {
    "summary": {"with_skill": {"mean_objective_pass_rate": 1.0, "cost_usd_total": 0.471},
                "without_skill": {"mean_objective_pass_rate": 0.8125, "cost_usd_total": None},
                "old_skill": {"mean_objective_pass_rate": 0.75, "cost_usd_total": 1234.5}},
    "paired_summary": {"absolute_delta": 0.1875},
    "results": [
        {"case_id": "c2", "variant": "old_skill", "qualitative_assertions": [],
         "assertions": [{"name": "A-rule", "passed": False}]},
        # A zero verdict first: the PowerShell runner dropped it from the mean.
        {"case_id": "c1", "variant": "without_skill", "qualitative_assertions": [{"score": 0.0}],
         "assertions": [{"name": "b-rule", "passed": False}, {"name": "kept", "passed": True}]},
        {"case_id": "c1", "variant": "without_skill", "qualitative_assertions": [{"score": 0.5}, {"score": None}],
         "assertions": [{"name": "b-rule", "passed": False}, {"name": "unknown", "passed": None}]},
        {"case_id": "c1", "variant": "with_skill", "qualitative_assertions": [{"score": 0.9}],
         "assertions": [{"name": "A-rule", "passed": True}]},
    ],
}
SUMMARY = [
    "  with_skill                     objective 1.00  judge 0.90  cost USD 0.47",
    "  without_skill                  objective 0.81  judge 0.25  cost USD n/a",
    "  paired delta, with minus without: 0.19",
    "  failed 2x  c1/without_skill: b-rule",
    "  failed 1x  c2/old_skill: A-rule",
]
TRIGGER = {"matrix": [{"agent": "claude", "model": "sonnet",
                       "summary": {"should_trigger": {"passed": 4, "total": 5},
                                   "should_not_trigger": {"passed": 5, "total": 5}},
                       "queries": [{"query": "open a PR", "runs": 3, "passed_runs": 1},
                                   {"query": "review this", "runs": 3, "passed_runs": 3}]}]}
TRIGGER_LINES = ["  trigger claude/sonnet: should-fire 4/5  should-not-fire 5/5",
                 "    missed (2 of 3 runs): open a PR"]


# The live files a run reads; no run may write them. The run manifest is a copy beside the run.
LIVE = [rse.REPO / p for p in ("skills/skill-authoring/evals/shared-benchmark.json", "skills/skill-authoring/SKILL.md",
                               "skills/pull-request/evals/shared-benchmark.json", "skills/pull-request/SKILL.md",
                               "evals/agents/verifier/shared-benchmark.json", "agents/verifier.md")]


def digests(paths):
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


class RunnerTest(unittest.TestCase):
    def setUp(self):
        before = digests(LIVE)
        self.addCleanup(lambda: self.assertEqual(digests(LIVE), before, "a run wrote a live manifest or SKILL.md"))
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.tool_dir = self.tmp / "tools"
        self.python = self.tool_dir / "skill-eval-harness" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        self.python.parent.mkdir(parents=True)
        self.python.write_text("", encoding="utf-8")
        self.out_root = self.tmp / "runs"
        self.fake = FakeRun(self.tool_dir, BENCHMARK)
        for patch in (unittest.mock.patch.object(rse, "run", self.fake), unittest.mock.patch.dict(os.environ)):
            patch.start()
            self.addCleanup(patch.stop)

    def main(self, *argv, out_root=True, cwd=None):
        """rse.main as its __main__ block runs it, in cwd when given: (exit code, stdout, stderr)."""
        argv = [*argv, "--out-root", str(self.out_root)] if out_root else list(argv)
        out, err = io.StringIO(), io.StringIO()
        old = os.getcwd()
        try:
            if cwd:
                os.chdir(cwd)
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = rse.main(argv)
                except rse.Fail as e:
                    print(e, file=sys.stderr)
                    code = 1
        finally:
            os.chdir(old)
        return code, out.getvalue(), err.getvalue()

    def wrapper(self, d, name):
        return str(d / f"{name}{'.cmd' if os.name == 'nt' else '.sh'}")

    def run_dir(self, name):
        (stamp,) = (self.out_root / name).iterdir()
        return stamp

    def lines(self, out):
        return out.splitlines()


class OptionsTest(RunnerTest):
    def test_each_option_reaches_the_harness(self):
        code, out, _ = self.main("--skill", "skill-authoring", "--runs", "3", "--trigger-runs", "2", "--model", "opus",
                                 "--judge-model", "haiku", "--effort", "high", "--split", "holdout",
                                 "--timeout-seconds", "30", "--parallel", "2")
        self.assertEqual(code, 0)
        (prepare,) = self.fake.verbs("prepare")
        self.assertEqual((option(prepare, "--runs-per-variant"), option(prepare, "--split")), ("3", "holdout"))
        answers = self.fake.verbs("run-agent")
        self.assertEqual(len(answers), 2)
        for a in answers:
            self.assertEqual((option(a, "--agent"), option(a, "--model"), option(a, "--timeout")),
                             ("claude", "opus", "30"))
        (shim,) = self.fake.shims()
        self.assertEqual((option(shim, "--runs-per-query"), option(shim, "--model"), option(shim, "--timeout")),
                         ("2", "opus", "30"))
        for j in self.fake.verbs("judge"):
            self.assertEqual((option(j, "--judge-model"), option(j, "--split"), option(j, "--judge-backend")),
                             ("haiku", "holdout", "claude"))
        (bench,) = self.fake.verbs("benchmark")
        self.assertEqual(option(bench, "--split"), "holdout")
        out_dir = self.run_dir("skill-authoring")
        self.assertIn("--effort high", (out_dir / f"claude-eval{self.ext()}").read_text())
        self.assertNotIn("--effort", (out_dir / f"claude-judge{self.ext()}").read_text())

    def ext(self):
        return ".cmd" if os.name == "nt" else ".sh"

    def test_defaults(self):
        o = rse.parse([])
        self.assertEqual((o.agent, o.model, o.judge_model, o.runs, o.trigger_runs, o.split, o.timeout_seconds,
                          o.parallel, o.effort, o.skill), ("claude", "sonnet", "sonnet", 1, 1, "tune", 600, 4, None, []))
        self.assertFalse(any((o.skip_trigger, o.skip_judge, o.trigger_only, o.include_old_skill, o.rejudge)))

    def test_skills_are_comma_separated_or_repeated(self):
        self.assertEqual(rse.skill_list(["a, b,", "c"]), ["a", "b", "c"])

    def test_every_suite_by_default(self):
        repo = self.tmp / "repo"
        for suite in ("skills/b", "skills/a", "archive/skills/a", "archive/skills/c"):
            (repo / suite / "evals").mkdir(parents=True)
            (repo / suite / "evals" / "shared-benchmark.json").write_text("{}", encoding="utf-8")
        (repo / "skills" / "no-evals").mkdir()
        (repo / "skills" / "a-file").write_text("", encoding="utf-8")
        with unittest.mock.patch.object(rse, "REPO", repo):
            self.assertEqual(rse.skill_list([]), ["a", "b", "c"])
            self.assertEqual(rse.manifest_path("c"), str(repo / "archive/skills/c/evals/shared-benchmark.json"))
            self.assertEqual(rse.manifest_path("a"), str(repo / "skills/a/evals/shared-benchmark.json"))

    def test_codex_takes_effort_in_its_command_and_no_wrapper(self):
        code, _, _ = self.main("--skill", "skill-authoring", "--agent", "codex", "--effort", "high")
        self.assertEqual(code, 0)
        for a in self.fake.verbs("run-agent"):
            self.assertEqual(option(a, "--codex-cmd"), "codex exec --json -c model_reasoning_effort=high")
            self.assertNotIn("--claude-bin", a)
        for c in self.fake.verbs("judge") + self.fake.shims():
            self.assertNotIn("--claude-bin", c)
        self.assertEqual(option(self.fake.verbs("judge")[0], "--judge-backend"), "codex")

    def test_usage_errors_exit_1(self):
        for argv in (["--runs", "0"], ["--runs", "51"], ["--parallel", "17"], ["--agent", "copilot"],
                     ["--effort", "huge"], ["--bogus"],
                     ["--agent-definition", "verifier", "--skill", "review"],
                     ["--agent-definition", "verifier", "--agent", "codex"],
                     ["--agent-definition", "verifier", "--trigger-only"],
                     ["--skill", "review,spec", "--baseline", str(self.skill_folder())]):
            with self.subTest(argv=argv):
                code, out, err = self.main(*argv)
                self.assertEqual(code, 1)
                self.assertTrue(err)
                self.assertEqual(self.fake.verbs("validate"), [])

    def skill_folder(self):
        folder = self.tmp / "base" / "prev-skill"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        return folder

    def test_usage_error_as_a_process(self):
        r = subprocess.run([sys.executable, str(Path(rse.__file__)), "--runs", "0"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("usage:", r.stderr)


class LayoutTest(RunnerTest):
    def test_run_directory(self):
        code, out, _ = self.main("--skill", "skill-authoring", "--parallel", "2")
        self.assertEqual(code, 0)
        d = self.run_dir("skill-authoring")
        manifest = rse.REPO / "skills" / "skill-authoring" / "evals" / "shared-benchmark.json"
        self.assertRegex(d.name, r"^\d{8}-\d{6}$")
        self.assertEqual((d / "source-manifest.txt").read_text(encoding="utf-8"), f"{manifest}\n")
        self.assertFalse((d / "manifest.json").exists())
        self.assertFalse((d / "baseline.txt").exists())
        (validate,) = self.fake.verbs("validate")
        self.assertEqual(validate[2:], [str(manifest), "--strict-leakage"])
        # Round-robin shards over the prepared rows.
        rows = (d / "tasks.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual((d / "tasks-0.jsonl").read_text(encoding="utf-8").splitlines(), rows[0::2])
        self.assertEqual((d / "tasks-1.jsonl").read_text(encoding="utf-8").splitlines(), rows[1::2])
        self.assertFalse((d / "tasks-2.jsonl").exists())
        # Shards run at once, so their calls arrive in any order.
        answers = self.fake.verbs("run-agent")
        self.assertCountEqual([option(a, "--tasks") for a in answers], [str(d / "tasks-0.jsonl"), str(d / "tasks-1.jsonl")])
        for a in answers:
            self.assertEqual((option(a, "--runs"), option(a, "--claude-bin")),
                             (str(d / "runs"), str(d / f"claude-eval{self.ext()}")))
        for i in range(2):
            self.assertTrue((d / "logs" / f"answers-{i}.log").exists())
        # One judge per arm, with the judge's own wrapper, concatenated in arm order.
        judges = self.fake.verbs("judge")
        self.assertCountEqual([option(j, "--variant") for j in judges], ["with_skill", "without_skill"])
        for j in judges:
            self.assertEqual(option(j, "--claude-bin"), str(d / f"claude-judge{self.ext()}"))
        self.assertEqual([json.loads(line)["judged"] for line in
                          (d / "judge-results.jsonl").read_text(encoding="utf-8").splitlines()],
                         ["with_skill", "without_skill"])
        (bench,) = self.fake.verbs("benchmark")
        self.assertEqual(variants_of(bench), ["with_skill", "without_skill"])
        self.assertEqual((option(bench, "--out"), option(bench, "--judge-results")),
                         (str(d / "benchmark.json"), str(d / "judge-results.jsonl")))
        (render,) = self.fake.verbs("render-viewer")
        self.assertEqual(option(render, "--out"), str(d / "review.html"))
        # The trigger matrix runs on the harness's Python, against the source manifest.
        (shim,) = self.fake.shims()
        self.assertEqual(shim[:3], [str(self.python), "-X", "utf8"])
        self.assertEqual((shim[-3], option(shim, "--out"), option(shim, "--trace-runs")),
                         (str(manifest), str(d / "trigger-matrix.json"), str(d / "trigger-traces")))
        self.assertTrue((d / "logs" / "trigger.log").exists())
        self.assertEqual(os.environ["PYTHONUTF8"], "1")
        lines = self.lines(out)
        self.assertIn("== skill-authoring ==", lines)
        self.assertIn(f"  artifacts: {d}", lines)

    def ext(self):
        return ".cmd" if os.name == "nt" else ".sh"

    def test_wrappers_load_project_settings_and_deny_acting_tools(self):
        d = self.tmp / "w"
        d.mkdir()
        wrapper = Path(rse.claude_wrapper(d, "max", name="x"))
        text = wrapper.read_text(encoding="ascii")
        self.assertEqual(wrapper.name, f"x{self.ext()}")
        self.assertIn("claude --setting-sources project --strict-mcp-config --effort max --disallowedTools", text)
        for tool in ("Bash", "PowerShell", "Write", "Edit", "Agent", "WebFetch"):
            self.assertIn(tool, text)
        for var in ("CLAUDECODE", "HERDR_PANE_ID", "HERDR_SOCKET_PATH"):
            self.assertIn(var, text)
        if os.name != "nt":
            self.assertTrue(text.startswith("#!/bin/sh\n"))
            self.assertTrue(text.rstrip("\n").endswith('"$@"'))
            self.assertTrue(os.access(wrapper, os.X_OK))

    def test_fewer_tasks_than_parallel_makes_one_shard_each(self):
        code, out, _ = self.main("--skill", "skill-authoring", "--parallel", "16", "--skip-trigger", "--skip-judge")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.fake.verbs("run-agent")), ROWS)
        self.assertIn(f"tasks in {ROWS} parallel shards", out)

    def test_skip_trigger_and_skip_judge(self):
        code, out, _ = self.main("--skill", "skill-authoring", "--skip-trigger", "--skip-judge")
        self.assertEqual(code, 0)
        self.assertEqual((self.fake.shims(), self.fake.verbs("judge")), ([], []))
        self.assertNotIn("--judge-results", self.fake.verbs("benchmark")[0])
        self.assertFalse(any(line.startswith("  trigger ") for line in self.lines(out)))

    def test_trigger_only(self):
        code, out, _ = self.main("--skill", "pull-request", "--trigger-only")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.fake.verbs("validate")), 1)
        for verb in ("prepare", "run-agent", "judge", "benchmark", "render-viewer"):
            self.assertEqual(self.fake.verbs(verb), [], verb)
        self.assertEqual(len(self.fake.shims()), 1)
        lines = self.lines(out)
        start = lines.index("== pull-request ==")
        self.assertEqual(lines[start + 1:start + 3], TRIGGER_LINES)
        self.assertFalse(any("objective" in line for line in lines))


class ArmsTest(RunnerTest):
    def test_baseline_folder_runs_as_old_skill(self):
        baseline = self.tmp / "base" / "prev-skill"
        baseline.mkdir(parents=True)
        (baseline / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        code, out, _ = self.main("--skill", "skill-authoring", "--baseline", str(baseline))
        self.assertEqual(code, 0)
        d = self.run_dir("skill-authoring")
        self.assertEqual((d / "baseline.txt").read_text(encoding="utf-8"), f"{baseline / 'SKILL.md'}\n")
        m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m["old_skill_paths"], [str(baseline / "SKILL.md")])
        skill_root = rse.REPO / "skills" / "skill-authoring"
        self.assertEqual(m["skill_paths"], [os.path.abspath(skill_root / p) for p in
                                            json.loads((skill_root / "evals" / "shared-benchmark.json")
                                                       .read_text(encoding="utf-8"))["skill_paths"]])
        files = [f for c in m["cases"] for f in c.get("files") or []]
        self.assertTrue(files)
        for f in files:
            self.assertTrue(os.path.isabs(f) and os.path.exists(f), f)
        answer_manifest = str(d / "manifest.json")
        self.assertEqual(self.fake.verbs("validate")[0][2], answer_manifest)
        (prepare,) = self.fake.verbs("prepare")
        self.assertEqual(prepare[2], answer_manifest)
        self.assertIn("--include-old-skill", prepare)
        self.assertCountEqual([option(j, "--variant") for j in self.fake.verbs("judge")],
                         ["with_skill", "without_skill", "old_skill"])
        self.assertEqual(variants_of(self.fake.verbs("benchmark")[0]), ["with_skill", "without_skill", "old_skill"])
        # The trigger matrix keeps the source manifest: triggering reads only the description.
        self.assertNotEqual(self.fake.shims()[0][-3], answer_manifest)
        self.assertIn("  old_skill (prev-skill)         objective 0.75  judge n/a  cost USD 1,234.50",
                      self.lines(out))

    def test_baseline_file_is_its_own_skill_md(self):
        skill_md = self.tmp / "SKILL.md"
        skill_md.write_text("---\nname: x\n---\n", encoding="utf-8")
        self.assertEqual(rse.skill_baseline(str(skill_md)), str(skill_md))

    def test_baseline_without_skill_md_fails_the_suite(self):
        code, _, err = self.main("--skill", "skill-authoring", "--baseline", str(self.tmp))
        self.assertEqual(code, 1)
        self.assertIn("skill-authoring", err)
        self.assertEqual(self.fake.verbs("validate"), [])

    def test_include_old_skill_uses_the_manifest_arms(self):
        code, _, _ = self.main("--skill", "skill-authoring", "--include-old-skill", "--skip-trigger")
        self.assertEqual(code, 0)
        manifest = str(rse.REPO / "skills" / "skill-authoring" / "evals" / "shared-benchmark.json")
        (prepare,) = self.fake.verbs("prepare")
        self.assertEqual(prepare[2], manifest)
        self.assertIn("--include-old-skill", prepare)
        self.assertEqual(len(self.fake.verbs("judge")), 3)

    def test_summary_lines(self):
        code, out, _ = self.main("--skill", "skill-authoring")
        self.assertEqual(code, 0)
        lines = self.lines(out)
        start = lines.index("== skill-authoring ==")
        # old_skill has a summary in the canned benchmark, so it prints even without a baseline name.
        self.assertEqual(lines[start + 1:start + 9],
                         SUMMARY[:2] + ["  old_skill                      objective 0.75  judge n/a  cost USD 1,234.50"]
                         + SUMMARY[2:] + TRIGGER_LINES)

    def test_agent_definition_runs_as_the_session(self):
        code, out, _ = self.main("--agent-definition", "verifier", "--effort", "low", "--model", "haiku")
        self.assertEqual(code, 0)
        d = self.run_dir("agent-verifier")
        definition = rse.REPO / "agents" / "verifier.md"
        staged = d / "definitions" / "with_skill" / "verifier.md"
        self.assertEqual(staged.read_text(encoding="utf-8"), definition.read_text(encoding="utf-8"))
        self.assertEqual(json.loads((d / "manifest.json").read_text(encoding="utf-8"))["skill_paths"], [str(staged)])
        pinned = rse.frontmatter_value(definition, "model")
        model = pinned if pinned and pinned != "inherit" else "haiku"
        effort = rse.frontmatter_value(definition, "effort")
        wrapper = d / f"claude-eval{'.cmd' if os.name == 'nt' else '.sh'}"
        self.assertNotIn("--effort", wrapper.read_text())
        answers = self.fake.verbs("run-subagent")
        self.assertTrue(answers)
        self.assertEqual(self.fake.verbs("run-agent"), [])
        expected_cmd = (f'"{self.python}" "{rse.SCRIPTS / "agent_eval_backend.py"}" --claude-bin "{wrapper}"'
                        + (f" --effort {effort}" if effort else ""))
        for a in answers:
            self.assertEqual((option(a, "--model"), option(a, "--agent-cmd")), (model, expected_cmd))
        self.assertEqual(self.fake.shims(), [])
        self.assertIn("  delegation evals for agent definitions are not supported yet; no trigger run",
                      self.lines(out))

    def test_agent_definition_that_inherits_runs_on_the_model_option(self):
        repo = self.tmp / "repo"
        (repo / "agents").mkdir(parents=True)
        (repo / "agents" / "x.md").write_text("---\nname: x\nmodel: inherit\n---\n", encoding="utf-8")
        (repo / "evals" / "agents" / "x").mkdir(parents=True)
        (repo / "evals" / "agents" / "x" / "shared-benchmark.json").write_text(
            json.dumps({"skill_paths": ["SKILL.md"], "cases": []}), encoding="utf-8")
        with unittest.mock.patch.object(rse, "REPO", repo):
            code, out, _ = self.main("--agent-definition", "x", "--model", "haiku")
        self.assertEqual(code, 0)
        for a in self.fake.verbs("run-subagent"):
            self.assertEqual(option(a, "--model"), "haiku")
            self.assertNotIn("--effort", option(a, "--agent-cmd"))

    def test_agent_definition_baseline_is_a_file(self):
        old = self.tmp / "old" / "verifier.md"
        old.parent.mkdir()
        old.write_text("---\nname: verifier\nmodel: opus\n---\nold body\n", encoding="utf-8")
        code, out, _ = self.main("--agent-definition", "verifier", "--baseline", os.path.join("old", "verifier.md"),
                                 "--skip-trigger", cwd=self.tmp)
        self.assertEqual(code, 0)
        d = self.run_dir("agent-verifier")
        recorded = (d / "baseline.txt").read_text(encoding="utf-8").strip()
        self.assertTrue(os.path.isabs(recorded) and os.path.samefile(recorded, old), recorded)
        staged_old = d / "definitions" / "old_skill" / "verifier.md"
        self.assertEqual(json.loads((d / "manifest.json").read_text(encoding="utf-8"))["old_skill_paths"],
                         [str(staged_old)])
        self.assertIn("--include-old-skill", self.fake.verbs("prepare")[0])
        self.assertTrue(any(line.startswith("  old_skill (verifier) ") for line in self.lines(out)))

    def test_agent_definition_without_a_name_fails(self):
        nameless = self.tmp / "nameless.md"
        nameless.write_text("---\nmodel: opus\n---\n", encoding="utf-8")
        with self.assertRaises(rse.Fail):
            rse.stage_definition(str(nameless), str(self.tmp / "staged"))


class SummaryTest(unittest.TestCase):
    def test_an_arm_with_an_empty_summary_still_prints_and_failures_sort_without_case(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "b.json"
            path.write_text(json.dumps({"summary": {"with_skill": {}}, "results": [
                {"case_id": "c", "variant": "with_skill", "assertions": [{"name": "B", "passed": False},
                                                                          {"name": "a", "passed": False}]},
                {"case_id": "c", "variant": "with_skill", "assertions": [{"name": "A", "passed": False}]}]}),
                            encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                rse.summary("s", str(path), None, None)
        self.assertEqual(out.getvalue().splitlines(), [
            "", "== s ==", "  with_skill                     objective n/a  judge n/a  cost USD n/a",
            "  paired delta, with minus without: n/a", "  failed 2x  c/with_skill: a", "  failed 1x  c/with_skill: B"])


class RegradeTest(RunnerTest):
    def make_run(self, name="skill-authoring", variants=("without_skill", "with_skill"), source=True):
        d = self.tmp / "old-runs" / name / "20261009-223826"
        for case in ("c2", "c1"):
            for v in variants:
                (d / "runs" / case / v / "run-1").mkdir(parents=True)
        (d / "runs" / "c1" / "notes.txt").write_text("", encoding="utf-8")
        if source:
            (d / "source-manifest.txt").write_text(f"{self.tmp / 'm.json'}\n", encoding="utf-8")
        (d / "judge-results.jsonl").write_text('{"first": true}\n', encoding="utf-8")
        (d / "trigger-matrix.json").write_text(json.dumps(TRIGGER), encoding="utf-8")
        return d

    def test_regrade_grades_every_arm_with_the_saved_verdicts(self):
        d = self.make_run(variants=("without_skill", "with_skill", "old_skill"))
        (d / "baseline.txt").write_text("/x/prev-skill/SKILL.md\n", encoding="utf-8")
        code, out, _ = self.main("--regrade", str(d), "--split", "holdout", out_root=False)
        self.assertEqual(code, 0)
        self.assertEqual(self.fake.verbs("judge"), [])
        (bench,) = self.fake.verbs("benchmark")
        self.assertEqual(bench[2], str(self.tmp / "m.json"))
        self.assertEqual(variants_of(bench), ["old_skill", "with_skill", "without_skill"])
        self.assertEqual((option(bench, "--runs"), option(bench, "--out"), option(bench, "--judge-results"),
                          option(bench, "--split")),
                         (str(d / "runs"), str(d / "benchmark-regraded.json"), str(d / "judge-results.jsonl"),
                          "holdout"))
        (render,) = self.fake.verbs("render-viewer")
        self.assertEqual(option(render, "--out"), str(d / "review-regraded.html"))
        lines = self.lines(out)
        start = lines.index("== skill-authoring ==")
        self.assertEqual(lines[start + 1:], SUMMARY[:2] + [
            "  old_skill (prev-skill)         objective 0.75  judge n/a  cost USD 1,234.50"] + SUMMARY[2:]
            + TRIGGER_LINES + [f"  artifacts: {d}"])

    def test_regrade_without_saved_verdicts_or_source_finds_the_manifest_by_name(self):
        d = self.make_run(source=False)
        (d / "judge-results.jsonl").unlink()
        code, _, _ = self.main("--regrade", str(d), out_root=False)
        self.assertEqual(code, 0)
        (bench,) = self.fake.verbs("benchmark")
        self.assertEqual(bench[2], str(rse.REPO / "skills" / "skill-authoring" / "evals" / "shared-benchmark.json"))
        self.assertNotIn("--judge-results", bench)

    def test_rejudge_writes_new_verdicts_beside_the_old(self):
        d = self.make_run()
        code, _, _ = self.main("--regrade", str(d), "--rejudge", "--judge-model", "opus", out_root=False)
        self.assertEqual(code, 0)
        judges = self.fake.verbs("judge")
        self.assertCountEqual([option(j, "--variant") for j in judges], ["with_skill", "without_skill"])
        for j in judges:
            self.assertEqual((option(j, "--judge-model"), option(j, "--claude-bin")),
                             ("opus", str(d / f"claude-judge{'.cmd' if os.name == 'nt' else '.sh'}")))
            self.assertTrue((d / "logs" / f"judge-results-regraded-{option(j, '--variant')}.log").exists())
        self.assertEqual(option(self.fake.verbs("benchmark")[0], "--judge-results"),
                         str(d / "judge-results-regraded.jsonl"))
        self.assertEqual((d / "judge-results.jsonl").read_text(encoding="utf-8"), '{"first": true}\n')
        self.assertEqual(len((d / "judge-results-regraded.jsonl").read_text(encoding="utf-8").splitlines()), 2)

    def test_regrade_needs_a_runs_folder(self):
        code, _, err = self.main("--regrade", str(self.tmp), out_root=False)
        self.assertEqual(code, 1)
        self.assertIn(str(self.tmp), err)
        self.assertEqual(self.fake.verbs("benchmark"), [])


B = "skill-benchmark"


class ArgvTest(RunnerTest):
    """Every command a run makes, each argv in full: an option dropped, added or misrouted fails here."""

    def shim(self, *args):
        return [str(self.python), "-X", "utf8", str(rse.SCRIPTS / "trigger_matrix_shim.py"), *args]

    def test_skill_run(self):
        code, _, _ = self.main("--skill", "skill-authoring", "--runs", "3", "--trigger-runs", "2", "--model", "opus",
                               "--judge-model", "haiku", "--effort", "high", "--split", "holdout",
                               "--timeout-seconds", "30", "--parallel", "2")
        self.assertEqual(code, 0)
        d = self.run_dir("skill-authoring")
        m, runs = str(rse.REPO / "skills" / "skill-authoring" / "evals" / "shared-benchmark.json"), str(d / "runs")
        answer, judge = self.wrapper(d, "claude-eval"), self.wrapper(d, "claude-judge")
        self.assertCountEqual(self.fake.calls, [
            ["uv", "tool", "dir"],
            [B, "validate", m, "--strict-leakage"],
            self.shim("--agent", "claude", "--model", "opus", "--runs-per-query", "2", "--timeout", "30",
                      "--trace-runs", str(d / "trigger-traces"), "--out", str(d / "trigger-matrix.json"), m,
                      "--claude-bin", answer),
            [B, "prepare", m, "--split", "holdout", "--runs-per-variant", "3", "--out", str(d / "tasks.jsonl")],
            *([B, "run-agent", "--agent", "claude", "--model", "opus", "--timeout", "30", "--tasks",
               str(d / f"tasks-{i}.jsonl"), "--runs", runs, "--claude-bin", answer] for i in range(2)),
            *([B, "judge", m, "--runs", runs, "--split", "holdout", "--judge-backend", "claude", "--judge-model", "haiku",
               "--variant", v, "--out", str(d / f"judge-results-{v}.jsonl"), "--claude-bin", judge]
              for v in ("with_skill", "without_skill")),
            [B, "benchmark", m, "--runs", runs, "--split", "holdout", "--out", str(d / "benchmark.json"),
             "--variant", "with_skill", "--variant", "without_skill", "--judge-results", str(d / "judge-results.jsonl")],
            [B, "render-viewer", "--benchmark", str(d / "benchmark.json"), "--runs", runs, "--out", str(d / "review.html")],
        ])

    def test_codex_run(self):
        code, _, _ = self.main("--skill", "skill-authoring", "--agent", "codex", "--model", "gpt", "--judge-model", "gpt",
                               "--effort", "high")
        self.assertEqual(code, 0)
        d = self.run_dir("skill-authoring")
        m, runs = str(rse.REPO / "skills" / "skill-authoring" / "evals" / "shared-benchmark.json"), str(d / "runs")
        self.assertCountEqual(self.fake.calls, [
            ["uv", "tool", "dir"],
            [B, "validate", m, "--strict-leakage"],
            self.shim("--agent", "codex", "--model", "gpt", "--runs-per-query", "1", "--timeout", "600",
                      "--trace-runs", str(d / "trigger-traces"), "--out", str(d / "trigger-matrix.json"), m),
            [B, "prepare", m, "--split", "tune", "--runs-per-variant", "1", "--out", str(d / "tasks.jsonl")],
            *([B, "run-agent", "--agent", "codex", "--model", "gpt", "--timeout", "600", "--tasks",
               str(d / f"tasks-{i}.jsonl"), "--runs", runs, "--codex-cmd",
               "codex exec --json -c model_reasoning_effort=high"] for i in range(4)),
            *([B, "judge", m, "--runs", runs, "--split", "tune", "--judge-backend", "codex", "--judge-model", "gpt",
               "--variant", v, "--out", str(d / f"judge-results-{v}.jsonl")] for v in ("with_skill", "without_skill")),
            [B, "benchmark", m, "--runs", runs, "--split", "tune", "--out", str(d / "benchmark.json"),
             "--variant", "with_skill", "--variant", "without_skill", "--judge-results", str(d / "judge-results.jsonl")],
            [B, "render-viewer", "--benchmark", str(d / "benchmark.json"), "--runs", runs, "--out", str(d / "review.html")],
        ])

    def test_codex_without_effort_keeps_its_own_command(self):
        code, _, _ = self.main("--skill", "skill-authoring", "--agent", "codex", "--skip-trigger", "--skip-judge",
                               "--parallel", "1")
        self.assertEqual(code, 0)
        d = self.run_dir("skill-authoring")
        self.assertEqual(self.fake.verbs("run-agent"), [
            [B, "run-agent", "--agent", "codex", "--model", "sonnet", "--timeout", "600", "--tasks",
             str(d / "tasks-0.jsonl"), "--runs", str(d / "runs")]])

    def test_relative_baseline_run(self):
        baseline = self.tmp / "base" / "prev-skill"
        baseline.mkdir(parents=True)
        (baseline / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        code, _, _ = self.main("--skill", "skill-authoring", "--baseline", os.path.join("base", "prev-skill"),
                               "--skip-trigger", cwd=self.tmp)
        self.assertEqual(code, 0)
        d = self.run_dir("skill-authoring")
        am, runs = str(d / "manifest.json"), str(d / "runs")
        old = json.loads(Path(am).read_text(encoding="utf-8"))["old_skill_paths"]
        self.assertEqual(len(old), 1)
        self.assertTrue(os.path.isabs(old[0]), old)
        self.assertTrue(os.path.samefile(old[0], baseline / "SKILL.md"))
        recorded = (d / "baseline.txt").read_text(encoding="utf-8").strip()
        self.assertTrue(os.path.isabs(recorded) and os.path.samefile(recorded, baseline / "SKILL.md"), recorded)
        arms = ("with_skill", "without_skill", "old_skill")
        self.assertCountEqual(self.fake.calls, [
            ["uv", "tool", "dir"],
            [B, "validate", am, "--strict-leakage"],
            [B, "prepare", am, "--split", "tune", "--runs-per-variant", "1", "--out", str(d / "tasks.jsonl"),
             "--include-old-skill"],
            *([B, "run-agent", "--agent", "claude", "--model", "sonnet", "--timeout", "600", "--tasks",
               str(d / f"tasks-{i}.jsonl"), "--runs", runs, "--claude-bin", self.wrapper(d, "claude-eval")]
              for i in range(4)),
            *([B, "judge", am, "--runs", runs, "--split", "tune", "--judge-backend", "claude", "--judge-model", "sonnet",
               "--variant", v, "--out", str(d / f"judge-results-{v}.jsonl"), "--claude-bin",
               self.wrapper(d, "claude-judge")] for v in arms),
            [B, "benchmark", am, "--runs", runs, "--split", "tune", "--out", str(d / "benchmark.json"),
             *(a for v in arms for a in ("--variant", v)), "--judge-results", str(d / "judge-results.jsonl")],
            [B, "render-viewer", "--benchmark", str(d / "benchmark.json"), "--runs", runs, "--out", str(d / "review.html")],
        ])

    def test_agent_definition_run(self):
        code, _, _ = self.main("--agent-definition", "verifier", "--timeout-seconds", "30", "--model", "haiku")
        self.assertEqual(code, 0)
        d = self.run_dir("agent-verifier")
        definition = rse.REPO / "agents" / "verifier.md"
        pinned, effort = rse.frontmatter_value(definition, "model"), rse.frontmatter_value(definition, "effort")
        model = pinned if pinned and pinned != "inherit" else "haiku"
        am, runs = str(d / "manifest.json"), str(d / "runs")
        cmd = (f'"{self.python}" "{rse.SCRIPTS / "agent_eval_backend.py"}" --claude-bin "{self.wrapper(d, "claude-eval")}"'
               + (f" --effort {effort}" if effort else ""))
        self.assertCountEqual(self.fake.calls, [
            ["uv", "tool", "dir"],
            [B, "validate", am, "--strict-leakage"],
            [B, "prepare", am, "--split", "tune", "--runs-per-variant", "1", "--out", str(d / "tasks.jsonl")],
            *([B, "run-subagent", "--model", model, "--timeout", "30", "--tasks", str(d / f"tasks-{i}.jsonl"),
               "--runs", runs, "--agent-cmd", cmd] for i in range(4)),
            *([B, "judge", am, "--runs", runs, "--split", "tune", "--judge-backend", "claude", "--judge-model", "sonnet",
               "--variant", v, "--out", str(d / f"judge-results-{v}.jsonl"), "--claude-bin",
               self.wrapper(d, "claude-judge")] for v in ("with_skill", "without_skill")),
            [B, "benchmark", am, "--runs", runs, "--split", "tune", "--out", str(d / "benchmark.json"),
             "--variant", "with_skill", "--variant", "without_skill", "--judge-results", str(d / "judge-results.jsonl")],
            [B, "render-viewer", "--benchmark", str(d / "benchmark.json"), "--runs", runs, "--out", str(d / "review.html")],
        ])

    def test_relative_out_root_gives_absolute_paths(self):
        code, _, _ = self.main("--skill", "skill-authoring", "--skip-trigger", "--skip-judge", "--parallel", "1",
                               "--out-root", "rel", out_root=False, cwd=self.tmp)
        self.assertEqual(code, 0)
        (stamp,) = (self.tmp / "rel" / "skill-authoring").iterdir()
        (answers,) = self.fake.verbs("run-agent")
        expected = {"--tasks": stamp / "tasks-0.jsonl", "--runs": stamp / "runs",
                    "--claude-bin": Path(self.wrapper(stamp, "claude-eval"))}
        for name, want in expected.items():
            path = option(answers, name)
            self.assertTrue(os.path.isabs(path), path)
            self.assertEqual(os.path.realpath(path), os.path.realpath(want))


class ManifestTest(unittest.TestCase):
    def test_the_run_copy_is_all_absolute_and_the_live_one_is_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "skills" / "s"
            (skill / "evals").mkdir(parents=True)
            live = skill / "evals" / "shared-benchmark.json"
            live.write_text(json.dumps({"skill_paths": ["SKILL.md"], "cases": [
                {"id": "c", "files": ["fixtures/a.md"], "prompt_ref": "prompts/c.md"}, {"id": "t"}]}), encoding="utf-8")
            before = live.read_bytes()
            out = Path(tmp) / "run"
            out.mkdir()
            copy = Path(rse.run_manifest(str(live), str(out), baseline_path="/b/SKILL.md"))
            self.assertEqual(copy, out / "manifest.json")
            self.assertEqual(live.read_bytes(), before)
            m = json.loads(copy.read_text(encoding="utf-8"))
            self.assertEqual(m["skill_paths"], [os.path.abspath(skill / "SKILL.md")])
            self.assertEqual(m["cases"][0]["files"], [os.path.abspath(skill / "evals" / "fixtures" / "a.md")])
            self.assertEqual(m["cases"][0]["prompt_ref"], os.path.abspath(skill / "evals" / "prompts" / "c.md"))
            self.assertEqual(m["old_skill_paths"], ["/b/SKILL.md"])
            self.assertNotIn("files", m["cases"][1])

    def test_a_manifest_outside_evals_resolves_skill_paths_against_its_own_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            live = Path(tmp) / "suite.json"
            live.write_text(json.dumps({"skill_paths": ["SKILL.md"], "cases": []}), encoding="utf-8")
            copy = rse.run_manifest(str(live), tmp, skill_path="/staged/x.md")
            self.assertEqual(json.loads(Path(copy).read_text(encoding="utf-8"))["skill_paths"], ["/staged/x.md"])
            self.assertNotIn("old_skill_paths", json.loads(Path(copy).read_text(encoding="utf-8")))


class OrderTest(unittest.TestCase):
    """Arms and suites come in name order whatever order the filesystem lists them in."""

    def test_listing_order_does_not_matter(self):
        listed = Path.iterdir
        with tempfile.TemporaryDirectory() as tmp, \
                unittest.mock.patch.object(Path, "iterdir", lambda self: iter(sorted(listed(self), reverse=True))):
            # Cases need not hold the same arms: the first case listed lacks some. Six arms, so a set's own order
            # matches name order by chance about once in 720 runs.
            arms = ["arm-a", "arm-b", "arm-c", "old_skill", "with_skill", "without_skill"]
            for case, held in (("c1", arms), ("c2", arms[3:])):
                for arm in held:
                    (Path(tmp) / "runs" / case / arm).mkdir(parents=True)
            self.assertEqual(rse.run_variants(str(Path(tmp) / "runs")), arms)
            for name in ("b", "a"):
                (Path(tmp) / "skills" / name / "evals").mkdir(parents=True)
                (Path(tmp) / "skills" / name / "evals" / "shared-benchmark.json").write_text("{}", encoding="utf-8")
            with unittest.mock.patch.object(rse, "REPO", Path(tmp)):
                self.assertEqual(rse.skill_list([]), ["a", "b"])


class FailureTest(RunnerTest):
    def test_one_failed_suite_does_not_stop_the_next(self):
        real = self.fake.__call__

        def fail_first(args, log=None):
            if args[1:2] == ["validate"] and "skill-authoring" in args[2]:
                return subprocess.CompletedProcess(args, 1, "", "")
            return real(args, log)
        with unittest.mock.patch.object(rse, "run", fail_first):
            code, out, err = self.main("--skill", "skill-authoring,pull-request", "--skip-trigger")
        self.assertEqual(code, 1)
        self.assertIn("== pull-request ==", self.lines(out))
        self.assertNotIn("== skill-authoring ==", self.lines(out))
        self.assertIn("skill-authoring", err.splitlines()[0])
        self.assertNotIn("pull-request", err)

    def test_a_failed_shard_names_its_log(self):
        self.fake.fail.add("run-agent")
        code, _, err = self.main("--skill", "skill-authoring", "--skip-trigger")
        self.assertEqual(code, 1)
        log = self.run_dir("skill-authoring") / "logs" / "answers-0.log"
        self.assertIn(str(log), err)
        self.assertEqual(self.fake.verbs("benchmark"), [])

    def test_a_failed_trigger_matrix_fails_the_suite(self):
        self.fake.fail.add("shim")
        code, out, err = self.main("--skill", "skill-authoring")
        self.assertEqual(code, 1)
        self.assertIn(str(self.run_dir("skill-authoring") / "logs" / "trigger.log"), err)
        self.assertEqual(len(self.fake.verbs("benchmark")), 1)

    def test_missing_harness_python(self):
        self.python.unlink()
        code, _, err = self.main("--skill", "skill-authoring")
        self.assertEqual(code, 1)
        self.assertIn(str(self.python), err)
        self.assertEqual(self.fake.verbs("validate"), [])

    def test_missing_skill_benchmark(self):
        self.fake.missing.add("validate")
        code, _, err = self.main("--skill", "skill-authoring")
        self.assertEqual(code, 1)
        self.assertIn("uv tool install skill-eval-harness", err)

    def test_unknown_skill(self):
        code, _, err = self.main("--skill", "no-such-skill")
        self.assertEqual(code, 1)
        self.assertIn("no-such-skill", err)


class SpawnTest(unittest.TestCase):
    """The real run(): it spawns, so these call the test's own Python."""

    def test_captures_output(self):
        # The child writes UTF-8 itself, as harness children do under the runner's PYTHONUTF8=1; run() decodes it.
        child = ("import sys; sys.stdout.reconfigure(encoding='utf-8'); print('out ✓'); print('err', file=sys.stderr); "
                 "sys.exit(3)")
        r = rse.run([sys.executable, "-c", child])
        self.assertEqual((r.returncode, r.stdout.strip(), r.stderr.strip()), (3, "out ✓", "err"))

    def test_log_takes_both_streams(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "x.log"
            log.write_text("stale\n", encoding="utf-8")
            r = rse.run([sys.executable, "-c", "import sys; print('o'); print('e', file=sys.stderr)"], log=str(log))
            self.assertEqual((r.returncode, r.stdout, r.stderr), (0, "", ""))
            self.assertEqual(sorted(log.read_text(encoding="utf-8").split()), ["e", "o"])

    def test_missing_command_is_127(self):
        r = rse.run(["no-such-command-for-the-eval-runner"])
        self.assertEqual(r.returncode, 127)


if __name__ == "__main__":
    unittest.main()
