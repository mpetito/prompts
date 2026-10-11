---
name: code-style
description: "Write or change code in the owner's pragmatic style: the least mechanism that does the job, what the platform and codebase already provide, trust in your own callers, registry dispatch, contract-level comments, nothing left behind by a change, and tests that never match copy. Use when implementing a feature, fixing a bug, refactoring, finishing a migration, adding a tool, handler, limit, script step or test, or when a brief says to load code-style before writing code, including one-line fixes with no spec. Load it before searching for the code to change. Not for reviewing a diff or deciding whether a change is safe to merge (review), reviewing a plan or spec before code exists (plan-review), writing or fixing a skill (skill-authoring), or setting up linters, formatters, compiler options or their thresholds (project-setup)."
---

# Code style

Role: worker. Loaded once per lane by Claude subagents and Codex before they write code; under 120 lines.

Project conventions always win over the owner's personal style: "project conventions always win
over my own personal style preferences."

## Rules

Each rule is the owner's; quoted text is the owner's own words.

1. **Least mechanism:** no stored field, counter, flag, job or policy until a real need shows; derive it from data already
   recorded. A lagging source is no reason to copy it or add a second read path; read it before your own write (inferred).
2. **Use what exists first:** a platform signal (queue depth, an existence check), the dependency's API, a stock tool,
   a shared helper. "We have a queue. The queue length is itself a signal of back pressure if we need it."
3. **Trust your own agents, scripts and services:** warn; never refuse, allowlist or gate them. "The orchestrator
   is not an adversary we're defending against." Outside input (a request, a user) is still validated where it enters.
4. **Registry dispatch:** "There should be no need for switch statements based on tool name. That's the
   purpose of a registry." Each entry carries its handler; move existing cases in; no second name-to-handler map beside it.
5. **Comments:** "Public contracts should have doc comments" stating limits, units and errors, without type tags,
   "and algorithms should have comments explaining why"; never narrate. A module you create, or whose public
   contract you add or change, opens with a short purpose header.
6. **In pre-release or internal code, delete what a change replaces,** even if exported: old helper, shim, alias, legacy path,
   and no note about it. "We don't need to maintain backwards compatibility." A published API keeps its deprecation path.
7. **Tests never match copy:** "I'd rather not rely on content text matching for test contract." Locate by role
   or test id; import expected text from the content source, and match no text it lacks, labels included.

## Procedure

1. Read the files you will change and the repository's written conventions. Where a convention
   and a rule above disagree, follow the convention and say so in your notes.
2. Before adding state, a check, a branch or a helper, name what already exists that does the job
   (rules 1, 2, 4) and who calls the code (rule 3).
3. Write the change. Then reread the diff against each rule and fix what breaks one.
