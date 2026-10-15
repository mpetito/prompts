"""Wait for a PR's gates on one exact head, then print one line. Exits early if the head moves.
  watch_gates.py <pr> <full head sha> [--check <name>] [--reviewers <name,...>] [--minutes <n>]
--reviewers names automated reviewers (copilot, codex, claude) that must each report on the head, findings or none;
the pull-request skill's get_pr_feedback.py decides whether one has.
Prints: GATES pr=<n> head=<sha7> check=<result|n/a|timeout> reviewers=<name:reviewed|timeout,...|n/a>
          unresolved_threads=<n|?>  (one line)
    or: MOVED pr=<n> head=<sha7> now=<sha7>
"""
import json
import re
import sys
import time
from pathlib import Path

import lib

USAGE = "usage: watch_gates.py <pr> <full head sha> [--check <name>] [--reviewers <name,...>] [--minutes <n>]"
OPTIONS = {"--check": True, "--reviewers": True, "--minutes": True}
FEEDBACK = Path(__file__).resolve().parents[2] / "pull-request" / "scripts" / "get_pr_feedback.py"
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
    check, minutes = opts.get("--check", ""), opts.get("--minutes", "25")
    pending = [n for n in opts.get("--reviewers", "").split(",") if n]
    if not re.fullmatch(r"[1-9][0-9]*", minutes):
        raise lib.Fail("--minutes takes a positive whole number")
    r = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")
    if r.returncode:
        raise lib.Fail("gh cannot read the repository")
    repo = r.stdout.strip()
    check_result, reviewed = "", []
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
        if pending:
            status = feedback(repo, pr)
            if status:
                unknown = [n for n in pending if n not in status["automatedReviewers"]]
                if unknown:
                    raise lib.Fail(f"unknown reviewer {','.join(unknown)}; known: "
                                   f"{','.join(status['automatedReviewers'])}")
                reviewed += [n for n in pending if status["automatedReviewers"][n]["reviewedHead"]]
                pending = [n for n in pending if n not in reviewed]
        if (not check or check_result) and not pending:
            break
        sleep(POLL_SECONDS)
    status = feedback(repo, pr)
    threads = len(status["threads"]) if status else "?"
    check_out = (check_result or "timeout") if check else "n/a"
    reviewers_out = ",".join([f"{n}:reviewed" for n in reviewed] + [f"{n}:timeout" for n in pending]) or "n/a"
    print(f"GATES pr={pr} head={head[:7]} check={check_out} reviewers={reviewers_out} unresolved_threads={threads}")
    return 0


def feedback(repo, pr):
    """The pull request's feedback from get_pr_feedback.py, or None when it fails; tests replace it."""
    r = lib.run([sys.executable, str(FEEDBACK), "--pr", pr, "--repo", repo])
    return json.loads(r.stdout) if r.returncode == 0 else None


def gh(*args):
    return lib.run(["gh", *args])


if __name__ == "__main__":
    lib.entry(main)
