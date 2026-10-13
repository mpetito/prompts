"""Collects a pull request's feedback in one call: every unresolved review thread and every review body, verbatim, so
findings in a body's collapsed "suppressed" section stay visible.
  get_pr_feedback.py [--pr <number>] [--repo <owner/name>]
--pr defaults to the pull request of the current branch, --repo to the current repository.

Prints one JSON object: {repo, pr, threads, reviews}. Threads come from GraphQL and reviews from REST, both through
`gh api --paginate --slurp`, so no page is dropped. Each thread carries its threadId (PRRT_..., for
resolveReviewThread), isOutdated, path, line and up to 100 comments, each with its REST fullDatabaseId as a string id
(for .../comments/<id>/replies). Exits 1 when either fetch fails, a missing pull request included: a failed fetch is
never reported as "no feedback". Requires an authenticated gh CLI.
"""
import json

from run import Fail, Parser, entry, output, run

QUERY = """query($owner: String!, $name: String!, $pr: Int!, $endCursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100, after: $endCursor) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id isResolved isOutdated path line
          comments(first: 100) { nodes { fullDatabaseId author { login } body url } }
        }
      }
    }
  }
}"""


def login(actor):
    return (actor or {}).get("login")


def gh_value(args, missing):
    """One value printed by gh, or Fail with missing."""
    r = run(["gh", *args])
    if r.returncode != 0 or not r.stdout.strip():
        raise Fail(missing)
    return r.stdout.strip()


def main(argv):
    parser = Parser(prog="get_pr_feedback.py")
    parser.add_argument("--pr", type=int)
    parser.add_argument("--repo")
    args = parser.parse_args(argv)
    repo = args.repo or gh_value(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
                                 "Could not resolve the repository; pass --repo owner/name.")
    pr = args.pr or int(gh_value(["pr", "view", "--json", "number", "-q", ".number"],
                                 "Could not resolve the pull request; pass --pr <number>."))
    owner, _, name = repo.partition("/")

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

    r = run(["gh", "api", f"repos/{repo}/pulls/{pr}/reviews", "--paginate", "--slurp"])
    if r.returncode != 0:
        raise Fail(f"Could not collect review bodies for {repo}#{pr}: {output(r)}")
    reviews = [{"id": v["id"], "author": login(v["user"]), "state": v["state"], "commitId": v["commit_id"],
                "url": v["html_url"], "body": v["body"]}
               for page in json.loads(r.stdout) for v in page]

    print(json.dumps({"repo": repo, "pr": pr, "threads": threads, "reviews": reviews}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    entry(main)
