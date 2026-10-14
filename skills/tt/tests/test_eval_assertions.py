"""The eval suite's objective assertions against planted answers, with no model call.

evals/planted/<case id>/ holds answers to a behaviour case: every right*.md must pass each regex and
not_regex assertion of its case, and every wrong*.md must fail at least one. An empty answer and a bare
refusal must fail every behaviour case. Patterns are matched as the eval harness matches them: re.search,
case-insensitive unless an assertion sets "ci": false.
"""
import json
import re
import unittest
from pathlib import Path

EVALS = Path(__file__).resolve().parents[1] / "evals"
MANIFEST = json.loads((EVALS / "shared-benchmark.json").read_text(encoding="utf-8"))
CASES = {c["id"]: c for c in MANIFEST["cases"] if c.get("kind") != "trigger"}
NON_ANSWERS = {"empty": "", "refusal": "I can't do that from this session.\n\nWrites: none"}


def failed(case, text):
    """Names of the case's regex and not_regex assertions that the text fails."""
    out = []
    for a in case["assertions"]:
        if a["type"] not in ("regex", "not_regex"):
            continue
        hit = re.search(a["pattern"], text, 0 if a.get("ci") is False else re.IGNORECASE)
        if bool(hit) != (a["type"] == "regex"):
            out.append(a["name"])
    return out


class PlantedAnswerTest(unittest.TestCase):
    def test_every_planted_folder_is_a_behaviour_case(self):
        for folder in (EVALS / "planted").iterdir():
            self.assertIn(folder.name, CASES)

    def test_right_answers_pass(self):
        for path in sorted((EVALS / "planted").glob("*/right*.md")):
            with self.subTest(path.relative_to(EVALS).as_posix()):
                self.assertEqual(failed(CASES[path.parent.name], path.read_text(encoding="utf-8")), [])

    def test_wrong_answers_fail(self):
        for path in sorted((EVALS / "planted").glob("*/wrong*.md")):
            with self.subTest(path.relative_to(EVALS).as_posix()):
                self.assertNotEqual(failed(CASES[path.parent.name], path.read_text(encoding="utf-8")), [])

    def test_empty_and_refusing_answers_fail_every_case(self):
        for cid, case in CASES.items():
            for label, text in NON_ANSWERS.items():
                with self.subTest(case=cid, answer=label):
                    self.assertNotEqual(failed(case, text), [])


if __name__ == "__main__":
    unittest.main()
