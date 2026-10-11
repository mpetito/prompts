# Retrospective: readmit spec and implement as spec (2026-10-11)

## Outcome

- **spec: readmitted.** `skills/spec/` is a 49-line worker skill with two sections:
  - **Write the spec and plan.** Five rules and one line of links. The rules: spec.md says what
    and why; open questions are numbered, each with context and a `Default:`; an unproven claim
    becomes an open question; plan.md is always written on the defaults; each plan step names
    its files and ends with a check that can fail.
  - **Carry out the plan.** This is all that remains of `implement`: resume at the first unticked
    step, tick each step in the same change that lands it, and update plan.md in place when a
    step proves wrong.
- **Archived folders:**
  - `archive/skills/spec/SKILL.md` was moved with `git mv` and rewritten.
  - `archive/skills/implement/` and both archived eval suites were removed. Their traps were
    reused where a rule survived.
- **Dropped, for lack of a gap or of owner evidence:**
  - folder numbering;
  - the spec and plan templates, complexity tiers and supporting-docs convention;
  - the no-estimates rule;
  - status fields and specs/README.md upkeep;
  - the archived "blocking questions remain: stop" gate, which the owner's corrections run
    against;
  - plan order (plan-review checks it);
  - simplicity (owned by code-style);
  - re-reading after compaction.
- **Inputs:**
  - the digest (`2026-10-11-spec-digest.md`), confirmed by the owner as D1;
  - owner evidence: 302 typed or queued Claude messages, about 150 typed Codex turns, 30 spec
    folders, and 13 PR comments judged to be the owner's.

## Measured delta

The held-out run graded with frozen assertions: Opus at effort high, 3 runs per arm; Codex
gpt-6-astra at effort xhigh, 1 run per arm. Objective assertions only; Opus judge means in
brackets.

| Case | Rule | Opus with | Opus without | Codex with | Codex without |
| --- | --- | --- | --- | --- | --- |
| r1-numbered-defaults | 1 | 3/3 (.95) | 1/3 pass (.53) | 1/1 | 0/1 |
| r3-unproven-claim | 3 | 3/3 (1.0) | 0/3 (.15) | 1/1 | 0/1 |
| r4-what-how | 4 | 3/3 (.77) | 0/3 (.22) | 1/1 | 0/1 |
| r5-tick-order | 5 | pass | pass (no gap) | pass | pass (no gap) |

- **Across all 12 Opus and 5 Codex runs per arm,** graded with the final assertions:
  - Every with-skill run passed r1, r3 and r4.
  - Every without-skill run failed r3 and r4.
  - Opus failed r1 without the skill in 10 of 12 runs. Both passes were real: numbered
    questions, each with a pick.
  - **Rule 1 misses the "3 of 3" bar on Opus.** It discriminates on Codex in every run, because
    Codex writes no numbered questions section unaided. On Opus only the "every question has a
    pick" half separates the arms.
- **Rule 5 is measured live, not by the harness.**
  - Text answers order the ticks correctly on both agents, so the r5 case shows no gap.
  - With tools, both agents batched every tick at the end without the skill, in 4 of 4 runs.
  - With the skill they ticked each step as it landed, in 4 of 4 runs (2 Opus, 2 Codex).
- **Triggers on Opus:**
  - Should-fire: 15 of 15.
  - Should-not-fire: 12 of 12 by Skill calls. The harness counts more fires, but each of those
    was a read of the mounted file while the model explored an empty workspace.
- **Codex isolation:** `codex exec --ignore-user-config` still loads `~/.agents/skills`, and the
  with-skill Codex arm read plan-review, project-setup and code-style through spec's links. So
  the Codex with-skill arm measures spec together with those skills; the Opus arm measures spec
  alone.

## What the gates caught

- **Plan review (1 round, 4 blocking findings):**
  - Probe under the harness's own conditions (no user skills, no write tools), or the probe
    predicts nothing about the eval.
  - Ticking can't be seen in a single-shot text answer.
  - The archive move must not take the evals with it.
  - Every hypothesis needs a trap and a pass rule.
