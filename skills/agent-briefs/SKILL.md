---
name: agent-briefs
description: "Write the brief, review prompt, fix-round note or research prompt that another agent will execute, and define what it reports back. Use when delegating implementation, review, investigation, research or docs work to a subagent, Herdr peer or `codex exec`; writing a review prompt or fix-round note; relaying review findings to an author; resuming an agent for another round; or deciding what an agent should report. agent-orchestration is the caller; herdr-delegation is the peer transport."
---

# Agent Briefs

How to write anything another agent will execute, and what it sends back. A good brief makes
the agent's first attempt the right one, and makes its report cheap to act on.

## When to Use

- Delegating implementation, review, investigation, research or docs work to a subagent, a
  Herdr peer or a one-shot `codex exec` run
- Writing a review prompt, or a fix-round note after a review
- Relaying review findings to the author
- Resuming an agent for another round or for adjacent work
- Deciding what an agent should report back

## Related Skills

| Need | Skill |
| --- | --- |
| Whether to delegate, lanes, gates, triaging findings, rulings | [agent-orchestration](../agent-orchestration/SKILL.md), the caller |
| Sending to a Herdr peer, waiting on it, result files, peer queues | [herdr-delegation](../herdr-delegation/SKILL.md) |
| `codex exec` flags, sandbox and network access | [cross-harness notes](../model-council/references/cross-harness.md) |
| The reviewer's probes and its report-only mode | [review](../review/SKILL.md) |
| Research method and source quality | [research](../research/SKILL.md) |
| Test stability gate and flake triage | [playwright-e2e](../playwright-e2e/SKILL.md) |
| The agent's model | [agent model selection](../skill-authoring/references/agent-model-selection.md) |

Select the model with that policy before launch. This skill does not choose models.

---

## Principles

1. **Self-contained.** A fresh subagent, a peer or a `codex exec` run starts without your
   conversation, your loaded skills or your memory. Name each skill it must load and the moment
   to load it ("load `code-authoring` before the first edit"). Restate the standing rules in
   every brief.
2. **File-based.** Put the long brief in a file. The spawn prompt names the file and restates
   the 5–8 rules most likely to be broken. A kickoff brief for an orchestrator goes in a file
   too, because long text pasted into a terminal can fragment.
3. **Facts come from commands at send time.** Generate the head SHA, base, check status and
   "what has moved" with `git` and `gh` when you send the brief, never from memory. Check every
   precondition the brief asserts, such as a file existing on the base. Then add: "The source
   beats this brief. List any discrepancy in your report."
4. **Prescriptions are hypotheses.** Label any fix, constant or option you prescribe as a
   hypothesis. Require a control that proves the guard still bites after the change, and ask
   what the option sacrifices.
5. **Examples use placeholders.** Agents copy examples verbatim. Write `<product-name>`, never
   realistic content. Grep the brief against the project's Do-Not list before sending it.
6. **Name every invariant.** List each property the area must keep, with one probe each, to
   run before the first push. Unnamed invariants surface one per review round. Draw them from
   the domain's threat list, for example:
   - UI: layout shift, hit targets, fallback fonts, reduced motion, state after close and reopen;
   - gates and validators: fail closed on unparseable input, origin and redirect trust;
   - PRs: closing keywords.
7. **Name the likely temptations.** Give the two or three shortcuts this task invites (invent
   an ID, edit another lane, add a trust root, weaken a check), each with its stop-and-report
   action.
8. **"Stop" is for safety and scope only.** A missing prerequisite parks only the items that
   depend on it. The agent lists it and carries on with the rest.
9. **Message early, keep working.** The agent messages the coordinator as soon as it finds a
   cross-lane blocker or needs a file outside its Owns list, with the evidence and a proposed
   fix. Then it continues with unblocked items.
10. **Ask asynchronously.** A question carries two options and a stated default, and the agent
    keeps working on independent items until it gets an answer. Questions are not for status
    pings or for facts the agent can read from the repo.

A spawn prompt that follows principles 1 and 2:

