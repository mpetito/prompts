# pr-review

Verdict: **good** · SKILL.md body 155 lines · description 278 chars

pr-review is a short, well-ordered workflow at 155 body lines. It has a hard approval gate, a strict draft template, posting done by a script, and links to shared tooling that sit one level deep. The biggest gap is the description: it is the shortest kind in the collection, it uses none of the plain-language triggers its own evals test ("look over his changes", "merge request", "what would you flag before I sign off"), and its "Not for" clause names no sibling skill. The body states the approval gate about nine times across Core Principles, Step 5, Guidelines and Boundaries, and these sections overlap enough to trim.

## Checklist

| Item | Status | Note |
| --- | --- | --- |
| Description is specific and includes key terms | partial | Has GitHub, PR number or URL, and review comments. It lacks the plain-language triggers the trigger evals use (look over changes, merge request, what to flag or push back on, before I sign off or approve). |
| Description includes both what the Skill does and when to use it | pass | "Review someone else's GitHub pull request..." plus a "Use when ..." clause. |
| SKILL.md body is under 500 lines | pass | 155 body lines (159 total minus 4 frontmatter lines). |
| Additional details are in separate files (if needed) | pass | Script usage and the non-Windows fallback live in ../pr-scripts/REFERENCE.md. The coding standards live in code-authoring and code-quality-standards. |
| No time-sensitive information (or in an "old patterns" section) | pass |  |
| Consistent terminology throughout | partial | "verdict" (lines 96, 128, 142, 156) and "event" (line 112, the script's -Event parameter) name the same thing, and the text never maps one to the other. Findings are also called comments, concerns and observations. |
| Examples are concrete, not abstract | pass | Concrete JSON comment shape, command lines and a question-style comment example. |
| File references are one level deep | pass | Every link goes straight from SKILL.md. The linked REFERENCE.md links on to README.md for parameters, but pr-review needs only the Invocation section. |
| Progressive disclosure used appropriately | pass |  |
| Workflows have clear steps | pass | Six numbered steps, with an explicit gate in Step 5. |
| Scripts solve problems rather than defer to Claude | pass | Submit-PrReview.ps1 checks each comment for path, line and body, defaults side to RIGHT, and throws with the gh response on failure. |
| Error handling is explicit and helpful | pass | The script names the offending entry in its error. REFERENCE.md has a Common Issues section. |
| No "voodoo constants" (all values justified) | pass |  |
| Required packages listed in instructions and verified as available | pass | PowerShell 7 and an authenticated gh are stated in REFERENCE.md#invocation, which Step 1 links. |
| Scripts have clear documentation | pass | Comment-based help with examples. The JSON shape is shown in Step 6. |
| No Windows-style paths (all forward slashes) | pass |  |
| Validation/verification steps for critical operations | pass | Approval gate before posting, script-side field validation, and confirmation of html_url after posting. |
| Feedback loops included for quality-critical tasks | pass | Step 5: draft, then the user edits, then iterate until explicit approval. |
| At least three evaluations created | partial | evals/shared-benchmark.json has 8 trigger cases (5 positive, 3 negative) and no behaviour cases with assertions. Nothing tests the body: no posting before approval, no lint nits, the draft format. |
| Tested with real usage scenarios | partial | The trigger prompts are realistic, but no scenario runs the workflow itself. |

## Findings

1. **medium** · Writing effective descriptions; checklist: Description is specific and includes key terms · SKILL.md frontmatter, description (line 3)
   > Use when asked to review a teammate's PR, post GitHub review comments, or check an external PR against project standards. Not for your own local changes.

   Fix: Add the plain-language triggers its own evals test (look over or go through a colleague's or contractor's changes or merge request, what to flag or push back on before signing off or approving, draft what to say before anything is submitted). End with the collection's named disambiguation: "Not for your own local changes (review), addressing comments on your own PR (pr-feedback), or replying to and resolving threads (pr-resolve)."

2. **medium** · Concise is key ("Does Claude really need this explanation?") · SKILL.md, Core Principles (lines 20-25), Guidelines (145-150), Boundaries (152-159)
   > 1. **Collaborate before posting** — draft everything locally, present it to the user, iterate, and only post after explicit approval. No exceptions.

   Fix: The approval gate appears at lines 8, 22, 99, 101, 112, 142, 155, 156 and 157. Keep it in Step 5 and one Boundaries line, and delete Core Principle 1. Principle 4 repeats Step 2 ("Project conventions override personal preferences") and principles 2-3 repeat Step 3's out-of-scope list and the Guidelines tone line, so delete them too. Collapse Boundaries to the three never-rules (post without sign-off, push to the author's branch, resolve others' threads). (about 220 tokens saved)

3. **low** · Concise is key; Default assumption: Claude is already very smart · SKILL.md, intro paragraph (line 8) and When to Use (lines 10-14)
   > - The user provides a PR number (or URL) and asks for a review of someone else's work
- The user wants help drafting or posting GitHub review comments

   Fix: The When to Use bullets and the intro sentence restate the description, which is already loaded when the skill triggers. Delete the three bullets and the "not a linter" intro. Keep only the paragraph at lines 16-18 that routes own changes and delegated report-only reviews to `review`. (about 110 tokens saved)

4. **low** · MCP tool references (fully qualified names); collection Cross-Tool Authoring Notes (describe tools as capabilities) · SKILL.md, Step 3 (line 55)
   > Pull surrounding file content (`get_file_contents` or local checkout) when the diff lacks context.

   Fix: `get_file_contents` is a bare GitHub MCP tool ID. It is neither qualified as `ServerName:tool_name` nor described as a capability. Replace it with a host-neutral instruction that matches Step 1's tooling, for example "read the file at the head ref (`gh api repos/{owner}/{repo}/contents/{path}?ref={head}`) or from a local checkout".

5. **low** · Workflows have clear steps (cross-repo case left implicit) · SKILL.md, Step 1 item 2 (line 32)
   > Fetch the diff itself with `gh pr diff {n}`.

   Fix: Item 1 explicitly allows a PR in another repository, but `gh pr diff {n}` without `-R` reads the current repository and returns the wrong PR or fails. Write `gh pr diff {n} -R {owner}/{repo}` so the step works in both cases.

6. **low** · Use consistent terminology · SKILL.md, Step 5 (line 96), Step 6 (line 112), Output Format (line 128), Boundaries (line 156)
   > - Default event is `COMMENT`; only use `APPROVE` or `REQUEST_CHANGES` when the user explicitly chooses it

   Fix: Use "verdict" throughout and say once in Step 6 that it is passed as the script's `-Event`. Call the drafted items "comments" consistently, not findings, concerns and observations interchangeably, except for the deliberate "Observations NOT Being Posted" bucket. (about 10 tokens saved)

7. **low** · Build evaluations first; checklist: At least three evaluations created / Tested with real usage scenarios · evals/shared-benchmark.json
   > "kind": "trigger" (all 8 cases); "assertions": []

   Fix: The suite tests triggering only, so the with-versus-without delta that CONTRIBUTING uses to judge removal says nothing about the body. Add about 3 behaviour cases with assertions: no posting tool is called before approval, the draft follows the Output Format and ends with "Nothing has been posted", and lint-only issues are absent from the proposed inline comments.

8. **low** · Concise is key (duplicate pointers) · SKILL.md, Step 6 (line 103) and Step 2 (lines 46-49)
   > `../pr-scripts/Submit-PrReview.ps1` (sibling folder within the skills tree)

   Fix: Step 1 already links REFERENCE.md for the script conventions, so drop the parenthetical. In Step 2, link code-authoring's Coding Standards section directly (an anchor) instead of explaining what to read in it. (about 20 tokens saved)

## Strengths

- A hard human gate on posting (Step 5), and a draft template that ends in "Nothing has been posted". Together they make the gate visible to the user, not just to the agent.
- Posting is a low-freedom operation: one script submits the review atomically from a JSON comments file, validates each entry with a specific error message, and returns html_url for confirmation.
- The skill pairs the dimensions to review, in priority order, with an explicit out-of-scope list (lint, style consistent with the surrounding code, pre-existing issues). That bounds a high-freedom task without scripting it.

## Cut candidates

- When to Use (lines 10-14): the bullets restate the description; keep only the review / report-only routing paragraph
- Core Principles (lines 20-25): each principle is restated in Steps 2-5 or Guidelines
- Intro paragraph (line 8): restates the description and the gate
- Guidelines (lines 145-150): tone advice a senior-reviewer model already follows; keep only 'don't pile on existing reviewers' if Step 1.3 does not already cover it (it does)
- Boundaries (lines 154-156): the allow and ask-first lines repeat Step 5; keep the three never-rules
