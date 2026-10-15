# Adopt lens

**The question.** Does the plan or change hand-roll something mature that a dependency, the
platform or a stock tool already does?

This lens builds on [plan-review's mechanisms step](../../plan-review/SKILL.md) (step 2.1, the
primitive the platform already provides) and [review's over-engineering rule](../../review/SKILL.md)
(§6), and on [code-style](../../code-style/SKILL.md) rules 2 (use what exists first) and 6 (delete
what a change replaces). It applies them to code from outside the repository.

## Order of preference

1. A dependency the project already has.
2. The language's standard library, or the platform (a queue's depth, a TTL, a conditional write).
3. A stock tool (a stock CLI, a stock backup or sync tool).
4. A new library.

Propose the first that does the job; a later one needs the earlier ones ruled out by name.

## Where to look

- **The manifest first** (`package.json`, `pyproject.toml`, `requirements*.txt`, `go.mod`,
  `Cargo.toml`, or the project's equivalent, and its lock file): what each dependency already
  exposes, read from its docs.
- The Primitives to prefer in `REVIEW.md`, if any.
- The hand-rolled code itself: parsing (dates, URLs, CSV, arguments), validation and schemas,
  retry and backoff, scheduling, date and time-zone arithmetic, HTTP clients, process supervision,
  templating.

## The evidence a finding carries

- The hand-rolled code by location, and the API in the replacement that does the job.
- For a dependency the project has: its manifest entry and the doc for that API.
- For a new library: its docs, its version, a maintenance signal (latest release, recent issue or
  release activity), and what adding it costs (transitive dependencies, licence, size).
- Library facts come from the docs or a probe pinned to the installed version, as
  [review §5](../../review/SKILL.md) says for vendor behaviour.

## What the lens does

- Adopting the replacement deletes the hand-rolled code in the same change (code-style rule 6).
- When no dependency the project has does the job, and the hand-rolled code is smaller than the
  one it would bring in and meets none of the edge cases that one exists for, no finding.

## What the lens must not do

- State a library fact from memory. A version, maintenance signal, licence or API you could not
  check in this review is marked unverified, with the check that would settle it.
- Propose a new library where an existing dependency, the standard library or the platform does
  the job.

## Tagging

Tag by [review §6](../../review/SKILL.md) or [plan-review step 3](../../plan-review/SKILL.md).
Hand-rolled code that works is upkeep (`follow-up`); hand-rolled code that gets an edge case the
library handles wrong (a time zone, a retry storm, malformed input) is wrong behaviour, tagged
as such.