```text
Read <brief path> and follow it. Write your result to <result path>.
Rules most likely to matter here:
1. Edit only the files under Owns. For anything else, message me and keep working.
2. <rule>
3. <rule>
Load <skill> before <moment>. End with the report contract in the brief.
```

---

## The Standing Block

Paste this into every brief whose agent runs commands, reviewers included. Fill the
placeholders from the shared-machine plan (ports, disk paths, worker caps), which the
orchestrator settles at kickoff. Delete a line only when it cannot apply.

```markdown
## How to work

- Work only in `<worktree path>`. Don't `cd` out of it and don't use `git -C`. Run plain,
  single commands. Write any script to a file first, then run it.
- Put scratch files in `<worktree path>/<scratch dir>/<task id>/` (gitignored). Never use a
  shared scratch directory or a shared file name. Your PR-body file is
  `<scratch dir>/<task id>/pr-body.md`.
- Set `TMPDIR=<disk path>` and keep caches on disk, never on a tmpfs such as `/tmp`. Use port
  `<port>` (from `<PORT_ENV_VAR>`) and at most `<n>` test workers.
- Stop every server you start, by PID or with its own stop command. Never run `pkill -f` with
  a pattern that appears in your own command line: it can match your own shell and kill it.
- Read a file before you edit or write it, and read it again after a formatter, a merge or a
  scripted edit.
- Commit each logical fix before any temporary edit. Never undo with `git checkout <file>`:
  it discards uncommitted work.
- Git: no stash, rebase or force-push. Merge `<base>` last, push once, and report the head SHA.
- GitHub: write only what this brief lists (<push to `<branch>`, open a draft PR>). Never put
  close, fix or resolve, in any tense, before `#N` unless the merge should close that issue.
- Run only the targeted browser specs locally. CI runs the full browser tier.
- Wait for your own long jobs inside your turn, with one foreground command or one blocking
  wait, then report once. Don't end your turn while work you started is still running.
- If a permission prompt or classifier blocks you, stop. Prove the claim another legitimate
  way if you can, and report the block. Never route around it.
- If a secret was printed, logged, committed or captured in a screenshot or trace, say so in
  your report.
```

**Claude Code note:** in an isolated worktree, Claude Code refuses a command when it can't
verify from the text that the command's git stays inside the worktree, for example a computed
command name or unparseable syntax, and suggests plain, separate commands
([worktree isolation](https://code.claude.com/docs/en/worktrees#how-claude-code-enforces-isolation)).
Work outside the worktree can also wait on a permission prompt, which stalls an unattended agent.

---

## Templates

Copy-ready skeletons are in [references/templates.md](references/templates.md). Pick one per
delegation, fill every `<placeholder>`, and paste in the standing block and the report contract.

| Template | Use for | It must carry |
| --- | --- | --- |
| Author brief | A lane, phase or fix | Owns, lockstep and Never-touch lists; numbered changes with sources; invariants; stop triggers; validation built from CI; red-without-change proof; self-check |
| Fix-round note | Review findings back to the author | Review file path; dispositions; verbatim findings by severity; rulings; `## Round N` |
| Reviewer brief | An adversarial review, first or delta round | Claims to verify; ranked check-hardest list; threat model; scratch worktree; severity independent of round |
| Investigation or flake brief | A failure with an unknown cause | Evidence with run IDs; hypotheses; allowed outcomes including "no change"; counts under load |
| Research brief | A turn-capped researcher or analyst | At most 5 ranked questions; output file written first; report by call N; assumptions to refute; provenance tags |
| Docs or status brief | Decision logs, status files, handoffs | Facts checked against the source; verbatim wording; must-keep list; discrepancy list |

- **Relaying findings:** triage them first (agent-orchestration). Then send each accepted
  finding verbatim with the reviewer's ID, and tell the author to verify each one against the
  code and docs and to reject a wrong one with evidence.
- **Reviewers that experiment:** give them a scratch worktree as their working directory, where
  edits and mutants are allowed and never committed. Never write "read-only" in a brief that
  also asks for experiments.
- **Turn-capped agents:** read the agent's turn cap before writing the brief (`maxTurns` in a
  Claude Code agent definition). At the cap, Claude Code returns the output marked partial
  ([subagents](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields)). Split
  anything larger than about five questions across agents.

