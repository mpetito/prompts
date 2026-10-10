# Fix request: the `preview-deploy` skill fires on the wrong things

Repo: `fernhill-web`. The team uses Claude Code and Codex daily. Skills live in
`.agents/skills/`, and `.claude/skills` is a symlink to that folder. Two other skills sit
beside this one:

- `.agents/skills/prod-deploy/SKILL.md` deploys to PRODUCTION and rolls production back.
- `.agents/skills/preview-cleanup/SKILL.md` deletes expired preview environments.

From the skill's owner: "People ask for 'a preview link', 'spin up a preview for this branch'
or 'somewhere QA can click my PR', and the agent never loads this skill; it improvises with the
fern CLI and gets the flags wrong. Meanwhile it loaded once for 'tear down last week's previews'
and once for 'roll back production to yesterday's build', and both times it created a preview
instead. My plan: move the When to Use bullets into the `when_to_use:` frontmatter key that
Claude Code supports, and leave the description alone so I don't break anything."

## Current file (complete)

~~~~markdown
---
name: preview-deploy
description: Ephemeral environment orchestration for the <branch> deployment pipeline, including provisioning, DNS, rollback and teardown hooks.
---

# Preview deploy

## When to Use

- The user asks for a preview link or a preview environment
- The user wants to spin up a preview for a branch or pull request
- QA needs a URL to test a pull request

## Procedure

1. Build: `fern build --target preview`
2. Deploy: `fern preview create --branch "$BRANCH" --ttl 72h`
3. Post the URL printed on the last line as a comment on the pull request.

## Related Skills

- prod-deploy
- preview-cleanup
~~~~
