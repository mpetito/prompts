# Brief Templates

Copy-ready skeletons for [agent-briefs](../SKILL.md). Copy the block inside the outer fence,
replace every `<placeholder>`, and delete any line that cannot apply. Paste the standing block
and the report contract from SKILL.md where the template says so.

Write the brief to a file and send a short spawn prompt that points at it.

---

## 1. Author brief

For implementing a lane, a phase or a fix.

````markdown
# <task id>: <one-line goal>

## Why
> <the user's or the spec's words, verbatim> (<source>)

## Where
- Create your worktree: `git worktree add -b <branch> <worktree path> origin/<base>`
- Work only there. Never edit `<main checkout path>`.
- Facts at send time: base `<base>` at `<sha>`; <PR #N head `<sha>`, checks <state>>;
  moved since planning: <list, or "nothing">.
- The source beats this brief. Where they disagree, follow the source and list the
  discrepancy in your report.

## Load first
- `<project instructions file>` now.
- `<skill>` before <moment, e.g. the first edit>.
- `<skill>` before <moment, e.g. reporting done>.
- If you start a subagent: select its model per <model policy path>, and pass it this brief's
  standing rules.

## Owns
- `<path or glob>`
- Lockstep exception, these lines only: `<file>:<lines>`, because `<check that couples them>`.

## Never touch
- `<path or area>`, owned by <lane>. If you need a change there, message the coordinator with
  the evidence and a proposed fix, then keep working.

## Changes
1. `<file>:<line>`: <change>. Source: <spec section, decision ID or finding ID>.
2. `<file>:<line>`: <change>. Source: <source>.
   Hypothesis: <prescribed fix, constant or option>. Prove it with <control showing the guard
   still bites>, and state what it sacrifices.

## Invariants (one probe each, before the first push)
| Invariant | Probe | Result |
| --- | --- | --- |
| <property the area must keep> | <command or check> | <fill in> |

## Stop and report (don't choose)
- If <temptation, e.g. the contract lacks an ID you need>: stop that item and report the
  options. Don't invent one.
- If <temptation, e.g. the fix needs a file outside Owns>: message the coordinator and carry on
  with the other items.
- If <temptation, e.g. green needs a weaker check or a new trust root>: stop and report.
- A missing prerequisite parks only the items that depend on it. List it and continue.

## Proof
- Every new guard, check, limit or fix has a test or probe that fails without the change and
  passes with it. Report both runs.
- Stability, for any new or changed test: run each one <n ≥ 5> times on every project under
  CPU load (<e.g. `--repeat-each=<n> --workers=<cap>`>), with 0 failures. Report the counts.

## Validation
Built from the jobs in `<CI workflow file>`, nested packages included, in this order. Run it
on the committed tree:

```
<command>
<command for a nested package>
<checker that reads the formatter's output, after the formatter>
```

Acceptance: all required checks green on the pushed head.

## Self-check before reporting
- [ ] File headers and contract comments follow the project rules
- [ ] Docs affected by the change are updated
- [ ] IDs are in test titles and the PR title
- [ ] The PR body matches the evidence and was regenerated after the last push
- [ ] No closing keywords unless closing is intended

## Merge order
<"Independent" or "Merge after #N">, because <the failure the order prevents>.

<standing block from SKILL.md>

## Report
<report contract from SKILL.md>
Result file: `<path>`. At most <n> lines in the reply.
````

---

## 2. Fix-round note

For sending review findings back to the author after triage. Send it to the same author.

````markdown
# <PR #N>, round <r> of <cap>

- PR: <url>. Reviewed head: `<sha>`. Review: `<path>`. Read it in full.
- This is round <r>. Unresolved items after round <cap> go to <human>.

## Confirmed: don't change
- <what the reviewer verified>

## Leave as is
- <finding ID>: <reason or ruling>

## Fix
Verify each finding against the code and docs first. If one is wrong, leave the code alone and
reject it in your report with evidence.

### Blocking
- <ID>: "<reviewer's text, verbatim>" (<file:line>)

### Should fix
- <ID>: "<reviewer's text, verbatim>"

### Nits
- <ID>: "<reviewer's text, verbatim>"

## Rulings
- <open question>: <invariant to keep>. Binding: <contract clause>. Verify with: <check>.

## Order
1. Fix and commit each item.
2. Run the validation below on the committed tree.
3. Merge `<base>` last, with no rebase or force-push. Push once.
4. Regenerate the PR body against the final diff. Delete any claim that is no longer true.

## Validation
```
<commands>
```

## Report
Append to `<result file>`:

```
## Round <r>
Head: <sha>
- <ID>: fixed | rejected (<evidence>) | blocked (<reason>)
```

Then hand back with the report contract.
````

---

## 3. Reviewer brief

For an adversarial review, first round or delta round. The reviewer reports; it does not fix.

