"""Land an approved PR whose head is checked out in <worktree> (a lane worktree, ../<repo>-wt-<lane>): merge the base
if it moved, prove the carry-over, push once, wait for the required check, squash-merge on the exact head.
  land.py <pr> <worktree> --check <name> --subject "<text>" --body-file <path>
          [--base main] [--max-rounds 4] [--check-minutes 40]
Prints one final line: LANDED pr=<n> head=<sha7>, or STOPPED pr=<n> <reason> with the facts a human needs (merge
state, unresolved threads, failing checks). It never loops past --max-rounds and never retries a STOPPED cause, so a
blocked PR costs one wake, not a watcher that spins.
"""
import os
import re
import sys
import time

import lib

USAGE = ('usage: land.py <pr> <worktree> --check <name> --subject "<text>" --body-file <path> [--base main] '
         '[--max-rounds 4] [--check-minutes 40]')
OPTIONS = {"--check": True, "--subject": True, "--body-file": True, "--base": True, "--max-rounds": True,
           "--check-minutes": True}
# One check-runs call per 20 s is three a minute, far inside GitHub's hourly API limit.
CHECK_POLL_SECONDS = 20
# mergeStateStatus reads UNKNOWN while GitHub computes it in the background; 12 polls of 10 s give it two minutes
# before the script stops with the state it saw.
MERGEABLE_POLL_SECONDS = 10
MERGEABLE_POLLS = 12
# Every wait goes through here, so tests replace it.
sleep = time.sleep


class Stopped(Exception):
    """A STOPPED line's reason."""


def main(argv):
    if len(argv) < 2:
        raise lib.Fail(USAGE)
    pr, wt = argv[:2]
    if not re.fullmatch(r"[0-9]+", pr):
        raise lib.Fail(f"PR must be a number, got {pr}")
    if not os.path.isdir(wt):
        raise lib.Fail(f"no worktree at {wt}")
    opts = lib.only_options(argv[2:], OPTIONS, USAGE)
    if not (opts.get("--check") and opts.get("--subject") and os.path.isfile(opts.get("--body-file", ""))):
        raise lib.Fail(USAGE)
    rounds, minutes = opts.get("--max-rounds", "4"), opts.get("--check-minutes", "40")
    if not (re.fullmatch(r"[1-9][0-9]*", rounds) and re.fullmatch(r"[1-9][0-9]*", minutes)):
        raise lib.Fail("--max-rounds and --check-minutes take positive whole numbers")
    try:
        print(Lander(pr, wt, opts).land(int(rounds), int(minutes)))
    except Stopped as e:
        print(f"STOPPED pr={pr} {e}")
    return 0


