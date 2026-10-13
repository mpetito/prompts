"""Run a skill's eval suite (skills/<name>/evals/shared-benchmark.json) through skill-eval-harness.

  python3 scripts/run_skill_eval.py --skill pull-request
  python3 scripts/run_skill_eval.py --skill review,spec --runs 3 --skip-trigger
  python3 scripts/run_skill_eval.py --skill skill-authoring --runs 3 --skip-trigger --baseline <skill folder>
  python3 scripts/run_skill_eval.py --agent-definition verifier --runs 3
  python3 scripts/run_skill_eval.py --regrade .eval-runs/skill-authoring/20261009-223826

Prepares paired with-skill / without-skill tasks, runs them through a coding agent CLI, grades deterministic
assertions, runs the LLM judge, aggregates a benchmark, measures autonomous skill triggering, and renders a review
page. Every run lands in <out root>/<name>/<yyyyMMdd-HHmmss>/. Requires `uv tool install skill-eval-harness`.

The harness runs one task at a time, so this script splits answer runs across --parallel processes, judges each
arm in its own process, and measures triggering while the answer runs are in flight. docs/evaluating-skills.md
says which options fit which kind of edit.

Claude runs are wrapped so they load project settings only: user-level skills, plugins and MCP servers from this
machine are not visible to the agent, while the normal login still works.

Exit codes: 0 when every suite ran; 1 for a usage error, a missing harness, or any suite that failed (the others
still run, and each failure is named on stderr).
"""
import argparse
import concurrent.futures
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"

if os.name == "nt":
    # shutil.which would otherwise look in the current directory first, where a worktree could hold a .cmd.
    os.environ.setdefault("NoDefaultCurrentDirectoryInExePath", "1")


class Fail(Exception):
    """A usage error or a failed step: the message goes to stderr and the exit code is 1."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Fail(f"{self.format_usage()}{self.prog}: error: {message}")


def run(args, log=None):
    """Run args (a list, no shell) and return a CompletedProcess with text stdout and stderr, decoded as UTF-8.

    args[0] is resolved on PATH (PATHEXT on Windows, so a .cmd shim is found); a command that isn't found returns
    code 127 with the reason on stderr, as a shell would. With log, a file path, stdout and stderr both go into
    that file, replacing it, and the result's stdout and stderr are empty. No call takes a timeout: the harness
    applies --timeout to each task itself, and a child left in the terminal's process group stops on Ctrl-C with
    the runner."""
    exe = shutil.which(args[0])
    if not exe:
        return subprocess.CompletedProcess(args, 127, "", f"{args[0]}: command not found\n")
    if log:
        with open(log, "wb") as sink:
            r = subprocess.run([exe, *args[1:]], stdin=subprocess.DEVNULL, stdout=sink, stderr=subprocess.STDOUT)
        return subprocess.CompletedProcess(args, r.returncode, "", "")
    r = subprocess.run([exe, *args[1:]], stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return subprocess.CompletedProcess(args, r.returncode, r.stdout, r.stderr)


def whole(lo, hi):
    """An option type: a whole number from lo to hi."""
    def convert(text):
        if not re.fullmatch(r"[0-9]+", text) or not lo <= int(text) <= hi:
            raise argparse.ArgumentTypeError(f"takes a whole number from {lo} to {hi}, got {text}")
        return int(text)
    return convert


def parse(argv):
    """The options, each the Python form of the PowerShell runner's parameter of the same name."""
    p = Parser(prog="run_skill_eval.py", description="Run skill eval suites through skill-eval-harness.")
    p.add_argument("--skill", action="append", default=[],
                   help="skill folder names under skills/, comma-separated or repeated; default: every skill "
                        "with an evals manifest")
    p.add_argument("--agent", choices=["claude", "codex"], default="claude")
    p.add_argument("--model", default="sonnet")
    p.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"],
                   help="reasoning effort for skill answer and trigger runs, every arm alike; agent runs use the "
                        "definition's own")
    p.add_argument("--judge-model", default="sonnet")
    p.add_argument("--runs", type=whole(1, 50), default=1)
    p.add_argument("--trigger-runs", type=whole(1, 50), default=1)
    p.add_argument("--split", choices=["tune", "holdout", "holdback"], default="tune")
    p.add_argument("--out-root", help="where run directories go; default: <repo>/.eval-runs")
    p.add_argument("--timeout-seconds", type=int, default=600, help="per answer and trigger run")
    p.add_argument("--parallel", type=whole(1, 16), default=4,
                   help="concurrent answer-run processes; judging uses one process per arm")
    p.add_argument("--skip-trigger", action="store_true")
    p.add_argument("--skip-judge", action="store_true")
    p.add_argument("--trigger-only", action="store_true",
                   help="measure autonomous triggering only; no answer runs, grading or judge")
    p.add_argument("--include-old-skill", action="store_true",
                   help="also run the old_skill arm; the manifest must declare old_skill_paths")
    p.add_argument("--baseline", help="a skill folder (or its SKILL.md) to run as the old_skill arm instead of "
                                      "old_skill_paths: an earlier revision, or a competing skill")
    p.add_argument("--agent-definition", help="an agent under agents/ to evaluate instead of skills; its suite is "
                                              "evals/agents/<name>/, and --baseline then takes an agent file")
    p.add_argument("--regrade", help="an existing run directory to grade again against the current manifest; no "
                                     "model calls unless --rejudge")
    p.add_argument("--rejudge", action="store_true", help="with --regrade, judge the saved outputs again")
    return p.parse_args(argv)


