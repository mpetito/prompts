"""Wait for a PR's gates on one exact head, then print one line. Exits early if the head moves.
  watch_gates.py <pr> <full head sha> [--check <name>] [--bot <login regex>] [--minutes <n>]
Prints: GATES pr=<n> head=<sha7> check=<result|n/a|timeout> bot=<reviewed|n/a|timeout> unresolved_threads=<n>
    or: MOVED pr=<n> head=<sha7> now=<sha7>
"""
import re
import time

import lib

USAGE = "usage: watch_gates.py <pr> <full head sha> [--check <name>] [--bot <login regex>] [--minutes <n>]"
OPTIONS = {"--check": True, "--bot": True, "--minutes": True}
# Four polls a minute notices a finished gate within 15 s at a cost of three API calls per poll.
POLL_SECONDS = 15
# Every wait goes through here, so tests replace it.
sleep = time.sleep


def main(argv):
    if len(argv) < 2:
        raise lib.Fail(USAGE)
    pr, head = argv[:2]
    if not re.fullmatch(r"[0-9]+", pr):
        raise lib.Fail(f"PR must be a number, got {pr}")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise lib.Fail(f"head must be a full 40-character SHA, got {head}")
    opts = lib.only_options(argv[2:], OPTIONS, USAGE)
    # 25 minutes: past it the watcher reports timeout, so the thread decides instead of waiting on a stuck gate;
    # pass --minutes for slower gates.
    check, bot, minutes = opts.get("--check", ""), opts.get("--bot", ""), opts.get("--minutes", "25")
    if not re.fullmatch(r"[1-9][0-9]*", minutes):
        raise lib.Fail("--minutes takes a positive whole number")
    r = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")
    if r.returncode:
        raise lib.Fail("gh cannot read the repository")
    repo = r.stdout.strip()
    check_result = bot_result = ""
    for _ in range(int(minutes) * 4):
        r = gh("pr", "view", pr, "--json", "headRefOid", "--jq", ".headRefOid")
        cur = r.stdout.strip() if r.returncode == 0 else ""
        if cur and cur != head:
            print(f"MOVED pr={pr} head={head[:7]} now={cur[:7]}")
            return 0
        if check and not check_result:
            r = gh("api", f"repos/{repo}/commits/{head}/check-runs", "--jq",
                   f'[.check_runs[] | select(.name=="{check}")] | if length==0 then "none" elif '
                   'all(.status=="completed") then (map(.conclusion)|join(",")) else "running" end')
            st = r.stdout.strip() if r.returncode == 0 else "none"
            if st not in ("none", "running"):
                check_result = st
        if bot and not bot_result:
            r = gh("api", f"repos/{repo}/pulls/{pr}/reviews", "--jq",
                   f'[.[] | select(.user.login|test("{bot}")) | select(.commit_id=="{head}")] | length')
            if r.returncode == 0 and r.stdout.strip().isdigit() and int(r.stdout) > 0:
                bot_result = "reviewed"
        if (not check or check_result) and (not bot or bot_result):
            break
        sleep(POLL_SECONDS)
    owner, name = repo.split("/", 1)
    r = gh("api", "graphql", "-f",
           f'query=query{{repository(owner:"{owner}",name:"{name}"){{pullRequest(number:{pr})'
           '{reviewThreads(first:100){nodes{isResolved}}}}}',
           "--jq", "[.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved|not)]|length")
    unresolved = r.stdout.strip() if r.returncode == 0 else "?"
    check_out = (check_result or "timeout") if check else "n/a"
    bot_out = (bot_result or "timeout") if bot else "n/a"
    print(f"GATES pr={pr} head={head[:7]} check={check_out} bot={bot_out} unresolved_threads={unresolved}")
    return 0


def gh(*args):
    return lib.run(["gh", *args])


if __name__ == "__main__":
    lib.entry(main)
