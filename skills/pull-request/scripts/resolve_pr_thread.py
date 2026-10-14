"""Replies to a pull request review thread, then resolves it; never resolves without the reply.
  resolve_pr_thread.py --thread-id <PRRT_...> --body <reply>

Posts --body as a reply on the thread (addPullRequestReviewThreadReply), then resolves it (resolveReviewThread).
Exits 1, leaving the thread open, if the reply fails. On success prints exactly one line:
`resolved <thread id> <reply url>`. Requires an authenticated gh CLI.
"""
import json

from run import Fail, Parser, entry, output, run

REPLY = ("mutation($id: ID!, $body: String!) { addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId: $id, "
         "body: $body}) { comment { url } } }")
RESOLVE = "mutation($id: ID!) { resolveReviewThread(input: {threadId: $id}) { thread { isResolved } } }"


def main(argv):
    parser = Parser(prog="resolve_pr_thread.py", allow_abbrev=False)
    parser.add_argument("--thread-id", required=True, help="the thread's node id, PRRT_...")
    parser.add_argument("--body", required=True)
    args = parser.parse_args(argv)
    thread = args.thread_id

    r = run(["gh", "api", "graphql", "-f", f"query={REPLY}", "-f", f"id={thread}", "-f", f"body={args.body}"])
    if r.returncode != 0:
        raise Fail(f"Reply to {thread} failed; the thread was left open: {output(r)}")
    url = json.loads(r.stdout)["data"]["addPullRequestReviewThreadReply"]["comment"]["url"]

    r = run(["gh", "api", "graphql", "-f", f"query={RESOLVE}", "-f", f"id={thread}"])
    if r.returncode != 0:
        raise Fail(f"Replied on {thread} ({url}) but resolving it failed: {output(r)}")

    print(f"resolved {thread} {url}")
    return 0


if __name__ == "__main__":
    entry(main)
