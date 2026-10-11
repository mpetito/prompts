# Pull-request digest (2026-10-11)

**Skill name:** `pull-request`. Alternatives: `pr-feedback` (too narrow), `own-pr`.
**Role (worker):** loaded by the session or subagent that owns a pull request, Claude or Codex;
under about 120 lines. It answers review feedback on your own PR (core), opens or updates a PR,
and posts a review of someone else's PR once the owner approves the text.
**Skill or agent: skill.** No agent definition.
- In real transcripts, a PR feedback loop's own `gh` traffic was small. Per PR it took a median
  of 3 calls and about 1.4k tokens (max 32 calls, about 8.3k tokens), and 3.8-8.3% of a main
  session's tool output. Seven transcripts covered 60 PR episodes.
- The heavy part is fixing and verifying, which belongs to whoever owns the code.
- The probe showed no bloat either.
- Revisit only if a build shows the loop crowding out the caller.

Sources, all in the private store: transcripts (S, typed or queued owner turns only), GitHub (G,
read-only, with a human-likely or agent-likely tag per item), Codex sessions (X), the archived seeds
and their reviews (seeds), and the probe (P). The probe gave unaided Opus 5.5 (with the owner's
CLAUDE.md, as in real use) and Codex gpt-6-astra one text-in/text-out run each on three fictional
scenarios, for $0.76 and 184k Codex tokens.

**Read the evidence honestly.**
- The owner rarely corrected an agent's PR handling. Most thread etiquette is a convention the
  owner wrote into orchestrator briefs, not a habit corrected turn by turn.
- Of 718 thread replies under the owner's login, every one is agent-written.
- The PR-body style rests on 8 bodies the owner wrote by hand before agents existed, plus the
  owner deleting filler from agent bodies. The owner never complained about body style.
- So every rule below needs a failing trap before it ships. "Untested" means the probe did not
  cover it, and the trap decides.

## Proposed rules

### Core: answering review feedback on your own PR

| # | Rule | Owner's evidence | Unaided model (P = probe, seeds = archived review) | Home |
| --- | --- | --- | --- | --- |
| F1 | A claim that stays ambiguous after you check the code and docs goes to model-council (or the owner); don't decide it alone. Leave its thread open until it is settled. | Agreed scope item 1; "you can also override / defer or decline its feedback" (S3, 2026-10-02T15:19:59Z); "Never merge around an open disagreement" (S2 brief) | P: both declined the tradeoff thread alone. Opus wrote "I didn't call in other models on this one", although CLAUDE.md already carries the rule. | skill step linking model-council; see D2-c on the CLAUDE.md line |
| F2 | Reply only after the fix is pushed, citing the pushed SHA; reply before you resolve, never resolve silently. | Orchestrator rule given to a worker: "reply on that thread with the fix SHA and resolve it" (X); 489 of 718 replies cite a SHA (G) | P: Codex posted "I propose… not applied yet" replies before any fix. Seeds: models call resolve alone. | skill (+ script, D2-b) |
| F3 | Resolve policy (D2-a): reply to every thread. Resolve threads you fixed, and Copilot threads you declined with evidence. A human reviewer's disagreement or deferral stays open for that reviewer. | "Resolve every comment: fix it, or reply with the reason it doesn't apply" (S2 brief); 274 threads were resolved with no reply and 275 left open with no reply (G, mostly 2025) | P: Opus resolved all 4, including the contested one; Codex resolved only the 2 it fixed | skill |
| F4 | Read the review bodies too, including Copilot's collapsed "suppressed" section. An empty thread list is not "no feedback"; a body-only finding gets no new public comment. | seeds (pr-feedback); no owner quote | untested | skill + fetch script |
| F5 | GitHub's `isOutdated` means the line moved, not that the point was addressed; re-check it at the head. | seeds (pr-resolve review) | untested | skill |
| F6 | A confirmed defect is a class: find and fix its siblings in scope, not just the flagged line. | seeds (pr-feedback); "Not properly scoped." (G, owner review comment) | untested | skill (the proof half stays in review) |
| — | Verify each claim against the code and docs before accepting it; reject with the evidence. | "if the docs contradict the reviewer, say so in the PR body with quotes" (X) | P: **not a gap**. Both refuted the false claim from the vendored code. | CLAUDE.md (docs first); one line in the procedure, no trap |

