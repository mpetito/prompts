# Python lint, line-count check and CI

Inferred defaults: the owner set no Python caps, so these mirror the TypeScript
numbers in [lint-typescript.md](lint-typescript.md). Every rule fails the run; ruff has no warning
level.

Contents: [ruff config](#ruff-config) · [Module length](#module-length) ·
[Existing violations](#existing-violations) · [CI job](#ci-job) ·
[Duplication and commit hook](#duplication-and-commit-hook)

## ruff config

`pyproject.toml`:

```toml
[tool.ruff.lint]
extend-select = ["C90", "PLR0912", "PLR0913", "PLR0915", "ANN401", "FIX", "TD"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 4

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["PLR0915"]
```

- C901 caps complexity at 10 and PLR0913 caps arguments at 4.
- PLR0912 (branches) and PLR0915 (statements) keep ruff's own defaults: the owner set no number.
- ANN401 bans `Any` in annotations; FIX and TD ban TODO, FIXME, XXX and HACK comments.
- Tests skip the statement cap, as TypeScript tests skip the function-length cap.

Rule reference: [ruff rules](https://docs.astral.sh/ruff/rules/), [settings](https://docs.astral.sh/ruff/settings/).

## Module length

ruff has no module-length rule
([astral-sh/ruff#970](https://github.com/astral-sh/ruff/issues/970)), so a script enforces 300
lines per source file and 800 per test file, skipping blank and comment lines.
`scripts/check_module_lines.py`:

```python
"""Fail when a Python module exceeds its line cap, counting non-blank, non-comment lines."""

import sys
from pathlib import Path

SOURCE_CAP = 300
TEST_CAP = 800


def is_test(path: Path) -> bool:
    """Return True for files under a tests directory or named test_*.py or *_test.py."""
    return (
        "tests" in path.parts
        or path.name.startswith("test_")
        or path.stem.endswith("_test")
    )


def counted_lines(path: Path) -> int:
    """Count lines that are neither blank nor a whole-line comment."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return sum(
        1 for line in lines if line.strip() and not line.lstrip().startswith("#")
    )


def main(roots: list[str]) -> int:
    """Print each module over its cap and return 1 if there was any."""
    over = []
    for root in roots:
        for path in sorted(Path(root).rglob("*.py")):
            cap = TEST_CAP if is_test(path) else SOURCE_CAP
            count = counted_lines(path)
            if count > cap:
                over.append(f"{path}: {count} lines (cap {cap})")
    if not over:
        return 0
    print("\n".join(over))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["src", "tests"]))
```

## Existing violations

ruff has no suppressions file (a baseline is requested in
[astral-sh/ruff#1149](https://github.com/astral-sh/ruff/issues/1149)). `ruff check --add-noqa`
writes a `# noqa` comment per violation, the Python form of `eslint-disable`. Before
bootstrapping a Python repository that already breaks these caps, ask the owner how to hold the
existing violations; never raise a cap to get green.

## CI job

The TypeScript workflow's `changes` job and pinned checkout apply unchanged
([lint-typescript.md](lint-typescript.md#ci-job)); the `ci` job's steps become:

```yaml
      - uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0
      - run: uv sync --locked
      - run: uv run ruff check
      - run: uv run ruff format --check
      - run: uv run python scripts/check_module_lines.py
      - run: uv run pytest
```

Add the project's type checker as a step; swap `uv run` for the project's runner if it has
another.

## Duplication and commit hook

Both confirmed defaults run on Node: jscpd ([lint-typescript.md](lint-typescript.md#duplication))
and husky plus lint-staged running `ruff format` on staged `*.py` files. In a Python-only
repository, ask the owner before adding Node or a different hook tool.
