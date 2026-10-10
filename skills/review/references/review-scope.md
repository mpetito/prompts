# Review scope brief

A repository's own answer to "what does a review here check hardest". It lives in `REVIEW.md` at
the repository root, the file Claude Code's managed Code Review also reads
([docs](https://code.claude.com/docs/en/code-review#review-md)), so one file serves every reviewer.
The lists in the review and plan-review skills are examples, drawn mostly from one web service;
this file names the repository's own.

## Read it

Before sizing, read `REVIEW.md` and any review guidance in the repository's agent instructions
or contributor docs. Its entries outrank the skills' examples; where it is silent, the examples
still apply.

## Derive it

When there is no brief, or a full revisit is due, derive each section from the repository, never
from another project:

- **Expensive to change:** what others build on, and who: exported packages and types, endpoints
  and their payloads, CLI flags, output and exit codes, file, event and message formats, schemas
  and migrations, config keys, names other repositories or stored data reference.
- **Risky to get wrong:** the paths that move money, delete or migrate data, decide access, hold
  secrets, run concurrently, or deploy.
- **Always check:** rules this repository learned the hard way, each with its source: an incident,
  a revert, a finding that recurred across reviews.
- **Primitives to prefer:** what the platform and the codebase already provide (a job runner, a
  queue, auth middleware, a retry helper), so a change that rebuilds one is a finding.
- **Do not report:** what CI already enforces; generated, vendored and lock files.

Sources: the README and contributor docs, CI config, package manifests and their exports, routes,
schemas and migrations, `git log` for reverts and fix-ups, and recent review threads.

## Keep it current

Every review ends with one `Scope brief:` line, `no change` or a proposed edit with its evidence:

- **Add** when the change creates or alters a surface or a risky path of a kind the brief doesn't
  list, or a finding's defect class has recurred and isn't under Always check.
- **Fix or remove** an entry that names a path or surface that no longer exists, or proved wrong.
- **Revisit in full** when there is no brief, or its `Revisited` line is more than about three
  months old.

Propose; never fold the edit into the change under review. Interactive: offer it as a separate
change and apply it on a yes. Delegated: the coordinator collects the lines and lands them as one
change. Keep the brief under about 60 lines; a long one dilutes the rules that matter.

## Template

```markdown
# Review instructions

Revisited <YYYY-MM-DD> at <short sha>. Kept current by the review skill's Scope brief line.

## Expensive to change (blast radius)
- <surface>: <who depends on it>

## Risky to get wrong (defect risk)
- <path or area>: <what breaks>

## Always check
- <rule> (from <incident, revert or PR>)

## Primitives to prefer
- <need>: <what already provides it>

## Do not report
- <what CI enforces; generated paths>
```