### Opening or updating a PR

| # | Rule | Owner's evidence | Unaided model | Home |
| --- | --- | --- | --- | --- |
| A1 | Body, kept short (D2-d): the motivation first, in plain prose; then the changes grouped by purpose; then validation that lists only what was actually run, with results, and says in the body what was not run. No Summary boilerplate, no filler lines. | 8 hand-written bodies, about 650 characters median: "Chrome inexplicably adds extra whitespace … Adding a border … appears to resolve the issue." (G, 2017), then bullets, then a manual-check list. The owner deleted an agent filler line 32 s after a PR opened (G). Agent-era bodies have a median of 3.9k characters. | P: Opus put "tests not run" in the chat only, not the body; Codex wrote prose, didn't group, and gave a non-conventional title | skill (short rule section, not a procedure) |
| A2 | Updating a PR: re-check every factual line against the final head, and replace Validation rather than appending to it. | Orchestrator to a worker, 6 times: "refresh the PR body's validation"; "a stale PR body" (X) | untested; seeds call it the most fragile path | skill |
| A3 | Closing keywords fire on ordinary prose: write `Closes #N` only when merging proves the fix, otherwise `Refs #N`. | seeds; the owner's own bodies use "Closes #N" deliberately (G) | untested | skill, if its trap fails |
| — | Branch, commit and PR policy come from the project's CONTRIBUTING.md. | "the commit skill should look for a contributing file" (S5, 2026-09-20T14:42:01Z) | P: both followed CONTRIBUTING.md when present, so not a gap | one pointer line; project-setup owns the file |
| — | No AI attribution. | Trailers stripped (S6, 2026-10-11; G, 2026-09-06) | P: neither added any (CLAUDE.md loaded) | global CLAUDE.md only |

### Reviewing someone else's PR

| # | Rule | Owner's evidence | Unaided model | Home |
| --- | --- | --- | --- | --- |
| R1 | The review skill makes the judgment. Then show the exact review text and post only after the owner approves that text, as one review: summary plus inline comments in a single API call, event COMMENT unless the owner picks one. | Agreed scope item 3. The owner's own review voice is short inline questions and directives ("Why not use zod here?", "Not properly scoped."), with empty-body approvals (G). | P: neither offered a gated post. The code-review plugin posts without asking and adds an attribution footer. | skill step linking review |
| R2 | Your own account can't approve a PR it opened: post the verdict as a comment. | "I commented that I approved it since I cannot approve my own PRs" (S1, 2026-09-27T16:46:04Z); "Approved!" (G) | untested | skill, if its trap fails |

### Dropped or owned elsewhere

- Waiting for CI or Copilot belongs to the `pr-watch` agent.
- Review judgment belongs to the `review` skill, and "trust your callers" (declining blanket null
  checks) to `code-style`.
- `pr-consolidate` is dropped.
- The seeds' employer branch patterns, work-item rules, time logging, reply templates and
  "ask before every reply" gate are stale. The owner never asked for a gate on their own PR (D2-e).
- Two seed questions have no owner evidence and need none: a pointer comment after a body update,
  and one issue per deferral.

## Scripts (D2-b)

Of the 9 pr-scripts, keep two in PowerShell with their offline mocked-`gh` Pester tests:
- a trimmed `Get-PrFeedback`: threads and review bodies, paginated, and it errors when a fetch
  fails;
- `Resolve-PrThread`: reply, then resolve, in that order.

Replace the rest with one documented `gh` call each, or drop them. Get-PrCheckFailures belongs to
pr-watch.

The owner's machines have pwsh, but Copilot hosts may not, so the skill also names the raw
`gh api graphql` call as the fallback.

## The plugin comparison (bar item 4)

- No plugin answers review threads, so F1-F6 have no competitor.
- A1-A3 are compared against `commit-commands` (commit-push-pr). Its body is "Summary + Test plan"
  plus an attribution footer.
- R1 is compared against `code-review` (which posts without asking) and `pr-review-toolkit`
  (which never posts).
- How the plugins are staged for the run is decision D1.
