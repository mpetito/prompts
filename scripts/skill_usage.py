"""Count skill loads across local agent sessions, so readmission and retention rest on usage.

usage: python3 scripts/skill_usage.py [--days 60] [--home <folder>]   (--home defaults to the user's home)

Reads Claude Code main-session and subagent transcripts (~/.claude/projects/**.jsonl, Skill tool
calls) and Codex session logs (~/.codex/sessions/**.jsonl, reads of a skills/<name>/SKILL.md path).
Copilot in VS Code and claude.ai leave no local record, so a zero here is not zero use.
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import sys
from pathlib import Path

SKILL_PATH = re.compile(r"skills/([a-z0-9-]+)/SKILL\.md")


def claude_loads(home, since):
    main = collections.Counter()
    sub = collections.Counter()
    main_sessions = 0
    paths = glob.glob(os.path.join(home, ".claude/projects/*/*.jsonl"))
    paths += glob.glob(os.path.join(home, ".claude/projects/*/*/subagents/*.jsonl"))
    for path in paths:
        if dt.datetime.fromtimestamp(os.path.getmtime(path)) < since:
            continue
        is_sub = "subagents" in Path(path).parts
        main_sessions += not is_sub
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"Skill"' not in line:
                    continue
                try:
                    record = json.loads(line)
                except ValueError:
                    continue
                if record.get("type") != "assistant":
                    continue
                for block in (record.get("message") or {}).get("content") or []:
                    if isinstance(block, dict) and block.get("type") == "tool_use" and block.get("name") == "Skill":
                        name = (block.get("input") or {}).get("skill", "?")
                        (sub if is_sub else main)[name] += 1
    return main, sub, main_sessions


def codex_reads(home, since):
    reads = collections.Counter()
    for path in glob.glob(os.path.join(home, ".codex/sessions/*/*/*/*.jsonl")):
        if dt.datetime.fromtimestamp(os.path.getmtime(path)) < since:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                for name in SKILL_PATH.findall(line):
                    reads[name] += 1
    return reads


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, f"{self.prog}: error: {message}\n")


def main(argv):
    parser = Parser(prog="skill_usage.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--days", type=int, default=60)
    parser.add_argument("--home", default=str(Path.home()))
    args = parser.parse_args(argv)
    since = dt.datetime.now() - dt.timedelta(days=args.days)
    main_loads, sub_loads, sessions = claude_loads(args.home, since)
    codex = codex_reads(args.home, since)
    names = sorted(set(main_loads) | set(sub_loads) | set(codex), key=lambda n: -(main_loads[n] + sub_loads[n] + codex[n]))
    print(f"window: last {args.days} days · Claude main sessions scanned: {sessions}")
    print("skill | main session loads | subagent loads | codex file reads")
    for name in names:
        print(f"{name} | {main_loads[name]} | {sub_loads[name]} | {codex[name]}")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
