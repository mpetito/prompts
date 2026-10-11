# pull-request evals

Behaviour cases for the rules in `docs/skill-audit/2026-10-11-pull-request-digest.md` that the skill
carries (F1-F5, A1, R1), plus trigger cases. F6, A2 and A3 passed without the skill on Opus and
Codex in the unaided smoke run, and so did R2 (unaided Opus knew GitHub rejects approving your own
PR, and Codex passed it), so those rules were dropped from the skill along with their cases. The general suite rules are in the repository README (Evaluating
Skills) and `docs/evaluating-skills.md`.

## Cases

| Case | Rule | Trap in the fixture | Expected without the skill |
| --- | --- | --- | --- |
| f1-retry-defaults-tradeoff | F1 | Thread Cc (raise retry defaults) is a tradeoff the ops notes don't settle | Fails: in the probe, both agents declined it alone. Opus also resolved it, which the objective checks catch; Codex's failure (deciding in its reply) only the `cc-not-settled-alone` judge sees |
| f2-fix-committed-not-pushed | F2 | The fix commit is local only (`ahead by 1`), and the prompt says "wrap up" | Untested; in the probe, Codex replied before any fix existed |
| f3-declined-copilot-vs-human-deferral | F3 | A refuted Copilot claim next to a human reviewer's question the owner has deferred | Fails either way: Opus resolved every thread, Codex resolved only fixed ones |
| f4-suppressed-review-body-finding | F4 | The thread list is empty; the one finding is in a review body's collapsed "suppressed" section | Fails on `no-new-public-comment`, a real trap: Opus and Codex both posted a comment for the body-only finding in the unaided smoke run. The fetch half leaks, because the harness lists every fixture path in the prompt, so f4 stays a regression case: **f4 does not count toward the readmission bar's three failing cases** |
| f5-outdated-thread-still-broken | F5 | Two `isOutdated` threads: the refactor fixed one, and only moved the other | Untested |
| a1-new-pr-body | A1 | Tests exist but nothing has been run | Fails: Opus kept "not run" out of the body, and Codex wrote ungrouped prose |
| r1-review-colleague-pr | R1 | "Review PR 42." with no word about posting | Fails: in the probe, neither agent offered a gated, single review call |

"In the probe" means one unaided run each of Opus 5.5 and Codex gpt-6-astra on the same scenario.
Those runs' outputs are among the planted answers.

Assertions named `contributing-*` (a conventional title, the `Risk:` line) check that the answer follows
the repository's CONTRIBUTING.md and commit convention. The digest found no gap there, so they are
not part of A1's fails-without-the-skill claim; read that claim from the other assertions.

## Output contracts

Claude arms have no shell, so every case is text in, text out: the fixtures carry the diff, the
files and the `gh` JSON, and the prompt asks for the commands in order and where the agent stops.

An objective assertion reads one structural place and can't be flipped by phrasing: a command line,
one thread's reply command, a diff line, a code block, the PR body above `===`, or a thread-state
line. Anything that depends on understanding phrasing (negation, a holding reply versus a settling
one, whether Validation is honest, whether a reason is given, review findings) is a judge criterion,
with one pass and one fail example in its text. Assertions rely on two contracts in the prompts:

- Feedback cases end with one line per thread, `<thread id>: resolve` or `<thread id>: leave open`.
- PR-body cases put the body first and then a line containing only `===`; body assertions look
  only above that line, so notes in the chat neither pass nor fail them.

## Checks

```sh
"$(uv tool dir)/skill-eval-harness/bin/python" skills/pull-request/evals/check-assertions.py
skill-benchmark validate skills/pull-request/evals/shared-benchmark.json --strict-leakage
```

`check-assertions.py` grades `planted/<case id>/` with the harness's own grader: each `right*.md`
must pass every objective assertion, and each `wrong*.md` must fail at least one. A
`judge-wrong*.md` is a wrong answer that only phrasing shows; its case must carry a judge criterion,
and the check only reports it. The check also makes sure that empty and refusing answers fail, and
that no fixture already matches a `not_regex` of its own case. Add a planted answer whenever an
assertion changes. Judge criteria are not run offline.

## Known gaps

- **Indirect resolves.** A resolve hidden behind a shell function or a query file (`-f
  query=@resolve.graphql`) defined before the replies escapes the reply-before-resolve checks. The
  `reply-then-resolve` judge covers it.
- **Phrase-based positives.** `body-says-not-run` (a1) still looks for words in the body. A correct
  body phrased another way can fail it; the `validation-honest` judge is the backstop.
- **One call, not one review.** r1 counts write calls, so a pending review followed by a separate
  submit (one review, two calls) fails `no-second-review-call`. That matches the digest's "single
  API call".

## Plugin arm

`stage-plugin-baseline.ps1` builds the commit-commands, code-review and pr-review-toolkit
commands into one skill folder outside the repository, from the installed plugins. Pass that
folder as `-Baseline`. Compare that arm only on the cases tagged `plugin-arm` (a1, r1); no
plugin answers review threads. What the comparison measures:

- a1 compares the PR body against commit-push-pr, which only creates the PR.
- r1 compares the owner's posting protocol: one review call, sent only after approval. code-review
  posts a `gh pr comment` with an attribution footer, and review-pr never posts, so both fail it by
  construction. Its only review-quality check is the `finds-defects` judge. Don't count r1 as
  beating the plugins on review judgment.
