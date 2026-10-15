---
name: plan-review
description: "Review a plan, spec or design document adversarially before any code is written: find mechanisms no requirement needs, decisions that will be expensive to change later, missing contracts, files two workstreams both touch, unverified claims, questions only the owner can answer, and an order that delays what the owner can see. Use when asked to review, check, challenge or poke holes in a plan, spec, design doc, RFC or task breakdown before it is approved or implemented, or when a coordinator delegates a plan review. Not for code, diffs, staged or uncommitted changes, commits or pull requests (review), or for writing the plan itself (spec)."
---

# Plan review

Role: worker. Loaded by a reviewer subagent briefed by a coordinator, or by a session asked to
review a plan; this file stays under 120 lines.

A plan's mistakes are the cheapest to fix now and the most expensive later: a mechanism nobody
needed gets built, reviewed and maintained; an interface decided in passing gets depended on. You
report; you never rewrite the plan.

## Procedure

1. **Read the plan in full, then its sources:** the owner's words, the spec, the contracts, the
   repository's review scope brief (`REVIEW.md` at its root, if any), and the code wherever the
   plan makes a claim about it. Don't trust the plan's summary of a source.
2. **Work through these in order.** Each finding names where it is (section or heading), what is
   wrong, and the smallest change that fixes it: a cut, a contract, a reorder, a question.
   First pick lenses from [review-lenses](../review-lenses/SKILL.md); they add a second look and
   replace none of these checks.
   1. **Mechanisms no requirement needs.** Every ledger, counter, queue, policy, second check,
      option or abstraction that no acceptance criterion and no owner instruction demands. Name
      the primitive the platform or codebase already provides (on AWS, say, a queue's depth, a
      TTL, IAM, a conditional write; the brief's Primitives to prefer), or the cut.
   2. **Blast radius.** List the decisions that will be expensive to change once others build on
      them, such as public or cross-team APIs, contracts between workstreams, schemas and
      migrations, wire, persisted or event formats, config and CLI surfaces, shared library
      interfaces, and whatever the brief lists as expensive to change. For each: who will depend
      on it, whether it is versioned, its error model, its naming, its room to extend, and
      whether it can be reversed. A plan that leaves one of these "to implementation" gets a
      finding: the decision becomes a contract, reviewed by its main consumer, before any
      workstream builds on it. Size the later code reviews by the [review](../review/SKILL.md)
      skill's two axes, defect risk and blast radius.
   3. **Contracts and ownership.** An interface between workstreams with no contract; a file two
      workstreams both edit; a shared file with no owning workstream.
   4. **Order.** Anything the owner can see or click scheduled behind work they can't see;
      dependencies that serialise work for no reason; a risky item blocking ready ones.
   5. **Claims and assumptions.** Every claim about existing code, vendor behaviour, quotas or
      limits is verified (a file and line, or a doc link) or marked unverified, with the probe
      that would settle it.
   6. **Acceptance.** Each workstream has acceptance a check can fail (numbers, a command, a
      behaviour the owner can try), not "works" or "is robust".
   7. **Questions only the owner can answer.** Each with the options, your recommendation and a
      default, so a short answer, or none, unblocks it.
3. **Tag each finding** `blocking` (the plan cannot be approved as written), `follow-up` (fix
   before the affected workstream starts) or `nit`.
4. **Report.** First line `VERDICT: approve|changes-required for <plan path> at <version or sha>`.
   Second line, in this form:
   `Lenses: picked Reuse (<reason>), Adopt (<reason>); skipped Reversibility (<reason>), Trust boundary (<reason>)`.
   A lens finding goes under the heading it fits and starts `<Lens> · <tag> · <section>: `.
   Then the findings, grouped by the headings of step 2, `blocking` first. Delegated by a
   coordinator: at most 40 lines, with the long form in the file the brief names.

## Rules

- **Propose the smallest change that removes the problem.** Don't redesign the plan; a finding
  that rewrites the architecture is a question for the owner, with a default.
- **Over-engineering is a finding, not a style note.** Its tag follows the cost it adds.
- **Anything you could not verify is labelled as such,** never stated as fact.
- **The examples in each check are representative, not exhaustive.** Look for this project's own
  primitives, surfaces and risks, on its platform.
- **Not a code review.** Code and diffs go to the review skill.
