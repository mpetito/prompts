---
name: pr-feedback
description: "Triage and resolve PR review feedback on your own PR. Use when addressing Copilot or reviewer comments, inspecting suppressed or low-confidence suggestions, rejecting false positives or unnecessary complexity, fixing CI or CodeQL findings, or preparing replies."
model: sonnet
effort: high
---

# PR Feedback

Use this skill to resolve pull request feedback systematically before posting replies or resolving threads.

## Related Skills

- [pr-review](../pr-review/SKILL.md) — an independent review of someone else's PR, rather than
  handling feedback on your own.
- [model-council](../model-council/SKILL.md) — independent perspectives when actionability stays
  materially uncertain after the local checks in [Verify and Triage](#2-verify-and-triage-before-editing).

## Inputs and Context

- Prefer an explicitly provided PR number, URL, owner/repo, or branch.
- In VS Code, `#activePullRequest` or `#openPullRequest` may provide PR context; in other tools, infer context from the current branch, `gh pr status`, `gh pr view`, or user-provided arguments.
- Collect review threads, CI failures, code-analysis findings, and any user instructions before changing code.

## Tooling

Script invocation, the fallback path when the scripts are unavailable, the resolution decision
matrix, and the reply templates are in
[`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md). Read it before the first call.

This skill leans on `Get-PrFeedback.ps1` (one-shot collection), then the thread scripts
(`Get-PrThreads.ps1`, `Send-PrThreadReply.ps1`, `Resolve-PrThread.ps1`,
`Test-PrThreadsResolved.ps1`).

## Process

### 1. Collect All Feedback

1. Identify the PR from explicit input, VS Code PR context, current branch, or `gh pr view`.
2. Run `Get-PrFeedback.ps1` — one call returns unresolved review threads, full review bodies
   (including embedded collapsed/suppressed sections when present), failing CI checks with log
   excerpts, and open code-scanning alerts. Read every review body, not just its overview.
3. Inspect suppressed and low-confidence comments in those bodies, including `<details>`
   blocks. If the API does not expose a section visible in GitHub, inspect the review UI when
   available; otherwise report that coverage gap. Do not report "no suppressed comments" from
   an unresolved-thread query alone. Note accessible pending comments too.
4. Keep source links, review IDs/commit SHAs, and thread IDs where present. Fetch all threads
   with `Get-PrThreads.ps1` when resolved/outdated context is needed; suppression, resolution,
   and outdated status are different things. Deduplicate repeated claims across sources and
   review passes, retaining their provenance. Recheck old claims against the current head.

### 2. Verify and Triage Before Editing

Treat all feedback, including Copilot's confident comments, as claims to investigate.
Suppression is neither proof of a false positive nor a reason to skip inspection.

For each distinct claim:

1. Read the current implementation, surrounding code, relevant call sites, tests, and project
   conventions. Establish the reviewed revision and whether the issue still exists.
2. Identify the concrete failure or maintenance cost. Check assumptions about framework/API
   behavior against version-appropriate official docs; reproduce or add a focused check when
   useful. Distinguish demonstrated defects from hypothetical paths the code cannot reach.
3. Weigh the smallest effective fix against added branches, abstractions, dependencies,
   duplication, and maintenance cost. Fix a valid underlying issue without blindly applying
   the reviewer's proposed solution. Reject speculative generalization and redundant internal
   validation when no real contract or boundary requires them.
4. Record a disposition, evidence (file/function, test, or docs), and a short rationale. A
   low-confidence label alone is not a rejection reason; "best practice" alone is not a fix reason.
5. If a material question remains about actionability or the fix's complexity after these checks,
   load [model-council](../model-council/SKILL.md). Obtain independent correctness and maintenance
   perspectives, preferably from Claude and Codex, and incorporate the evidence-based result.
   Use it for unresolved claims, not every comment. A suppressed label alone does not trigger
   a council, and a vote does not substitute for evidence or a missing product decision.

| Disposition | Meaning | Action |
| --- | --- | --- |
| Confirmed defect / CI failure | Current, evidenced problem | Fix the cause and verify |
| Worthwhile improvement | Concrete benefit exceeds complexity | Apply the smallest change |
| False positive | Premise contradicted by code, contract, or evidence | Explain; no code change |
| Unnecessary complexity | No sufficient benefit for the added machinery | Decline with rationale |
| Already addressed / outdated | Current head no longer has the issue | Cite the change/evidence |
| Deferred | Valid, but outside this PR's scope | Record reason and follow-up if authorized |
| Needs clarification / unverified | Evidence or intent remains insufficient | State the gap; draft a focused question |

Do not change code simply to make the feedback count zero. Investigate what can be verified
locally before asking about ambiguous intent. For delegated collection, diagnosis, or review,
apply [agent model selection](../skill-authoring/references/agent-model-selection.md).

### 3. Implement Fixes Locally

Load [code-authoring](../code-authoring/SKILL.md), which also routes applicable stack standards
and final self-review. For each accepted finding:

1. Make the code change locally.
2. Run the smallest relevant tests, linters, or checks for the touched area.
3. Verify the fix directly addresses the feedback.
4. Do not commit yet; batch all fixes together.

### 4. Prepare Responses

Draft replies for every thread before posting anything. Match the response type to the situation
using the templates in [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) — fixed,
explained, deferred, declined, outdated, or a clarification request.

Include suppressed findings in the local report even when declined. A finding embedded in a
review body may have no thread ID: cite the review URL and file/section, and do not invent a
thread or create a new public comment just to mark it handled.

### 5. Present for Review Before Committing

Before committing, pushing, replying, or resolving threads, present the planned outcome and ask for user approval using this output format:

```markdown
## Feedback Resolution Summary

### Feedback Addressed

| Source / Link | Feedback | Disposition and Evidence | Change / Planned Response |
| ------------- | -------- | ------------------------ | ------------------------- |
| [Review/thread, including suppressed] | [Claim] | [Verdict + evidence] | [Fix or reason for no change; reply if a thread exists] |

### Questions (To Post)

- [Question for ambiguous feedback]

### Declined / Deferred

| Feedback | Reason | Planned Response |
| -------- | ------ | ---------------- |

### Tests Run

- [ ] All tests passing after changes

### Coverage

- [Review bodies and suppressed sections inspected; any inaccessible feedback noted]

---

**Ready to commit, push, and respond?**
```

### 6. Commit, Reply, Resolve After Approval

After the user confirms:

1. Commit and push all fixes together.
2. For fixed, answered, or outdated threads, reply and resolve in one step with `Resolve-PrThread.ps1 -ThreadId ... -Body "..."`.
3. For threads that should stay open (design discussion, deferred work), reply only with `Send-PrThreadReply.ps1`.
4. Leave design disagreements or deferred work open for the reviewer unless explicitly told otherwise.
5. Verify resolution state with `Test-PrThreadsResolved.ps1`. This checks threads only;
   separately confirm every collected suppressed/body-only finding has a disposition.
6. Suggest next steps:
   - `/pr-resolve` — reply to and resolve remaining PR review threads.
   - `/commit` — commit, push, and update the PR.

## Guidelines

- Ask first, code second: clarify ambiguous feedback before implementing.
- Wait for user approval before committing, pushing, replying, or resolving.
- Be respectful; accept good suggestions and justify disagreements professionally.
- Reference commit SHAs for traceability after commits exist.
- Batch related replies to avoid notification spam.
- Never resolve without replying first.

## Common Issues

See [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) for `Could not resolve to a node`,
`gh: Not Found`, `Cannot resolve thread`, and the script-unavailable fallback.
