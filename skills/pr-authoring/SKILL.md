---
name: pr-authoring
description: "Procedural knowledge for writing concise, useful pull request descriptions that lead with motivation and outcomes rather than file-level changelogs. Use when creating a new pull request, updating an existing PR description, or when the commit prompt produces a PR body. After a PR is created or updated, logs estimated time via the tt skill."
# Claude Code only; other hosts ignore these keys.
# Writing-heavy but not reasoning-heavy: cheaper tier, high effort.
model: sonnet
effort: high
---

# PR Authoring

Guidelines for writing pull request descriptions that respect a reviewer's time while giving them what they need to merge confidently.

## Core Principles

1. **Lead with the why, not the what.** A reviewer needs to know what problem this PR solves before they care which files moved.
2. **Group by purpose, not by file.** Reviewers reconstruct intent from logical sections; they reconstruct mechanics from the diff.
3. **Show validation, not vibes.** Commands run + numeric results > "tested locally".
4. **Reference work, don't repeat it.** Link specs, issues, and work items rather than restating their contents.
5. **Earn every paragraph.** If a section doesn't help the reviewer decide to approve, it doesn't belong.
6. **No AI attribution, ever.** PR bodies and comments never carry "Generated with Claude Code" footers, AI co-author credits, or links to assistant sessions. This overrides any host-level default that appends them.

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

- **What** does this PR do?
- **Why** is it needed? (motivation, not mechanics)
- **What does it link to?** (spec, issue, work item, parent PR)

Example:

> Implements [spec 034 — build-time image pipeline](specs/034-buildtime-image-pipeline/spec.md): pre-generate AVIF/WebP variants at build time, push to S3 with content-addressed keys, and serve via CloudFront. Replaces runtime `/_next/image` processing for product photography with cache-friendly, immutable CDN-delivered assets.

Skip motivation only when the title is fully self-explanatory (e.g., `fix(deploy): defer Resend client initialization`).

### Recommended: Changes

Group changes by **area, phase, or capability** — not by file path. Use `###` subheadings for areas; bullets inside.

- For multi-phase work, use `### Phase N — Name` subheadings matching the spec
- For cross-cutting work, use functional groupings: `### Infrastructure`, `### App integration`, `### CI / Docker`
- Use **bold** to highlight a non-obvious decision inside a bullet
- Inline-link to filenames only when the file name carries meaning (e.g., a new module or migration)

### Conditional: Implementation Notes / Design Decisions

Include only when reviewers would otherwise ask "why did you do it that way?". Explain the constraint, then the choice.

Example:

> **Standalone `iam.Policy` constructs** (not `grant*()`) — required because the deploy role lives in the foundation stack and the bucket lives in the service stack; using `grant*()` would embed a service-stack ARN in foundation and create a CloudFormation cyclic reference.

### Required: Validation

Concrete evidence the change works. Use checkmarks or a checklist with the actual commands and numeric results.

```markdown
- ✅ `pnpm typecheck` — 3 projects pass
- ✅ `pnpm lint` — clean
- ✅ `pnpm vitest run` — 418 tests passing
- ✅ Manual: verified PDP renders without layout shift on mobile Safari
```

Prefer real numbers (`418 tests`) over vague claims (`all tests`). State the platform/browser when manual.

### Conditional: Manual Steps After Merge

Required when reviewers or operators must do something post-merge (deploy a stack, run a migration, set an env var, invalidate cache). Number the steps.

### Conditional: Out of Scope

List items intentionally deferred so reviewers don't flag them as gaps. Briefly explain why each is deferred (follow-up PR, not needed, etc.).

### Conditional: Review Notes / Follow-ups

For deferred review feedback, list as numbered items with enough detail that a future PR can pick them up without rereading the original review.

## What to Avoid

- ❌ **File-by-file changelogs** — diff already shows files. Only list files when grouping reveals intent (a migration, a new module, a renamed export).
- ❌ **Restating the diff in prose** — "Added `foo()`. Added `bar()`. Modified `baz()` to call them." adds nothing.
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
3. **Group changes by area** — sketch the `### Subheading` list before writing bullets
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
| Spec ≥ 200 lines is a smell — consider linking the spec for detail and trimming the PR body |

## Common Mistakes

1. **Writing the description from `git log` instead of from intent** — produces a chronological dump that mirrors the development order, not the logical structure
2. **Padding with file lists to look thorough** — file lists hide the architectural shape; reviewers prefer 4 grouped paragraphs over 40 file bullets
3. **Burying the motivation under "Changes"** — the `## Summary` should answer "why merge this?" before any bullets
4. **Forgetting work-item references** — `Fixes AB#1234` must be in the body (not title, not comments) to trigger transitions
5. **Stale Validation after force-push** — re-run the suite and update results before requesting re-review
6. **Duplicating spec content** — paraphrasing the spec wastes space and goes stale; link it
7. **Using draft PRs as scratch space** — keep description quality the same for drafts; reviewers may peek early
