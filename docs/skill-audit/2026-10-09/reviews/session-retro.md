# session-retro

Verdict: **needs-work** · SKILL.md body 72 lines · description 730 chars

The SKILL.md is short at 72 body lines. It has a clear seven-step procedure, a single reference file linked one level deep, and a fixed contract for reader findings that blocks vague reports. Its biggest gap is that several mechanical steps are left for Claude to do by hand even though they belong in condense.py: filtering for the owner's words, chunking, and counting idle gaps, context size and owner messages. Step 5 also tells Claude to count `usage` fields "from the narratives", but the narratives never contain them.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | pass | Names JSONL condensing, chunking, the reader fan-out, cost/idle/review-round metrics and skill edits, with plain-language triggers. |
| Description includes both what the Skill does and when to use it | pass | 730 chars: what it does, 'Use whenever…', 'Load it before opening any transcript file', and a Not-for clause. |
| SKILL.md body is under 500 lines | pass | 72 body lines. |
| Additional details are in separate files (if needed) | pass | The reader brief is in references/reader-brief.md. |
| No time-sensitive information (or in an 'old patterns' section) | fail | subagent-costs.py hardcodes a PRICE table with no source or date, and the reader brief describes one build's shape (two coordinators A and B, a shared inbox file). |
| Consistent terminology throughout | partial | Mostly consistent ('owner', 'reader', 'findings file'). The brief mixes 'orchestrator/coordinator' and 'human owner'/'owner'. Minor. |
| Examples are concrete, not abstract | pass | Concrete commands and file names; the brief lists concrete failure classes to look for. |
| File references are one level deep | pass | SKILL.md links reader-brief.md directly. The brief links nothing further. |
| Progressive disclosure used appropriately | pass | The brief is loaded only for the fan-out. At 69 lines it needs no table of contents. |
| Workflows have clear steps | pass | Seven numbered steps with commands. |
| Scripts solve problems rather than defer to Claude | fail | Owner-only filtering (step 3), chunking at 450K (step 4), and the idle-gap, context-size and owner-message counts (step 5) are all left to Claude. |
| Error handling is explicit and helpful | partial | condense.py gives a raw IndexError when arguments are missing and uses a bare `except Exception`. subagent-costs.py prints its usage on missing args, but a bad meta.json stops it with an unhandled error. |
| No 'voodoo constants' (all values justified) | fail | The truncation lengths in condense.py (2000, 1500, 400, 350/700, 2500, 20000), the 450K chunk size and the PRICE tuple carry no rationale. |
| Required packages listed in instructions and verified as available | partial | python3 is listed. `gh` is used in step 5 but missing from Prerequisites. |
| Scripts have clear documentation | partial | Both scripts have usage docstrings. subagent-costs.py silently writes subagent-rows.json to the cwd, and neither the docstring nor SKILL.md mentions it. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | partial | The Common Issues table returns generic reader reports for evidence. Synthesis (step 6) has no check that every action names evidence and a target skill. |
| Feedback loops included for quality-critical tasks | partial | A loop exists for reader output, but only as a Common Issues row, not as a step. |
| At least three evaluations created | fail | No evals/ directory. |

## Findings

1. **high** · Solve, don't defer / Scripts solve problems rather than defer to Claude · SKILL.md step 3 and Common Issues last row; scripts/condense.py lines 90-95
   > Filter `<label>-user-prompts.md` to messages the owner typed, dropping pasted skill text, harness notices and task notifications.

   Fix: Make condense.py write `<label>-owner.md` directly. Apply the prefix filter now listed in Common Issues (`<\system-reminder>`, `<local-command`, 'Base directory for this skill', `<\task-notification>`) to string-content user messages too; today only list-content blocks are filtered. Then cut step 3 to one line, 'Read `<label>-owner.md` in full', and delete the Common Issues row. (about 90 tokens saved)

2. **high** · Solve, don't defer / Validation steps for critical operations · SKILL.md step 5, second paragraph
   > From the narratives, also count: context size per call (`usage` fields), compactions, idle
   gaps over 30 minutes, owner messages, review rounds per lane

   Fix: The narratives never contain `usage` (condense.py drops it), so this instruction cannot be followed. Add context-size percentiles, idle gaps over a named threshold and the owner-message count to `<label>-stats.md` in condense.py (compactions are already there). The step then only asks Claude to count review rounds from the lane folders. (about 50 tokens saved)

