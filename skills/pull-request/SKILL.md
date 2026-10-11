---
name: pull-request
description: "Work a GitHub pull request: answer review feedback on your own PR (check each Copilot or reviewer claim, fix what is right, reply to every thread, then resolve it or leave it open), open a PR or bring its description up to date, and post a review of someone else's PR once the owner approves the text. Use when asked to address, handle or go through review comments or Copilot feedback on my PR, reply to or resolve review threads, open or create a pull request, write or refresh a PR description, or review a PR and post the comments after an okay. Not for reviewing a local diff or uncommitted changes for bugs (review), waiting for CI or Copilot to finish (pr-watch agent), having Claude and Codex debate a decision (model-council), making a plain commit (commit-commands), or writing a CONTRIBUTING.md (project-setup)."
---

# Pull request

Role: worker. Loaded by the session or subagent that owns a pull request, Claude or Codex; this
file stays under about 120 lines.

Branch, commit and PR policy come from the project's CONTRIBUTING.md and, where it is silent, from
the convention its `git log` shows; a PR title follows the commit convention. The two scripts in
`scripts/` in this skill's folder need PowerShell 7; on a host without `pwsh`, run the raw `gh api`
calls shown with them.

## Answer review feedback on your own PR

1. Fetch every unresolved thread (id, `isOutdated`, comments with their REST `fullDatabaseId`)
   and every review body: `pwsh <skill dir>/scripts/Get-PrFeedback.ps1 -Pr <n>`, or

   ```sh
   gh api graphql --paginate --slurp -f owner=<owner> -f name=<repo> -F pr=<n> -f query='
     query($owner:String!,$name:String!,$pr:Int!,$endCursor:String){repository(owner:$owner,name:$name){
       pullRequest(number:$pr){reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor}
         nodes{id isResolved isOutdated path line comments(first:100){nodes{fullDatabaseId author{login} body}}}}}}}' &&
   gh api repos/<owner>/<repo>/pulls/<n>/reviews --paginate
   ```

   A failed fetch is an error to report, never "no feedback". Read the review bodies too,
   including Copilot's collapsed "suppressed" section. An empty thread list is not "no feedback";
   a body-only finding gets no new public comment.
2. Verify each claim against the code and docs before accepting it; reject with the evidence.
   Declining a blanket guard is [code-style](../code-style/SKILL.md)'s "trust your callers".
3. A claim that stays ambiguous after you check the code and docs goes to
   [model-council](../model-council/SKILL.md) (or the owner); don't decide it alone. Leave its
   thread open until it is settled.
4. Commit the fixes, run the project's checks, and `git push`.
5. Reply only after the fix is pushed, citing the pushed SHA; reply before you resolve, never
   resolve silently.
6. Reply to every thread. Resolve threads you fixed, and Copilot threads you declined with
   evidence. A human reviewer's disagreement or deferral stays open for that reviewer.
   - Reply, then resolve: `pwsh <skill dir>/scripts/Resolve-PrThread.ps1 -ThreadId PRRT_... -Body '<reply>'`
     (it never resolves when the reply fails), or

     ```sh
     gh api repos/<owner>/<repo>/pulls/<n>/comments/<first comment fullDatabaseId>/replies -f body='<reply>' &&
     gh api graphql -f id=PRRT_... -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}'
     ```

   - Reply and leave open: the `.../replies` call alone.
7. Report each thread's end state, and each body-only finding with what you did about it.

## Open or update a PR

- Body, kept short: the motivation first, in plain prose; then the changes grouped by purpose;
  then validation that lists only what was actually run, with results, and says in the body what
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
