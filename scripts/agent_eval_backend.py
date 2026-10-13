"""Answer one eval task with a Claude Code agent definition running as the session.

skill-eval-harness calls this through `skill-benchmark run-subagent --agent-cmd`, with
{prompt, model, workspace} as JSON on stdin, and reads {answer, returncode, elapsed_ms,
usage, trace} as JSON on stdout. The harness mounts the arm's definition under
skills/root-0/ (with_skill, old_skill) or nothing (without_skill), and opens the prompt with
an instruction to read and follow skill files. An agent definition is a system prompt, not a
file to read, so this script moves the definition to .claude/agents/, removes that opening
from every arm alike, and runs `claude -p --agent <name>` for the arms that carry one.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

USAGE = "usage: agent_eval_backend.py --claude-bin <path> [--effort <level>]"

# The harness's prompt layout: an arm-specific opening, then this marker and the case prompt.
TASK_MARKER = "\n\nTask prompt:\n"


def fail(message: str) -> None:
    # A nonzero exit makes the harness record the run as failed instead of grading an answer.
    print(f"agent_eval_backend: {message}", file=sys.stderr)
    sys.exit(2)


def definition_name(path: Path) -> str:
    match = re.search(r"(?ms)\A---\s*\n.*?^name:[ \t]*['\"]?([^'\"\n]+?)['\"]?[ \t]*$", path.read_text(encoding="utf-8"))
    if not match:
        fail(f"no name in the frontmatter of {path.name}")
    return match.group(1).strip()


def mount_definition(workspace: Path) -> str | None:
    skills = workspace / "skills"
    if not skills.is_dir():
        return None
    found = sorted(skills.glob("root-*/*.md"))
    # The runner stages each definition alone in its folder, so more than one file means the
    # harness mounted something other than a staged definition.
    if len(found) != 1:
        fail(f"expected one staged agent definition under skills/, found {len(found)}")
    agents = workspace / ".claude" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    target = agents / found[0].name
    shutil.copy2(found[0], target)
    shutil.rmtree(skills)
    return definition_name(target)


def neutral_prompt(prompt: str) -> str:
    if TASK_MARKER not in prompt:
        fail("the harness prompt no longer contains the task marker; refusing to send its skill wording")
    return "Task prompt:\n" + prompt.split(TASK_MARKER, 1)[1]


class Parser(argparse.ArgumentParser):
    def error(self, message):
        # A usage error exits 1, apart from the 2 that fail() gives a run that went wrong.
        print(f"{USAGE}\nagent_eval_backend: {message}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str]) -> int:
    parser = Parser(usage=USAGE)
    parser.add_argument("--claude-bin", required=True)
    parser.add_argument("--effort")
    args = parser.parse_args(argv)
    payload = json.load(sys.stdin)
    workspace = Path(payload["workspace"])
    agent = mount_definition(workspace)
    argv = [args.claude_bin, "-p", "--output-format", "stream-json", "--verbose"]
    if payload.get("model"):
        argv += ["--model", payload["model"]]
    if args.effort:
        argv += ["--effort", args.effort]
    if agent:
        argv += ["--agent", agent]
    started = time.time()
    proc = subprocess.run(argv, input=neutral_prompt(payload["prompt"]), text=True, capture_output=True, cwd=workspace)
    elapsed_ms = int((time.time() - started) * 1000)
    answer, usage, trace, served = "", {}, [], set()
    for line in proc.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("type") == "assistant" and not event.get("parent_tool_use_id"):
            served.add(event["message"].get("model"))
            for block in event["message"].get("content", []):
                if block.get("type") == "tool_use":
                    tool_input = block.get("input") or {}
                    record = {"type": "tool_call", "tool": block.get("name")}
                    if tool_input.get("file_path") or tool_input.get("path"):
                        record["path"] = tool_input.get("file_path") or tool_input.get("path")
                    if tool_input.get("command"):
                        record["command"] = tool_input["command"]
                    trace.append(record)
        elif event.get("type") == "result":
            answer = event.get("result") or ""
            raw = event.get("usage") or {}
            usage = {
                "input_tokens": raw.get("input_tokens"),
                "output_tokens": raw.get("output_tokens"),
                "cache_read_tokens": raw.get("cache_read_input_tokens"),
                "cache_creation_tokens": raw.get("cache_creation_input_tokens"),
                "cost_usd": event.get("total_cost_usd"),
                "num_turns": event.get("num_turns"),
            }
            if event.get("subtype") != "success":
                fail(f"claude ended with {event.get('subtype')}")
    if proc.returncode != 0 or not answer:
        fail(f"claude exited {proc.returncode} with no answer: {proc.stderr.strip()[:500]}")
    # A served model other than the requested one would compare models, not definitions.
    requested = payload.get("model")
    if requested and served and not all(requested in (m or "") for m in served):
        fail(f"requested {requested} but served {sorted(m for m in served if m)}")
    usage = {k: v for k, v in usage.items() if v is not None}
    print(json.dumps({"answer": answer, "returncode": 0, "elapsed_ms": elapsed_ms, "usage": usage, "trace": trace,
                      "served_models": sorted(m for m in served if m)}))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