- **The probe ($2.89 with the live tick runs):**
  - Format was never the gap. All 6 runs picked the next spec number, all named a review before
    code, and none gave an estimate.
  - The gaps were what and how mixed (6 of 6), unproven claims stated as fact (6 of 6), and
    ticks batched at the end (4 of 4).
- **The evidence lane reversed the archived gate.** The owner corrected models that stopped to
  wait 3 times and never asked one to stop. Two project briefs had already overridden the
  archived gate.
- **Skill review, round 1:**
  - Rules 3 and 4 contradicted each other: a literal reader stopped before plan.md whenever a
    question touched money or a product fact.
  - The README still named `/implement`.
  - The "Not for" clause named a skill that never fires for that request.
  - The candidate counts overstated the evidence.
- **The example step in the skill was in the eval fixture's own domain.** It was replaced before
  the final runs.
- **Assertions, three rounds of the same flaw.** Regexes that list the phrasings of a semantic
  property (asks for confirmation, gives a default, states a fact) failed correct answers and
  passed wrong ones:
  - wrapped lines;
  - "Does every…?";
  - "No recommendation";
  - a claim named inside an unrelated question.

  Round 3 fixed the whole class, and planted mutants checked it. No assertion changed after the
  held-out run.

## What it cost

- **Claude: about $24.72 of the $30 cap.**
  - Probe and live tick: $2.89
  - Smoke and hardening: $5.02
  - Full suite: $7.07
  - Final run: $4.55
  - Trigger case: $0.27
  - Held-out: $4.92
- **Codex:** about 5.4M eval tokens, under the 6M ask point. The Codex meter stayed at 13%, because it reads only
  interactive rollouts.
- **Rounds:** plan 1; skill 2; suite 3, the third for blocking problems only.
- **Owner decisions:** D1 (the digest, confirmed as written) and D2 (spend past $20 for one
  held-out run).

## What transfers

- **Probe before writing rules, and probe in the eval's conditions.** The owner's guess ("the
  gap is likely the owner's format") was half right: the format rules held already, and the
  gaps were separation, claims and ticking.
- **A behaviour that shows only with tools needs a live probe.** A text snapshot can't show it.
  Measure it with and without the skill and record it as a signal (readmission.md, "Testing rules
  that only show up in long-running work").
- **Semantic checks:**
  - Make the regex name the object and require the act in the same sentence.
  - Plant mutants in both directions: a correct answer that must pass and a wrong one that must
    fail.
  - Freeze the manifest before a held-out run.
- **Keep the skill's examples out of the fixture's domain.**
- **Claude Code treats `~/.claude/jobs` as a sensitive path.** A tool-using probe there gets
  every edit denied, so put its fixtures in the worktree's git-ignored `.orchestration/`.

## Follow-ups

- **Owner-only:** after merge, run `setup-skills-link.ps1` so `~/.claude/skills/spec` and
  `~/.agents/skills/spec` exist.
- **Proposed sibling edit (the owner's call):** in plan-review's description, change "Not for …
  writing the plan itself" to "… writing the plan itself (spec)".
- **Two owner-reserved lists** (spec rule 4 and agent-orchestration's owner-before) have
  different members. Unify them.
- **With-skill plans still mark steps as waiting on cosmetic questions.** Unaided Opus does the
  same. If the owner sees it in use, add "steps that depend only on other questions are carried
  out on their defaults".
- **Known survivors:** the claim check misses some synonyms ("provide", "as confirmed by"), and
  a deeper-indented step with no path is read as part of the step above. The judge backs the
  first up.
- **`archive/skills/research/SKILL.md` links `../spec/SKILL.md`,** which no longer exists.
- **Bar item 5:** check loads with `python3 scripts/skill-usage.py` within 30 days.