class Lander:
    def __init__(self, pr, wt, opts):
        self.pr, self.wt, self.check = pr, wt, opts["--check"]
        self.subject, self.body, self.base = opts["--subject"], opts["--body-file"], opts.get("--base", "main")
        r = gh("repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner")
        if r.returncode:
            raise Stopped("gh cannot read the repository")
        self.repo = r.stdout.strip()

    def git(self, *args):
        return lib.git(self.wt, *args)

    def land(self, rounds, minutes):
        """Up to rounds rounds of: bring the base in, wait up to minutes for the check, merge on a CLEAN head. The
        LANDED line, or Stopped."""
        for n in range(1, rounds + 1):
            self.merge_base()
            head = self.git("rev-parse", "HEAD")
            st = "none"
            for _ in range(minutes * 60 // CHECK_POLL_SECONDS):
                r = gh("api", f"repos/{self.repo}/commits/{head}/check-runs", "--jq",
                       f'[.check_runs[]|select(.name=="{self.check}")]|if length==0 then "none" elif '
                       'all(.status=="completed") then (map(.conclusion)|join(",")) else "running" end')
                st = r.stdout.strip() if r.returncode == 0 else "none"
                if st not in ("none", "running"):
                    break
                sleep(CHECK_POLL_SECONDS)
            if st != "success":
                raise Stopped(f"{self.check}={st} on {head[:7]} after up to {minutes} min; {self.facts()}")
            cur = ""
            for _ in range(MERGEABLE_POLLS):
                cur = gh("pr", "view", self.pr, "--json", "headRefOid,mergeStateStatus", "--jq",
                         '.headRefOid+" "+.mergeStateStatus').stdout.rstrip("\n")
                if not cur.endswith("UNKNOWN"):
                    break
                sleep(MERGEABLE_POLL_SECONDS)
            state = cur.split(" ", 1)[1] if cur.startswith(f"{head} ") else None
            if state == "CLEAN":
                if gh("pr", "merge", self.pr, "--squash", "--match-head-commit", head, "--subject", self.subject,
                      "--body-file", self.body).returncode:
                    raise Stopped(f"merge failed on {head[:7]}; {self.facts()}")
                return f"LANDED pr={self.pr} head={head[:7]}"
            if state == "BEHIND":
                print(f"round {n}: {self.base} moved; merging again", file=sys.stderr)
            elif state in ("BLOCKED", "DIRTY", "UNSTABLE"):
                raise Stopped(f"state={state} on {head[:7]}; {self.facts()}")
            else:
                raise Stopped(f"unexpected state '{cur}' for {head[:7]}; {self.facts()}")
        raise Stopped(f"after {rounds} rounds; {self.facts()}")

    def merge_base(self):
        """Fetch, and when origin/<base> moved, merge it, prove the merge carries nothing else over, push it and
        record the proof on the PR."""
        if self.git("fetch", "-q", "origin") is None:
            raise Stopped("fetch failed")
        prev, base = self.git("rev-parse", "HEAD"), self.base
        if self.git("merge-base", "--is-ancestor", f"origin/{base}", "HEAD") is not None:
            return
        # A union merge attribute on append-only files (decision logs) keeps this merge clean; anything else stops.
        if self.git("-c", "core.editor=true", "merge", "-q", "--no-edit", f"origin/{base}") is None:
            conflicted = lib.run(["git", "-C", self.wt, "diff", "--name-only", "--diff-filter=U"]).stdout
            self.git("merge", "--abort")
            raise Stopped(f"merge of {base} conflicts in: {conflicted.replace(chr(10), ' ')}")
        new = self.git("rev-parse", "HEAD")
        if self.git("rev-parse", f"{new}^1") != prev:
            raise Stopped(f"first parent of {new[:7]} is not the previous head")
        if self.git("merge-base", "--is-ancestor", f"{new}^2", f"origin/{base}") is None:
            raise Stopped(f"second parent of {new[:7]} is not on {base}")
        touched = lib.run(["git", "-C", self.wt, "show", "--remerge-diff", "--format=", "--name-only", new]).stdout
        extra = "".join(f"{p} " for p in sorted(set(touched.splitlines())))
        if extra:
            raise Stopped(f"remerge-diff touches: {extra}(needs a delta review)")
        if self.git("push", "-q", "origin", "HEAD") is None:
            raise Stopped("push failed")
        gh("pr", "comment", self.pr, "--body",
           f"Carry-over check (automated) for head `{new[:7]}`: first parent is the previous head `{prev[:7]}`, "
           f"second parent `{self.git('rev-parse', '--short', f'{new}^2')}` is on {base}, and `--remerge-diff` is "
           "empty.")

    def facts(self):
        """The merge state, review decision, unresolved thread count and failing checks, on one line."""
        owner, name = self.repo.split("/", 1)
        head = self.git("rev-parse", "HEAD")
        out = gh("pr", "view", self.pr, "--json", "mergeStateStatus,reviewDecision", "--jq",
                 '"mergeState=" + .mergeStateStatus + " review=" + (.reviewDecision // "none")').stdout
        out += gh("api", "graphql", "-f",
                  f'query=query{{repository(owner:"{owner}",name:"{name}"){{pullRequest(number:{self.pr})'
                  '{reviewThreads(first:100){nodes{isResolved}}}}}',
                  "--jq", '"unresolved_threads=" + ([.data.repository.pullRequest.reviewThreads.nodes[]'
                          '|select(.isResolved|not)]|length|tostring)').stdout
        out += gh("api", f"repos/{self.repo}/commits/{head}/check-runs", "--jq",
                  '.check_runs[] | select(.conclusion != "success" and .conclusion != null) | '
                  '"check " + .name + "=" + .conclusion').stdout
        return out.replace("\n", " ")


def gh(*args):
    return lib.run(["gh", *args])


if __name__ == "__main__":
    lib.entry(main)
