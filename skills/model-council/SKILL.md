---
name: model-council
description: "Settle one bounded technical decision by debate between two real model calls, one Claude and one Codex: a blind first round, then exchange rounds in which each member answers the other's position until both hold the same disposition and action, or the council reports no consensus and the crux for the human. Use when asked for a model council, a second opinion from another model, or Claude and Codex to judge something independently; when reviewers or agents disagree on a contract, a reachable failure or a tradeoff; or when a Copilot or review claim stays unclear after checking the code and docs, such as a suspected false positive or a fix that may not be worth its complexity. Not for checking one claim or fix yourself (verifier agent), reviewing a diff or pull request (review), or reviewing a plan or spec (plan-review)."
---

# Model council

Role: orchestrator. Loaded once by the coordinating session (main or orchestration thread), which
runs the council; members never load it.

The council's result is the members' own: either both reach the same position, or the result is
`no consensus`, which is itself a finding for the human. The coordinator frames, dispatches,
tallies and verifies. It never synthesizes the answers, merges two actions, picks a winner or adds
a tiebreaker member. Skip the council for an obvious defect, a false positive one check disproves,
or a fact one lookup or test settles; product intent, credentials and authorization are questions
for the human, not for models.

## Procedure

1. **Pin the evidence.** One scratch directory per council, absolute paths. Write the packet: the
   exact question and candidate actions (always including no change), base and head SHAs, the diff
   with untracked contents for uncommitted work, call sites, contracts and docs with versions
   (quoted: members have no network), test results already run, and what is observed versus
   assumed. Both members get the same snapshot; hold the files unchanged until the council ends.
   Group claims that share code or a contract into one council. Leave your own preferred answer
   out.
2. **Choose two members.** Claude: a fresh subagent with explicit model `opus`, of a type without
   file-edit tools where the host has one; it still has a shell, so it is read-only by its prompt
   alone. Codex: `scripts/codex-member.sh` in this skill's folder, with an explicit high-capability
   model from the installed catalogue (`codex debug models` in codex-cli 0.160; never an Anthropic
   alias) and `--effort high`. Give each a focus (correctness and contract; simplicity and
   maintenance; or one narrow domain question); a focus is where to look, never an assigned
   verdict. Record each member's harness, model, effort and focus. If one provider is unavailable
   now, before the blind round, run two fresh Opus members and mark every result `(single-family)`;
   a member lost after launch is never replaced (step 7).
3. **Blind round (k = 0).** Fill the blind-round template in
   [member-prompt.md](references/member-prompt.md) per member. Launch both in parallel; neither
   sees the other's answer. Codex, as a host background task so its exit wakes you:

   ```sh
   <skill dir>/scripts/codex-member.sh <repo> <dir>/round0-codex.prompt.md <dir>/round0-codex.md --model <codex model id> --effort high
   ```

   It prints `MEMBER done|failed|timeout|malformed ... session=<id> ...`; keep the session for the
   next round. Save the Claude member's reply verbatim to `<dir>/round0-claude.md`.
4. **Tally the round** (k = 0 for the blind round):

   ```sh
   <skill dir>/scripts/tally.sh <dir>/round<k>-claude.md <dir>/round<k>-codex.md --exchange <k>
   ```

   It prints one line and you follow it: `consensus` (go to step 6), `exchange` (step 5),
   `no-consensus` (step 7) or `incomplete` (rerun the failed member once and tally again; still
   incomplete, step 7). Identical positions are consensus whether reached blind or through
   `agree`: the script decides identity, never you. The same disposition with a different action
   is not consensus, however close the wording. The round cap is `MAX_EXCHANGE_ROUNDS` there.
5. **Exchange round.** Fill the exchange template: each member gets the other's latest answer,
   reasoning and block, with every identifying detail removed (no model or vendor name, no counts,
   no hint, question or summary from you). Continue the same members: message the same Claude
   subagent (a fresh one gets its own previous answer too, if the host cannot continue it) and save
   its reply verbatim to `round<k>-claude.md`; rerun Codex with `--resume <session>` and the same
   model and effort, writing `round<k>-codex.md`. Then step 4.
6. **Verify a consensus.** Open the decisive citation each member gave and check it against the
   pinned code or docs. If one fails, the result is `no consensus: decisive citation failed`, with
   what you found; do not repair the members' reasoning or substitute your own citation.
7. **Report.** A member that failed, timed out, returned no answer block, or was not a real model
   call (your own guess, a role-play, a placeholder, a substitute launched after it failed) leaves
   the council `incomplete`, never a consensus, whatever the other member said.

   ```text
   COUNCIL: consensus | no consensus | incomplete [(single-family)]
   Question: <one line>
   Members: <harness, model, effort, focus per member>; rounds: blind + <k> exchange
   Consensus: <disposition; action; decisive citations, verified>
   No consensus: <per member: final disposition, action, decisive citation and crux, quoted from its block>
   Default until the human decides: the pre-council state (<the code as pinned>)
   Incomplete: <which member, what happened, what was rerun>
   ```

   Keep only the lines that apply. Without a consensus (no consensus or incomplete) the default is
   the pre-council state, said so even when it matches one member's action; never a recommendation
   of yours. One member's answer is reported as that member's. An action class that needs the
   owner's approval still does.

## Rules

- A council result is advice: not permission to post, merge, resolve a thread or widen scope.
  Hand it back to the workflow that asked.
- If the code changed during the council, rerun the members whose evidence it touched.
