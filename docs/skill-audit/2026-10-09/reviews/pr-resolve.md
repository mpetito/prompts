# pr-resolve

Verdict: **needs-work** · SKILL.md body 106 lines · description 242 chars

pr-resolve is short and script-driven. It hands GitHub calls to tested PowerShell wrappers (one-call reply-and-resolve, an exit-code verifier) and keeps reply templates in one shared REFERENCE.md so the three PR skills cannot drift. The most important gap is that the rule for when to resolve and when to only reply is repeated about five times in 106 lines, while the final verification step never says that the reply-only threads it deliberately leaves open will make Test-PrThreadsResolved.ps1 exit 1.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Includes the key terms (review threads, resolve, after changes are pushed). It is the only PR skill without the collection's 'Not for … (pr-feedback)' clause, even though its own evals include negative cases for pr-feedback, pr-review and commit. |
| Description includes both what the Skill does and when to use it | pass | The first sentence says what it does; the second starts 'Use when responding to PR review comments, resolving review threads…'. |
| SKILL.md body is under 500 lines | pass | 106 body lines (lines 10-115). |
| Additional details are in separate files (if needed) | pass | Invocation, the decision matrix, reply templates and troubleshooting live in ../pr-scripts/REFERENCE.md. |
| No time-sensitive information | pass |  |
| Consistent terminology throughout | partial | The same category is called 'outdated' and 'obsolete'. 'Outdated' also collides with GitHub's isOutdated flag, which Get-PrThreads.ps1 returns. |
| Examples are concrete, not abstract | pass | The batch example uses real-looking PRRT_ IDs and reply text. |
| File references are one level deep | partial | SKILL.md links REFERENCE.md directly. REFERENCE.md then links README.md and ../pr-feedback/SKILL.md, but pr-resolve does not need either one. |
| Progressive disclosure used appropriately | partial | 'Read it before the first call' makes the agent load all 153 lines of a reference shared by three skills, much of it about pr-feedback and pr-review. The same file is also linked four separate times. |
| Workflows have clear steps | partial | The nine-step Process is clear, but the 'Resolution Procedure' pseudocode and the Guidelines repeat steps 4-7. |
| Scripts solve problems rather than defer to Claude | pass | Resolve-PrContext throws actionable messages; Resolve-PrThread.ps1 does reply-then-resolve in one call. |
| Error handling is explicit and helpful | pass | The Common Issues table in REFERENCE.md maps each gh/GraphQL error to a fix. |
| No voodoo constants | partial | PrCommon.psm1 uses reviewThreads(first: 100), which is GitHub's maximum page size, and comments(first: 50), which has no rationale and no pagination. Comments past 50 in a thread are dropped silently. |
| Required packages listed in instructions and verified as available | pass | REFERENCE.md Invocation states PowerShell 7 and an authenticated gh, and gives a fallback (GitHub MCP or raw gh api graphql). |
| Scripts have clear documentation | pass | Each script has a .SYNOPSIS and .EXAMPLE, and README.md lists every script. |
| No Windows-style paths | pass |  |
| Validation/verification steps for critical operations | pass | Step 4 checks each fix before replying; step 9 runs Test-PrThreadsResolved.ps1. |
| Feedback loops included for quality-critical tasks | partial | The verifier exits 1 whenever any thread is open, including the ones the skill deliberately leaves open. The skill does not say how to read that result. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 negative). It has no behavior case for the critical rule that disagreements stay open and replies come before resolves. |

## Findings

1. **medium** · Concise is key; Workflows have clear steps · SKILL.md: Process steps 6-7, 'Resolution Procedure', 'Guidelines'
   > 3. IF the thread is fixed, answered, or outdated: … 4. IF it is a design discussion, deferred work, or disagreement:
- Resolve only when fixed, answered, or obsolete. - Leave design discussions, deferred work, and disagreements open

   Fix: State the resolve-versus-reply rule once, in Process step 6. Delete the 'Resolution Procedure' pseudocode block, which repeats Process steps 4-7 line for line, and delete Guidelines bullets 1-3 and 6, which repeat the matrix and step 9. Keep only the reply-style and batching bullets. (about 230 tokens saved)

2. **medium** · Implement feedback loops; Validation/verification steps for critical operations · SKILL.md: Process step 9 and Guidelines
   > 9. Verify final state with `Test-PrThreadsResolved.ps1`.

   Fix: Test-PrThreadsResolved.ps1 exits 1 and lists every open thread, including the reply-only threads the skill leaves open on purpose. Change step 9 to say that the remaining threads must be exactly the reply-only set. Any other open thread means a resolve failed, so retry it or report it.