````markdown
# Review <PR #N> at `<sha>`, round <r>

## Purpose
<what the PR does and why, in one paragraph>
Sources of truth, in precedence order: <spec section>, <contract section>, <decision IDs>.

## Facts at send time
Head `<sha>`, base `<base>` at `<sha>`, checks <state>. The source beats this brief; list any
discrepancy.

## Author's claims to verify
- <claim from the PR body, e.g. a count, a cause or a coverage statement>: re-derive it.

## Check hardest (ranked)
1. <your strongest suspicion>
2. <a defect class seen in earlier lanes>
3. <next>

## Threat model and accepted limits (gates, validators, security-relevant code)
- Protects: <property>. Against: <bypass classes>. Accepted limits: <list>.

## Mode
Load the `review` skill and work in its Delegated Report-Only Mode. Your working directory is
the scratch worktree `<path>`; edits and mutants are allowed there and never committed.
Severity is independent of the round number; the coordinator decides escalation.

## Required probes (a floor, not a ceiling)
Run the probes in the review skill's "Prove the Change Can Fail" that match this diff. At
minimum:
- <named mutants to plant in the code under test>
- <a bug to restore, to show the new proof fails without the fix>
- <repeat runs under load, or a dependent-PR overlay>

## Delta round (round 2 onward)
Review `<old sha>..<new sha>`. Re-run these probes and survivors: <list>. Mark each earlier
finding fixed, not fixed or regressed.

<standing block from SKILL.md>

## Output
The report shape from Delegated Report-Only Mode, first line
`VERDICT: approve|changes-required|close for <sha>`. Long form in `<path>`.
````

---

## 4. Investigation or flake brief

For a failure whose cause is unknown. Evidence first; a fix is one possible outcome.

````markdown
# Investigate <symptom> (<issue or run link>)

## Evidence
- Run <id>, attempt <n>: `<exact failing line>`
- Frequency: <k of n runs> on <projects or engines>, first seen <sha or date>.

## Hypotheses (unconfirmed)
1. <hypothesis>: test it with <probe>.
2. <hypothesis>: test it with <probe>.

## Method
- Check the upstream tracker for the crash or error signature first.
- Reproduce on the unfixed code under CI-like load before changing anything.
- Fix the cause, not the timeout. Label each cause confirmed (with the probe that confirmed
  it) or hypothesis.

## Allowed outcomes
- (a) A fix inside Owns, with before and after counts.
- (b) The cause is in another lane: write it up with evidence and leave that lane untouched.
- (c) Quarantine with an issue and the evidence.
- (d) No change: not reproduced, or the cause is outside our control, with evidence. This is a
  valid result.

## Measurement
Before and after failure counts under load at N = <n>, sized so the old failure rate would
show about 3 failures, on every affected project. First attempts and reruns reported
separately.

<standing block from SKILL.md>

## Report
<report contract from SKILL.md>
````

---

## 5. Research brief (turn-capped agent)

For a researcher or analyst with a turn cap. Check the cap before writing; split larger work.

````markdown
# Research: <topic>

You have about <cap> turns. At about <two thirds of cap>, stop exploring and report.

## Output file: write it first
<Agents with a file-writing tool only. Delete this section for a read-only researcher or
analyst; the stop rule above protects its report.>
Create `<path>` now with this skeleton, then append after each finding:

```
# <topic>
## Q1 <question>: open
## Q2 <question>: open
```

## Questions (priority order, at most 5)
1. <question>
2. <question>

## Assumptions to confirm or refute, each with a URL
- <assumption>

## Rules
- Docs first, then the issue tracker, then source or a probe. Pin claims to the installed
  version (`<tool> --version`).
- Tag every claim: DOCS (<url>), SOURCE (<file:line or repo@version>), INFERRED or UNVERIFIED.
- Exact values (versions, hashes, prices, limits) need a second source.
- Report by call <n> even if partial, with unreached questions marked UNVERIFIED.

## Report
<report contract from SKILL.md>. The output file is the long form.
````

---

## 6. Docs or status brief

For decision logs, status files and handoff notes. Claim hygiene is the whole job.

````markdown
# Docs: <what to record> in `<file>`

## Record
- What happened, not a new rule. Date-stamp anything pending.
- <item>: source <PR, SHA, run ID or link>

## Verify every fact against the source
- Check every SHA, PR number, run ID, count and state with `<git or gh command>`. List
  discrepancies in your report.
- Cite file:line for every code claim.

## Copy verbatim
> <negotiated wording> (<source link>)

## Must keep
- <sentence or restriction that must survive the edit>

## Facts that exist only in chat (the coordinator vouches for these)
- <fact>

## Waiting on human
Diff the old and new "waiting on human" lists. Report each item added or dropped.

<standing block from SKILL.md>

## Report
<report contract from SKILL.md>
````