3. **medium** · Solve, don't defer / Provide utility scripts · SKILL.md step 4; scripts/condense.py docstring
   > Split each narrative at about 450K characters.

   Fix: Add a chunk option to condense.py, e.g. `--chunk-chars 450000`, that writes `<label>-narrative-NN.md` split on entry boundaries. Justify the size in a constant comment (roughly 110K tokens leaves the reader room for the brief and its output). Step 4 then names the chunk files instead of asking Claude to split by hand. (about 15 tokens saved)

4. **medium** · Avoid time-sensitive information / No voodoo constants · scripts/subagent-costs.py line 14 and family()
   > PRICE = {"opus": (5, 25, 0.5, 6.25), "sonnet": (3, 15, 0.3, 3.75)}
    return "sonnet" if "sonnet" in (model or "") else "opus"

   Fix: Comment the price source and as-of date, and add a haiku entry. As written, any non-sonnet model, including haiku and unset, is priced as opus and the estimate is inflated. Print unknown model families as 'unpriced' instead of guessing.

5. **low** · No voodoo constants / Error handling is explicit and helpful · scripts/condense.py lines 8, 28-29, 49-111
   > src, outdir, label = sys.argv[1], sys.argv[2], sys.argv[3]
        except Exception: stats['badline'] += 1; continue

   Fix: Exit with `__doc__` when fewer than three args are given, as subagent-costs.py does. Collect the truncation lengths (2000, 1500, 400, 350/700, 2500, 20000) into named constants with one comment on why each bound exists, so a reader of a truncated hand-back knows the cut is deliberate.

6. **medium** · Template pattern / Avoid time-sensitive information · references/reader-brief.md lines 3-15
   > Two coordinator sessions ran in parallel (A and B); they exchanged
messages through a shared inbox file.

   Fix: Replace the one-build paragraph with placeholders (`{project}`, `{date range}`, `{session roles}`, `{delegation channels}`, `{orchestration doc}`, `{output path}`) and drop the 'edit it to match' instruction, so readers of a different build are not primed with Codex, two coordinators or an inbox file. Do the same for the hardcoded skill list in item 6.

7. **low** · Concise is key / Consistent terminology (single source) · SKILL.md step 4 last sentence; Common Issues rows 2 and 3
   > | `gh pr list` fails with a GraphQL node limit | Drop the `commits` field from `--json` |
| The subagent cap rejects a fan-out | Launch up to the cap, then the remainder as each reader returns |

   Fix: Delete the GraphQL row, because the step 5 command never requests `commits`. Delete the subagent-cap row, because step 4 already says to launch the rest as slots free. Replace step 4's parenthetical list of findings sections, which repeats the brief, with 'per the brief'. (about 70 tokens saved)

8. **low** · Avoid assuming tools are installed / Scripts have clear documentation · SKILL.md Prerequisites and step 5; scripts/subagent-costs.py line 83
   > - `python3`; the session files under `~/.claude/projects/<project slug>/<session id>.jsonl`
    json.dump(rows, open("subagent-rows.json", "w"))

   Fix: Add `gh` (authenticated, run in the repo) to Prerequisites. Have subagent-costs.py take an output directory, or document that it writes subagent-rows.json to the cwd, so the run does not drop a file into the repository the skill says must stay clean.

## Strengths

- Its reader contract is fixed and enforced by evidence: each claim needs a timestamp and a quote of two lines or less, the section list is set, the file is capped near 200 lines, it is written early so a cutoff keeps partial work, and the reply is limited to 15 lines. This keeps fan-out results small and checkable.
- It splits mechanical and judgment work cleanly: scripts handle condensing and costs, subagents read, and the main agent reads the owner's own words in full.
- The last step turns lessons into edits and prefers a script or hook wherever a written rule was already broken. That closes the loop from retro to skill change.

## Cut candidates

- Common Issues: the `gh pr list` GraphQL node limit row (step 5 never requests `commits`)
- Common Issues: the subagent-cap row (duplicates step 4)
- Common Issues: the owner-only filter row (move into condense.py)
- Step 3 prose on filtering harness text (move into condense.py)
- Step 4 parenthetical list of findings sections (duplicates references/reader-brief.md)