3. **medium** · Provide utility scripts (make execution intent clear, document the command line); Set appropriate degrees of freedom (low freedom for fragile operations) · SKILL.md: 'Batch Resolution Example'
   > # 1. Get unresolved threads
../pr-scripts/Get-PrThreads.ps1 -Pr 42 -Unresolved

   Fix: The example is written as if the scripts can run directly, relative to the current directory. Claude Code runs Bash with the repository as its working directory, and REFERENCE.md says to use `pwsh -NoProfile -File` and to resolve paths from the skill folder. Show the Bash form (`pwsh -NoProfile -File <skill-dir>/../pr-scripts/Get-PrThreads.ps1 …`) once, or add one line saying the path is relative to this skill's folder.

4. **medium** · Structure longer reference files with a table of contents; Progressive disclosure pattern 2 (domain-specific organization); Avoid deeply nested references · SKILL.md 'Tooling' (lines 23-24) -> ../pr-scripts/REFERENCE.md
   > Script invocation, the fallback path when the scripts are unavailable, and the reply templates
are in [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md). Read it before the first call.

   Fix: REFERENCE.md is 153 lines with no table of contents. It mixes in pr-feedback and pr-review material (Get-PrFeedback, the raw review-body fallback, Submit-PrReview) and links on to README.md and ../pr-feedback/SKILL.md. Add a table of contents to REFERENCE.md, and have SKILL.md name only the sections pr-resolve needs (Invocation, Resolution Decision Matrix, Reply Templates, Common Issues) instead of requiring a full read.

5. **medium** · Writing effective descriptions (specific triggers; collection's 'Not for … (other-skill)' convention) · SKILL.md frontmatter description
   > Use when responding to PR review comments, resolving review threads, closing out addressed feedback, or verifying thread resolution status after commits are available.

   Fix: 'Responding to PR review comments' overlaps pr-feedback, and this skill's own negative evals target that boundary. Append: 'Not for deciding which comments to act on or making the fixes (pr-feedback), reviewing a teammate's PR (pr-review), or committing and pushing (commit).' Optionally add the plain-words triggers the evals use, such as 'mark conversations done' and 'check nothing is left unresolved before re-approval'.

6. **low** · Concise is key; File references are one level deep (one link per target) · SKILL.md: intro line 13, Prerequisites bullet 1, stub sections 'Resolution Decision Matrix', 'Reply Templates', 'Common Issues'
   > Use this skill after changes have been committed and pushed, or when the user asks to reply to and resolve PR review threads.
See [`../pr-scripts/REFERENCE.md`](../pr-scripts/REFERENCE.md) for `Could not resolve to a node`,

   Fix: Delete the intro line, which restates the description, and Prerequisites bullet 1, which duplicates Process step 1's list of PR sources. Fold the three one-paragraph pointer sections into the single Tooling link so REFERENCE.md is linked once, with its contents named. (about 150 tokens saved)

7. **low** · Use consistent terminology · SKILL.md: Process step 6, Resolution Procedure, Guidelines; REFERENCE.md matrix
   > - Resolve only when fixed, answered, or obsolete.

   Fix: Use one term, 'outdated', and define it once as 'the commented code was removed or rewritten'. This keeps it distinct from GitHub's isOutdated flag, which Get-PrThreads.ps1 returns and which only means the commented line moved. (about 10 tokens saved)

8. **low** · Workflows have clear steps (contradictory instruction) · SKILL.md: after 'Output Format'
   > If further changes were pushed, suggest `/commit` to update the PR.

   Fix: Changes that are already pushed do not need a commit. Reword it to: 'If changes remain uncommitted or unpushed, use the commit skill before replying.' Or delete the line, since the Prerequisites already require pushed changes. (about 5 tokens saved)

## Strengths

- The decision matrix and reply templates live in one shared file (../pr-scripts/REFERENCE.md) that pr-feedback, pr-resolve and pr-review all link to, so the three PR skills cannot drift apart.
- GitHub mutations run through small tested scripts: Resolve-PrThread.ps1 replies and resolves in one call, and Test-PrThreadsResolved.ps1 is a verifier with clear exit codes, so the agent never hand-writes GraphQL.
- It pins model: sonnet and effort: medium for mechanical work, and its trigger evals include negative cases that name the sibling skill that should fire instead (pr-feedback, pr-review, commit).

## Cut candidates

- Resolution Procedure (pseudocode repeats Process steps 4-7)
- Guidelines bullets 1-3 and 6 (repeat the decision matrix and step 9)
- Resolution Decision Matrix (stub pointer that restates the matrix inline)
- Reply Templates (stub pointer)
- Common Issues (stub pointer)
- Intro sentence under '# PR Resolve' (restates the description)
- Prerequisites bullet 1 (duplicates Process step 1's list of PR sources)
