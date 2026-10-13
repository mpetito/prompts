"""The eval helpers: skill_usage.py, agent_eval_backend.py and trigger_matrix_shim.py in scripts/, and the
pull-request suite's stage_plugin_baseline.py and check_assertions.py. The harness modules the shim and
check_assertions.py import are stubbed on PYTHONPATH, so nothing here needs skill-eval-harness installed."""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
import unittest.mock
from pathlib import Path

import agent_eval_backend
import skill_usage

SCRIPTS = Path(__file__).resolve().parents[1]
EVALS = SCRIPTS.parent / "skills" / "pull-request" / "evals"


def load(path):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


stage_plugin_baseline = load(EVALS / "stage_plugin_baseline.py")


def call(module, *argv):
    """module.main(argv) in-process: (exit code, stdout, stderr), with SystemExit and Fail as exit codes."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = module.main([str(a) for a in argv])
        except SystemExit as e:
            code = e.code
        except getattr(module, "Fail", ()) as e:
            print(e, file=sys.stderr)
            code = 1
    return code, out.getvalue(), err.getvalue()


def process(script, *argv, pythonpath=None):
    env = {**os.environ, "PYTHONPATH": str(pythonpath)} if pythonpath else None
    return subprocess.run([sys.executable, str(script), *argv], capture_output=True, text=True, env=env)


class Tmp(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def write(self, rel, text, age_days=0):
        path = self.tmp / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        if age_days:
            old = time.time() - age_days * 86400
            os.utime(path, (old, old))
        return path


def skill_call(name):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}})


class SkillUsageTest(Tmp):
    def test_counts_main_subagent_and_codex_loads_in_the_window(self):
        self.write(".claude/projects/p1/s1.jsonl", "\n".join([skill_call("review"), skill_call("review"),
                                                               skill_call("spec"), "not json \"Skill\""]) + "\n")
        # A user record that carries a Skill-shaped block is not a load.
        self.write(".claude/projects/p1/s2.jsonl", json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_use", "name": "Skill", "input": {"skill": "review"}}]}}) + "\n")
        self.write(".claude/projects/p1/s1/subagents/a.jsonl", skill_call("review") + "\n")
        self.write(".claude/projects/p2/old.jsonl", skill_call("spec") + "\n", age_days=90)
        self.write(".codex/sessions/2026/10/13/r.jsonl", 'cat skills/review/SKILL.md\nskills/spec/SKILL.md\n')
        code, out, _ = call(skill_usage, "--days", "60", "--home", self.tmp)
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("window: last 60 days"))
        self.assertTrue(lines[0].endswith(": 2"))  # two main sessions in the window; the old one is skipped
        self.assertEqual(lines[2:], ["review | 2 | 1 | 1", "spec | 1 | 0 | 1"])

    def test_usage_error_as_a_process(self):
        r = process(SCRIPTS / "skill_usage.py", "--days", "x")
        self.assertEqual(r.returncode, 1)
        self.assertIn("usage:", r.stderr)


class AgentBackendTest(Tmp):
    def stream(self, model="claude-opus-5-5", subtype="success"):
        events = [
            {"type": "assistant", "message": {"model": model, "content": [
                {"type": "tool_use", "name": "Read", "input": {"file_path": "inputs/a.md"}},
                {"type": "tool_use", "name": "Grep", "input": {"command": "grep x"}}]}},
            {"type": "assistant", "parent_tool_use_id": "t1", "message": {"model": "claude-haiku-5-5", "content": []}},
            {"type": "result", "subtype": subtype, "result": "the answer", "total_cost_usd": 0.5, "num_turns": 2,
             "usage": {"input_tokens": 10, "output_tokens": 5}},
        ]
        return "\n".join(json.dumps(e) for e in events) + "\nnoise\n"

    def workspace(self):
        ws = self.tmp / "ws"
        self.write("ws/skills/root-0/verifier.md", "---\nname: 'verifier'\nmodel: opus\n---\nbody\n")
        return ws

    def backend(self, payload, stdout, returncode=0, *argv):
        seen = {}

        def fake(argv_, **kw):
            seen.update(argv=argv_, input=kw["input"], cwd=kw["cwd"])
            return subprocess.CompletedProcess(argv_, returncode, stdout, "err")
        with unittest.mock.patch.object(agent_eval_backend.subprocess, "run", fake), \
                unittest.mock.patch("sys.stdin", io.StringIO(json.dumps(payload))):
            code, out, err = call(agent_eval_backend, "--claude-bin", "/w/claude-eval.sh", *argv)
        return code, out, err, seen

    def test_runs_the_definition_as_the_session(self):
        ws = self.workspace()
        payload = {"workspace": str(ws), "model": "opus", "prompt": "Read the skill file.\n\nTask prompt:\nDo it."}
        code, out, _, seen = self.backend(payload, self.stream(), 0, "--effort", "high")
        self.assertEqual(code, 0)
        self.assertEqual(seen["argv"], ["/w/claude-eval.sh", "-p", "--output-format", "stream-json", "--verbose",
                                        "--model", "opus", "--effort", "high", "--agent", "verifier"])
        self.assertEqual(seen["input"], "Task prompt:\nDo it.")
        self.assertEqual(seen["cwd"], ws)
        self.assertFalse((ws / "skills").exists())
        self.assertTrue((ws / ".claude" / "agents" / "verifier.md").is_file())
        result = json.loads(out)
        self.assertEqual((result["answer"], result["returncode"], result["served_models"]),
                         ("the answer", 0, ["claude-opus-5-5"]))
        self.assertEqual(result["usage"], {"input_tokens": 10, "output_tokens": 5, "cost_usd": 0.5, "num_turns": 2})
        self.assertEqual(result["trace"], [{"type": "tool_call", "tool": "Read", "path": "inputs/a.md"},
                                           {"type": "tool_call", "tool": "Grep", "command": "grep x"}])

    def test_without_skill_runs_plain_claude(self):
        ws = self.tmp / "plain"
        ws.mkdir()
        code, _, _, seen = self.backend({"workspace": str(ws), "prompt": "x\n\nTask prompt:\nDo it."}, self.stream())
        self.assertEqual(code, 0)
        self.assertNotIn("--agent", seen["argv"])
        self.assertNotIn("--model", seen["argv"])

    def test_failures_exit_2(self):
        ws = self.workspace()
        good = {"workspace": str(ws), "model": "opus", "prompt": "x\n\nTask prompt:\nDo it."}
        for name, payload, stdout, rc in (
                ("served another model", good, self.stream(model="claude-sonnet-5-5"), 0),
                ("no task marker", {**good, "prompt": "Do it."}, self.stream(), 0),
                ("claude failed", good, self.stream(), 1),
                ("error result", good, self.stream(subtype="error_max_turns"), 0)):
            with self.subTest(name):
                self.write("ws/skills/root-0/verifier.md", "---\nname: verifier\n---\n")
                code, out, err, _ = self.backend(payload, stdout, rc)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err.startswith("agent_eval_backend: "))

    def test_more_than_one_staged_definition_exit_2(self):
        ws = self.workspace()
        self.write("ws/skills/root-0/other.md", "---\nname: other\n---\n")
        code, _, _, seen = self.backend({"workspace": str(ws), "prompt": "x\n\nTask prompt:\ny"}, self.stream())
        self.assertEqual((code, seen), (2, {}))

    def test_usage_error_as_a_process(self):
        r = process(SCRIPTS / "agent_eval_backend.py")
        self.assertEqual(r.returncode, 1)
        self.assertIn("usage:", r.stderr)


class TriggerShimTest(Tmp):
    """The shim against stub harness modules: the stub CLI prints the folder name each skill path would get."""

    def setUp(self):
        super().setUp()
        self.write("stubs/skill_benchmark.py", "def _skill_root_key(rel):\n    return 'orig:' + rel\n")
        self.write("stubs/run_trigger_matrix.py",
                   "import sys, skill_benchmark\n"
                   "def main():\n"
                   "    for rel in ('SKILL.md', 'sub\\\\SKILL.md/', 'other.md'):\n"
                   "        print(skill_benchmark._skill_root_key(rel))\n"
                   "    return 7\n")

    def test_names_the_skill_folder_after_the_skill(self):
        manifest = self.write("m.json", json.dumps({"skill_name": "pull-request"}))
        r = process(SCRIPTS / "trigger_matrix_shim.py", "--out", "x", str(manifest), pythonpath=self.tmp / "stubs")
        self.assertEqual(r.returncode, 7, r.stderr)
        self.assertEqual(r.stdout.splitlines(), ["pull-request", "pull-request", "orig:other.md"])

    def test_without_a_skill_name_defers_to_the_harness(self):
        manifest = self.write("m.json", json.dumps({}))
        r = process(SCRIPTS / "trigger_matrix_shim.py", str(manifest), pythonpath=self.tmp / "stubs")
        self.assertEqual(r.stdout.splitlines()[0], "orig:SKILL.md")


class StagePluginBaselineTest(Tmp):
    def marketplace(self):
        m = self.tmp / "market"
        self.write("market/.gcs-sha", "0123456789abcdef\n")
        self.write("market/plugins/commit-commands/commands/commit.md",
                   "---\ndescription: Create a git commit\n---\n\n## Context\n\n- Status: !`git status`\n")
        self.write("market/plugins/commit-commands/commands/commit-push-pr.md",
                   '---\nallowed-tools: x\ndescription: "Commit, push, and open a PR."\n---\nPush it.\n')
        self.write("market/plugins/code-review/commands/code-review.md", "---\ndescription: Code review\n---\nReview.\n")
        self.write("market/plugins/pr-review-toolkit/commands/review-pr.md",
                   '---\ndescription: Review a PR\n---\nAspects: "$ARGUMENTS"\n')
        for agent in ("code-reviewer.md", "silent-failure-hunter.md"):
            self.write(f"market/plugins/pr-review-toolkit/agents/{agent}", f"agent {agent}\n")
        return m

    def test_stages_the_commands_and_agents(self):
        dest = self.tmp / "out" / "pr-plugins"
        self.write("out/pr-plugins/agents/stale.md", "stale\n")
        code, out, _ = call(stage_plugin_baseline, "--destination", dest, "--marketplace", self.marketplace())
        self.assertEqual(code, 0)
        self.assertEqual(out, f"Staged {dest} (build 0123456789ab): SKILL.md and 2 agents\n")
        self.assertEqual(sorted(p.name for p in (dest / "agents").iterdir()),
                         ["code-reviewer.md", "silent-failure-hunter.md"])
        lines = (dest / "SKILL.md").read_text(encoding="utf-8").split("\n")
        self.assertEqual(lines[:3], ["---", "name: pr-plugins",
                                     'description: "Create a git commit. Commit, push, and open a PR. Code review. '
                                     'Review a PR."'])
        self.assertIn("0123456789ab", lines[7])
        headings = [line for line in lines if line.startswith("## /")]
        self.assertEqual(headings, ["## /commit-commands:commit", "## /commit-commands:commit-push-pr",
                                    "## /code-review:code-review", "## /pr-review-toolkit:review-pr"])
        self.assertIn("- Status: (expanded: see `## git status` in the input file)", lines)
        self.assertIn('Aspects: ""', lines)
        self.assertEqual(lines[-3:], ['Aspects: ""', "", ""])

    def test_default_destination_is_under_the_job_folder(self):
        with unittest.mock.patch.dict(os.environ, {"CLAUDE_JOB_DIR": str(self.tmp / "job")}):
            code, _, _ = call(stage_plugin_baseline, "--marketplace", self.marketplace())
        self.assertEqual(code, 0)
        self.assertTrue((self.tmp / "job" / "tmp" / "plugin-baseline" / "pr-plugins" / "SKILL.md").is_file())

    def test_needs_a_destination(self):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_JOB_DIR"}
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            code, _, err = call(stage_plugin_baseline, "--marketplace", self.marketplace())
        self.assertEqual(code, 1)
        self.assertIn("--destination", err)

    def test_a_command_without_frontmatter_fails(self):
        m = self.marketplace()
        self.write("market/plugins/code-review/commands/code-review.md", "no frontmatter\n")
        code, _, err = call(stage_plugin_baseline, "--destination", self.tmp / "d", "--marketplace", m)
        self.assertEqual(code, 1)
        self.assertIn("code-review/code-review", err)

    def test_usage_error_as_a_process(self):
        r = process(EVALS / "stage_plugin_baseline.py", "--bogus")
        self.assertEqual(r.returncode, 1)
        self.assertIn("usage:", r.stderr)


class CheckAssertionsTest(Tmp):
    def test_usage_error_as_a_process(self):
        self.write("stubs/skill_benchmark.py", "def assertion_result(a, text, base):\n    return {'passed': True}\n")
        r = process(EVALS / "check_assertions.py", "extra", pythonpath=self.tmp / "stubs")
        self.assertEqual(r.returncode, 1)
        self.assertIn("usage:", r.stderr)


if __name__ == "__main__":
    unittest.main()
