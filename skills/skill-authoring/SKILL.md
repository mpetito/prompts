---
name: skill-authoring
description: "Write, review, split or fix an agent skill: a SKILL.md folder with optional references/ and scripts/. Use when turning a runbook, doc or repeated workflow into a skill; when a skill does not fire, fires on the wrong requests, or needs its description rewritten; when a SKILL.md has grown too long and should become a short procedure plus reference files; or when checking a skill's frontmatter, links or model settings before merge. Not for AGENTS.md, CLAUDE.md or copilot-instructions.md (always-loaded project context), committing or opening a PR for skill edits, or running and benchmarking a skill's evals."
---

# Skill authoring

Role: worker. Loaded by whichever agent writes or reviews a skill; this file stays under 120 lines.

Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
are the baseline. This file adds what that page leaves out; where the two differ, this file wins.

## Procedure

1. **Decide it belongs in a skill.** A skill is a bounded procedure or reference loaded on
   demand. Conventions for a whole repository go in AGENTS.md or CLAUDE.md; knowledge the model
   already has goes nowhere. Redirect that content and say so in your output.
2. **Name the gap.** State what a model does wrong without the skill, quoting its output when
   you have it. Every rule traces to a gap; each gap becomes an eval case in step 7.
3. **Name and place the folder.** `name` is lowercase letters, digits and hyphens, and equals
   the folder name exactly (the Agent Skills spec requires it); rename a folder that differs.

   | Host | Project root | User root |
   | --- | --- | --- |
   | Claude Code | `.claude/skills/` | `~/.claude/skills/` |
   | Codex | `.agents/skills/` | `~/.agents/skills/` |
   | GitHub Copilot | `.github/skills/`, `.claude/skills/` or `.agents/skills/` | `~/.copilot/skills/` or `~/.agents/skills/` |

   For several hosts, keep one copy and symlink the other roots to it.
4. **Write the description.** It is all a host sees before the skill fires.
   - What the skill does, then "Use when …" with the phrasings people actually type.
   - Then "Not for <near-miss task> (<sibling>)" for each skill a request could be mistaken for.
   - Under about 900 characters; no `<` or `>`.
   - Triggers go in `description`, never only in Claude Code's `when_to_use`, which Codex and
     Copilot ignore.
5. **Write the body.**
   - Line one names the consumer role (table below); stay within its budget.
   - No "When to Use", Overview or Related Skills section; the description has already fired.
   - Numbered steps with exact commands. Run each command, and label any you could not run as
     unverified. Precede a destructive step with its backup and follow it with the rollback.
   - One line per rule; one checklist, inside the procedure; no build anecdotes.
   - One home per rule: link a sibling skill's section instead of copying it.
   - Code libraries, long tables and worked examples go in `references/`, or in `scripts/` when
     they should be run rather than read. Link each reference directly from SKILL.md, and open
     any reference over 100 lines with a table of contents.
   - Link other skills relative to this folder (`../other-skill/SKILL.md`), never from a
     repository root: skill folders are symlinked into home directories with no repository.
   - When an embedded template contains a fenced block, fence the template with more backticks
     than any fence inside it (or with `~~~~`). Otherwise the inner closing fence ends the
     template and the rest leaks into the instructions.
   - Describe tools as capabilities ("the GitHub MCP server's issue tools"); tool IDs differ
     by host.
6. **Set host keys deliberately.** Hosts differ: Codex ignores Claude Code's extra keys, and a
   claude.ai upload rejects them.
   - `disable-model-invocation: true` when only a person should start the skill, such as one
     with a destructive or outward-facing step. For Codex, also set
     `policy.allow_implicit_invocation: false` in the skill's `agents/openai.yaml`.
   - Leave `model` unset on a skill read inside another task: a pin switches the model for the
     rest of the caller's turn. Pin a cheaper `model` only with a reason tied to the steps
     (mechanical, script-driven, easy to verify), and never `haiku` where a step is destructive
     or needs judgment. "Keep it cheap" alone is not a reason.
   - A skill that delegates names each worker's model in its steps: `opus` unless a weaker tier
     is justified by bounded, verifiable work, and never `inherit`. The skill's own `model`
     does not choose its workers' models.
   - Other keys: [Claude Code skills](https://code.claude.com/docs/en/skills).
7. **Check, fix, repeat** until all hold:
   - The frontmatter parses as YAML, and the body fits the role's budget (`wc -l SKILL.md`).
   - Every relative link resolves from the skill folder.
   - Three behaviour evals, each with a trap in its fixture, fail without the skill and pass
     with it. Should-fire trigger queries use people's words; should-not-fire queries come from
     the Not-for clause. Rerun them before and after every edit.

## Consumer roles

| Role | Loaded | Budget |
| --- | --- | --- |
| orchestrator | once per session | may be long |
| worker | once per lane, by subagents or Codex | under about 120 lines |
| human | when a person types `/name` | short, procedural |
| domain reference | when a project needs it | short SKILL.md, detail in `references/` |

## In the shared prompts repository

If `readlink -f` on this skill's folder lands in a repository that has
`docs/skill-audit/readmission.md`, that file is the bar a skill must clear to enter `skills/`,
`docs/evaluating-skills.md` says how to run and read its evals, and `CONTRIBUTING.md` gives the
setup step that links a new skill.