def harness(args):
    """Run one skill-benchmark command in the foreground, echoing it and its output."""
    print(f"> skill-benchmark {' '.join(args)}", flush=True)
    r = run(["skill-benchmark", *args])
    print(r.stdout, end="", flush=True)
    print(r.stderr, end="", file=sys.stderr, flush=True)
    if r.returncode == 127:
        raise Fail("skill-benchmark is not on PATH. Install it with: uv tool install skill-eval-harness")
    if r.returncode != 0:
        raise Fail(f"skill-benchmark {args[0]} failed with exit code {r.returncode}")


def harness_parallel(jobs, log_dir):
    """Run each (label, args) job as its own skill-benchmark process at once, each logged to <log_dir>/<label>.log;
    Fail names every job that exited nonzero, with its log."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logs = {label: str(Path(log_dir) / f"{label}.log") for label, _ in jobs}
    with concurrent.futures.ThreadPoolExecutor(len(jobs)) as pool:
        codes = dict(zip(logs, pool.map(lambda job: run(["skill-benchmark", *job[1]], log=logs[job[0]]).returncode,
                                        jobs)))
    bad = [f"{label} (log: {logs[label]})" for label, code in codes.items() if code != 0]
    if bad:
        raise Fail(f"skill-benchmark failed: {', '.join(bad)}")


def harness_python():
    """The skill-eval-harness tool's own Python, which imports the harness for the trigger shim and agent backend."""
    r = run(["uv", "tool", "dir"])
    python = Path(r.stdout.strip()) / "skill-eval-harness" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if r.returncode != 0 or not python.is_file():
        raise Fail(f"skill-eval-harness python not found at {python}. Install it with: uv tool install "
                   "skill-eval-harness")
    return str(python)


def skill_list(requested):
    if requested:
        return [s.strip() for item in requested for s in item.split(",") if s.strip()]
    # Live skills first; archived skills (archive/skills) are measured on their way back in.
    names = []
    for root in (REPO / "skills", REPO / "archive" / "skills"):
        if root.is_dir():
            names += [d.name for d in sorted(root.iterdir()) if (d / "evals" / "shared-benchmark.json").is_file()]
    return list(dict.fromkeys(names))


