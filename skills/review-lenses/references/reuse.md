# Reuse lens

**The question.** What already in the repository could be reused, extended, generalised or
replaced so that the new code and the existing callers share one thing? And what does the plan or
change make obsolete?

This lens builds on [plan-review's mechanisms step](../../plan-review/SKILL.md) (step 2.1) and
[review's over-engineering rule](../../review/SKILL.md) (§6), and on
[code-style](../../code-style/SKILL.md) rules 2 (use what exists first) and 6 (delete what a
change replaces). It applies them to code that already exists in this repository.

## Where to look

- **Beyond the changed files.** Search the whole repository for the same responsibility, by name
  and by behaviour: synonyms of the new function or module's name, the data it reads or writes,
  the command, endpoint or file it calls, and tests that exercise the same behaviour.
- **The repository's shared places:** helper and utility modules, a registry the new code could
  join instead of a second name-to-handler map beside it (code-style rule 4), and the
  Primitives to prefer in `REVIEW.md`, if any.
- **On a diff,** spend the lens on what a pass over the changed code alone misses: duplicates
  outside the changed files, and what the change makes obsolete.
- **What the change replaces:** the old helper, shim, alias, legacy path, flag or config key, and
  their tests. Search for their remaining callers once the change lands.

## The evidence a finding carries

- The existing thing by location (file and symbol, or file and line) and its current callers.
- What it would take to make it fit both callers: a parameter, a split, a move to a shared
  module, or the new code replacing the old outright.
- For an obsolete path: the path, and its callers after the change (none, shown by a search).

A resemblance with no location, or no say on what fitting both callers takes, is not a finding.

## What the lens does

- Obsolete internal or pre-release code is deleted in the same change, not deprecated, kept "for
  safety" or left for later (code-style rule 6). Only a published API keeps its deprecation path.
- One thing serves both callers: the existing code extended, or the new code replacing it.

## What the lens must not do

- Propose a new layer or abstraction over the two; that is a mechanism no requirement needs.
- Merge two things that only look alike: if they change for different reasons, say so and drop
  the finding.

## Tagging

Tag by [review §6](../../review/SKILL.md) or [plan-review step 3](../../plan-review/SKILL.md).
A duplicate that will drift is maintainability (`follow-up`); an obsolete path left callable that
still gives a different result from its replacement is wrong behaviour (`blocking`).
