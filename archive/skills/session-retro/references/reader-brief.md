# Transcript reader brief

Copy this into each reader's prompt, after a first paragraph that names the project, the date range, the
orchestration doc path and the output path. The paragraph below describes one build's shape; edit it to
match the transcript being read.

The readers' findings and the report name the project. When they feed the prompts configuration
repository, project names, session ids and PR links go to the private evidence store
(`~/dev/prompts-evidence`); what lands in that repository says "a project" or a count.

You are reading one chunk of a condensed Claude Code session transcript from the project named in your
prompt. In these sessions Claude Code (Opus) acted as **orchestrator/coordinator**
of a multi-agent build: it wrote lane briefs, delegated implementation to Codex (`codex exec`,
background) and to Claude subagents (Agent tool; `SendMessage` resumes a subagent), ran adversarial
reviewer subagents, triaged findings, committed, opened PRs, merged, deployed to dev, and talked to
the human owner. Two coordinator sessions ran in parallel (A and B); they exchanged
messages through a shared inbox file. The owner was often away (autonomous
operation). The intended process is in the orchestration doc named in your prompt; you may
read it for context but do not read other repo files.

## Transcript format

- `#### [ts] USER:` the owner's own words (highest-value signal). Some USER lines are harness
  notices (task notifications, hook output); treat those as harness, not owner.
- `[ts] ASSISTANT:` the coordinator's visible text.
- `[ts] TOOL <name> ...` a tool call (Agent = subagent launch with type/model/prompt; SendMessage =
  resume a subagent; Bash commands; Skill loads).
- `[ts] RESULT:` tool output, truncated. `RESULT ERROR:` a failed call.
- `[ts] SUBAGENT REPORT:` a subagent's hand-back, truncated.
- `=== COMPACTION ===` / `=== COMPACT SUMMARY ===` context compaction and its summary.
- `QUEUED USER INPUT:` owner text typed while the coordinator was busy.

## Your job

Read the whole chunk once, carefully. Then write a findings file (Markdown) with exactly these
sections. Be concrete: every claim carries a timestamp and a short evidence quote (≤ 2 lines).
Prefer episodes over generalities. No praise, no padding.

1. `## Timeline` — 8–15 bullets: what the coordinator was doing in this chunk, in order, with
   timestamps. Name lanes, PR numbers and agents where visible.
2. `## Worked well` — episodes where the process produced a good outcome efficiently (a review
   that caught a real defect, a delegation that landed first try, a recovery after compaction
   that went cleanly, an owner interaction that resolved quickly). Timestamp + evidence + why it
   worked.
3. `## Did not work` — the most important part. Each item: timestamp(s), what happened, the
   likely cause, and a rough cost (wall-clock idle time, number of rounds, tokens/agents wasted,
   owner frustration). Look especially for:
   - stalls: long gaps with lanes idle; blocking prompts; waits that never woke; lost messages;
   - wasted rounds: review loops > 2 rounds; fix rounds that re-opened earlier findings;
     reviewers disagreeing; findings the owner later overruled as over-engineering;
   - coordinator doing work it should have delegated, or delegating trivial work;
   - subagents that were killed (TaskStop), timed out, hit turn caps, or returned unusable reports;
   - harness/tool trouble: permission denials, classifier blocks, rate limits, compaction losing
     state, wrong SHAs/IDs after compaction, scratchpad/tmp/port collisions, Codex quota;
   - owner corrections: anything the owner pushed back on (scope, complexity, UX, speed, cost,
     visibility of progress, questions asked that should have been decided);
   - the coordinator writing estimated timestamps or unverified claims;
   - excessive state-file churn or giant hand-backs blowing context.
4. `## Owner feedback (verbatim)` — every substantive owner statement that corrects, redirects,
   approves a class of action, or expresses satisfaction/frustration. Timestamp + exact quote.
   Skip pure approvals like "ok" unless they resolve something notable.
5. `## Patterns` — recurring behaviours across the chunk (good or bad), each with 2+ instances.
6. `## Improvement candidates` — concrete, actionable changes to skills, briefs, the orchestration
   doc, hooks/automation, or coordinator habits, each tied to the evidence above. Say which skill
   or doc would change (agent-orchestration, agent-briefs, herdr-delegation, review, docs/orchestration.md,
   AGENTS.md, a hook, a new skill) and what the rule would say in one sentence.
7. `## Metrics` — counts you observed in this chunk: subagent launches by model; review rounds per
   PR where visible; compactions; owner messages; stalls > 30 min with no visible progress (list
   them with start/end); TaskStop kills; errors.

Cap the file at ~200 lines. Write it to the output path given in your prompt (write it early
and overwrite as you go, so a partial result survives a cutoff). Your final reply to me is at
most 15 lines: the output path, then the 5 most important findings with timestamps.
