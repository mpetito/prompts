# Reversibility lens

**The question.** Which decisions in the plan or change are one-way doors to decide now, and
which are reversible and can wait?

This lens builds on [plan-review's blast radius step](../../plan-review/SKILL.md) (step 2.2) and
[review's interface design review](../../review/SKILL.md) (§2 and §3). Those say what to decide
now and what to ask of it; the lens adds the other half, what to defer and when to come back.

## Decide now

- The decide-now list is the blast-radius list in plan-review step 2.2 and review §2: what others
  will build on or what is persisted, read with the repository's own Expensive to change in
  `REVIEW.md`, if any.
- For each one, the questions are review §3's. A plan that leaves one "to implementation" gets
  plan-review step 2.2's finding.

## Defer

- Everything else is reversible: internal names, module layout, private helpers, in-memory
  structures, tuning values, and any mechanism no requirement needs yet.
- A mechanism nobody needs yet is deferred by not building it, even one that would be persisted:
  leaving it out is reversible, while a stored field others have started to read is not.
- Report a deferral only where the plan or change spends work on it now, or asks about it. A
  reversible decision nobody raised needs no line.

## The evidence a finding carries

- **Decide now:** the surface by location, who will depend on it (clients, lanes, stored data,
  partners), and what changing it later costs (a migration, a coordinated release, broken
  clients).
- **Defer:** the decision by location, why it is reversible, and the signal that should bring it
  back (a second caller, a measured number crossing a stated limit, a request from a user).

## What the lens must not do

- Propose a guard, counter, option or abstraction for anything reversible, not even "to be safe"
  or "for future needs". The fix for one the plan or change already adds is the cut, plus its
  signal.

## Tagging

Tag by [review §6](../../review/SKILL.md) or [plan-review step 3](../../plan-review/SKILL.md).
A costly-to-change shape with no answer to review §3 is `blocking`, as §3 says. A reversible
mechanism built now is over-engineering, tagged by its upkeep.
