# Evaluating skills

How to run, read and extend a skill's eval suite with `scripts/run_skill_eval.py`. The suite
format is [skill-eval-harness](https://github.com/adewale/skill-eval-harness) (tested with
0.6.0); `skills/skill-authoring/evals/` is a complete example with three behaviour cases.

## Contents

- Setup
- Pick the run for the edit
- Compare against an earlier revision or a competing skill
- Read the results
- Write and fix assertions
- What each arm can see
- Agents
- Running on Codex
- Speed and cost

## Setup

Python 3.12+ as `python3`, a logged-in `claude` CLI (or `codex` for `--agent codex`), then once:

```sh
uv tool install skill-eval-harness
```

Every run lands in `.eval-runs/<skill>/<timestamp>/` (gitignored).

## Pick the run for the edit

| You changed | Run (`python3 scripts/run_skill_eval.py --skill <name> …`) |
| --- | --- |
| Only the description | `--trigger-only --trigger-runs 3` |
| The body or `references/` | `--runs 3 --skip-trigger --baseline <previous revision>` |
| Only assertions | `--regrade .eval-runs/<name>/<timestamp>`; no model calls |
| Only a judge rubric | `--regrade .eval-runs/<name>/<timestamp> --rejudge`; judge calls only |
| A fixture or a case prompt | a new run; earlier runs no longer pair with it |
| A new or readmitted skill | `--runs 3 --trigger-runs 3` |
| An agent definition under `agents/` | `--agent-definition <name> --runs 3` (see Agents) |
| Anything, while iterating | `--runs 1 --skip-judge --skip-trigger`; confirm with `--runs 3` |
| Only newly added cases | Mark them `"split": "holdout"`, run with `--split holdout`, regrade with the same `--split`, then set them back to `tune` |

One run is noisy; decide on three. `--runs 3` means three runs per arm per case.

