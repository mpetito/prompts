---
name: review-lenses
description: "Review a plan or a code change through focused lenses: Reuse (what the repository already has, and what the change makes obsolete), Adopt (an existing dependency, the standard library or a stock tool instead of hand-rolled code), Reversibility (what to decide now because it is expensive to change later, and what to defer) and Trust boundary (guards only where outside input enters). Use when a review request or brief asks for a lens, asks whether something in the repository or a library already does what a plan or change under review builds, asks what in a plan or change to decide now and what can wait, or asks whether a change's guards sit at the right boundary. Not for a general plan review (plan-review), a general code review or merge verdict (review), writing or changing the code (code-style), or researching a library on its own (researcher agent)."
---

# Review lenses

Role: worker. Loaded by a reviewer beside plan-review or review, or by the coordinator that
briefs reviewers; this file stays under 120 lines.

A lens is one angle on a plan or a change, with its own evidence rule. It runs on top of
[plan-review](../plan-review/SKILL.md) or [review](../review/SKILL.md): their procedure, tags,
verdict and report stay as they are, and a lens adds findings to them, never replaces a check.

## 1. Pick the lenses

While sizing the review, match what the plan or change contains:

| The plan or change contains | Lens |
| --- | --- |
| New modules, helpers or scripts | Reuse |
| Hand-rolled parsing, validation, retry, scheduling, dates, argument parsing or the like, or a new dependency | Adopt |
| Any surface that is expensive to change later (the blast-radius lists in plan-review step 2 and review §2) | Reversibility |
| A new guard, allowlist, validator or auth check, or code that handles outside input | Trust boundary |

- A lens named in the request or the brief runs regardless of the table, and only the named
  lenses run.
- State the pick on one line, in exactly this form, each lens with a one-line reason:
  `Lenses: picked Reuse (<reason>), Adopt (<reason>); skipped Reversibility (<reason>), Trust boundary (<reason>)`.
  Every lens appears once, in whichever group it falls. Put the line where the sibling's report template
  places it, or straight after the report's first line.
- Lens names are always written `Reuse`, `Adopt`, `Reversibility` and `Trust boundary`.

## 2. Run them by depth

Take the depth from [review §2](../review/SKILL.md)'s two axes, defect risk and blast radius,
applied to what the plan or change builds.

- **Low on both:** you apply each picked lens inline, after the sibling's own checks, reading its
  reference file (section 5).
- **High on either, and you can start reviewers:** give each picked lens its own reviewer, at most
  one per picked lens and never more than four, each on explicit `opus`, or a cross-family model
  where the host offers one. Each brief names its one lens and its reference file, the sibling
  skill whose tags and delegated report it follows, the input and the head or version under
  review. You still run the sibling's own review; then merge the lens reviewers' findings into
  your report, folding duplicates into one and settling conflicts by section 3.
- **Delegated** (a coordinator briefed you): apply the brief's lenses inline and report. Never
  start reviewers of your own ([review §7](../review/SKILL.md), Delegated).

## 3. Settle conflicts

- A Reversibility finding outweighs a Reuse or Adopt finding only for a one-way door; for anything
  reversible, the smaller option wins.
- Between Reuse and Adopt, existing repository code beats a new dependency, and a dependency the
  project already has beats both.
- Trust boundary decides whether a gate belongs at all. [Review §4](../review/SKILL.md)'s proofs
  for a gate, validator or parser (a threat model, one mutant per bypass class) apply only to the
  gates that stay; a gate the lens cuts gets no mutants.

## 4. Write lens findings

- A lens finding starts with the lens name and a middle dot, then the review's own tag and the
  location: `<Lens> · <tag> · <location>: <issue>`, for example
  `Reuse · follow-up · <location>: <issue>`. Findings from several lens reviewers then merge
  without rewriting.
- Where the report numbers its findings, the prefix follows the id:
  `- B1 Reuse · blocking · <file>:<line>: <issue>`. The rest of the line keeps the report's own
  form (evidence, fix).
- Tags are the sibling's own: [review §6](../review/SKILL.md) for a change,
  [plan-review step 3](../plan-review/SKILL.md) for a plan. Each lens reference says only how its
  findings map onto them.
- Each finding carries its lens's evidence rule (section 5). A finding without it is a
  preference, not a finding; drop it.

## 5. The lenses

- [Reuse](references/reuse.md): what already in the repository could be reused, extended,
  generalised or replaced so that new and existing callers share one thing, and what the change
  makes obsolete. Evidence: the existing thing by location, and what it would take to fit both
  callers.
- [Adopt](references/adopt.md): whether the plan or change hand-rolls something mature. Evidence:
  the dependency, library or tool that does it; for a new library, its docs, version, a
  maintenance signal and what adding it costs, each marked unverified when not checked.
- [Reversibility](references/reversibility.md): which decisions to decide now (one-way doors)
  and which to defer. Evidence: for decide-now, who will depend on it and what changing it later
  costs; for a deferral, the signal that should bring it back.
- [Trust boundary](references/trust-boundary.md): whether each guard, check or validation sits
  where outside input enters, and only there. Evidence: the caller, and whether it is trusted.
