# Review request: draft skill `release-notes`

Path in the repo: `.github/skills/release-notes/SKILL.md`. The draft is 640 lines.
It is NOT invoked directly by users: the `ship-release` skill reads it as background
material in its step 3, while drafting the release, and finds it by the folder name
`release-notes`, which other tooling also depends on.

Author's note: "Lines 120-560 are the Node changelog generator script I wrote (about
300 lines) plus a per-ecosystem command table for npm, NuGet and pip. I also copied the
'Grouping changes' section word for word from `.github/skills/pr-authoring/SKILL.md`
so the two stay consistent. The drafting step runs on the cheapest model to save tokens."

## Draft (abridged; elided lines are marked)

~~~~markdown
---
name: release-notes-writer
description: Helps with release notes.
model: haiku
---

# Release notes

Write release notes for a tagged release.

See .github/skills/pr-authoring/SKILL.md for how we write PR bodies.

## Procedure

1. Collect merged PRs since the last tag:

   ```bash
   gh pr list --state merged --search "merged:>=$LAST_TAG_DATE" --json number,title,body
   ```

2. Generate the raw changelog (untested, flags may be wrong):

   ```bash
   npx changelog-gen --since last --format md
   ```

3. Fan out one drafting worker per section (Features, Fixes, Breaking changes):

   ```yaml
   stage: draft-sections
   agent: general-purpose
   model: inherit
   ```

4. Publish using this template:

   ```markdown
   ## <version> - <date>

   ### Upgrade steps
   ```bash
   npm install <package>@<version>
   ```

   ### Changes
   <grouped list>
   ```

## Grouping changes

(copied verbatim from pr-authoring, 34 lines)

<!-- lines 120-560: changelog generator script (Node) and per-ecosystem command table -->

## General writing conventions

Write clearly. Prefer active voice. Avoid jargon.
~~~~
