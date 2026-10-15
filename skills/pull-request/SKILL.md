---
name: pull-request
description: "Work a GitHub pull request: answer review feedback on your own PR (check each claim from Copilot, Codex, Claude or a human reviewer, fix what is right, reply to every thread, then resolve it or leave it open), open a PR or bring its description up to date, and post a review of someone else's PR once the owner approves the text. Use when asked to address, handle or go through review comments or Copilot, Codex or Claude feedback on my PR, reply to or resolve review threads, open or create a pull request, write or refresh a PR description, or review a PR and post the comments after an okay. Not for reviewing a local diff or uncommitted changes for bugs (review), waiting for CI or automated reviews to finish (pr-watch agent), having Claude and Codex debate a decision (model-council), making a plain commit (commit-commands), or writing a CONTRIBUTING.md (project-setup)."
---

# Pull request

Role: worker. Loaded by the session or subagent that owns a pull request, Claude or Codex; this
file stays under about 120 lines.

Branch, commit and PR policy come from the project's CONTRIBUTING.md; a PR title follows the
commit convention. The two scripts in
`scripts/` in this skill's folder run as `python3 "<skill dir>/scripts/<name>.py"` (Python 3.12+),
with `<skill dir>` written as a full path such as `$HOME/.claude/skills/pull-request`; on a host
without `python3`, run the raw `gh api` calls shown with them.

In the owner's main session only, never in an orchestrated lane or as a worker, load the tt skill
after a PR is created, updated, reviewed or merged. tt logs only the day's time Harvest does not
already hold, so a PR whose time a build or an earlier session already logged adds nothing.

## Answer review feedback on your own PR

1. Fetch every unresolved thread (id, `isOutdated`, comments with their REST `fullDatabaseId`),
   every review body and every conversation comment:
   `python3 "<skill dir>/scripts/get_pr_feedback.py" --pr <n>`, whose `automatedReviewers` says
   whether Copilot, Codex and Claude have each reported on the head; or

   ```sh
   gh api graphql --paginate --slurp -f owner=<owner> -f name=<repo> -F pr=<n> -f query='
     query($owner:String!,$name:String!,$pr:Int!,$endCursor:String){repository(owner:$owner,name:$name){
       pullRequest(number:$pr){reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor}
         nodes{id isResolved isOutdated path line comments(first:100){nodes{fullDatabaseId author{login} body}}}}}}}' &&
   gh api repos/<owner>/<repo>/pulls/<n>/reviews --paginate &&
   gh api repos/<owner>/<repo>/issues/<n>/comments --paginate
   ```

   A failed fetch is an error to report, never "no feedback". Read the review bodies too,
   including Copilot's collapsed "suppressed" section, and the conversation comments, where Codex
   keeps its review summary. An empty thread list is not "no feedback";
   a body-only finding gets no new public comment.
2. Verify each claim against the code and docs before accepting it; reject with the evidence.
   Declining a blanket guard is [code-style](../code-style/SKILL.md)'s "trust your callers".
3. A claim that stays ambiguous after you check the code and docs goes to
   [model-council](../model-council/SKILL.md) (or the owner); don't decide it alone. It stays
   ambiguous when the code and docs leave two defensible answers: they state the goals but not
   which one wins, so an argument you find for one side is a lean, not a settlement. Leave its
   thread open until it is settled; its reply only says it is held for that decision, and your
   lean and reasons go to the owner, not the thread.
4. Commit the fixes, run the project's checks, and `git push`.
5. Reply to every thread. Resolve threads you fixed, and an automated reviewer's threads you
   declined with evidence. A human reviewer's disagreement or deferral stays open for that
   reviewer. A reply never mentions `@codex` or `@claude`: either starts a run of that reviewer,
   and Codex's can push commits to the branch.
   - Reply, then resolve: `python3 "<skill dir>/scripts/resolve_pr_thread.py" --thread-id PRRT_... --body '<reply>'`
     (it never resolves when the reply fails), or

     ```sh
     gh api repos/<owner>/<repo>/pulls/<n>/comments/<first comment fullDatabaseId>/replies -f body='<reply>' &&
     gh api graphql -f id=PRRT_... -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}'
     ```

   - Reply and leave open: the `.../replies` call alone.
6. Report each thread's end state, and each body-only finding with what you did about it.

## Open or update a PR

- Body, kept short: the motivation first, in plain prose; then the changes grouped by purpose,
  as a bulleted list with one bullet per purpose saying what it now does, not one per file; then
  validation that lists only what was actually run, with results, and says in the body what
  was not run. No Summary boilerplate, no filler lines.
- Write the body to a temporary file outside the repository, then
  `gh pr create --title '<title>' --body-file <file>`, or `gh pr edit <n> --body-file <file>` for
  an update.

## Review someone else's PR

1. The [review](../review/SKILL.md) skill makes the judgment.
2. Then show the exact review text and post only after the owner approves that text, as one
   review: summary plus inline comments in a single API call, event COMMENT unless the owner
   picks one. Show the call as pending and stop:

   ```sh
   gh api repos/<owner>/<repo>/pulls/<n>/reviews --input - <<'EOF'
   {"body": "<summary>", "event": "COMMENT",
    "comments": [{"path": "<file>", "line": <line>, "side": "RIGHT", "body": "<comment>"}]}
   EOF
   ```
