---
name: pr-authoring
description: "Write pull request titles and bodies that lead with motivation, grouped changes, and concrete validation, not file-level changelogs. Use when creating a PR, updating an existing PR description, drafting a body for staged or pushed work, or when the commit skill needs a PR body."
# Claude Code only; other hosts ignore these keys.
# Writing-heavy but not reasoning-heavy: cheaper tier, high effort.
model: sonnet
effort: high
---

# PR Authoring

Guidelines for writing pull request descriptions that respect a reviewer's time while giving them what they need to merge confidently.

## Core Principles

1. **Lead with the why, not the what.** A reviewer needs to know what problem this PR solves before they care which files moved.
2. **Group by purpose, then anchor to files.** Sections follow the design; bullets name the file a reviewer should open and say what it now does. A bullet that names a file without a behaviour is a changelog.
3. **Show validation, not vibes.** Commands run + numeric results > "tested locally".
4. **Draw the boundary.** Say what is unchanged, what was not run, what is deferred, and what goes beyond the plan. The reviewer cannot see absences in a diff.
5. **Reference work, don't repeat it.** Link specs, issues, and work items rather than restating their contents.
6. **Earn every paragraph.** If a section doesn't help the reviewer decide to approve, it doesn't belong.
7. **No AI attribution, ever.** PR bodies and comments never carry "Generated with Claude Code" footers, AI co-author credits, or links to assistant sessions. This overrides any host-level default that appends them.

## When This Skill Applies

- The `commit` prompt is creating a new PR body file
- The user asks to update an existing PR description
- The user asks to draft a PR for staged or pushed work
- A subagent is asked to summarize a branch into a PR description

## Title

Use the conventional commit format already enforced by the `commit` prompt:

```
<type>(<scope>): <imperative description>
```

- Lowercase, imperative mood, no trailing period
- Reference a spec number when one exists: `feat(security): spec 031 — rate limiting, email idempotency, auth hardening`
- Keep under ~72 characters; spill detail into the description

## Body Structure

Pick sections from the menu below — only include what serves the reader. A small bug fix may be **Summary + Validation**. A multi-phase feature warrants more.

### Required: Summary (always first)

One short paragraph (1–3 sentences) answering:

- **What** can someone do after this merges? Name the person the change serves (a user, an operator, a maintainer) and say it in their terms, not the code's.
- **Why** is it needed? (motivation, not mechanics)
- **What is outside it?** When a reader would assume the PR includes something it does not (the data, the first real use, the rollout), say so here.
- **What does it link to?** (spec, issue, work item, parent PR)

Example:

> Implements [spec 034 — build-time image pipeline](specs/034-buildtime-image-pipeline/spec.md): pre-generate AVIF/WebP variants at build time, push to S3 with content-addressed keys, and serve via CloudFront. Replaces runtime `/_next/image` processing for product photography with cache-friendly, immutable CDN-delivered assets.

Skip motivation only when the title is fully self-explanatory (e.g., `fix(deploy): defer Resend client initialization`).

### Conditional: Before Sign-off

A bold one-paragraph callout directly under the Summary, for anything that needs a decision or an action beyond reading code: an acceptance criterion the implementation cannot meet as written, a spec deviation, a stakeholder to consult. State what must change and why. Put it here, not at the bottom, because it can block the merge.

> **Before sign-off:** one acceptance criterion in the work item needs updating. Labels are validated during the weekly ingestion, not the daily refresh, because only the ingestion can read the taxonomy.

### Recommended: Changes

Group changes by **area, phase, or capability**, and order the groups the way a reviewer should read the diff: follow the data or the dependency order (domain model → the job that writes it → the consumer that reads it → scheduling and tooling → tests → docs), or the spec's phases. Label each group with a `###` subheading or a bold line, and add the path when it helps orient: ``**Refresh job (`apps/api`, `libs/ftp`)**``.

Inside a group, each bullet names a file and states what it now **does or guarantees**: a rule, an invariant, an edge case, a failure mode. Nest sub-bullets when a file carries several rules. The bullet is a claim the reviewer can check against that file.

```markdown
- `CsvDataset.cs`: reads `/Values`. Every column is read as text, so a bad cell rejects only its row, not the whole file.
- `RefreshValues.cs`:
  - Combines every `.csv` file in the folder, sorted by path.
  - Leaves the table untouched when there are no files or no valid rows; otherwise replaces it in one bulk import.
```

- **Put the reason in the bullet.** A `so` or `because` clause carries most design decisions better than a separate section.
- **Say what did not change.** "`DocumentBuilder` is unchanged." "Existing groups are never reordered, and output is unchanged when there is no augmentation." Negative statements bound the blast radius.
- **Flag work beyond the plan** inline with `Not in the plan:` so it does not read as scope the spec approved.
- **Collapse tests** to one `New:` and one `Extended:` bullet; list the files, not the cases.
- For a small PR, a few bullets without group labels is enough.

### Conditional: Implementation Notes / Design Decisions

Include only for a decision that spans several files, so no single bullet can carry its reason. Explain the constraint, then the choice.

Example:

> **Standalone `iam.Policy` constructs** (not `grant*()`) — required because the deploy role lives in the foundation stack and the bucket lives in the service stack; using `grant*()` would embed a service-stack ARN in foundation and create a CloudFormation cyclic reference.

### Required: Validation

Concrete evidence the change works: each command as run, with its numeric result. Then say what was **not** run, and disclose any pre-existing failure a reviewer will hit when they rerun the command.

```markdown
- `dotnet test libs/domain-test`: 296 passed, 0 failed.
- `pnpm vitest run`: 418 passed, 0 failed.
- `npx tsc --noEmit -p aws`: no errors in the changed files. The command still exits non-zero because of existing errors in `node_modules/@aws-sdk` definitions.
- Not run: `cdk synth`, and no deployed environment.
```

