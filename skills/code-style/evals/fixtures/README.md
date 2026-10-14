# code-style fixtures

Conventions for the code cases in `../shared-benchmark.json`. The general suite rules are in the
repository's `docs/evaluating-skills.md`.

## One fixture, one trap, one rule

- Each fixture carries exactly one trap, tied to one rule the skill states. A case that fails
  says which rule broke.
- The task is an ordinary change (add an option, fix a bug, extend a function). The trap sits
  in the code the change touches, so applying the rule is part of doing the task. The prompt
  never names the rule.
- Name the file for its domain (`invoice_totals.py`), never for its rule
  (`redundant_comments.py`): the harness lists every fixture path in the prompt.
- Before a case is kept, run its `without_skill` arm on Opus and on Codex. If the unaided model
  avoids the trap in every run, re-trap the fixture or drop the case.

## Fixture files

- Keep each one short (under about 150 lines) and in one language. The code should parse.
- The harness copies every fixture flat into `inputs/<file name>`, so file names must be
  unique within a case; subdirectories are not kept.
- A case cannot rely on running code, tests or a linter. Claude arms have no shell, and Codex
  arms have a read-only sandbox.

## Case prompt

```text
<the task>. Read the input file; a read-only command such as cat is fine for that, but do not
change any file or run anything else. Output every file you changed in full: for each, a
level-2 heading with its file name, then its complete new content in one fenced code block.
After the files, add at most three lines of notes, and do not quote the original code.
```

- **The reading sentence must allow a read-only command.** Codex has no file-read tool. With
  "do not run any commands" or "read the input file, but do not run commands", Codex refused to
  read the fixture in both arms and asked for it to be pasted. The sentence above let both Codex
  and Opus read it (pr-authoring smoke, 2026-10-10).
- **The whole changed file comes back,** so regex assertions check the code as written, not a
  description of it.
- **No quoted originals.** A `not_regex` assertion for the trap would also match a note that
  quotes the old line.

## Assertions

- Per rule, assert the rule-following form (`regex`) and, where it is distinct, the trap's
  absence (`not_regex`).
- Test each pattern against a real passing output and a real failing output before relying on
  it.
