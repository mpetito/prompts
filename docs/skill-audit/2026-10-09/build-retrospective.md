# Orchestrated build retrospective: sessions 2026-10-02 to 2026-10-09

Sources: the two coordinator transcripts (A: 94 MB, B: 45 MB), 311 subagent transcripts, the
149 lane folders under `.orchestration/lanes/`, GitHub PR data, Codex session logs. Method: the
transcripts were condensed and split into 25 chunks, each read in full by a Sonnet reader with a
fixed findings contract; a 26th agent analysed the lane artifacts; I read every owner message,
all reader outputs, and computed the numbers below directly from the JSONL. Per-chunk findings
stayed with the build, outside this repository.

## 1. The build in numbers

| Measure | Value |
| --- | --- |
| Wall clock | 7.5 days, two coordinator sessions (A from 10-02 13:28, B from 10-03 20:09) |
| PRs merged | 173 (1 closed unmerged). Median open-to-merge 0.3 h, p90 1.2 h |
| Code | ~155K lines of TypeScript, ~10K lines of docs/specs, 515K lines changed across PRs |
| Subagent launches | 311 (236 Opus, 75 Sonnet) plus 947 `SendMessage` resumes; 38 Codex lanes, all before 10-04 |
| Coordinator context | Median 517K tokens per call (A), 493K (B); p90 845K; 14 compactions |
| Token volume | Coordinators: 8.6B cache-read tokens. Subagents: the two largest ran 1,258 and 1,428 turns (both eval lanes) |
| Estimated list-price equivalent | ~USD 14K (coordinators ~5K, subagents ~9K). Estimate only: assumed per-token prices, and the account is on a plan, so the real constraint was the limits |
| Limits hit | Codex weekly meter 100% by ~10-03 evening (173 Codex sessions in two days, then 12 in five days). Claude 5-hour limit 10-04 04:08; weekly limit 10-04 07:30 → 10-05 18:16 (35 h, both coordinators dead) |
| Idle gaps > 30 min between coordinator turns | A: 13 gaps, 66 h total. B: 17 gaps, 74 h total (both include the 35 h limit outage and a 20 h owner-away gap on 10-07/08) |
| Owner messages | A: 112 (48 on day 1, then 2–10 per day). B: 9. Owner asked "what do you need from me?" or equivalent 8 times; warned about context limits 4 times; ran `/compact` 6 times |
| Lane reviews | 126 lanes with verdicts: 67% changes-required on round 1 (91% and 56% in the two largest milestones); mean 2.1 rounds; 13 lanes at 4+ rounds; longest 8 verdicts on one lane and 12 fix rounds on another |
| Review findings | ~1,087 across 175 review files: ~289 missing or surviving-mutant tests (27%), ~221 doc/code mismatch (20%), ~77 inaccurate comments. Only 3 of 175 reviews raise over-engineering |
| Blocking `AskUserQuestion` calls | 2, both in the first hour of day 1. The no-blocking rule held after that |
| `TaskStop` calls | 34, almost all stale CI/gate watchers after a head moved |
| State file | `.orchestration/state.md` grew to 129 KB; ~1,600 write commands and 29 backups across the build; the RESUME section alone is 135 lines |

## 2. What worked (keep, and say so in the skills)

