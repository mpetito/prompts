"""Stage the commit-commands, code-review and pr-review-toolkit plugins as one skill folder, the plugin arm
(--baseline) of the pull-request suite.

  python3 skills/pull-request/evals/stage_plugin_baseline.py [--destination <folder>] [--marketplace <folder>]
  python3 scripts/run_skill_eval.py --skill pull-request --runs 3 --skip-trigger --baseline <destination>

The folder is generated from the installed plugins on each run and lives outside the repository, so the plugins'
third-party text is never committed. It holds:
- SKILL.md: the four command descriptions joined as its description, one paragraph of harness glue labelled as
  such, then each command body verbatim under `## /<plugin>:<command>`. Each host-expanded context line (!`cmd`)
  becomes a pointer to the fixture section headed `## cmd`, and review-pr's "$ARGUMENTS" becomes "" (its default:
  every review aspect).
- agents/: the pr-review-toolkit agents, verbatim.
The suite's cases tagged plugin-arm (a1, r1) are the ones this arm is compared on; the runner runs the arm on every
case, so read only those.

--destination defaults to $CLAUDE_JOB_DIR/tmp/plugin-baseline/pr-plugins; its SKILL.md and agents/ are replaced.
--marketplace is the installed claude-plugins-official marketplace. Exits 1 on a usage error or a command file it
can't read.
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path

COMMANDS = [("commit-commands", "commit"), ("commit-commands", "commit-push-pr"), ("code-review", "code-review"),
            ("pr-review-toolkit", "review-pr")]


class Fail(Exception):
    """A usage error or an unreadable plugin: the message goes to stderr and the exit code is 1."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Fail(f"{self.format_usage()}{self.prog}: error: {message}")


def main(argv):
    p = Parser(prog="stage_plugin_baseline.py", description="Stage the PR plugins as one skill folder.")
    job_dir = os.environ.get("CLAUDE_JOB_DIR")
    p.add_argument("--destination",
                   default=str(Path(job_dir) / "tmp" / "plugin-baseline" / "pr-plugins") if job_dir else None)
    p.add_argument("--marketplace", default=str(Path.home() / ".claude" / "plugins" / "marketplaces" /
                                                "claude-plugins-official"))
    o = p.parse_args(argv)
    if not o.destination:
        raise Fail("Pass --destination, or set CLAUDE_JOB_DIR for the default.")
    plugins = Path(o.marketplace) / "plugins"
    build = (Path(o.marketplace) / ".gcs-sha").read_text(encoding="utf-8").splitlines()[0][:12]

    descriptions, sections = [], []
    for plugin, command in COMMANDS:
        text = (plugins / plugin / "commands" / f"{command}.md").read_text(encoding="utf-8")
        m = re.fullmatch(r"---\r?\n(.*?)\r?\n---\r?\n(.*)", text, re.S)
        if not m:
            raise Fail(f"No frontmatter in {plugin}/{command}")
        frontmatter, body = m[1], m[2]
        d = re.search(r'^description:\s*"?(.*?)"?\s*$', frontmatter, re.M | re.I)
        if not d:
            raise Fail(f"No description in {plugin}/{command}")
        descriptions.append(d[1].rstrip(".") + ".")
        body = re.sub(r"!`([^`]+)`", r"(expanded: see `## \1` in the input file)", body)
        body = re.sub(r'"\$ARGUMENTS"', '""', body, flags=re.I)
        sections.append(f"## /{plugin}:{command}\n\n{body.strip()}\n")
    glue = ("**Harness glue (not plugin text).** These are the enabled commit-commands, code-review and "
            f"pr-review-toolkit commands (marketplace build {build}), verbatim below. Use the one the request "
            "calls for. A context line marked as expanded was run by the host before you saw it; its output "
            "is in the input file under a heading with the same command. You cannot launch subagents here: "
            "where a command says to use an agent, apply that agent's instructions (agents/) yourself. You "
            "cannot call tools either: where a command says to make tool calls and send no other text, write "
            "the commands you would run as text, in the format the request asks for.")
    skill = ["---", "name: pr-plugins", f'description: "{" ".join(descriptions)}"', "---", "", "# PR plugins", "",
             glue, "", *sections]

    destination = Path(o.destination)
    agents = destination / "agents"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(agents, ignore_errors=True)
    agents.mkdir()
    (destination / "SKILL.md").write_text("\n".join(skill) + "\n", encoding="utf-8", newline="\n")
    for agent in sorted((plugins / "pr-review-toolkit" / "agents").glob("*.md")):
        shutil.copy(agent, agents)
    print(f"Staged {destination} (build {build}): SKILL.md and {len(list(agents.iterdir()))} agents")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    try:
        sys.exit(main(sys.argv[1:]))
    except (Fail, OSError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
