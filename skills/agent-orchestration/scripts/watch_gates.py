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
# Four polls a minute notices a finished check within 15 s at two API calls a poll. Reviewers take minutes and a
# feedback read costs about six calls, so reviewer state is read once a minute.
POLL_SECONDS = 15
REVIEWER_EVERY = 4
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
    for poll in range(int(minutes) * 4):
        r = gh("pr", "view", pr, "--json", "headRefOid", "--jq", ".headRefOid")
        cur = r.stdout.strip() if r.returncode == 0 else ""
        if cur and cur != head:
            return moved(pr, head, cur)
        if check and not check_result:
            st = lib.check_state(repo, head, check)
            if st not in ("none", "running"):
                check_result = st
        if pending and poll % REVIEWER_EVERY == 0:
            status = feedback(repo, pr)
            if status and status["head"] != head:
                return moved(pr, head, status["head"])
            pending = settle(status, pending, reviewed)
        if (not check or check_result) and not pending:
            break
        sleep(POLL_SECONDS)
    # The last read also settles reviewers, so one finishing in the final minute is not reported as timeout.
    status = feedback(repo, pr)
    if status and status["head"] != head:
        return moved(pr, head, status["head"])
    pending = settle(status, pending, reviewed)
    threads = len(status["threads"]) if status else "?"
    check_out = (check_result or "timeout") if check else "n/a"
    reviewers_out = ",".join([f"{n}:reviewed" for n in reviewed] + [f"{n}:timeout" for n in pending]) or "n/a"
    print(f"GATES pr={pr} head={head[:7]} check={check_out} reviewers={reviewers_out} unresolved_threads={threads}")
    return 0


def moved(pr, head, now):
    print(f"MOVED pr={pr} head={head[:7]} now={now[:7]}")
    return 0


def settle(status, pending, reviewed):
    """The reviewers still pending once status, feedback for the watched head or None, is read; each one it shows
    finished is appended to reviewed."""
    if not status:
        return pending
    unknown = [n for n in pending if n not in status["automatedReviewers"]]
    if unknown:
        raise lib.Fail(f"unknown reviewer {','.join(unknown)}; known: {','.join(status['automatedReviewers'])}")
    reviewed += [n for n in pending if status["automatedReviewers"][n]["reviewedHead"]]
    return [n for n in pending if n not in reviewed]


def feedback(repo, pr):
    """The pull request's feedback from get_pr_feedback.py, or None when it fails; tests replace it."""
    r = lib.run([sys.executable, str(FEEDBACK), "--pr", pr, "--repo", repo])
    return json.loads(r.stdout) if r.returncode == 0 else None


def gh(*args):
    return lib.run(["gh", *args])


if __name__ == "__main__":
    lib.entry(main)
