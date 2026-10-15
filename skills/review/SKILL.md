---
name: review
description: "Review a code change adversarially and give a merge verdict: size the review by defect risk and blast radius, prove the change's tests and guards can fail, check its claims and its interfaces, and report findings as blocking, follow-up or nit. Use when asked to review, check or look over code changes (staged or uncommitted changes, a branch, a pasted diff or patch, a PR's diff), to say whether a change is safe to merge or ship, to hunt for bugs or regressions, to prove a regression or flake fix actually fails without the fix, to review a new API, contract or schema before others build on it, or as a delegated reviewer that reports without editing. Not for reviewing a plan or spec before work starts (plan-review), posting comments on someone's GitHub PR, working through review comments on your own PR, or replying to and resolving review threads."
---

# Review

Role: worker. Loaded mostly by reviewer subagents; this file stays under 120 lines.

## 1. Read the change

Read every changed file at the head under review (`git diff`, `git diff --cached`, untracked files,
or the PR's diff), apart from unrelated work in the tree; the project's instructions and the
neighbouring code, whose conventions win; what the change must satisfy, with the author's claims;
and the repository's review scope brief, `REVIEW.md` at its root
([read, derive and keep it current](references/review-scope.md)).

## 2. Size the review

Size every review on two axes and take the deeper of the two:

| Axis | Ask | High for, e.g. | Then |
| --- | --- | --- | --- |
| Defect risk | What breaks if this is wrong now? | Auth, deletion, money, data integrity, security, concurrency | Adversarial review with planted mutants for the named invariants, plus a delta round |
| Blast radius | How much must change if this is wrong later? | Public or cross-team APIs, cross-lane contracts, schemas and migrations, wire, persisted or event formats, config and CLI surfaces, shared library interfaces, names that leak into URLs or events | An interface design review (section 3), ideally at the contract stage before implementation, by its main consumer plus an adversarial reviewer |

The examples are representative, not exhaustive; size by this repository's own surfaces and
risky paths, from its brief. An API boundary is cheap to get working and expensive to change
later: size it by the radius. Low on both: one adversarial pass, or a fact-check for docs-only and
mechanical changes (every SHA, number and state against its source). State the depth and why.
Then pick lenses from [review-lenses](../review-lenses/SKILL.md) and report its `Lenses:` line; a
lens finding keeps the template's id and group, then `<Lens> · <tag> · <file>:<line>: `.

## 3. Interface design review

For a high blast radius, ask what changing the interface later costs, in the terms of the surface
at hand (a payload, a CLI's flags and exit codes, a library's exported types, an event's schema):

- **Dependents:** who builds on it now and soon (clients, lanes, stored data, partners)?
- **Compatibility:** can a field change without breaking one? Is it versioned, with a deprecation path?
- **Error model:** are failures typed, documented and distinguishable by a caller?
- **Exposure:** does it leak internal IDs, table, column or class names into URLs, payloads or events?
- **Room to extend:** pagination, filtering, units, time zones, enums with an unknown value.

A shape that is costly to change and has no answer to these is `blocking`, however clean its code
and green its tests.

## 4. Prove the change can fail

Green checks show that a change passes, not that its tests or guards can fail. Run the matching
probes in a scratch copy, never the author's tree ([procedures](references/adversarial-probes.md)).

| The diff | Required proof |
| --- | --- |
| Adds or changes tests | Mutants of the code under test for the named invariants (every guard when none are named); restore each targeted bug; compare test counts |
| Fixes a flaky or timing-bound test | Reproduce on unfixed code under CI-like load; failure rates before and after; ablate the fix |
| Relaxes a shared test helper | The old helper's real-code mutants still caught |
| Adds a gate, validator or parser, unless the Trust boundary lens cuts it | Threat model stated; one mutant per bypass class; fails closed on bad input |
| Touches secrets or redaction | A synthetic secret checked in every sink; each protection disabled in turn |
| Claims no behaviour change | A mechanical identity proof, re-run independently |

A surviving mutant is a finding; the author's mutants and numbers are a floor, not evidence. A
stated root cause is unproven until an instrumented probe confirms it. A proof you could not run
(no shell, no environment) is listed as not run, never reported as run.

## 5. Audit the evidence

- CI covers only the head and base it ran on; once the base gains merges touching the same files,
  a green run no longer covers this head.
- Mark each causal, numeric and coverage claim as verified, refuted or unverified, against the logs.
- Cite vendor behaviour from its docs, or from a probe pinned to the installed version.

## 6. Findings and verdict

- **Tag every finding on its own merits, never on the review round:**
  - `blocking`: wrong behaviour, a security hole, data loss, a surviving mutant of a named
    invariant, a costly-to-change interface, or a test gap that guards a safety invariant, an
    auth boundary or data integrity;
  - `follow-up`: any other test gap, maintainability, missing docs;
  - `nit`: style the surrounding code does not already settle.
- **Over-engineering is a finding:** code no acceptance criterion or ruling requires (a ledger, a
  counter, a policy, an option). Name the primitive or cut that would do; tag it by its upkeep.
- **Each finding needs a concrete code path or maintenance cost,** not a preference.
- **Verdict:** `approve`, `changes-required`, or `close` when the change does not fix what it
  claims or removes coverage. Never approve with a blocking finding, failing tests or an
  unexplained surviving mutant.

## 7. Report

**Interactive** (a person asked): cite file and function, not line numbers. Fix only trivial items
(typos, formatting, dead code) and list them; a larger mid-review request gets scope, risks and
trade-offs first, and waits for a yes. Never commit or push.

```markdown
## Review: <what> at <head>
**Verdict:** approve | changes-required | close
**Depth:** <one pass | adversarial with mutants | interface design review>, because <risk or radius>
Lenses: picked Reuse (<reason>), Adopt (<reason>); skipped Reversibility (<reason>), Trust boundary (<reason>)
**Blocking** · **Follow-up** · **Nits**: - <file> `<function>`: <issue>. Evidence: <proof>. Fix: <validated fix>
**Not required by any acceptance criterion:** <mechanism>; <primitive or cut>
**Proofs:** <mutant or probe> | <killed, survived or not run> | <killing assertion>, survivors first
**Claims checked:** <claim>: verified | refuted | unverified
**Questions:** <open design questions>
**Scope brief:** no change | <proposed edit to REVIEW.md>, because <evidence>
```

**Delegated** (a coordinator briefed you): report only. Edit only in the scratch folder the brief
names (or a uniquely named one); never edit the change, post, push, commit, resolve threads or
start subagents. Match the depth the brief sets, bind the verdict to the head you reviewed, and
return at most about 40 lines, with the long form in the file the brief names. No markdown
headings.

```text
VERDICT: approve | changes-required | close for <head-sha>
Depth: <depth>, because <risk or radius>
Lenses: picked Reuse (<reason>), Adopt (<reason>); skipped Reversibility (<reason>), Trust boundary (<reason>)
Blocking
- B1 <file>:<line> <defect>. Evidence: <probe, log or quote>. Fix: <validated suggestion>
Follow-up
- F1 <file>:<line> <issue and suggestion>
Nits
- N1 <file>:<line> <issue>
Not required by any acceptance criterion or ruling:
- O1 <mechanism> at <file>; primitive or cut: <what would do instead>
Mutants (mutant | result | killing assertion), survivors first:
- M1 <change> | survived, killed or not run | <assertion, or see B1>
Claims checked: <claims, each verified, refuted or unverified>
Not verified: <check, and why>
Outside this PR: <item, proposed as an issue>
Scope brief: no change | <proposed edit to REVIEW.md>, because <evidence>
Long form: <path>
```
