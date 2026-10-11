"""Print a ruff per-file-ignores baseline from `ruff check --output-format json` on stdin.

Run it from the target repository's root; paths are printed relative to that directory.
Exits 1 without printing a baseline when ruff reports a syntax error, which has no rule code
that per-file-ignores accepts.
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RULE_CODE = re.compile(r"^[A-Z]+[0-9]+$")


def collect(violations: list[dict]) -> tuple[dict[str, set[str]], set[str]]:
    """Group rule codes by repo-relative path, and return the paths with syntax errors."""
    codes: defaultdict[str, set[str]] = defaultdict(set)
    unparsable: set[str] = set()
    for violation in violations:
        path = Path(violation["filename"]).resolve().relative_to(Path.cwd()).as_posix()
        code = violation.get("code") or ""
        if RULE_CODE.match(code):
            codes[path].add(code)
        else:
            unparsable.add(path)
    return codes, unparsable


def main() -> int:
    """Print one TOML entry per file, or list the files to fix first and return 1."""
    codes, unparsable = collect(json.load(sys.stdin))
    if unparsable:
        print("Fix the syntax errors in these files first:", file=sys.stderr)
        print("\n".join(sorted(unparsable)), file=sys.stderr)
        return 1
    for path, rules in sorted(codes.items()):
        print(f'"{path}" = {json.dumps(sorted(rules))}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
