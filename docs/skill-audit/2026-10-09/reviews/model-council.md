# model-council

Verdict: **good** · SKILL.md body 114 lines · description 280 chars

model-council is compact (a 114-line body, five numbered steps, two reference files linked directly from SKILL.md) and takes care of the hard parts: keeping members independent, pinning the code state, weighing evidence over majority votes, and returning an honest unresolved result. Its biggest gap is the description. It is the only one in the collection's pattern without a "Not for … (other-skill)" clause, even though its own negative evals target pr-feedback, herdr-delegation and research. Next is the CLI transport: it gives no ready command line, so the model rebuilds a fragile two-provider read-only invocation from --help every time.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Names Claude, Codex, Copilot, model council, and second opinions. But 'false positive or overcomplex fix' is a cryptic fragment, and there is no disambiguation from pr-feedback, herdr-delegation, or research. |
| Description includes both what the Skill does and when to use it | pass | 'Resolve one bounded technical decision…' then 'Use when asked for a model council…' |
| SKILL.md body is under 500 lines | pass | 114 body lines |
| Additional details are in separate files (if needed) | pass | The member prompt template and the transport and CLI details are in references/ |
| No time-sensitive information (or in an 'old patterns' section) | partial | cross-harness.md pins a behaviour claim to 'Codex CLI 0.157.1 (Linux)'. It is labelled as provenance, which is acceptable, but the claim can go stale. |
| Consistent terminology throughout | partial | The participant is called member, reviewer, worker, seat, and participant interchangeably. |
| Examples are concrete, not abstract | partial | The perspective table and report contract are concrete. The CLI transport has a flag table but no assembled command example. |
| File references are one level deep | pass | SKILL.md links both reference files directly. cross-harness.md's link to member-prompt.md is a sibling cross-link to a file SKILL.md also links. |
| Progressive disclosure used appropriately | pass | Transport details load only at step 3, and the prompt template only at step 1. |
| Workflows have clear steps | pass | Five numbered steps, from framing the decision to returning it, with a budget and a stop rule. |
| Scripts solve problems rather than defer to Claude | not-applicable | No scripts. The CLI path defers command assembly to the model ('Read their installed help before assembling commands'). |
| Error handling is explicit and helpful | pass | Covers a failed or slow member, an unavailable provider, and a single-review fallback. |
| No 'voodoo constants' (all values justified) | pass | The two-member, one-extra, one-round limits are given as defaults with a rationale. |
| Required packages listed in instructions and verified as available | pass | Requires installed, already-authenticated claude and codex CLIs, and checks them with --help. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | Verify decisive citations, inspect the exit status rather than file existence, and revalidate if the code changed. |
| Feedback loops included for quality-critical tasks | pass | Isolate the disputed premise, then one focused test, lookup, or clarification round, then an optional third member, then stop at the budget. |
| At least three evaluations created | partial | Eight cases (5 positive, 3 negative) in evals/shared-benchmark.json, all kind 'trigger' with empty assertions. None tests council behaviour. |

## Findings

