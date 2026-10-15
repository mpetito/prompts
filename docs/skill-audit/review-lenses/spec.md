# Spec: review lenses

A lens is one angle a reviewer takes on a plan or a change. The plan-review and review skills
already say what every review checks; a lens adds a focused second look from one angle, with its
own evidence rule, so that a reviewer briefed with it finds what a general pass skims over. The
owner's recorded gaps say where that second look pays. In the candidates ledger, Adopt rests on
the four `reuse` entries (curl, zod, a stock backup tool, herdr), all of them a dependency or
stock tool passed over. Reuse rests on the three `dead code` entries and the registry `dispatch`
entry, which are about existing code kept or duplicated. The four `least mechanism` entries back
both. Trust boundary rests on the two `trust` entries, both guards placed on trusted callers. The owner also wants a counterweight to those two: a lens that names what is
worth deciding now because it will be expensive to change later, and defers everything else.

## Behaviour

One new skill, `review-lenses`, consumed by reviewers (worker role) and by whoever briefs them.
It holds four lenses, a rule for picking them, a rule for settling conflicts between them, and
the shape of a lens finding.

### The four lenses

1. **Reuse.** What already in the repository could be reused, extended, generalised or replaced
   so that the new and the existing callers share one thing, and what the change makes obsolete,
   to be deleted in the same change. A finding cites the existing thing by location and says what
   it would take to make it fit both callers.
2. **Adopt.** Whether the plan or change hand-rolls something mature. The order of preference is
   a dependency the project already has, then the language's standard library or the platform,
   then a stock tool, then a new library. A finding that proposes a new library cites its docs,
   version and a maintenance signal, and states what adding it costs (transitive dependencies,
   licence, size); a fact the reviewer could not check is marked unverified, never stated from
   memory.
3. **Reversibility.** Sorts the decisions in the plan or change into *decide now* and *defer*.
   Decide now is for one-way doors: what others will build on or what is persisted, such as
   schemas, wire, persisted or event formats, public APIs and names that leak into them. Each
   decide-now finding names who will depend on it and what changing it later would cost. Defer is
   for everything reversible, and each deferral names the signal that should bring it back. This
   lens never proposes a guard, counter, option or abstraction for something reversible.
4. **Trust boundary.** Whether each guard, check or validation sits where outside input enters,
   and only there. Missing validation of outside input is a finding; an allowlist, refusal or
   gate on the project's own callers, agents or scripts is a finding too. A finding names the
   caller and whether it is trusted.

### Picking lenses

- A signals table maps what a plan or change contains to the lenses it calls for: new modules,
  helpers or scripts call for Reuse; hand-rolled parsing, validation, retry, scheduling, dates,
  argument parsing or the like, or a new dependency, call for Adopt; any surface that is
  expensive to change later calls for Reversibility; a new guard, allowlist, validator or auth
  check, or code that handles outside input, calls for Trust boundary.
- A lens named in the request or the brief runs regardless of the table, and only the named
  lenses run.
- Every review states which lenses it picked and which it skipped, each with a one-line reason,
  on one line in exactly this form:
  `Lenses: picked Reuse (<reason>), Adopt (<reason>); skipped Reversibility (<reason>), Trust boundary (<reason>)`.
  Lens names are always written `Reuse`, `Adopt`, `Reversibility` and `Trust boundary`.
- How lenses run follows the review's depth as the review skill sizes it. Low on both axes: the
  one reviewer applies the picked lenses inline. High on either: a coordinator that can start
  reviewers gives each picked lens its own reviewer, on explicit Opus or a cross-family model,
  then merges their findings. A delegated reviewer never starts reviewers of its own; it applies
  the lenses inline and reports.

### Settling conflicts

A Reversibility finding outweighs a Reuse or Adopt finding only for a one-way door; for anything
reversible the smaller option wins. Between Reuse and Adopt, existing repository code beats a new
dependency, and a dependency the project already has beats both.

Trust boundary decides whether a gate belongs at all. The review skill's proofs for a gate,
validator or parser (a threat model, one mutant per bypass class) apply only to the gates that
stay.

### Findings

A lens finding uses the review's own tags (`blocking`, `follow-up`, `nit`) and report, and starts
with the lens name and a middle dot, for example `Reuse · follow-up · <location>: <issue>`, so
findings from several lens reviewers merge without rewriting. Each lens's
evidence rule (above) is part of the finding; a finding without it is a preference, not a finding.

### Consumers

- plan-review and review each gain one short pointer: pick lenses from `review-lenses` during
  sizing and name the picked and skipped lenses in the report. Their existing guidance (cutting
  mechanisms no requirement needs, blast radius, the interface design review, over-engineering as
  a finding) stays where it is. A lens builds on that guidance and links to it rather than
  restating it, and nothing in a lens contradicts it.
- The orchestration skill's review section gains one line: a reviewer's brief names its lenses.

## Scope

In: the skill, its four lenses, its eval suite (three or more behaviour cases, a picking case and
trigger cases), the pointers in plan-review, review and agent-orchestration, a candidates ledger
entry for the accepted Reversibility gap, the repository's skill list, and the readmission
evidence (eval results, including a baseline run of plan-review and review showing no regression).

Out: an operability or observability lens (no recorded gap yet), a separate deletion lens (it is
Reuse's "replace" half), lens agent definitions (Claude Code only, and reviews often run on
Codex), and moving existing guidance out of plan-review or review.

## Decisions

- Four lenses; operability is left out until the ledger records a gap. (Owner, 2026-10-15.)
- One shared skill with one reference file per lens, not one skill per lens. (Owner, 2026-10-15.)
- Existing high-level guidance in plan-review and review stays; lenses must not conflict with it.
  (Owner, 2026-10-15.)
- The Reversibility lens's gap is accepted as known: the ledger has no entry where a model missed
  a one-way door. (Owner, 2026-10-15.)

## Open questions

1. **Does Reuse on a diff have to beat the built-in `/simplify` on the same fixture?** The bar's
   item 4 requires it where a skill overlaps a plugin; the built-ins cover reuse within changed
   code, while the lens searches the rest of the repository and works on plans before code.
   `/simplify` is built into the host and has no folder on disk that could be staged as a
   `--baseline` arm. Default: record that the comparison could not be run, and scope Reuse on a
   diff to what the built-ins leave out: search beyond the changed files, and the deletion of what
   the change makes obsolete.
2. **Can a cross-family reviewer take a lens in an interactive review, or only in an orchestrated
   build?** An interactive session may lack a Codex lane. Default: the skill says "explicit Opus,
   or a cross-family model where the host offers one", and requires neither.
3. **Should the main session's `review` invocation fan out lenses by itself when depth is high?**
   Fan-out costs one Opus reviewer per lens. Default: yes, at most one reviewer per picked lens,
   and never more than four, since the owner asked for lens reviewers.
