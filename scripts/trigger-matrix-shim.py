"""Run skill-trigger-matrix with the mounted skill folder named after the skill.

skill-eval-harness 0.6.0 names the temporary skill folder after the manifest's
skill_paths string, so `skill_paths: ["SKILL.md"]` mounts the skill at
`.claude/skills/SKILL.md/SKILL.md` and Claude Code registers it as "SKILL.md".
Skill-tool calls made under that name are then counted as misses. This shim
patches the folder-name function so the folder carries the manifest's skill_name,
and otherwise defers to the harness's own CLI. Remove it once the fix is upstream.
"""
import json
import sys
from pathlib import Path

import run_trigger_matrix
import skill_benchmark


def _skill_name_from_argv(argv: list[str]) -> str | None:
    for arg in argv[1:]:
        if arg.endswith(".json") and Path(arg).is_file():
            try:
                return json.loads(Path(arg).read_text(encoding="utf-8")).get("skill_name") or None
            except (OSError, ValueError):
                return None
    return None


SKILL_NAME = _skill_name_from_argv(sys.argv)
_original_key = skill_benchmark._skill_root_key


def _skill_root_key(rel: str) -> str:
    if SKILL_NAME and rel.replace("\\", "/").rstrip("/").endswith("SKILL.md"):
        return SKILL_NAME
    return _original_key(rel)


skill_benchmark._skill_root_key = _skill_root_key

if __name__ == "__main__":
    sys.exit(run_trigger_matrix.main())