Measure a skill on the model and effort it will run on: `--model opus --effort high` for the
orchestration skills. `--effort` reaches the answer and trigger runs, every arm alike, through the
Claude wrapper (the installed harness's `run-agent` has no effort option); the judge keeps its
default so verdicts stay comparable. For Codex, see Running on Codex.

## Compare against an earlier revision or a competing skill

`--baseline <folder>` runs that folder's `SKILL.md` as a third arm, `old_skill`, beside
`with_skill` and `without_skill`. The harness mounts the whole folder, minus `evals/` and
dotfiles, so a multi-file skill keeps its references. The runner writes an all-absolute copy of
the manifest to the run directory, so neither the live skill nor its manifest changes.

```sh
# the committed revision of a skill, as the baseline for an uncommitted edit; a fresh folder per run,
# so two evals running at once never share or delete each other's baseline
baseline="$(mktemp -d)" && git archive HEAD skills/<name> | tar -x -C "$baseline"
python3 scripts/run_skill_eval.py --skill <name> --runs 3 --skip-trigger --baseline "$baseline/skills/<name>"
```

A competing skill, such as an official plugin's, is compared the same way: pass its folder. The
readmission bar requires this for a skill that overlaps a plugin. `--include-old-skill` instead
uses the manifest's own `old_skill_paths`.

## Read the results

The runner ends with one line per arm, then every failed assertion with its count:

```text
  with_skill                     objective 1.00  judge 0.83  cost USD 0.47
  without_skill                  objective 0.81  judge 0.63  cost USD 0.38
  old_skill (skill-creator)      objective 0.74  judge 0.58  cost USD 0.88
  paired delta, with minus without: 0.19
  failed 3x  pos-review-draft-skill/without_skill: worker-model-opus
```

- **objective** is the share of deterministic assertions passed. It is the number the
  readmission bar and CONTRIBUTING mean by pass rate.
- **judge** is the mean rubric score from 0 to 1. Judge assertions are soft by default in the
  harness, so they never change the pass rates; the script reports them separately. Judging
  the same outputs twice has moved an arm's mean by 0.08, so decide on the objective rate.
- The readmission bar's "fails without the skill" is read here as: the `without_skill` arm
  fails at least one of the case's assertions in every run.
- Before trusting a failure, read `runs/<case>/<arm>/run-N/output.md`. `review.html` shows
  every run side by side, `benchmark.json` holds the full report, and `logs/` holds the
  output of each parallel process.

## Write and fix assertions

The suite rules (one fixture per case, assertions that trace to a rule with a trap in the
fixture, near-miss trigger negatives) are in the README's Evaluating Skills section. These
are the ways an assertion goes wrong once outputs arrive:

- **Tense and phrasing.** Outputs say "Deleted the section" as often as "delete it". Match stems:
  `\b(?:remov|delet|drop|cut)\w*`, not `\bdelete\b`.
- **Version-bound numbers.** An assertion that wants "500 lines" fails a skill that rightly
  states a different budget. Assert the behaviour (a stated budget plus `references/`).
- **The input echoed back.** A line-anchored pattern such as `^description:` also matches a
  quoted copy of the fixture. Ask in the case prompt for originals to be quoted inline.
- **Fixing after the fact.** An assertion added or widened after reading outputs must trace to
  a rule the skill already states and a trap the fixture already had. Regrade every earlier
  run with it, all arms alike.

Test a new pattern against a real passing and a real failing output before relying on it.

Read the trace before tuning a description for a missed should-not-fire query
(`trigger-traces/…/<query>/run-N/trace.jsonl`). The harness counts any read of the mounted
SKILL.md as loading it, and in an otherwise empty workspace the model may read the file while
exploring after it has already routed the request elsewhere, such as to a built-in skill.

## What each arm can see

Claude runs load project settings only, with every tool that can act on the machine denied, so
user-level skills, plugins and MCP servers stay out of every arm. A competing skill installed
on this machine is therefore never in play unless passed as `--baseline`. Trigger rates measured
with the shell allowed are not comparable: the model explores with git instead of loading a
skill. `without_skill` sees only the fixtures.

Two consequences for writing cases, both from the model-council and firecrawl readmission
(`docs/skill-audit/2026-10-10-readmit-retrospective.md`):

- **Say "read the input file, but do not run commands",** never "do not call any tools". The
  second wording stopped Sonnet reading its fixture in 12 of 21 runs.
- **A skill built on an MCP server is measured against that server's own guidance.** Answer runs
  see no MCP tool, so copy the server's instructions and the tool descriptions a live session
  would see into the fixture, verbatim. Without them the eval credits the skill with rules the
  live session already has; with them, Firecrawl's archived routing table mostly fell away.

The harness (0.6.0) copies each fixture to `inputs/` and lists every one in the task prompt, so
both arms are pointed at every file. A case cannot test whether a skill makes the model look for
a file unprompted, such as a repository's `REVIEW.md`; test what the skill does once it has read
it, or what it does when the file is absent.

Claude arms still load the user's `~/.claude/CLAUDE.md`: `--setting-sources project` does not
exclude it (probe, 2026-10-11). `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` would block it; the runner
keeps it because Claude subagents load it in real use too. Read a Claude `without_skill` arm as
"the owner's global instructions, no skill". Codex arms never see it.

## Agents

`--agent-definition <name>` evaluates `agents/<name>.md` instead of a skill. Its suite lives in
`evals/agents/<name>/`, outside `agents/`, because setup links that folder whole into
`~/.claude/agents` and Claude Code loads every `.md` beneath it as an agent.
`evals/agents/verifier/` is the example.

- `with_skill` runs the definition as the session (`claude -p --agent <name>`), so its system
  prompt and tool list apply. `without_skill` is plain Claude Code.
- Every arm runs on the definition's `model` and `effort`. The CLI's `--model` overrides an
  agent's own pin, so the runner passes the pin to all arms, and the comparison measures the
  definition rather than the model.
- `--baseline <file>` adds an earlier definition as `old_skill`. `--regrade` and `--rejudge` work
  as for skills.

Agent tasks go through `scripts/agent_eval_backend.py` (the harness's `run-subagent
--agent-cmd`). It moves the definition into the workspace's `.claude/agents/`, removes the
harness's "read and follow the skill file" opening from every arm alike, and fails the run if
Claude serves a model other than the one requested.

Write cases for what the definition adds. In the verifier pilot, Opus without the definition
found the same defects; the output contract and the one-claim rule separated the arms.

Not supported yet: delegation evals (whether a main session hands work to the agent), and
Codex, since agent definitions are Claude Code's format.

## Running on Codex

`--agent codex` runs every arm through `codex exec` with the user config ignored, so nothing in
`~/.codex/config.toml` applies. Checked with codex-cli 0.160.0 on a ChatGPT login (2026-10-10):

- **Pass a Codex model.** `--model` and `--judge-model` go to Codex unchanged, and their default,
  `sonnet`, fails: "The 'sonnet' model is not supported when using Codex with a ChatGPT
  account." Use, for example, `--model gpt-6-astra`, and `--judge-model gpt-6-astra` unless you
  pass `--skip-judge`.
- **Pass `--effort`.** Without it Codex runs at reasoning effort `none`. `--effort` reaches the
  answer runs only (as `-c model_reasoning_effort=<level>`); the trigger and judge runs stay at
  `none`.
- **Word the case prompt so Codex can read.** Codex has no file-read tool, only a read-only
  shell. Under "do not run any commands" or "read the input file, but do not run commands" it
  refused to read the skill and the fixture in both arms and asked for them to be pasted, which
  scores as a failure in both. "Read the input file; a read-only command such as cat is fine for
  that, but do not change any file or run anything else" worked on Codex and on Opus. Every
  existing suite forbids commands in some form, so before trusting its Codex results, check the
  outputs for a request to paste the files.
- **Cost is tokens, not dollars.** The summary prints `cost USD n/a`; each run's
  `metadata.json` has the token counts, and the ChatGPT plan meter is the only spend signal.
- **Isolation differs.** The skill is mounted at `skills/root-0/SKILL.md` and named in the task
  prompt, the same as for Claude. Codex can also run read-only shell commands, which Claude arms
  cannot, and the account's `codex_apps` connector stays visible.

## Speed and cost

The harness runs one task at a time. The script splits answer runs round-robin across
`--parallel` processes (default 4), judges each arm in its own process, and measures triggering
while the answer runs are in flight. Answer runs dominate: about 20 seconds each on Sonnet.

| skill-authoring suite: 27 answer runs (3 cases, 3 arms, 3 runs) | Wall clock |
| --- | --- |
| Answer runs and judge, one process at a time (before) | about 11 minutes |
| Answer runs, judge and trigger matrix, `--parallel 4` | about 3.5 minutes, 2.4 of them answer runs |
| `--regrade … --rejudge`, 27 verdicts | about 1 minute |

On Sonnet, an answer run costs about $0.04–0.10 (a longer skill costs more) and a judge call
about $0.02–0.03, so a three-arm, three-run suite of three cases costs about $2–2.50. Raise `--parallel`
if the account's rate limit allows. The harness records a run that fails to launch or times
out as unscorable and leaves it out of the pairing, so check `logs/` when an arm reports fewer
runs than expected.