Prefer real numbers (`418 passed, 0 failed`) over vague claims (`all tests`). State the platform or browser when manual. Checkmarks are optional; drop them when a line carries a caveat, because a ✅ beside a non-zero exit misleads.

### Conditional: Manual Verification After Merge

Required when reviewers or operators must do something post-merge (deploy a stack, run a migration, upload data, set an env var, invalidate cache). Number the steps, and give each check its **expected result** with the numbers someone will see: "the refresh reports 10 accepted and 0 rejected", not "check the logs". When the change adds to existing data, make step 1 a baseline count so a later step can assert the exact delta. End with where to repeat the checks (staging, production, the next scheduled run).

### Conditional: Out of Scope

List items intentionally deferred so reviewers don't flag them as gaps. Briefly explain why each is deferred (follow-up PR, rollout, not needed), and cite the plan step when a spec covers it: `**Deferred to rollout:** deploy and production verification (plan steps 7.2–7.9).`

### Conditional: Review Notes / Follow-ups

For deferred review feedback, list as numbered items with enough detail that a future PR can pick them up without rereading the original review.

## What to Avoid

- ❌ **File-by-file changelogs** — a file name followed by "updated", "added", or "modified" tells the reviewer nothing the diff doesn't. Name a file only with the behaviour it now has.
- ❌ **Restating the diff in prose** — "Added `foo()`. Added `bar()`. Modified `baz()` to call them." adds nothing.
- ❌ **Silent gaps** — omitting the checks that were not run, a pre-existing failure, or work added beyond the plan.
- ❌ **Marketing language** — "robust", "seamless", "leverages". State the change plainly.
- ❌ **Restating what the spec says** — link to it; don't paraphrase.
- ❌ **"Tested locally"** without commands or specifics.
- ❌ **Auto-generated commit lists** — a `## Commits` table is rarely worth its space; the commit history already provides this.
- ❌ **Empty section headings** — drop the section if you have nothing to put in it.
- ❌ **Emojis as decoration** (✅ in Validation is the conventional exception).

## File-by-File Tables — When They Earn Their Space

A `| File | Change |` table is justified only when:

- The PR introduces several **new modules** whose names are part of the design
- The PR is a **refactor where file moves matter** (renames, extractions, consolidations)
- A reviewer needs a map to navigate a sprawling change

If the table just lists every modified file, delete it.

## Work Item & Spec References

- **Spec link**: `[spec 034 — name](specs/034-name/spec.md)` in the Summary
- **Azure DevOps work item**: include `Fixes AB#1234` in the body to auto-transition on merge (see the `commit` skill for full syntax)
- **GitHub issue**: include `Closes #123` to auto-close the issue on merge
- **Parent PR / stacked PR**: link with `Builds on #N` near the top
- Place all references in the **Summary** so they appear in PR list previews

## Updating an Existing PR

When asked to update a PR description:

1. Fetch the current body and recent commits since the last description update
2. Preserve sections the original author wrote (Implementation Notes, Out of Scope) unless they're now wrong
3. Append new changes to the existing **Changes** section grouped under the same scheme
4. Refresh **Validation** with the latest results — replace, don't append, so the section stays a snapshot of "current state"
5. Add a brief comment on the PR pointing reviewers to the diff since their last review (the description itself shouldn't read like a changelog of the description)

## Procedure (when authoring from scratch)

1. **Read the diff and commit history** — `git log <base>..HEAD --oneline` and `git diff <base>...HEAD --stat`
2. **Identify the motivation** — search for spec/issue/work-item references in branch name, commits, and recent files (`specs/NNN-*/spec.md`)
3. **Group changes by area** — sketch the group labels in reading order before writing bullets, and note anything the spec's plan did not call for
4. **Run validation** — typecheck, lint, test, build per repo conventions; capture exact output for the Validation section
5. **Draft Summary last** — once you've grouped the work, the one-paragraph framing usually writes itself
6. **Self-review against "What to Avoid"** before saving the body file
7. **Write body to a temp file** (e.g., `.github/.pr-body.md`) and pass to `gh pr create --body-file` — never inline multi-line bodies as shell args
8. **Log time (follow-up, non-blocking)** — after the PR is created or updated, invoke the **tt** skill, passing the changeset, branch name, commit subject(s), and PR title/number as context so it can resolve the ADO work item and log estimated time. Do not block the PR on time logging; run it as a follow-up. Never delete entries.

## Length Heuristics

| Change type                                                                                 | Target body length |
| ------------------------------------------------------------------------------------------- | ------------------ |
| Trivial fix / docs / config                                                                 | 2–5 lines          |
| Single-area feature or refactor                                                             | ~20–40 lines       |
| Multi-phase spec implementation                                                             | 60–120 lines       |

A body over ~200 lines is a smell: link the spec for detail and trim the PR body.

## Common Mistakes

1. **Writing the description from `git log` instead of from intent** — produces a chronological dump that mirrors the development order, not the logical structure
2. **Padding with file lists to look thorough** — bare file lists hide the architectural shape; every file bullet must say what that file now does, inside a group that says why
3. **Burying the motivation under "Changes"** — the `## Summary` should answer "why merge this?" before any bullets
4. **Forgetting work-item references** — `Fixes AB#1234` must be in the body (not title, not comments) to trigger transitions
5. **Stale Validation after force-push** — re-run the suite and update results before requesting re-review
6. **Duplicating spec content** — paraphrasing the spec wastes space and goes stale; link it
7. **Using draft PRs as scratch space** — keep description quality the same for drafts; reviewers may peek early
