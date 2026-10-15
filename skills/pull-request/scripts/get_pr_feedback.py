"""Collects a pull request's feedback in one call: every unresolved review thread, every review body and every
conversation comment, verbatim, so findings in a body's collapsed "suppressed" section stay visible, plus whether each
automated reviewer (Copilot, Codex, Claude) has reviewed the current head.
  get_pr_feedback.py [--pr <number>] [--repo <owner/name>]
--pr defaults to the pull request of the current branch, --repo to the current repository.

Prints one JSON object: {repo, pr, head, threads, reviews, comments, automatedReviewers}. Threads come from GraphQL;
reviews, conversation comments and the head's check runs from REST, all through `gh api --paginate --slurp`, so no
page is dropped. Each thread carries its threadId (PRRT_..., for resolveReviewThread), isOutdated, path, line and up
to 100 comments, each with its REST fullDatabaseId as a string id (for .../comments/<id>/replies). A bot's login
ends in [bot] everywhere, as REST spells it.
automatedReviewers has one entry per reviewer in REVIEWERS: {seen, reviewedHead}; seen means it has posted anything
on this pull request, reviewedHead that it has reported on the head commit, findings or none. Exits 1 when any fetch
fails, a missing pull request included: a failed fetch is never reported as "no feedback". Requires an authenticated
gh CLI.
"""
import json
import re

from run import Fail, Parser, entry, output, run

QUERY = """query($owner: String!, $name: String!, $pr: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line
          comments(first: 100) { nodes { fullDatabaseId author { login __typename } body url } }
        }
      }
    }
  }
}"""

# Codex reports a review that found nothing as a conversation comment, not a review: "**Reviewed commit:** `ec42780f14`".
CODEX_REVIEWED = re.compile(r"Reviewed commit:\**\s*`([0-9a-f]{7,40})`")


def codex_clean_comment(feedback, check_runs, logins):
    """Codex's no-findings comment names the head it reviewed."""
    return any(c["author"].lower() in logins and m and feedback["head"].startswith(m.group(1))
               for c in feedback["comments"] for m in [CODEX_REVIEWED.search(c["body"] or "")])


def claude_check_run(feedback, check_runs, logins):
    """Claude's managed Code Review finishes a check run on the head, neutral whatever it found. Only the Claude app's
    run counts: a workflow in the pull request could name a job the same."""
    return any(r["app"] == "claude" and r["name"] == "Claude Code Review" and r["status"] == "completed"
               for r in check_runs)


# Each automated reviewer: the bot logins it posts under (lowercase), and how it reports a head it reviewed other than
# by a review on that commit, or None. A review whose commit is the head counts for every one of them. The [bot] suffix
# is part of each login, so a person's account of the same name, which anyone can comment from, never matches.
REVIEWERS = {
    "copilot": ({"copilot-pull-request-reviewer[bot]", "copilot[bot]", "github-copilot[bot]"}, None),
    "codex": ({"chatgpt-codex-connector[bot]"}, codex_clean_comment),
    "claude": ({"claude[bot]"}, claude_check_run),
}


def login(actor):
    """The actor's login, with [bot] for a bot: REST includes it, GraphQL drops it but names the Bot type."""
    actor = actor or {}
    return f"{actor.get('login')}[bot]" if actor.get("__typename") == "Bot" else actor.get("login")


def gh_value(args, missing):
    """One value printed by gh, or Fail with missing."""
    r = run(["gh", *args])
    if r.returncode != 0 or not r.stdout.strip():
        raise Fail(missing)
    return r.stdout.strip()


def rest_pages(path, what):
    """Every item of a paginated REST list, or Fail naming what could not be collected."""
    r = run(["gh", "api", path, "--paginate", "--slurp"])
    if r.returncode != 0:
        raise Fail(f"Could not collect {what}: {output(r)}")
    return json.loads(r.stdout)


def automated_reviewers(feedback, check_runs):
    authors = {(a or "").lower() for a in [r["author"] for r in feedback["reviews"]] + [c["author"] for c in feedback["comments"]]
               + [c["author"] for t in feedback["threads"] for c in t["comments"]]}
    status = {}
    for name, (logins, reported) in REVIEWERS.items():
        reviewed = any((r["author"] or "").lower() in logins and r["commitId"] == feedback["head"] for r in feedback["reviews"]) \
            or bool(reported and reported(feedback, check_runs, logins))
        status[name] = {"seen": reviewed or bool(authors & logins), "reviewedHead": reviewed}
    return status


def main(argv):
    parser = Parser(prog="get_pr_feedback.py", allow_abbrev=False)
    parser.add_argument("--pr", type=int)
    parser.add_argument("--repo")
    args = parser.parse_args(argv)
    repo = args.repo or gh_value(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                                 "Could not resolve the repository; pass --repo owner/name.")
    pr = args.pr or int(gh_value(["pr", "view", "--json", "number", "-q", ".number"],
                                 "Could not resolve the pull request; pass --pr <number>."))
    owner, _, name = repo.partition("/")
    head = gh_value(["api", f"repos/{repo}/pulls/{pr}", "-q", ".head.sha"],
                    f"Could not read the head of {repo}#{pr}.")

    r = run(["gh", "api", "graphql", "--paginate", "--slurp", "-f", f"query={QUERY}", "-f", f"owner={owner}",
             "-f", f"name={name}", "-F", f"pr={pr}"])
    if r.returncode != 0:
        raise Fail(f"Could not collect review threads for {repo}#{pr}: {output(r)}")
    threads = [
        {"threadId": t["id"], "isOutdated": t["isOutdated"], "path": t["path"], "line": t["line"],
         "comments": [{"id": c["fullDatabaseId"], "author": login(c["author"]), "body": c["body"], "url": c["url"]}
                      for c in t["comments"]["nodes"]]}
        for page in json.loads(r.stdout)
        for t in page["data"]["repository"]["pullRequest"]["reviewThreads"]["nodes"]
        if not t["isResolved"]]

    reviews = [{"id": v["id"], "author": login(v["user"]), "state": v["state"], "commitId": v["commit_id"],
                "url": v["html_url"], "body": v["body"]}
               for page in rest_pages(f"repos/{repo}/pulls/{pr}/reviews", f"review bodies for {repo}#{pr}")
               for v in page]
    comments = [{"id": c["id"], "author": login(c["user"]), "createdAt": c["created_at"], "url": c["html_url"],
                 "body": c["body"]}
                for page in rest_pages(f"repos/{repo}/issues/{pr}/comments", f"comments on {repo}#{pr}")
                for c in page]
    check_runs = [{"name": c["name"], "status": c["status"], "app": (c.get("app") or {}).get("slug")}
                  for page in rest_pages(f"repos/{repo}/commits/{head}/check-runs", f"check runs on {head}")
                  for c in page["check_runs"]]

    feedback = {"repo": repo, "pr": pr, "head": head, "threads": threads, "reviews": reviews, "comments": comments}
    feedback["automatedReviewers"] = automated_reviewers(feedback, check_runs)
    print(json.dumps(feedback, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    entry(main)