def manifest_path(name):
    for root in ("skills", "archive/skills"):
        path = REPO / root / name / "evals" / "shared-benchmark.json"
        if path.is_file():
            return str(path)
    raise Fail(f"No manifest for {name} under skills/ or archive/skills/")


def write_lines(path, lines):
    Path(path).write_text("".join(f"{line}\n" for line in lines), encoding="utf-8")


def run_manifest(manifest, directory, skill_path=None, baseline_path=None):
    """Write <directory>/manifest.json, a copy of manifest with every path absolute; skill_path replaces its
    skill_paths and baseline_path becomes its old_skill_paths. Returns the copy's path."""
    # The harness resolves skill paths against the skill folder (the manifest's own folder outside an evals/
    # layout) and fixtures against the manifest's folder, so this copy, written beside the run, carries every
    # path absolute.
    manifest_dir = Path(manifest).parent
    in_evals = Path(manifest).name == "shared-benchmark.json" and manifest_dir.name == "evals"
    skill_root = manifest_dir.parent if in_evals else manifest_dir
    m = json.loads(Path(manifest).read_text(encoding="utf-8"))
    absolute = lambda p, base: os.path.abspath(os.path.join(base, p))  # noqa: E731
    m["skill_paths"] = [skill_path] if skill_path else [absolute(p, skill_root) for p in m.get("skill_paths") or []]
    for case in m.get("cases") or []:
        if case.get("files"):
            case["files"] = [absolute(f, manifest_dir) for f in case["files"]]
        if case.get("prompt_ref"):
            case["prompt_ref"] = absolute(case["prompt_ref"], manifest_dir)
    if baseline_path:
        m["old_skill_paths"] = [baseline_path]
    path = Path(directory) / "manifest.json"
    path.write_text(json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return str(path)


def skill_baseline(baseline):
    """The SKILL.md of a baseline skill folder (or the file itself), absolute; Fail when there is none."""
    skill_md = Path(baseline) / "SKILL.md" if Path(baseline).is_dir() else Path(baseline)
    if not skill_md.is_file():
        raise Fail(f"Baseline has no SKILL.md: {baseline}")
    # The harness mounts the whole folder that holds this SKILL.md, minus evals/ and dotfiles.
    return os.path.abspath(skill_md)


def frontmatter_value(path, key):
    """A frontmatter key's value, unquoted, matched case-insensitively; None when absent."""
    m = re.match(r"---\s*\n(.*?)\n---", Path(path).read_text(encoding="utf-8"), re.S)
    v = m and re.search(rf"^{re.escape(key)}[ \t]*:[ \t]*['\"]?([^'\"\r\n]+?)['\"]?[ \t]*\r?$", m[1], re.M | re.I)
    return v[1] if v else None


def stage_definition(source, directory):
    """Copy an agent definition alone into directory and return the copy's path."""
    # The harness mounts the whole folder that holds a skill path, so each definition is staged alone;
    # agent_eval_backend.py refuses a workspace with more than one.
    if not Path(source).is_file():
        raise Fail(f"No agent definition at {source}")
    if not frontmatter_value(source, "name"):
        raise Fail(f"No name in the frontmatter of {source}")
    Path(directory).mkdir(parents=True, exist_ok=True)
    return str(shutil.copy(source, Path(directory) / Path(source).name))


def claude_wrapper(directory, effort=None, name="claude-eval"):
    """Write <directory>/<name>.sh (.cmd on Windows), a claude that loads project settings only and can't act on
    the machine, and return its path. effort, when given, applies to every claude call through it: the installed
    harness's run-agent has no --effort of its own."""
    # A nested `claude -p` refuses to start while CLAUDECODE marks the parent session, so clear it. Eval cases
    # only read fixtures and write text, so every tool that can act on the machine is denied outright: managed
    # settings can grant Bash to a headless run, and a sandboxed run that inherits the Herdr variables will
    # otherwise treat the user's real terminal panes as its own.
    denied = "Bash,PowerShell,Write,Edit,MultiEdit,NotebookEdit,Agent,WebFetch,WebSearch"
    cleared = ["CLAUDECODE", "HERDR_PANE_ID", "HERDR_TAB_ID", "HERDR_WORKSPACE_ID", "HERDR_SOCKET_PATH",
               "HERDR_BIN_PATH", "HERDR_ENV", "TERM_PROGRAM"]
    effort_arg = f" --effort {effort}" if effort else ""
    claude = f'claude --setting-sources project --strict-mcp-config{effort_arg} --disallowedTools "{denied}"'
    if os.name == "nt":
        wrapper = Path(directory) / f"{name}.cmd"
        lines = ["@echo off", *(f"set {v}=" for v in cleared), f"{claude} %*"]
        wrapper.write_bytes("\r\n".join(lines).encode("ascii") + b"\r\n")
    else:
        wrapper = Path(directory) / f"{name}.sh"
        wrapper.write_bytes(f'#!/bin/sh\nunset {" ".join(cleared)}\nexec {claude} "$@"\n'.encode("ascii"))
        wrapper.chmod(0o755)
    return str(wrapper)


def arm_judges(o, manifest, runs_dir, variants, results_path, claude_bin, log_dir):
    """Judge each arm in its own process, then concatenate their verdicts into results_path."""
    stem = Path(results_path).with_suffix("")
    jobs = []
    for v in variants:
        judge = ["judge", manifest, "--runs", runs_dir, "--split", o.split, "--judge-backend", o.agent,
                 "--judge-model", o.judge_model, "--variant", v, "--out", f"{stem}-{v}.jsonl"]
        if o.agent == "claude":
            judge += ["--claude-bin", claude_bin]
        jobs.append((f"{stem.name}-{v}", judge))
    print(f"> skill-benchmark judge: one process per arm ({', '.join(variants)})", flush=True)
    harness_parallel(jobs, log_dir)
    write_lines(results_path, [line for v in variants
                               for line in Path(f"{stem}-{v}.jsonl").read_text(encoding="utf-8").splitlines()])


def run_variants(runs_dir):
    """The arms present under runs/<case>/, in name order."""
    return sorted({v.name for case in Path(runs_dir).iterdir() if case.is_dir() for v in case.iterdir() if v.is_dir()})


def rate(value):
    return "n/a" if value is None else f"{float(value):,.2f}"


def summary(name, benchmark_path, trigger_path, baseline_file):
    """Print one line per arm, every failed assertion with its count, and the trigger matrix."""
    print(f"\n== {name} ==")
    if benchmark_path:
        b = json.loads(Path(benchmark_path).read_text(encoding="utf-8"))
        baseline_name = None
        if baseline_file and Path(baseline_file).exists():
            # A skill baseline is named by its folder, an agent baseline by its file.
            path = Path(Path(baseline_file).read_text(encoding="utf-8").splitlines()[0])
            baseline_name = path.parent.name if path.name == "SKILL.md" else path.stem
        # Judge rubrics are soft by default, so they never move the pass rates; report them apart.
        judge = {}
        for r in b.get("results") or []:
            for q in r.get("qualitative_assertions") or []:
                if q.get("score") is not None:
                    judge.setdefault(r["variant"], []).append(float(q["score"]))
        for v in ("with_skill", "without_skill", "old_skill"):
            s = (b.get("summary") or {}).get(v)
            if s is None:
                continue
            label = f"old_skill ({baseline_name})" if v == "old_skill" and baseline_name else v
            judge_mean = sum(judge[v]) / len(judge[v]) if v in judge else None
            print(f"  {label:<30} objective {rate(s.get('mean_objective_pass_rate'))}  judge {rate(judge_mean)}  "
                  f"cost USD {rate(s.get('cost_usd_total'))}")
        print(f"  paired delta, with minus without: {rate((b.get('paired_summary') or {}).get('absolute_delta'))}")
        # Counted and sorted case-insensitively, each under its first spelling, as PowerShell's Group-Object did.
        failures = {}
        for r in b.get("results") or []:
            for a in r.get("assertions") or []:
                if a.get("passed") is False:
                    key = f"{r['case_id']}/{r['variant']}: {a['name']}"
                    first, count = failures.get(key.casefold(), (key, 0))
                    failures[key.casefold()] = (first, count + 1)
        for first, count in sorted(failures.values(), key=lambda fc: (fc[0].casefold(), fc[0])):
            print(f"  failed {count}x  {first}")
    if trigger_path and Path(trigger_path).exists():
        t = json.loads(Path(trigger_path).read_text(encoding="utf-8"))
        for cell in t.get("matrix") or []:
            fire = cell["summary"].get("should_trigger") or {}
            quiet = cell["summary"].get("should_not_trigger") or {}
            print(f"  trigger {cell['agent']}/{cell['model']}: should-fire {fire.get('passed', '')}/"
                  f"{fire.get('total', '')}  should-not-fire {quiet.get('passed', '')}/{quiet.get('total', '')}")
            for q in cell.get("queries") or []:
                if q["passed_runs"] < q["runs"]:
                    print(f"    missed ({q['runs'] - q['passed_runs']} of {q['runs']} runs): {q['query']}")


def regrade(o):
    out = os.path.abspath(o.regrade)
    runs_dir = os.path.join(out, "runs")
    if not os.path.isdir(runs_dir):
        raise Fail(f"No runs/ directory under {out}")
    name = Path(out).parent.name
    # Runs record their suite's manifest; earlier skill runs are found by folder name.
    source = Path(out) / "source-manifest.txt"
    manifest = source.read_text(encoding="utf-8").splitlines()[0] if source.exists() else manifest_path(name)
    benchmark_path = os.path.join(out, "benchmark-regraded.json")
    variants = run_variants(runs_dir)
    grade = ["benchmark", manifest, "--runs", runs_dir, "--split", o.split, "--out", benchmark_path]
    grade += [a for v in variants for a in ("--variant", v)]
    judge_results = os.path.join(out, "judge-results.jsonl")
    if o.rejudge:
        # A changed rubric needs new verdicts, not new answers; the first run's verdicts stay as they were.
        judge_results = os.path.join(out, "judge-results-regraded.jsonl")
        arm_judges(o, manifest, runs_dir, variants, judge_results, claude_wrapper(out, name="claude-judge"),
                   os.path.join(out, "logs"))
    if os.path.exists(judge_results):
        grade += ["--judge-results", judge_results]
    harness(grade)
    harness(["render-viewer", "--benchmark", benchmark_path, "--runs", runs_dir, "--out",
             os.path.join(out, "review-regraded.html")])
    summary(name, benchmark_path, os.path.join(out, "trigger-matrix.json"), os.path.join(out, "baseline.txt"))
    print(f"  artifacts: {out}")
    return 0


def evaluate(o, name, out, python, pool):
    """Run one suite into its run directory out. The trigger matrix runs on pool alongside the answer runs."""
    if o.agent_definition:
        # Suites live outside agents/: setup links that folder whole into ~/.claude/agents, and Claude Code
        # loads every .md beneath it as an agent.
        definition = str(REPO / "agents" / f"{o.agent_definition}.md")
        manifest = str(REPO / "evals" / "agents" / o.agent_definition / "shared-benchmark.json")
        if not os.path.exists(manifest):
            raise Fail(f"No manifest for agent {o.agent_definition} at {manifest}")
    else:
        manifest = manifest_path(name)
    runs_dir, log_dir = os.path.join(out, "runs"), os.path.join(out, "logs")
    os.makedirs(out, exist_ok=True)
    write_lines(os.path.join(out, "source-manifest.txt"), [manifest])
    # One wrapper per run directory: concurrent invocations rewriting a shared .cmd made launches fail with
    # WinError 193, and every failed launch was scored as a miss. Answer and trigger runs carry --effort; agent
    # runs take the definition's own, and the judge keeps the default so verdicts stay comparable across runs.
    claude_bin = claude_wrapper(out, None if o.agent_definition else o.effort)
    judge_bin = claude_wrapper(out, name="claude-judge")

    if o.agent_definition:
        staged = stage_definition(definition, os.path.join(out, "definitions", "with_skill"))
        staged_baseline = None
        if o.baseline:
            staged_baseline = stage_definition(o.baseline, os.path.join(out, "definitions", "old_skill"))
            write_lines(os.path.join(out, "baseline.txt"), [os.path.abspath(o.baseline)])
        answer_manifest = run_manifest(manifest, out, skill_path=staged, baseline_path=staged_baseline)
        # Every arm runs on the definition's own model and effort, so the comparison measures the definition,
        # not the model. The CLI's --model overrides an agent's model pin.
        agent_model = frontmatter_value(definition, "model")
        if not agent_model or agent_model == "inherit":
            agent_model = o.model
        agent_effort = frontmatter_value(definition, "effort")
    elif o.baseline:
        baseline_skill = skill_baseline(o.baseline)
        write_lines(os.path.join(out, "baseline.txt"), [baseline_skill])
        answer_manifest = run_manifest(manifest, out, baseline_path=baseline_skill)
    else:
        answer_manifest = manifest
    variants = ["with_skill", "without_skill"] + (["old_skill"] if o.include_old_skill or o.baseline else [])
    harness(["validate", answer_manifest, "--strict-leakage"])

    trigger_report = trigger = None
    if o.agent_definition and not o.skip_trigger:
        print("  delegation evals for agent definitions are not supported yet; no trigger run")
    elif not o.skip_trigger:
        # Triggering reads only the description, so it runs alongside the answer runs.
        trigger_report = os.path.join(out, "trigger-matrix.json")
        args = ["--agent", o.agent, "--model", o.model, "--runs-per-query", str(o.trigger_runs),
                "--timeout", str(o.timeout_seconds), "--trace-runs", os.path.join(out, "trigger-traces"),
                "--out", trigger_report, manifest]
        if o.agent == "claude":
            args += ["--claude-bin", claude_bin]
        # The shim names the mounted skill folder after the skill (see scripts/trigger_matrix_shim.py).
        shim = str(SCRIPTS / "trigger_matrix_shim.py")
        os.makedirs(log_dir, exist_ok=True)
        trigger_log = os.path.join(log_dir, "trigger.log")
        print(f"> trigger_matrix_shim.py {' '.join(args)} (log: {trigger_log})", flush=True)
        trigger = pool.submit(run, [python, "-X", "utf8", shim, *args], log=trigger_log)

    if not o.trigger_only:
        tasks = os.path.join(out, "tasks.jsonl")
        prepare = ["prepare", answer_manifest, "--split", o.split, "--runs-per-variant", str(o.runs), "--out", tasks]
        if "old_skill" in variants:
            prepare.append("--include-old-skill")
        harness(prepare)

        # Every task writes only its own runs/<case>/<variant>/run-N, so shards cannot collide. Round-robin keeps
        # each shard's mix of slow and fast cases even.
        rows = [r for r in Path(tasks).read_text(encoding="utf-8").splitlines() if r.strip()]
        shards = max(1, min(o.parallel, len(rows)))
        if o.agent_definition:
            # run-agent would tell the model to read the definition as a skill file; the backend runs it as the
            # session instead (see scripts/agent_eval_backend.py).
            backend = SCRIPTS / "agent_eval_backend.py"
            agent_cmd = f'"{python}" "{backend}" --claude-bin "{claude_bin}"' + (
                f" --effort {agent_effort}" if agent_effort else "")
        jobs = []
        for i in range(shards):
            shard = os.path.join(out, f"tasks-{i}.jsonl")
            write_lines(shard, rows[i::shards])
            if o.agent_definition:
                args = ["run-subagent", "--model", agent_model, "--timeout", str(o.timeout_seconds), "--tasks",
                        shard, "--runs", runs_dir, "--agent-cmd", agent_cmd]
            else:
                args = ["run-agent", "--agent", o.agent, "--model", o.model, "--timeout", str(o.timeout_seconds),
                        "--tasks", shard, "--runs", runs_dir]
                if o.agent == "claude":
                    args += ["--claude-bin", claude_bin]
                elif o.effort:
                    args += ["--codex-cmd", f"codex exec --json -c model_reasoning_effort={o.effort}"]
            jobs.append((f"answers-{i}", args))
        runner = (f"run-subagent ({o.agent_definition} on {agent_model}"
                  f"{f', effort {agent_effort}' if agent_effort else ''})") if o.agent_definition else "run-agent"
        print(f"> skill-benchmark {runner}: {len(rows)} tasks in {shards} parallel shards (logs: {log_dir})",
              flush=True)
        harness_parallel(jobs, log_dir)

        # Without --variant, judge and benchmark score only the manifest's default arms, so the old_skill runs
        # would be paid for and never graded.
        benchmark = ["benchmark", answer_manifest, "--runs", runs_dir, "--split", o.split, "--out",
                     os.path.join(out, "benchmark.json")] + [a for v in variants for a in ("--variant", v)]
        if not o.skip_judge:
            judge_results = os.path.join(out, "judge-results.jsonl")
            arm_judges(o, answer_manifest, runs_dir, variants, judge_results, judge_bin, log_dir)
            benchmark += ["--judge-results", judge_results]
        harness(benchmark)
        harness(["render-viewer", "--benchmark", os.path.join(out, "benchmark.json"), "--runs", runs_dir, "--out",
                 os.path.join(out, "review.html")])

    if trigger:
        code = trigger.result().returncode
        if code != 0:
            raise Fail(f"skill-trigger-matrix failed with exit code {code} (log: {trigger_log})")

    summary(name, None if o.trigger_only else os.path.join(out, "benchmark.json"), trigger_report,
            os.path.join(out, "baseline.txt"))
    print(f"  artifacts: {out}")


def main(argv):
    o = parse(argv)
    # The harness decodes agent output with the console code page unless Python runs in UTF-8 mode; on Windows
    # that silently drops any run whose transcript contains a non-cp1252 byte.
    os.environ["PYTHONUTF8"] = "1"
    python = harness_python()
    if o.regrade:
        return regrade(o)
    if o.agent_definition:
        if o.skill:
            raise Fail("--agent-definition and --skill are separate runs; pass one of them.")
        if o.agent != "claude":
            raise Fail("Agent definitions are Claude Code subagents; run them with --agent claude.")
        if o.trigger_only:
            raise Fail("Delegation evals for agent definitions are not supported yet; --trigger-only has nothing "
                       "to run.")
        names = [f"agent-{o.agent_definition}"]
    else:
        names = skill_list(o.skill)
    if not names:
        raise Fail("No skill has an evals/shared-benchmark.json manifest.")
    if o.baseline and len(names) != 1:
        raise Fail("--baseline compares one skill; name it with --skill.")
    out_root = os.path.abspath(o.out_root) if o.out_root else str(REPO / ".eval-runs")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    failed = []
    for name in names:
        try:
            # Leaving the pool waits for a trigger run still in flight, even when its suite has already failed.
            with concurrent.futures.ThreadPoolExecutor(1) as pool:
                evaluate(o, name, os.path.join(out_root, name, stamp), python, pool)
        except (Fail, OSError, ValueError) as e:
            # One broken suite must not hide the results of the others; the exit code reports it at the end.
            print(f"WARNING: {name} failed: {e}", file=sys.stderr, flush=True)
            failed.append(name)
    if failed:
        raise Fail(f"Eval failed for: {', '.join(failed)}")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as e:
        print(e, file=sys.stderr)
        sys.exit(1)
