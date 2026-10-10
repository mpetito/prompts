---
name: session-retro
description: "Run a retrospective over Claude Code session transcripts: condense the JSONL into a readable narrative, chunk it, fan out reader subagents with one fixed findings contract, compute throughput, cost, idle and review-round metrics, and synthesise prioritised actions and skill changes. Use whenever someone wants to learn from past sessions, even in plain words: analyse the transcripts from this project, what worked and what did not in the last build, where did the time and tokens go, how many review rounds did lanes take, what did the owner keep correcting, or turn the lessons into skill edits. Load it before opening any transcript file. Not for reviewing code (review), or for running the build itself (agent-orchestration)."
---

# Session Retro

Transcripts are too long to read in one context. This procedure turns them into a report that
names costs and actions, using scripts for the mechanical parts and readers for judgment.

## Prerequisites

- `python3`; the session files under `~/.claude/projects/<project slug>/<session id>.jsonl`, with
  subagent logs under `<session id>/subagents/`
- A scratch directory for the outputs; nothing here goes in the repository

## Procedure

1. **Pick the sessions.** List them by size and date; the coordinators' sessions are the large
   ones. Note each session's role (coordinator A, coordinator B, a one-off).

   ```bash
   ls -lS ~/.claude/projects/<project slug>/*.jsonl | head
   ```

2. **Condense each session.**

   ```bash
   python3 -I scripts/condense.py <session.jsonl> <out dir> <label>
   ```

   It writes `<label>-narrative.md` (owner words, assistant text, tool calls, results and
   subagent hand-backs, truncated), `<label>-user-prompts.md` and `<label>-stats.md` (tool and
   agent counts by model, skills loaded, denials, errors, compactions).

3. **Extract the owner's words on their own.** Filter `<label>-user-prompts.md` to messages the
   owner typed, dropping pasted skill text, harness notices and task notifications. This file is
   the highest-value input; read all of it yourself.

4. **Chunk and fan out readers.** Split each narrative at about 450K characters. Launch one
   reader per chunk with [the reader brief](references/reader-brief.md) and an output path; a
   mid-tier model is enough for reading with a fixed contract, so select it explicitly per the
   model policy. Keep the concurrency under the host's subagent cap and launch the rest as slots
   free. Each reader writes a findings file (timeline, worked well, did not work with cost,
   owner feedback verbatim, patterns, improvement candidates, metrics) and replies in 15 lines.

5. **Compute the numbers** while readers run:

   ```bash
   python3 -I scripts/subagent-costs.py <session.jsonl>...      # subagent turns, tokens, estimated cost
   gh pr list --state all --limit 400 --json number,title,createdAt,mergedAt,additions,deletions > prs.json
   ```

   From the narratives, also count: context size per call (`usage` fields), compactions, idle
   gaps over 30 minutes, owner messages, review rounds per lane (the lane folders' `review*.md`
   and `fix-r*.md`), and finding counts by class. The Codex meter history is in
   `~/.codex/sessions/**/*.jsonl` (`rate_limits.primary.used_percent`).

6. **Synthesise.** Concatenate the readers' "Did not work", "Patterns" and "Improvement
   candidates" sections, then write the report in this order: the build in numbers; what worked;
   what did not work, ranked by cost with evidence; prioritised actions ranked by impact over
   effort, each naming the skill or doc where the rule will live; a skills table; two or three
   meta-lessons. Quote the owner where the owner said it first.

7. **Act on it.** Turn the actions into edits of the named skills and docs, preferring a script
   or a hook over a paragraph wherever the rule was already written down and still broke.

## Common Issues

| Problem | Solution |
| --- | --- |
| A directory name starting with `-` breaks `ls` or `du` | Prefix the path with `./` |
| `gh pr list` fails with a GraphQL node limit | Drop the `commits` field from `--json` |
| The subagent cap rejects a fan-out | Launch up to the cap, then the remainder as each reader returns |
| Readers return generalities | Their brief asks for a timestamp and a two-line quote per claim; send it back for the evidence |
| The owner-only filter keeps harness text | Drop messages starting with `<system-reminder>`, `<local-command`, "Base directory for this skill" and task notifications |
