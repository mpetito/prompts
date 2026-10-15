"""Check the story suite's objective assertions offline, with the harness's own grader.

For every behaviour case in shared-benchmark.json:
- each not_regex is paired with at least one positive assertion, and an empty answer and a
  refusal both fail the case;
- no input fixture already matches a not_regex of its case, so an answer that echoes its
  input is not failed by the input;
- the planted answers in planted/<case id>/ grade as labelled: every right*.md passes every
  objective assertion, and every wrong*.md fails at least one. A case needs one right and
  two wrong answers;
- a judge-wrong*.md is a wrong answer that only phrasing shows, so only a judge criterion is
  meant to catch it. Its case must carry a judge assertion; the check reports whether the
  objective assertions catch it too, and requires nothing more.

Grading goes through skill_benchmark.assertion_result, so patterns are matched exactly as in
a run (case-insensitively unless an assertion sets "ci": false). No model is called. Run it
with the harness's Python and read the summary line; exit status 1 means a check failed:

    "$(uv tool dir)/skill-eval-harness/bin/python" skills/story/evals/check_assertions.py

It takes no arguments; any argument is a usage error, exit 1.
"""
import json
import sys
from pathlib import Path

from skill_benchmark import assertion_result

HERE = Path(__file__).resolve().parent
NEGATIVE = {"not_regex", "excludes_any"}
NON_ANSWERS = {"empty": "", "refusal": "I can't help with that: I don't have access to Azure DevOps."}
POSITIVE = {"regex", "contains", "contains_any", "contains_all"}


def failed_names(assertions, text):
    return [a["name"] for a in assertions if not assertion_result(a, text, HERE)["passed"]]


def main(argv):
    if argv:
        print("usage: check_assertions.py (no arguments; run it with the harness's Python)", file=sys.stderr)
        return 1
    manifest = json.loads((HERE / "shared-benchmark.json").read_text(encoding="utf-8"))
    problems, caught, wrong_total, right_ok, right_total = [], 0, 0, 0, 0
    for case in manifest["cases"]:
        if case.get("kind") == "trigger":
            continue
        cid = case["id"]
        objective = [a for a in case["assertions"] if a["type"] in POSITIVE | NEGATIVE]
        negatives = [a for a in objective if a["type"] in NEGATIVE]
        if negatives and not any(a["type"] in POSITIVE for a in objective):
            problems.append(f"{cid}: not_regex without a positive assertion")
        for label, text in NON_ANSWERS.items():
            if not failed_names(objective, text):
                problems.append(f"{cid}: the {label} answer passes")
        for rel in case.get("files", []):
            echoed = failed_names(negatives, (HERE / rel).read_text(encoding="utf-8"))
            if echoed:
                problems.append(f"{cid}: fixture {rel} already matches {echoed}")
        answers = sorted((HERE / "planted" / cid).glob("*.md"))
        rights = [p for p in answers if p.name.startswith("right")]
        wrongs = [p for p in answers if p.name.startswith("wrong")]
        judged = [p for p in answers if p.name.startswith("judge-wrong")]
        if judged and not any(a["type"] == "judge" for a in case["assertions"]):
            problems.append(f"{cid}: judge-wrong answers but no judge assertion")
        if len(rights) < 1 or len(wrongs) < 2:
            problems.append(f"{cid}: needs 1 right and 2 wrong planted answers, has {len(rights)} and {len(wrongs)}")
        print(f"{cid} ({len(objective)} objective assertions)")
        for path in answers:
            failed = failed_names(objective, path.read_text(encoding="utf-8"))
            if path in judged:
                verdict = "judge only" if not failed else "also objective"
            elif path in rights:
                right_total += 1
                right_ok += not failed
                verdict = "ok" if not failed else "WRONGLY FAILS"
            else:
                wrong_total += 1
                caught += bool(failed)
                verdict = "caught" if failed else "NOT CAUGHT"
            if verdict in ("WRONGLY FAILS", "NOT CAUGHT"):
                problems.append(f"{cid}/{path.name}: {verdict}")
            print(f"  {path.name:<34} {verdict:<14} {', '.join(failed)}")
    judged_total = sum(1 for _ in HERE.glob("planted/*/judge-wrong*.md"))
    print(f"\nwrong answers caught: {caught} of {wrong_total}; right answers passing: {right_ok} of {right_total}; "
          f"left to a judge: {judged_total}")
    for p in problems:
        print(f"PROBLEM {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
