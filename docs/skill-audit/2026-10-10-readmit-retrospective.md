# Retrospective: readmit model-council and firecrawl (2026-10-10)

## What the gates caught

- **Plan review (1 round, Opus).** Three blockers before any lane started:
  - "Same disposition and action" let the coordinator judge free-text equality, which is synthesis by another name. It became tally-decided identity.
  - A no-consensus default could silently pick a member. It became the status quo.
  - Eval answer runs see no Firecrawl tool and none of the server's instructions, so fixture-only cases would inflate the delta. Fixtures now copy them verbatim.
  - The last one decided the firecrawl outcome.
- **Firecrawl overlap.** With the live MCP descriptions in the fixtures, unaided Opus and Sonnet passed 5 of 7 routing rows. The archived skill's opinions mostly live in Firecrawl's own tool descriptions now. Two rules survive.
- **A confounded measurement.** "Do not call any tools" stopped Sonnet reading its fixture in 12 of 21 runs. The review suites' wording ("read the input file, but do not run commands") fixed it. Use that wording in every fixture prompt.
- **Council review, round 1:** 23 mutants, 2 surviving consensus guards in the tally. Round 2: 32 of 32 killed. The follow-up found a symlinked answer path that deleted its target.
- **Firecrawl review, round 1:** "a subtree copy needs a key" was false (a keyless multi-URL scrape works). Round 2: the CLI flattens paths into one file name, so pages silently overwrite each other. Round 3: closed as a class, checked with a 13-line hostile link list.
- **Non-discriminating cases kept as regression checks, not weakened:** failed citation, lost member, map guard.

## Outcome

- **model-council: readmitted.** Merged as 573d8a8 and cdda810. It is a blind round, then up to two
  exchange rounds, ending in consensus (decided mechanically by `tally.sh`), `no consensus`
  (status-quo default, flagged for the human) or `incomplete`.
- **firecrawl: readmitted under D4,** with the owner's explicit partial waiver of bar item 2.
  Merged as be3e26a. It has two many-page rules; the routing-table draft is kept on
  `evidence/firecrawl-routing-table`.
- **D3 c, d, e and g: applied** in 5dd638e.
- **D3 a, b and f: not applied.** They edit `instructions/CLAUDE.md` and `agents/researcher.md`, and
  a decision relayed through MAIN is not the owner's consent for those.

## What it cost

- Eval and probe spend: about $40 of the $100 grant (council about $12, firecrawl about $27).
- Codex meter: flat at 5%.
- Rounds: plan 1; council 2 plus a follow-up batch; firecrawl 3.
- Two firecrawl authors: the first passed 300K tokens of context.

## What transfers

- **Measure overlap against the real tool descriptions,** not a bare model. Any MCP-backed skill should carry the server's instructions and tool descriptions verbatim in its fixtures.
- **Measure on the real consumer models.** Firecrawl's rows split by model (json across many pages: Opus passes unaided, Sonnet doesn't).
- **The orchestrator's write-guard hook blocks subagent Edit/Write in their own lane worktrees.** It keys on cwd, and authors fell back to Bash heredocs. Fix the hook or launch lanes with cwd in the lane worktree.
- **Scratch worktrees made by subagents can't be removed by them** (the hook plus the classifier). Brief them to use a plain directory copy, not `git worktree add`.
- **MAIN's address changed when MAIN was forked.** For about an hour, every upward message went to a stale socket and was held. Watch for a held-delivery notice as a sign MAIN moved.

## Scope brief proposals

None (both reviewers: no REVIEW.md change).
