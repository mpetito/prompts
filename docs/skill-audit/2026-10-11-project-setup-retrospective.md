# project-setup build retrospective (2026-10-11)

Readmitted `skills/project-setup/`, seeded from the archived `agents-md-authoring`. It is a
domain reference for setting a repository up for agentic development, or bootstrapping an
existing one. Digest: [2026-10-11-project-setup-digest.md](2026-10-11-project-setup-digest.md).

## Result

| | With skill | Without skill |
| --- | --- | --- |
| Objective, 3 holdout cases × 3 Opus runs | 1.00 (9 of 9) | 0.53 |
| Judge (Sonnet) | 0.83 | 0.34 |

Paired delta: 0.47. Every without-skill run fails at least two deterministic assertions. One
Codex run (case 3, with the skill) scored 1.00. The trigger matrix got 4 of 5 right; the miss is
discussed under "What to reuse". A three-run recheck of that query stayed quiet
in 3 of 3.

What unaided Opus got wrong, and the skill fixes:
- a lint script without `--max-warnings 0`;
- the file cap turned off for test files;
- no size or complexity caps on a new repository;
- specs under `docs/design/` or `docs/plans/`;
- a Copilot file that restates every AGENTS.md rule;
- no REVIEW.md and no CONTRIBUTING.md.

What it already did, so the skill only points to it: CLAUDE.md as `@AGENTS.md`, and ESLint bulk
suppressions at error.

## What the reviews caught

- **Plan review:**
  - Evidence provenance. Commits carry no AI trailer by rule since 2026-08-24, so "no trailer"
    proved nothing. The evidence lanes were steered mid-run.
  - Evals had to come before the skill body. The ruling ran the without-skill smoke first; it cut
    or reshaped the traps unaided Opus already passed (the CLAUDE.md import, suppressions).
- **Review round 1:**
  - The Copilot template restated REVIEW.md's scope, which Copilot code review on GitHub.com
    reads itself.
  - The docs-only CI filter failed open: a bad base SHA let the required check pass without
    running anything.
- **Review round 2:**
  - Hollow answers passed. Complexity 99 scored 7/7 because only key presence was checked.
  - The AGENTS.md template let one rule sit under both Standing rules and Do Not, which cost two
    case-2 judge scores. The round-3 fix ("Standing rules holds only positive rules") made it
    worse: every rerun split each rule into a positive and a negative line. "One rule, one
    bullet" fixed it (D3, default applied), and `agents-md-rule-once` now checks it.
- **Thread checks:**
  - Two with-skill "failures" were pattern misses. The answers were right: a `testFiles`
    variable, and `CarrierError` named as a contract.
  - A reviewer nit on Visual Studio was wrong. The live docs agreed with the author.

## Cost

- Claude eval spend: $12.15, inside the owner's $15 cap. The owner was asked at $10 (D2: "up to $4 more").
- Codex: 86k tokens.
- Workers, all on Opus: 5 evidence and plan lanes, the skill author (3 rounds), the eval author
  (rounds 0-2 plus parts A-E), and the reviewer (3 rounds). Review rounds cost no model spend.

## What to reuse

- **Smoke first.** One without-skill run per case (about $0.50) showed which traps discriminate
  before the body was written.
- **Read the with-skill failures yourself before loosening a pattern.** Both were form misses,
  not behaviour.
- **The trigger harness counts an exploratory read as a load.** The neg-trig-skill-md "fire" had
  no Skill call.
- **A positive value check beats a not_regex on a relaxed value.** An unaided answer dodged
  "max-lines off" by scoping caps to `src/**`.

## Follow-ups (owner)

- The trim path (step 8) and the labelled-override convention have no eval case; the archived
  harborview fixture would supply one.
- The 30-day load target (readmission item 5) is bootstrapping a named project with the skill.
- `../code-style/SKILL.md` resolves once the code-style build lands.
- ESLint doesn't report suppression entries for deleted files until `--prune-suppressions`.
- The case-2 judge marks REVIEW.md "Check hardest" items as restated rules, although
  review-scope.md's template puts them there. The rubric should allow it.
- Eval patterns that are lenient or depend on wording, none affecting an observed run:
  - command forms in bulleted or numbered lists;
  - one-line package.json;
  - negated mentions;
  - `agents-md-rule-once` counts occurrences, not bullets.
- The build lands without the cherry-picked runner fix (fcd7e83), which the code-style build
  owns. Codex runs need it at effort above `none`.
