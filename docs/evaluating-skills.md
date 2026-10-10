# Evaluating skills

How to run, read and extend a skill's eval suite with `scripts/run-skill-eval.ps1`. The suite
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
- Speed and cost

## Setup

PowerShell 7.4+, a logged-in `claude` CLI (or `codex` for `-Agent codex`), then once:

```sh
uv tool install skill-eval-harness
```

Every run lands in `.eval-runs/<skill>/<timestamp>/` (gitignored).

## Pick the run for the edit

| You changed | Run (`pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill <name> …`) |
| --- | --- |
| Only the description | `-TriggerOnly -TriggerRuns 3` |
| The body or `references/` | `-Runs 3 -SkipTrigger -Baseline <previous revision>` |
| Only assertions | `-Regrade .eval-runs/<name>/<timestamp>`; no model calls |
| Only a judge rubric | `-Regrade .eval-runs/<name>/<timestamp> -Rejudge`; judge calls only |
| A fixture or a case prompt | a new run; earlier runs no longer pair with it |
| A new or readmitted skill | `-Runs 3 -TriggerRuns 3` |
| An agent definition under `agents/` | `-AgentDefinition <name> -Runs 3` (see Agents) |
| Anything, while iterating | `-Runs 1 -SkipJudge -SkipTrigger`; confirm with `-Runs 3` |

One run is noisy; decide on three. `-Runs 3` means three runs per arm per case.

## Compare against an earlier revision or a competing skill

`-Baseline <folder>` runs that folder's `SKILL.md` as a third arm, `old_skill`, beside
`with_skill` and `without_skill`. The harness mounts the whole folder, minus `evals/` and
dotfiles, so a multi-file skill keeps its references. The runner writes an all-absolute copy of
the manifest to the run directory, so neither the live skill nor its manifest changes.

```sh
# the committed revision of a skill, as the baseline for an uncommitted edit
rm -rf /tmp/baseline && mkdir -p /tmp/baseline && git archive HEAD skills/<name> | tar -x -C /tmp/baseline
pwsh -NoProfile -File ./scripts/run-skill-eval.ps1 -Skill <name> -Runs 3 -SkipTrigger -Baseline /tmp/baseline/skills/<name>
```

A competing skill, such as an official plugin's, is compared the same way: pass its folder. The
readmission bar requires this for a skill that overlaps a plugin. `-IncludeOldSkill` instead
uses the manifest's own `old_skill_paths`.

## Read the results

The script ends with one line per arm, then every failed assertion with its count:

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

## What each arm can see

Claude runs load project settings only, with every tool that can act on the machine denied, so
user-level skills, plugins and MCP servers stay out of every arm. A competing skill installed
on this machine is therefore never in play unless passed as `-Baseline`. Trigger rates measured
with the shell allowed are not comparable: the model explores with git instead of loading a
skill. `without_skill` sees only the fixtures.

## Agents

`-AgentDefinition <name>` evaluates `agents/<name>.md` instead of a skill. Its suite lives in
`evals/agents/<name>/`, outside `agents/`, because setup links that folder whole into
`~/.claude/agents` and Claude Code loads every `.md` beneath it as an agent.
`evals/agents/verifier/` is the example.

- `with_skill` runs the definition as the session (`claude -p --agent <name>`), so its system
  prompt and tool list apply. `without_skill` is plain Claude Code.
- Every arm runs on the definition's `model` and `effort`. The CLI's `--model` overrides an
  agent's own pin, so the runner passes the pin to all arms, and the comparison measures the
  definition rather than the model.
- `-Baseline <file>` adds an earlier definition as `old_skill`. `-Regrade` and `-Rejudge` work
  as for skills.

Agent tasks go through `scripts/agent-eval-backend.py` (the harness's `run-subagent
--agent-cmd`). It moves the definition into the workspace's `.claude/agents/`, removes the
harness's "read and follow the skill file" opening from every arm alike, and fails the run if
Claude serves a model other than the one requested.

Write cases for what the definition adds. In the verifier pilot, Opus without the definition
found the same defects; the output contract and the one-claim rule separated the arms.

Not supported yet: delegation evals (whether a main session hands work to the agent), and
Codex, since agent definitions are Claude Code's format.

## Speed and cost

The harness runs one task at a time. The script splits answer runs round-robin across
`-Parallel` processes (default 4), judges each arm in its own process, and measures triggering
while the answer runs are in flight. Answer runs dominate: about 20 seconds each on Sonnet.

| skill-authoring suite: 27 answer runs (3 cases, 3 arms, 3 runs) | Wall clock |
| --- | --- |
| Answer runs and judge, one process at a time (before) | about 11 minutes |
| Answer runs, judge and trigger matrix, `-Parallel 4` | about 3.5 minutes, 2.4 of them answer runs |
| `-Regrade … -Rejudge`, 27 verdicts | about 1 minute |

On Sonnet, an answer run costs about $0.04–0.10 (a longer skill costs more) and a judge call
about $0.02–0.03, so a three-arm, three-run suite of three cases costs about $2–2.50. Raise `-Parallel`
if the account's rate limit allows. The harness records a run that fails to launch or times
out as unscorable and leaves it out of the pairing, so check `logs/` when an arm reports fewer
runs than expected.