---

## Report Contract

Every brief ends with a report contract whose first line a coordinator can parse:

- **Reviewers:** `VERDICT: approve|changes-required|close for <sha>`, where `close` means
  "close, don't merge" and needs evidence. The rest of the shape is in review's
  [Delegated Report-Only Mode](../review/SKILL.md#delegated-report-only-mode).
- **Authors and every other agent:** the block below.

```text
STATUS: done|blocked|partial, head <sha>

Checks run: <command>: <first-attempt result>
Checks not run: <check>: <reason>
Reruns: <check>: <result>  (separate from first attempts; invalid runs labelled, e.g. "server lost")
Deviations from the brief: <item>: <evidence>
Decisions needing a ruling: <question>: <options>, default <option>
Not verified or not reproduced: <claim>
Brief vs source discrepancies: <brief said>: <source says>
Outside scope (proposed issues): <title>: <evidence>
Secret exposure: none | <what, where>
CI watcher: <who or what is watching, or "none">
Long form: <result file or PR comment URL>
```

- **At most about 40 lines.** The long form goes in the result file or a PR comment.
- **A multi-round agent ends each round with its full report** (its hand-back). It uses
  mid-run messages only for questions and cross-lane blockers.
- **One result file per task.** Each round appends a `## Round N` section with the head SHA and
  one line per item, so the history survives the coordinator's compaction.

---

## Follow-ups

- **Resume the same agent** for later rounds and adjacent work in the same area. It keeps its
  probes and decisions, so fixes are targeted. Send a structured message: where the verdict is
  ("read it in full"), the disposition of each finding, your rulings and the report cap. For
  review rounds that message is the fix-round note. In Claude Code, a resumed subagent keeps
  its full history ([resume subagents](https://code.claude.com/docs/en/sub-agents#resume-subagents)).
- **Start fresh** when independence matters, as for a new reviewer. Also start fresh when the
  follow-up doesn't need the agent's history and its context is already large.
- **Stage dependent work explicitly:** "do part 1 only; start part 2 when I message you", with
  a "Merge after #N" line in the PR body.
- **Never patch a running agent with addenda.** Rewrite the one authoritative brief file and
  send a pointer to it. Peer specifics (lost queued messages, question replies, queue and
  standing-rules files) are in [herdr-delegation](../herdr-delegation/SKILL.md).

---

## Before Sending

- [ ] Model selected with agent model selection
- [ ] Facts and preconditions generated from commands just now
- [ ] Skills to load named, each with its moment
- [ ] Owns, lockstep and Never-touch lists explicit
- [ ] Invariants listed, one probe each; temptations named with their stop action
- [ ] Prescribed fixes and constants labelled as hypotheses, with a control
- [ ] Examples are placeholders; brief grepped against the project's Do-Not list
- [ ] Standing block pasted and filled; report contract pasted
- [ ] A result file path and a line cap given

## Common Issues

| Problem | Fix |
| --- | --- |
| The agent acted on a stale SHA or an unmerged dependency | Generate facts at send time; tell it the source beats the brief |
| An example in the brief became shipped content | Use placeholder syntax; grep against the Do-Not list |
| Each review round surfaced one more invariant | List every invariant up front, with a probe each |
| A prescribed fix passed but its test can no longer fail | Label it a hypothesis; require a control that fails without the change |
| A peer idled on one missing prerequisite | Park only the dependent item; reserve "stop" for safety and scope |
| A reviewer stalled on permission prompts | Run it in a scratch worktree as its cwd; drop "read-only" from experiment briefs |
| A reviewer softened a late finding to avoid escalation | State that severity is independent of the round; the coordinator decides escalation |
| A researcher hit its turn cap with nothing written | Output file first, append per finding, report by call N |
| An addendum was lost while the peer answered a question | Rewrite the brief file and send a pointer; send replies alone |
| Parallel agents collided on ports, `/tmp` or scratch files | Paste the standing block with per-agent values |
| Repeated "finished, still running" notices | The agent waits on its own jobs inside its turn and reports once |