1. **medium** · Writing effective descriptions; checklist: Description is specific and includes key terms (plus the collection's 'Not for …' convention) · SKILL.md frontmatter, description
   > Use when asked for a model council or second opinions, when reviewers disagree on a contract or tradeoff, or when a Copilot claim stays unclear after local checks: false positive or overcomplex fix.

   Fix: Rewrite the ending as plain trigger words ('…stays unclear after local checks, such as a suspected false positive or an overcomplex fix'). Then add the collection's disambiguation clause, which the three negative evals already assume: 'Not for triaging or fixing PR comments (pr-feedback), handing work to a peer pane (herdr-delegation), or comparing libraries from sources (research).'

2. **medium** · Set appropriate degrees of freedom (low freedom for fragile operations); Provide utility scripts; checklist: Examples are concrete · references/cross-harness.md, step 3 (CLI transport)
   > Read their installed help before assembling commands:
| Reasoning effort | `--effort high` where supported | Supported reasoning setting from installed help/config docs |

   Fix: Running two providers read-only with stdin packets and separate captured output is fragile, and the file itself warns about quoting and permission bypass. Replace the flag table with one exact command per CLI, with placeholders only for the packet path, repo, model ID and output path. For example: `codex exec --model <id> --sandbox read-only --cd <repo> --output-last-message <out.md> - < <packet>`, and the Claude equivalent with --print, --model opus, --output-format json and a read-only tool allowlist. Then say to run `--help` only when a flag is rejected.

3. **medium** · Concise is key ('Does Claude really need this explanation?'); avoid duplicating a linked reference · SKILL.md, '## 2. Select Members and Models', lines 47-52
   > Apply [agent model selection](...) before launch. **Claude workers default to explicit Opus**, irrespective of the coordinator or skill model. ... Any weaker worker needs a task-specific justification; an ambiguous judgment is generally a reason to retain capability.

   Fix: Keep the link and the two council-specific rules: explicit Opus for Claude, and a high-capability model from the actual catalog for Codex, never 'opus'. Cut the restated downgrade policy, which the linked agent-model-selection.md and the global instructions already carry. (about 60 tokens saved)

4. **low** · Concise is key; Progressive disclosure (detail lives once, in the reference) · SKILL.md, '## 3. Dispatch Independent Reviews', lines 73-77
   > Provide the same packet, role-specific focus, output contract, and a read-only task: no source
edits, commits, public replies, thread resolution, or further delegation.

   Fix: The read-only boundaries, the result-capture rule, and the no-writes-into-the-checkout rule are all in member-prompt.md 'Boundaries' already, and repeated in cross-harness.md. Reduce this paragraph to 'Send each member the filled member-prompt; do not loosen permissions to run a reviewer.' (about 55 tokens saved)

5. **low** · Avoid offering too many options; Concise is key (out-of-scope guidance) · references/cross-harness.md, step 3, lines 47-51
   > A one-shot review outside a council that must read GitHub or run the test suite may use
`--sandbox workspace-write -c sandbox_workspace_write.network_access=true`

   Fix: Delete the sentence about one-shot reviews outside a council. It describes a non-council use, gives a writable, networked sandbox that contradicts the council's read-only boundary, and belongs in herdr-delegation or the Codex lane guidance if anywhere. Keep only 'put the diff, PR text and cited docs in the packet'.

6. **low** · Use consistent terminology · SKILL.md steps 2-5 and references/cross-harness.md
   > Codex workers use an explicitly selected... / any unavailable or incomplete seat / Do not label a simulated persona as a Codex/Claude participant

   Fix: Use 'member' throughout, as the skill and member-prompt.md mostly do. Replace 'worker', 'seat', 'participant' and the generic 'reviewer' (where it means a council member) with 'member'. (about 5 tokens saved)

7. **low** · Concise is key; Writing effective descriptions (avoid restating triggers in the body) · SKILL.md, '## When a Council Helps', lines 12-17
   > - Reviewers disagree about a contract, reachable failure path, or architectural tradeoff
- The user explicitly asks for independent model perspectives

   Fix: Three of the four bullets repeat the description's triggers, and the body loads only after triggering. Keep the 'Skip the council for…' paragraph, which adds new information, and fold the one new nuance into it in a single clause: a fix that prevents a real defect but adds disproportionate complexity. (about 50 tokens saved)

8. **low** · Build evaluations first; checklist: At least three evaluations created / Tested with real usage scenarios · evals/shared-benchmark.json
   > "kind": "trigger", ... "assertions": []  (all 8 cases)

   Fix: Add two or three behaviour cases with assertions for the failure modes the skill exists to prevent. Examples: role-playing both models in one response; omitting an explicit model per member; sharing one member's verdict with the other; reporting consensus when a member failed. Then the with-versus-without delta in CONTRIBUTING.md measures the procedure, not only triggering.

## Strengths

- States plainly what the skill will not do: the output is a recommendation, not a code change or a majority vote, and the skill says 'A council recommendation is not permission to post, merge, or change scope'. That keeps the skill from creeping into pr-feedback's job.
- Has a budgeted feedback loop with an honest stop. It isolates the disputed premise and allows one test or one clarification round, then at most one third member without vote counts or authority cues, then 'Stop at the budget with an explicit unresolved result rather than claiming consensus.'
- Keeps an exact, numbered report contract in a reference template (member-prompt.md), and step 5's disposition labels match it word for word, so members and coordinator share one vocabulary.

## Cut candidates

- SKILL.md '## When a Council Helps': the four trigger bullets, which repeat the description (keep the skip paragraph)
- SKILL.md '## 2. Select Members and Models': the restated downgrade policy in lines 48-52, already in agent-model-selection.md
- SKILL.md '## 3. Dispatch Independent Reviews': the read-only boundary paragraph in lines 73-77, a duplicate of the member-prompt.md 'Boundaries' block
- references/cross-harness.md step 3: the one-shot review outside a council with a workspace-write sandbox (lines 47-51)
- references/cross-harness.md '## Runtime sources and verification': condense to the doc links and one version-pinned note
