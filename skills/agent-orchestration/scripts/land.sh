#!/usr/bin/env bash
# Land an approved PR whose head is checked out in <worktree> (a lane worktree, ../<repo>-wt-<lane>): merge the
# base if it moved, prove the carry-over, push once, wait for the required check, squash-merge on the exact head.
#   land.sh <pr> <worktree> --check <name> --subject "<text>" --body-file <path>
#           [--base main] [--max-rounds 4] [--check-minutes 40]
# Prints one final line: LANDED pr=<n> head=<sha7>, or STOPPED pr=<n> <reason> with the facts a human needs
# (merge state, unresolved threads, failing checks). It never loops past --max-rounds and never retries a
# STOPPED cause, so a blocked PR costs one wake, not a watcher that spins.
set -uo pipefail
. "$(dirname "$0")/lib.sh"
usage='usage: land.sh <pr> <worktree> --check <name> --subject "<text>" --body-file <path> [--base main] [--max-rounds 4] [--check-minutes 40]'
[ $# -ge 2 ] || { echo "$usage" >&2; exit 1; }
pr=$1; wt=$2; shift 2
[[ $pr =~ ^[0-9]+$ ]] || { echo "PR must be a number, got $pr" >&2; exit 1; }
[ -d "$wt" ] || { echo "no worktree at $wt" >&2; exit 1; }
check=""; subject=""; body=""; base=main; max=4
# The wait for the required check. A check that runs longer stops the script with the facts rather than
# spinning; pass --check-minutes for a slower suite.
check_minutes=40
while [ $# -gt 0 ]; do
  case $1 in
    --check) need_value "$1" $#; check=$2; shift 2 ;;
    --subject) need_value "$1" $#; subject=$2; shift 2 ;;
    --body-file) need_value "$1" $#; body=$2; shift 2 ;;
    --base) need_value "$1" $#; base=$2; shift 2 ;;
    --max-rounds) need_value "$1" $#; max=$2; shift 2 ;;
    --check-minutes) need_value "$1" $#; check_minutes=$2; shift 2 ;;
    *) echo "unknown option $1; $usage" >&2; exit 1 ;;
  esac
done
[ -n "$check" ] && [ -n "$subject" ] && [ -f "$body" ] || { echo "$usage" >&2; exit 1; }
[[ $max =~ ^[1-9][0-9]*$ ]] && [[ $check_minutes =~ ^[1-9][0-9]*$ ]] || { echo "--max-rounds and --check-minutes take positive whole numbers" >&2; exit 1; }
# One check-runs call per 20 s is three a minute, far inside GitHub's hourly API limit.
check_poll_seconds=${LAND_POLL_SECONDS:-20}
# mergeStateStatus reads UNKNOWN while GitHub computes it in the background; 12 polls of 10 s give it two
# minutes before the script stops with the state it saw.
mergeable_poll_seconds=${LAND_POLL_SECONDS:-10}
mergeable_polls=12
check_polls=$(( check_minutes * 60 / 20 ))
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner) || { echo "STOPPED pr=$pr gh cannot read the repository"; exit 0; }
stop() { echo "STOPPED pr=$pr $*"; exit 0; }
facts() {
  gh pr view "$pr" --json mergeStateStatus,reviewDecision --jq '"mergeState=" + .mergeStateStatus + " review=" + (.reviewDecision // "none")'
  owner=${repo%/*}; name=${repo#*/}
  gh api graphql -f query="query{repository(owner:\"$owner\",name:\"$name\"){pullRequest(number:$pr){reviewThreads(first:100){nodes{isResolved}}}}}" \
    --jq '"unresolved_threads=" + ([.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved|not)]|length|tostring)'
  gh api "repos/$repo/commits/$(git -C "$wt" rev-parse HEAD)/check-runs" --jq '.check_runs[] | select(.conclusion != "success" and .conclusion != null) | "check " + .name + "=" + .conclusion'
}
for round in $(seq 1 "$max"); do
  git -C "$wt" fetch -q origin || stop "fetch failed"
  prev=$(git -C "$wt" rev-parse HEAD)
  if ! git -C "$wt" merge-base --is-ancestor "origin/$base" HEAD; then
    # A union merge attribute on append-only files (decision logs) keeps this merge clean; anything else stops.
    if ! git -C "$wt" -c core.editor=true merge -q --no-edit "origin/$base" >/dev/null 2>&1; then
      conflicted=$(git -C "$wt" diff --name-only --diff-filter=U | tr '\n' ' ')
      git -C "$wt" merge --abort
      stop "merge of $base conflicts in: $conflicted"
    fi
    new=$(git -C "$wt" rev-parse HEAD)
    [ "$(git -C "$wt" rev-parse "$new^1")" = "$prev" ] || stop "first parent of ${new:0:7} is not the previous head"
    git -C "$wt" merge-base --is-ancestor "$new^2" "origin/$base" || stop "second parent of ${new:0:7} is not on $base"
    extra=$(git -C "$wt" show --remerge-diff --format= --name-only "$new" | sort -u | tr '\n' ' ')
    [ -z "$extra" ] || stop "remerge-diff touches: $extra(needs a delta review)"
    git -C "$wt" push -q origin HEAD || stop "push failed"
    gh pr comment "$pr" --body "Carry-over check (automated) for head \`${new:0:7}\`: first parent is the previous head \`${prev:0:7}\`, second parent \`$(git -C "$wt" rev-parse --short "$new^2")\` is on $base, and \`--remerge-diff\` is empty." >/dev/null
  fi
  head=$(git -C "$wt" rev-parse HEAD)
  st=none
  for _ in $(seq 1 "$check_polls"); do
    st=$(gh api "repos/$repo/commits/$head/check-runs" --jq "[.check_runs[]|select(.name==\"$check\")]|if length==0 then \"none\" elif all(.status==\"completed\") then (map(.conclusion)|join(\",\")) else \"running\" end" 2>/dev/null || echo none)
    case "$st" in none|running) sleep "$check_poll_seconds" ;; *) break ;; esac
  done
  [ "$st" = success ] || stop "$check=$st on ${head:0:7} after up to ${check_minutes} min; $(facts | tr '\n' ' ')"
  cur=""
  for _ in $(seq 1 "$mergeable_polls"); do
    cur=$(gh pr view "$pr" --json headRefOid,mergeStateStatus --jq '.headRefOid+" "+.mergeStateStatus')
    case "$cur" in *UNKNOWN) sleep "$mergeable_poll_seconds" ;; *) break ;; esac
  done
  case "$cur" in
    "$head CLEAN")
      gh pr merge "$pr" --squash --match-head-commit "$head" --subject "$subject" --body-file "$body" >/dev/null \
        || stop "merge failed on ${head:0:7}; $(facts | tr '\n' ' ')"
      echo "LANDED pr=$pr head=${head:0:7}"; exit 0 ;;
    "$head BEHIND") echo "round $round: $base moved; merging again" >&2 ;;
    "$head BLOCKED"|"$head DIRTY"|"$head UNSTABLE") stop "state=${cur#* } on ${head:0:7}; $(facts | tr '\n' ' ')" ;;
    *) stop "unexpected state '$cur' for ${head:0:7}; $(facts | tr '\n' ' ')" ;;
  esac
done
stop "after $max rounds; $(facts | tr '\n' ' ')"
