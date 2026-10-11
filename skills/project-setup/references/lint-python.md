# Python lint, line-count check and CI

Every default here is **inferred**: the owner set no Python caps, so these mirror the TypeScript
numbers in [lint-typescript.md](lint-typescript.md), and the thread ruled on the rest within
that. Every rule fails the run; ruff has no warning level.

Contents: [ruff config](#ruff-config) · [Module length](#module-length) ·
[Existing violations](#existing-violations) · [CI job](#ci-job) ·
[Commit hook](#commit-hook) · [Helper scripts](#helper-scripts)

## ruff config

`pyproject.toml`:

```toml
[tool.ruff.lint]
extend-select = ["C90", "PLR0912", "PLR0913", "PLR0915", "ANN401", "FIX", "TD"]

[tool.ruff.lint.mccabe]
max-complexity = 10

[tool.ruff.lint.pylint]
max-args = 4
max-branches = 12
max-statements = 50

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["PLR0915"]
```

- C901 caps complexity at 10 and PLR0913 caps arguments at 4.
- PLR0912 and PLR0915 cap branches at 12 and statements at 50, ruff's own defaults, written out
  so they show (inferred).
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

Inferred. ruff has no suppressions file (a baseline is requested in
[astral-sh/ruff#1149](https://github.com/astral-sh/ruff/issues/1149)), so the baseline lives in
`per-file-ignores`: one entry per file that breaks a cap today, listing only the rules it breaks.
Never `ruff check --add-noqa` or an inline `# noqa`; never raise a cap.

Generate the entries once with this skill's [ruff_baseline.py](../scripts/ruff_baseline.py),
run from the target repository's root (the script stays in the skill, not in the repository):

```bash
uv run ruff check --output-format json --exit-zero | python3 <this skill's folder>/scripts/ruff_baseline.py
```

It exits 1 and lists the files when ruff reports a syntax error; fix those first.

Paste the output under `[tool.ruff.lint.per-file-ignores]`, after a comment
`# Baseline at bootstrap: entries may only be removed.` The baseline may only shrink: after a
fix, delete that file's entry (or one rule from it) and rerun `ruff check`. It is coarser than
ESLint's counts: a listed file can gain more violations of a listed rule, so review rejects any
change that adds an entry or a rule to one.

## CI job

The TypeScript workflow's checkout and fail-closed diff step apply unchanged
([lint-typescript.md](lint-typescript.md#ci-job)); the steps after them become, each gated the
same way:

```yaml
      - if: steps.diff.outputs.code == 'true'
        uses: astral-sh/setup-uv@1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0
      - if: steps.diff.outputs.code == 'true'
        run: uv sync --locked
      - if: steps.diff.outputs.code == 'true'
        run: uv run ruff check
      - if: steps.diff.outputs.code == 'true'
        run: uv run ruff format --check
      - if: steps.diff.outputs.code == 'true'
        run: uv run python scripts/check_module_lines.py
      - if: steps.diff.outputs.code == 'true'
        run: npx --yes jscpd@5.4.1 --min-tokens 50 --threshold <N> src
      - if: steps.diff.outputs.code == 'true'
        run: uv run pytest
```

Add the project's type checker as a step; swap `uv run` for the project's runner if it has
another. jscpd runs through `npx` in CI only (inferred), with the threshold set from its first
report as in [lint-typescript.md](lint-typescript.md#duplication); GitHub's Ubuntu runners
include Node.

## Commit hook

Inferred. A Python-only repository uses the [pre-commit](https://pre-commit.com/) framework with
ruff's hooks instead of husky, fixing formatting at commit. `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.17.0
    hooks:
      - id: ruff-format
```

```bash
uv add --dev pre-commit
uv run pre-commit install
```

Keep `rev` at the ruff version the project pins. A repository that already has Node keeps husky
plus lint-staged ([lint-typescript.md](lint-typescript.md#commit-hook)), running `ruff format`
on staged `*.py` files.

## Helper scripts

Inferred. In a Python repository, helper scripts under `scripts/` may be Python (as
`check_module_lines.py` is); they run on Linux CI and on Windows alike.
