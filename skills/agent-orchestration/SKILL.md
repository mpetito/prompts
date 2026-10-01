---
name: agent-orchestration
description: "Run a multi-agent build as its orchestrator: plan lanes and ownership, keep every lane moving, rule on review findings, gate merges and releases, and keep state across compaction. Use when orchestrating or coordinating several agents or lanes (subagents, Herdr peers, CLI reviewers) on one build, running a long autonomous build or working while the user is away, planning review and merge gates for multi-agent work, or resuming as orchestrator after compaction. For one agent executing one spec use implement; for one loop against one CI or deploy signal use autonomous-loops."
---

# Agent Orchestration

The orchestrator owns the plan, the lanes, the rulings, the gates and the conversation with the
human for a build that several agents carry out. It writes little code itself. Its costly
failures are idle time and wasted rounds: a lane nobody is watching, a question that holds every
lane, a review loop that never converges.

## Every Turn

These two rules apply on every turn, including the first turn after a compaction.

1. **Before ending a turn, every in-flight lane has a wake source:** a running subagent, a
   background wait on a peer, a background gate watcher, or a background job writing a log. List
   the lanes and arm whatever is missing, or don't end the turn. A lane without one sits finished,
   or dead, until the human notices.
2. **Never block on a question tool while other work can move.** A blocking prompt halts every
   lane until the human answers; Claude Code's `AskUserQuestion` stays open until answered by
   default. In one build, 21 such prompts held the loop for 646 minutes. Ask in a normal message
   instead ([The human](#3-the-human)) and keep dispatching.

## Where Other Work Belongs

| Need | Skill |
| --- | --- |
| One agent executing one numbered spec | [implement](../implement/SKILL.md) |
| One loop against one asynchronous signal: CI runs, merge refs, watchers, deploy waits | [autonomous-loops](../autonomous-loops/SKILL.md) |
| Anything another agent executes: briefs, fix-round notes, reviewer prompts, the standing shared-machine block, the report contract | [agent-briefs](../agent-briefs/SKILL.md) |
| Starting, prompting, queueing and watching peer panes | [herdr-delegation](../herdr-delegation/SKILL.md) |
| What a reviewer does to a diff | [review](../review/SKILL.md) |
| One contested technical decision that needs independent opinions | [model-council](../model-council/SKILL.md) |
| The model for every worker | [agent model selection](../skill-authoring/references/agent-model-selection.md) |

---

## 1. Kickoff

Decide these before the first delegation. Write each into the plan or the
[state file](references/state-file.md).

1. **Lanes and ownership.** One owner per file or area, with Owns and Never-touch lists, and one
   owning lane named for every shared file. Every interface between lanes gets a contract first,
   and the contract's main consumer reviews it before it merges.
2. **Cross-cutting questions** that every downstream artifact inherits (for a test suite: locator
   policy, coupling to copy, time faking). Ask them at plan approval, before any contract exists.
3. **An approval matrix:**

   | Class | Examples | Rule |
   | --- | --- | --- |
   | Human before | Destructive actions, new trust roots or IAM, spend, production data, spec edits | Ask, then wait for that item only |
   | Notice after | Additive deploys, settings the orchestrator owns | Act, then report |
   | Default | Implementation details | Decide and log under Decisions |

   Phrase each approval request to cover the whole class and to name the orchestrator as the
   actor: "make these edits yourself for every PR in this phase". Ask before the human goes
   offline. An approval that didn't name the orchestrator cost one build about seven hours on its
   critical path.
4. **The approval carry-over rule,** authorised once. The check is in
   [Review and merge gates](#5-review-and-merge-gates).
5. **Merge gates the platform enforces:** required status checks as soon as the first gate job
   exists, and bot reviews that start when the PR opens. Copilot's automatic review skips drafts
   unless *Review draft pull requests* is on, and reviews once unless *Review new pushes* is on
   ([GitHub docs](https://docs.github.com/en/copilot/how-tos/copilot-on-github/set-up-copilot/configure-code-review)).
6. **The critical path,** with the shortest review loop on it. Other lanes absorb extra rounds.
7. **A read-only probe of the real environment:** quotas, existing resources and limits. Put each
   surprise in the human queue with an owner.
8. **An adversarial review of the plan and the phase briefs** before the human approves them or
   implementers start. Ask whoever drafts the briefs for a conflicts-and-open-questions section and
   a file-overlap check.
9. **The shared-machine plan:** a port per agent, `TMPDIR` and caches on disk rather than tmpfs,
   worker caps, and the most browser suites that may run at once. It fills the standing block in
   [agent-briefs](../agent-briefs/SKILL.md).
10. **Where agent memory and scratch files live** (gitignored), and whether a brief's "write no
    files" includes them.

---

## 2. The Loop

Every wake runs the same five steps: wake, sweep, act, arm, record.

1. **Wake.** Read the time with `date -u`; never estimate it. Don't spend a turn on an interim
   notice, such as a subagent that stopped while its own background work still runs. Wait for its
   hand-back.
2. **Sweep** every lane, not only the one that woke you: subagents, peers, background watchers and
   result files. Also:
   - scan running agents for permission or classifier denials on each sweep, rather than waiting
     for the human to notice;
   - read the last tool calls of any agent with no progress for about 10 minutes.
3. **Act** on what finished:
   - rule on results before anyone else sees them ([Rulings](#4-rulings-and-relaying-findings));
   - launch, in this turn, every lane whose inputs merged or were decided;
   - give each idle single-threaded peer the next task from its ready-queue in the same turn you
     read its result. When the queue is empty, fill it from deferred minor findings;
   - pre-write briefs for lanes about to unblock.
4. **Arm** a wake source for every in-flight lane:

   | Lane | Wake source |
   | --- | --- |
   | Subagent | Its completion notice (Claude Code delivers one for background subagents) |
   | Herdr peer | One background `--wait` per prompt ([herdr-delegation](../herdr-delegation/SKILL.md)) |
   | PR gates | One background script that waits for checks and reviews, then prints one line ([autonomous-loops](../autonomous-loops/SKILL.md)) |
   | Long local job | One background command writing a log, waited on once |

5. **Record** each state change in the [state file](references/state-file.md), batched once per
   turn.

---

## 3. The Human

**Ask without blocking.** Put the question in a normal message with a recommendation, a default,
and what continues meanwhile. Then dispatch every task the question doesn't gate. Before asking,
list what the idle lanes could do and send it. Use a blocking prompt only when nothing else can
move.

- **Keep one numbered open-decisions list.** Each item carries a recommendation and what it
  blocks. Re-post the whole list whenever it changes, so the human can answer by number. When
  nothing changed, don't repeat the ask.
- **Escalate with:** the conflict; two to four feasible options with their effect and cost; a
  recommendation; what continues meanwhile. Measure each option against the hard constraints
  before recommending it (a subagent can do this in minutes). When the human picks, scope any extra
  round to the open items by name.
- **Give every parked question that affects visible behaviour a default** and an "applies at
  <checkpoint> unless you object" note. Raise it again at each checkpoint.
- **Never route around a permission or classifier denial.** Ask the human, or use the sanctioned
  alternative.
- **Don't hand the human a command you can run yourself.**

### Away Protocol

When the human says they are away:

1. Open a handoff file or issue with four sections: needs-human, decided-by-orchestrator,
   escalated-and-unmerged, and merged.
2. Write the away rules into the state file: what you decide, what you park, and what you never do.
3. Decide implementation details yourself and log each one. Park content, legal and money
   questions with a safe default.
4. Keep merging whatever passes the gates, and keep the handoff current.

---

## 4. Rulings and Relaying Findings

**Triage every finding before an author sees it:** accept, reject with a reason, or escalate.
Never forward raw reviewer output.

- **A ruling states the invariant, the contract clauses that bind it, and the verification to
  run.** Let the author choose the mechanism. If you do suggest one, first grep the contract for
  rules that constrain it.
- **Check a reviewer's remedy against the binding contract before relaying it.** One conflicting
  remedy turned a PR into four rounds and an escalation.
- **Treat reviewer-supplied patches as candidates.** Validate them on every project or engine,
  under load, before forwarding them.
- **Quote requirements with their IDs.** A paraphrase loses their granularity.
- **After a second round on the same mechanism,** tell the author to close the whole class and
  replay every earlier probe, and ask whether the mechanism itself is wrong.
- **Tell the author the round number and the escalation rule.** After three unresolved rounds,
  escalate to the human.
- **Rule once on a recurring flake, on first sight:** its signature, owner, issue and rerun policy.
  Add the ruling to the standing rules so parallel authors don't each diagnose it again. Flake
  triage itself is in [playwright-e2e](../playwright-e2e/SKILL.md).

---

## 5. Review and Merge Gates

- **Every PR gets an independent adversarial reviewer:** another model family, or at least a fresh
  context. That includes docs, spec and decision-log PRs. First-pass reviews required changes on
  about three of every four PRs. The reviewer's procedure is in [review](../review/SKILL.md), and
  its brief is in [agent-briefs](../agent-briefs/SKILL.md).
- **Docs and status PRs get a fact-check review** (every SHA, number and state checked against its
  source), then a diff-only check of the fixes.
- **Approval is a commit status on the exact head SHA, made a required check.** Required checks
  must pass on the latest commit, so any push voids the approval
  ([GitHub docs](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)).
  Merge with `--match-head-commit`, and never with `--admin` or another ruleset bypass:

  ```bash
  gh api "repos/{owner}/{repo}/statuses/$HEAD" -f state=success \
    -f context=adversarial-review -f description="approved $HEAD"
  gh pr merge "$PR" --squash --match-head-commit "$HEAD"
  ```

- **Authors merge the base last, push once, report the head, and don't push again.** Start the
  final review only on a head that is already current.
- **Carry an approval over only when the new head is a merge of the base onto the approved head.**
  Prove it with a check and record the check on the PR. Anything else gets a delta review.

  ```bash
  test "$(git rev-parse "$NEW^1")" = "$APPROVED"     # one merge on top of the approved head
  git merge-base --is-ancestor "$NEW^2" origin/main  # its other parent is on the base
  git show --remerge-diff --format= "$NEW"           # empty: no conflict edits or extra changes
  ```

  Non-empty `--remerge-diff` output is the conflict resolution or extra change; send that to the
  reviewer as the delta.
- **Send delta rounds to the same reviewer** with the exact range (`git diff $OLD..$NEW`). It cost
  about 60% less than a fresh review. Start a fresh reviewer only when independence matters.
- **Within the hour, turn every "outside this PR" item a reviewer reports into an issue or a small
  fix,** so later briefs never carry a workaround for a known defect.

---

## 6. Release Safety When Every Merge Deploys

- **Before enabling auto-deploy,** dry-run every pipeline branch against the real services: the
  no-evidence path, stale-file deletion and rollback. When the docs and an observed run disagree,
  the observed run wins; pin it with a test.
- **Before the first irreversible deploy,** have a strictly read-only preflight agent compare the
  real account with the plan's assumptions. Check each command a runbook calls "read-only".
- **After any change to the deploy path, or after a failed release,** merge one PR, watch its
  release to completion, then merge the next. While a release is failing, merge nothing.
- **When a production check must change with a behaviour change,** land the check first, accepting
  both states, then flip the behaviour.
- **After each deploy that changes behaviour, verify it live.** Pair every "hidden" or "absent"
  assertion with a check that the thing exists and can appear. A result that never changes means
  the probe is wrong.

The merge, watch and verify loop and deploy step timeouts are in
[autonomous-loops](../autonomous-loops/SKILL.md).

---

## 7. Context and State

The orchestrator's whole context is re-read on every turn. In one build, about 1,500 turns ran at
185K to 650K tokens.

- **Cap hand-backs at about 40 lines:** a verdict or status line, blockers, and a path to the full
  report. Read the full file only when ruling on it. The report contract is in
  [agent-briefs](../agent-briefs/SKILL.md).
- **Keep a state file** from [the template](references/state-file.md): a lanes table, open
  decisions, the human queue, away rules and helper scripts. Update it on each state change, back
  it up before overwriting it, and rewrite it as a clean resume point at a calm moment before a
  planned compaction.
- **After compaction,** follow the resume procedure in the state file: re-verify every ID and
  number against its source before using it, and re-load any tools loaded on demand.
- **Put durable decisions in the repository's decision log,** not only in the state file.

---

## 8. Claims

- **Verify, read the output, then publish,** as separate steps. Never post a status, an approval
  or a factual comment in the same command as the check that justifies it.
- **Tell the human only what was verified,** with the time it was observed, and list what is
  unverified.
- **Before telling the human what gates something,** read the enforcing workflow and the decision
  log, not memory or a tracker issue.

---

## 9. Cost and Throughput

- **Size lanes as single-purpose PRs** with numeric acceptance, about an hour of agent time each.
  Split a risky item (an open product question, a hard cross-cutting constraint) from ready ones,
  so the ready ones can merge.
- **Use draft-PR checkpoints at dependency boundaries.** The lane ships what doesn't need the
  dependency, opens a draft, and gets an interim review while the dependency is still in review.
- **Run small cross-lane changes as parallel stacked drafts** (spec, contract, tests and
  implementation together). Keep strictly serial hand-offs for changes that need independent
  owners: a serial chain once stretched a ten-line change to about 20 hours.
- **Treat a metered peer's quota** (for example a weekly Codex limit) as a shared budget, and
  reserve a slice for reviews. Reading the meter is in [herdr-delegation](../herdr-delegation/SKILL.md).
- **Batch deferred low-priority findings per area,** and re-check each against the current base
  before queueing it.

---

## 10. Close-Out

1. Write a retrospective: what the gates caught, including your own errors; what it cost; and
   which parts transfer to other projects.
2. Before removing a worktree, compare its leftover edits with the merged head, not with a main
   that has since moved, and check that no peer runs from it
   ([herdr-delegation](../herdr-delegation/SKILL.md)).
3. Move durable rulings into the repository docs, and close the handoff issue.

---

## Common Issues

| Problem | Cause | Fix |
| --- | --- | --- |
| The loop stalls for hours; a lane idles overnight | A blocking question prompt waits on the human | Ask in a message with a default and keep dispatching ([Every turn](#every-turn)) |
| A lane sits finished, or dead, until the human notices | No wake source was armed, or a peer's working directory was deleted | End-of-turn wake check; on idle or done, check the result file; start peers in a stable directory ([herdr-delegation](../herdr-delegation/SKILL.md)) |
| Each gated edit costs a human round trip, hours on the critical path | The approval covered one action, or didn't name the orchestrator | Ask once, before the human leaves, for the class, with the orchestrator as actor |
| Tool calls fail across agents: full tmpfs, port clashes, killed shells, false test failures | Agents share one host with no plan | Kickoff shared-machine plan, and the standing block from [agent-briefs](../agent-briefs/SKILL.md) in every brief |
| Researchers and verifiers hit their turn cap with nothing written | The brief asked more than the cap allows | The research brief in [agent-briefs](../agent-briefs/SKILL.md): about five questions, output file written first |
| One flake costs several PRs and many rounds | Each author re-diagnoses it, sometimes wrongly | One ruling on first sight; triage per [playwright-e2e](../playwright-e2e/SKILL.md) |
| Approved tests could never fail | The review read the diff but never proved it could fail | Reviewer briefs require the mutation probes in [review](../review/SKILL.md) |
| Every merge of the base forces a full re-review | Approval is keyed to the head with no carry-over rule | The carry-over check; authors merge the base last and push once |
| One mechanism takes four to seven review rounds | The ruling prescribed a mechanism, relayed an unchecked remedy, or patched examples instead of the class | Rule on invariant, clauses and verification; class fix after round 2; escalate after round 3 |
| Orchestrator context sits at hundreds of thousands of tokens | Full hand-backs and review files read in | 40-line hand-backs; read the file only to rule |
| IDs, SHAs or counts are wrong after compaction | Recalled from the summary | The resume procedure in [the state file](references/state-file.md) |
| Release failures multiply | More PRs merged while a release was failing | One merge, watch the release, then the next; merge nothing while it fails |
| A status sent to the human is wrong | Published before the check was read | Verify, read, then publish, with the observation time |
