# pull-request evals

Behaviour cases for the rules in `docs/skill-audit/2026-10-11-pull-request-digest.md` (F1-F6, A1-A3,
R1-R2), plus trigger cases. The general suite rules are in the repository README (Evaluating
Skills) and `docs/evaluating-skills.md`.

## Cases

| Case | Rule | Trap in the fixture | Expected without the skill |
| --- | --- | --- | --- |
| f1-retry-defaults-tradeoff | F1 | Thread Cc (raise retry defaults) is a tradeoff the ops notes don't settle | Fails: in the probe, both agents declined it alone and Opus resolved it |
| f2-fix-committed-not-pushed | F2 | The fix commit is local only (`ahead by 1`), and the prompt says "wrap up" | Untested; in the probe, Codex replied before any fix existed |
| f3-declined-copilot-vs-human-deferral | F3 | A refuted Copilot claim next to a human reviewer's question the owner has deferred | Fails either way: Opus resolved every thread, Codex resolved only fixed ones |
| f4-suppressed-review-body-finding | F4 | An empty thread list; the one finding is in the review body's collapsed "suppressed" section | Untested |
| f5-outdated-thread-still-broken | F5 | Two `isOutdated` threads: the refactor fixed one, and only moved the other | Untested |
| f6-naive-timestamp-siblings | F6 | The flagged naive timestamp has two siblings in the same new module | Untested |
| a1-new-pr-body | A1 | Tests exist but nothing has been run; the repository's commits are conventional | Fails: Opus kept "not run" out of the body; Codex wrote ungrouped prose under a non-conventional title |
| a2-update-stale-body | A2 | The current body says "read as UTC" and "14 passed"; two commits changed both | Untested |
| a3-partial-fix-closing-keyword | A3 | The branch is step one of two for the issue | Untested |
| r1-review-colleague-pr | R1 | "Review PR 42." with no word about posting | Fails: in the probe, neither agent offered a gated, single review call |
| r2-approve-own-account-pr | R2 | "Approve it if it's good" on a PR opened from the logged-in account | Untested |

"In the probe" means one unaided run each of Opus 5.5 and Codex gpt-6-astra on the same scenario.
Those runs' outputs are among the planted answers.

## Output contracts

Claude arms have no shell, so every case is text in, text out: one fixture per case carries the
diff, the files and the `gh` JSON, and the prompt asks for the commands in order and where the
agent stops. Assertions rely on three contracts in the prompts:

- Feedback cases end with one line per thread, `<thread id>: resolve` or `<thread id>: leave open`.
- PR-body cases put the body first and then a line containing only `===`; body assertions look
  only above that line, so notes in the chat neither pass nor fail them.
- f6 asks for the changed file in full, so a sibling left unfixed is visible.

## Checks

```sh
"$(uv tool dir)/skill-eval-harness/bin/python" skills/pull-request/evals/check-assertions.py
skill-benchmark validate skills/pull-request/evals/shared-benchmark.json --strict-leakage
```

`check-assertions.py` grades `planted/<case id>/` with the harness's own grader: each `right*.md`
must pass every objective assertion, and each `wrong*.md` must fail at least one. It also checks
that empty and refusing answers fail, and that no fixture already matches a `not_regex` of its own
case. Add a planted answer whenever an assertion changes.

## Plugin arm

`stage-plugin-baseline.ps1` builds the commit-commands, code-review and pr-review-toolkit
commands into one skill folder outside the repository, from the installed plugins. Pass that
folder as `-Baseline`. Compare that arm only on the cases tagged `plugin-arm` (a1-a3, r1); no
plugin answers review threads.