1. **Adversarial Opus review with planted mutants found real defects, first pass, in most code lanes.** Six examples between 10-03 and 10-07: an edge function using syntax its runtime rejects, which would have failed every API request; a token consumed without its claim attached, found independently by two reviewers; a regex HTML check that a real parser bypassed in 15,302 of 40,000 fuzz cases; a check-then-act race and a policy-condition hole in an allowlist; safety thresholds that failed open when injected; a dialog that remounted so Enter could publish. The lane data agrees: no lane was abandoned, and round-2 approval is the norm.
2. **The kickoff model council** (two model families per lens, pinned SHA, citation required, Codex fact-check batches) found three product-blocking constraints from third-party services in 14 minutes, before any code.
3. **Merge mechanics were reliable.** Approval as a commit status on the exact head, `--match-head-commit`, the carry-over check (`^1` = approved head, `^2` on main, empty `--remerge-diff`), `land.sh`: 173 merges, zero bypasses, zero AI-attribution leaks, and no re-review for clean main merges.
4. **Compaction recovery through the state file worked every time.** 14 compactions, and no reader found a wrong SHA or lost lane afterwards; the first post-compaction action was always `date -u`, `git status`, `gh pr list`, `pgrep`.
5. **Pre-writing the next brief while a gate runs.** Lanes started within a minute of the prior merge in every chunk that measured it.
6. **Cheap, bounded verifier agents** (20–46K tokens, about a minute) for carry-over proofs and fact-checks. They twice caught the coordinator recording more than the owner had approved (10-07 11:58, 10-08 18:15).
7. **Resuming the same reviewer for deltas** cost 13–24 s for comment-only diffs, versus a fresh 30-minute review.
8. **Stop rules in briefs.** A Codex lane reported `STATUS: blocked` instead of weakening a check; another lane stopped on missing prerequisites; two live eval rounds halted themselves on regressions at cents of spend.
9. **Sonnet authors with Opus review**, once the owner suggested it on 10-05: the first such PR landed in 9 minutes, and four later lanes, including a setup rework, shipped on Sonnet authors.
10. **Consumer-first spec review** (B reviewed A's spec before four web lanes built on it) caught contract and safety gaps up front.
11. **Classifier and permission denials were respected**, never laundered, and disclosed. Cost was paid in time (see 3.6) but not in trust.
12. **When the owner was asked with defaults, decisions were fast**: 7 items answered in 3 minutes (10-03 12:20), 5 in 2 minutes (10-04 01:56), the rulings batch of 10-07 11:55. Question quality, not owner availability, decided whether a question cost minutes or days.

## 3. What did not work, by cost

### 3.1 Effort went where the owner could not see it (largest cost)

The owner said it three times, escalating: 10-03 20:01 "you could have a codex lane implementing the UI and API at this point"; 10-05 20:23 "When will I be able to register and try using the dev site?"; 10-06 10:11 "I need to be able to observe your progress so I know you're not wasting effort." Meanwhile:

- The two most expensive subagents of the build (1,258 and 1,428 turns) were eval lanes, and A spent the night of 10-05/06 on performance, scoring and eval rounds after the dev-first steer.
- On 10-07, A ran about eight serial spend and queue lanes with no visible dev change; the owner then cut the running total: "Why do we need a running total at all? We have a queue." and "Honestly, you've overcomplicated a lot of this."
- On 10-08: "You are again OVER complicating this entire application, which doesn't even work end to end, but you're continuing to add tons of extra guardrails and policies that can all come _later_." One automated-reporting PR had been built, reviewed through 5 rounds and CI-green before being closed. A stored counter PR went the same way.
- The lane analysis found a stored pending-items ledger was carried through three milestone briefs before the owner cut it, and the build's simplification analysis lists 12 further cuts. Reviewers never challenged necessity: 3 of 175 reviews mention over-engineering, while 161 of 175 hunt mutants.
- The first product-lane coordinator (B) started only after the owner suggested it, 3 minutes after "feel free to spawn a clone" (10-03 20:06). Build lanes also sat idle 3.6 h on day 1 waiting for a spec PR that the approved plan said they did not depend on.

The memory file `owner-prefers-simplest-design` existed from day 1 and was updated three times; it did not change behaviour. The owner's rulings reversed coordinator recommendations at least four times on day 1 alone, each time toward the simpler mechanism, and an owner-facing taxonomy went through 3.5 h of council and review before the owner saw a sample and rejected the register ("reads like a manual").

### 3.2 Owner decisions were asked badly and waited on too long

- Asks were buried at the bottom of long status posts and restated verbatim: ~25 to 45 identical "Waiting on you" footers per chunk; 14 repeats of one question in a single night (10-08). The owner had to ask "brief me on what needs my decisions" or similar 8 times, and on 10-06 09:55: "You'll also have to remind me of the context."
- Coordinators idled on questions that had defaults: A was fully idle 06:20–09:55 on 10-06 ("Nothing else moves until you answer"); B had no lane running for 2 h 22 m on 10-06 waiting on six decisions whose stand-in default was already in memory; B waited ~40 h on three questions (10-07 04:07 to 10-08 20:48); A stopped for ~20 h on 10-07 with five decisions and nothing in flight. When the answers came, they matched the defaults almost every time.
- Approvals already given were re-requested (10-03 20:01 "I'm pretty sure I already approved").

### 3.3 Both metered budgets were exhausted within 36 hours each

- Codex (the plan's primary implementer) hit 100% by the end of 10-03. Every lane from the second milestone onward ran on Claude Opus, which was never the plan.
- The Claude 5-hour limit hit at 04:08 on 10-04 while five lanes were finishing; nothing woke the session for 41 minutes after the reset. B then launched seven more Opus agents after the warning, and three Opus implementers were mid-edit when the weekly limit killed everything at 07:30. 35 hours lost.
- No turn read either meter before a fan-out. The orchestration doc's "keep 20% back" rule was not operationalised.

### 3.4 The coordinator's own context was the cost and quality driver

- Median context per call was over 500K tokens and p90 845K, so every turn re-read half a million tokens. The owner, not the coordinator, noticed the limit approaching (4 warnings, 6 manual compacts).
- Sources: 4.2 MB of Bash output in A alone (62 results over 8 KB); 1.05 MB of the coordinator's own prose (8–15 line status posts per turn, about 60 in 5 h while the owner was absent); resumed reviewers at 500–800K tokens; hand-rolled state-file surgery (~1,600 write commands, several corrupting the lanes table); replies to interim "completed but not reported" notices; ~120 harness notifications per chunk; a `to-a.md` watcher that woke on the coordinator's own writes a dozen times.
- The coordinator did the git plumbing, the full check suite after every round, merges, conflict resolution and deploys inline rather than through scripts or `test-runner`.

### 3.5 Recurring mechanical churn

- **`docs/decision-log.md` conflicted on nearly every merge** (every reader chunk reports it: 6–20 hand or script resolutions per chunk; one PR re-merged 3 times, another had 4 heads). Each costs a re-merge, a carry-over comment and a fresh 15–20 minute CI run.
- **Estimated timestamps** were written and then `sed`-corrected after `date -u`: 9–24 corrections per chunk early on, placeholders like "13:1xZ" late on. The memory rule from 10-04 did not stop it; B's 10-03 promise did not either.
- **Serial merge train with a 15-minute CI per hop**: four approved lanes sat unmergeable for hours behind one slow lane (10-06), and one PR took 2 h 15 m from PR to merge. CI's 15-minute timeout cancelled passing runs until it was raised; the lint job ran out of a 4 GB heap twice.
- **Background jobs killed by the 30-minute default timeout** (a Codex round and a 60-minute live eval), `pkill -f` killing the coordinator's own shell twice, `/tmp` inode exhaustion (436K files in a scratchpad) breaking B's commits, `git worktree remove --force` destroying live evidence once, 34 stale-watcher `TaskStop`s.
- **Every lane got the same ceremony regardless of size**: a two-env-var change got an Opus implementer plus an Opus adversarial reviewer; docs-only PRs went author → fact-check → round 2 → delta → merge-main → carry-over; a pure helper took 6 review rounds, three of them for a comma, a `startsWith` and follow-up nits.

### 3.6 Review loops ran long for the wrong reasons

- Mean 2.1 rounds, 10% of lanes at 4+, one lane at 8 verdicts over 3 h 14 m (~600K implementer tokens, ~350K per reviewer per round). The coordinator wrote "fourth fix round, one more than my usual limit" and carried on; the three-round escalation rule was never applied.
- Most rounds were test gaps, not product defects: "nothing is broken today", "No code defects", 27% of all findings are missing or surviving mutants that the brief's own "one mutant per invariant" rule already requested. Round 1 fixes patched the cited example and the reviewer found the next member of the class; the "close the whole class" instruction only arrived at round 3 or 4 (four lanes).
- Two independent Opus reviewers on every high-risk lane often returned the same blocker; the lane analysis recommends measuring unique-finding overlap before keeping the second seat.
- Reviewer-suggested additions grew scope the owner later cut (alarms 2 → 6 across three PRs; a multi-step transaction for a rate window).

### 3.7 Coordinator-authored rulings and briefs were wrong often enough to cost rounds

Every reader found 3–7 instances per chunk: a brief claiming a TSDoc that did not exist; a ruling on a wrong premise that cost 3 author and 3 review rounds; a counter ruling reversed after the author found the function it relied on returns a boolean; a "defer" ruling that would have queued 1,000 items on a bad key; a dead-letter queue removed minutes after the owner approved the spec with it; a wrong build-tool option claim. Rulings cited memory rather than the contract line or vendor doc. The coordinator also hand-edited code under time pressure and introduced defects (a lint complexity failure, a dev stack synthesised into the prod account, a `git checkout <file>` rule breach, 82 failing tests after a hand-spliced diagnostic).

### 3.8 "Complete" was declared on machine evidence, and the owner found the gaps

10-06 21:00 a dev slice was declared complete with its acceptance criterion met by synthetic users. 21:26 owner: "I still cannot register." 23:01 "Saved and errored again." 10-07 00:42 "The ux for setup is atrocious. Save and next buttons? Two sign out links in the footer? ... Dumps you into a page with nothing ...?" B had rebuilt the spec's six-step wizard against the owner's earlier "one long continuous form" remark, and the brief did not carry the minimal-onboarding rule. The diagnostics then logged `reasons: [Array]`, wasting the owner's retry.

### 3.9 Blocked by things only the owner could do, while the owner was away

An orphan `vite preview` left by an implementer held the Playwright port for ~30 h; the classifier forbade killing it and the kill command was reprinted in ~28 messages. Cloud SSO device codes expired twice before the owner returned. Notification-subscription confirmation links were consumed by unauthenticated unsubscribes twice before the API path was used.

## 4. Prioritised actions

Ranked by impact divided by effort. Each names where the rule lives.

### Tier 1: changes the outcome

1. **Visible-first scheduling, as a standing rule in `agent-orchestration` and `docs/orchestration.md`.** Every status to the owner leads with the shortest path to something they can click on dev. Lanes are ordered by distance to the owner-visible slice; anything not on that path (evals, ledgers, counters, alarms, hardening) is capped at one review round or parked until the owner opts in. Before briefing any mechanism the spec prescribes, challenge it: name the platform primitive that already gives the property (queue depth, TTL, IAM, a conditional write), and propose the cut to the owner in one line instead of building as written. Evidence: 3.1.
2. **One decision queue file with defaults that apply themselves.** Replace the per-turn "Waiting on you" footer with `.orchestration/decisions.md`: one item per line with what, why now, what it blocks, the default, and the time the default applies ("applies at 18:00Z unless you object"). Post the digest once at the top of a message, and again only when it changes or the owner returns. When the owner is away and the item is not owner-before by the approval matrix, apply the default at the deadline and log it. The owner answered defaults within minutes every time they were offered; the build lost about 70 h of coordinator idle time waiting for answers that matched the defaults. Lives in `agent-orchestration` §3 and the state-file reference.
3. **A budget check in the wake loop.** Each wake reads both meters (Codex `used_percent` from the session log, Claude usage from the harness) and records them in the state file. Above 70%: authors go to Sonnet, second reviewers are dropped, live eval rounds pause. On a limit notice: write the resume point, record the reset time with `date -u`, and arm a timed wake (`ScheduleWakeup` or a background `sleep` to the reset) so finishing lanes are serviced at reset. Never launch a fan-out within 3 h of a limit warning. Lives in `agent-orchestration` §2 and §9, and `herdr-delegation`'s meter note. Evidence: 3.3.
4. **A context diet, enforced by tooling rather than advice.** The `agent-orchestration` §7 guidance existed and did not hold. Mechanise it: a `state` helper that appends dated lines and edits one row (interpolating `date -u` itself); scripts for land, deploy, gate-watch and finish-lane (below); hand-backs capped at 40 lines by the report contract with the long form in a file; no reply to interim notifications; status posts to an absent owner limited to one line per change; fresh reviewer with the review file as input once a resumed reviewer passes about 300K tokens; `test-runner` for the check suite instead of inline runs. Target: median context under 250K. Evidence: 3.4.
5. **Owner-acceptance gate before "complete" on anything owner-facing.** A slice is complete only after one real browser pass through the owner's entry path on dev (sign-in, setup, first action) and a friction check against the minimal-onboarding memory (one primary action, short copy, never an empty page). For owner-facing content (taxonomy, copy) show the owner 8–10 samples before any pipeline runs. Lives in `agent-orchestration` §6 and the UX lane brief in `agent-briefs`; could be a short `owner-acceptance` checklist skill. Evidence: 3.8, taxonomy 10-03.

### Tier 2: removes recurring churn

6. **Make `docs/decision-log.md` conflict-free**: per-entry files under `docs/decisions/` with a generated index, or a `merge=union` attribute for the append zone. Removes dozens of re-merge and CI cycles. Pair with CI test sharding and a merge order rule so approved lanes do not stack behind one slow contract lane (cap the root lane at one fix round before escalation).
7. **Ship the operational scripts as a project skill with hooks** (project-level, or a generic `orchestration-ops`): `state` helper (timestamps and single-row edits), `land.sh` (prints `mergeStateStatus`, unresolved threads and failing checks on BLOCKED instead of looping), `watch-gates.sh` keyed to the PR number and exiting when the head moves, `deploy-dev.sh <sha>` (diff, deploy, smoke check, archive, one-line summary), `finish-lane.sh` (rsync `.orchestration/tmp` before `worktree remove`), a `codex exec` launcher template with a 2 h timeout and credential stripping, a `to-a.md` watcher that ignores the writer's own lines. Hooks: refuse `HH:MMZ` or `HH:xZ` strings in `.orchestration/` files unless produced by the helper; block `pkill -f`; block `git worktree remove --force` without the archive step; warn when `/tmp` inode usage passes 70%. The build already proved the pattern: every rule that became a script (carry-over check, land.sh) held, and every rule that stayed in memory (timestamps, simplest design) did not.
8. **Size the review to the lane** (`agent-orchestration` §5, `review`, `agent-briefs`): docs-only and mechanical lanes get one fact-check pass; only safety, auth, deletion, IAM and data-integrity lanes get adversarial review plus delta. After round 2 only blockers reopen; should-fix test gaps are batched into one commit and merged on CI without a delta review; findings carry `blocking | follow-up | nit` tags; mutants are required only for the invariants named in the brief; a second independent reviewer only on high-risk lanes, and only while unique-finding overlap justifies it. Enforce the three-round escalation that already exists.
9. **Add an over-engineering lens to the reviewer brief** ("which code is not required by an acceptance criterion or a ruling?") and a "simplest mechanism" section to the author brief listing each mechanism not demanded by an AC. Evidence: 3 of 175 reviews, the pending-items ledger, alarms 2 → 6.
10. **Leave-no-process and shared-resource rules in the standing block of `agent-briefs`**: kill every server or watcher you start and record its PID; one port per lane from the shared-machine table; TMPDIR on disk. Pre-authorise the coordinator in the approval matrix to kill listeners started by its own lanes, so a stray preview never costs 30 h again. Ask for credential renewals and subscription confirmations only while the owner is present, and confirm subscriptions through the API.

### Tier 3: brief and ruling hygiene

11. **Premise check before a ruling or brief claim**: any statement about existing code or vendor behaviour is verified by reading the file or citing the doc line, or labelled a hypothesis; rulings that add a mechanism go to a reviewer before the implementer, or are marked provisional; no Codex or Opus round is launched while the owner is mid-discussion on the same design; a ruling that removes something the owner just approved is re-confirmed first. Lives in `agent-orchestration` §4 and `agent-briefs` principle 3/4.
12. **The coordinator does not hand-edit code.** Resume the idle author or launch a Sonnet fixer; anything beyond a comment or log line gets a delta check. Evidence: 3.7.
13. **Brief template additions** (`agent-briefs`): pre-granted standard slots (transport, a database mock, exports, test-only lint bans) so authors stop asking "may I?" (8 of 8 granted); a prerequisite check listing each upstream item with its merged SHA; base SHA as a checked field rather than prose; a class-closure instruction in every round-2 fix note ("list every site in this class by grep, not memory"); result file mandatory for every lane; `STATUS` as line 1 of fix-round reports too; the standing environment facts (known load-timeout tests, `CI=true`) in a generated block.
14. **Owner-ask format**: a two-line stake, the default and the recommendation in the first sentence; never a bare label; never relay a reviewer or author label to the owner without opening the artifact (two content-safety flags were unassessed placeholders).

## 5. Skills: what to change and what to create

| Skill or doc | Change |
| --- | --- |
| `agent-orchestration` | Add: visible-first scheduling; decision queue file with default-after deadlines; owner-away rule (ask once, apply the default); budget meter in the wake loop with the 70% switch and limit-stop checklist; review sizing by risk and the hard three-round rule; context targets with the helper scripts named; "do not reply to interim notifications"; "the coordinator does not edit code". Trim §7 prose in favour of the tooling. |
| `agent-briefs` | Add: simplest-mechanism section; premise-check line; pre-granted slots; prerequisite table with SHAs; class-closure in round-2 fix notes; leave-no-process and port lines in the standing block; UX lane checklist from the owner memories; result file and `STATUS` on every round. |
| `review` | Add the over-engineering lens; severity tags; mutants limited to named invariants; test-gap severity rubric (should-fix unless a safety invariant or auth boundary). |
| `herdr-delegation` | Make the meter read a per-wake step with a recorded value; add the `codex exec` launcher template with the 2 h timeout. |
| `docs/orchestration.md` | Decision-log split; merge-order rule; visible-first priority; the operational scripts as the documented path; the port and process rules; credential-renewal and subscription-confirmation timing. |
| New: `orchestration-ops` (project-level or generic) | The scripts and hooks in action 7. This is the highest-leverage new artifact: the build shows that mechanised rules held and remembered rules did not. |
| New: `owner-acceptance` (small) | The pre-deploy owner-path run and the friction checklist; the "sample before pipeline" rule for owner-facing content. |
| New: `session-retro` (optional) | The condense script and reader brief used for this analysis are reusable: condense JSONL, chunk, fan out Sonnet readers with a fixed contract, compute the metrics. Worth keeping if retros like this one will recur. |

## 6. Two meta-lessons

- **Mechanise, don't memorise.** Every rule that became a script or a check held across 173 merges (carry-over, head-match, attribution grep, land.sh). Every rule that lived in memory or a skill paragraph decayed under load within hours (timestamps, simplest design, 40-line hand-backs, three-round cap, "sweep the meter"). Hooks and helpers are the fix, and they are cheap.
- **The owner's words were the best signal and the least used.** The owner's steer was consistent from the first hour (simplest design, visible progress, platform primitives, decisions by number with defaults). The expensive mistakes were each a case of the process optimising for its own rigour (mutant counts, dual reviews, spec fidelity) over the owner's stated priorities. The decision queue, the visible-first rule and the owner-acceptance gate all exist to put those words back in front of the coordinator on every turn.
