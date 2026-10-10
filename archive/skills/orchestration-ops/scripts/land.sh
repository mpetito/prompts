#!/usr/bin/env bash
# Land an approved PR whose head is checked out in <worktree>: merge the base if it moved, prove the
# carry-over, push once, wait for the required check, squash-merge on the exact head.
#   land.sh <pr> <worktree> --check <name> --subject "<text>" --body-file <path> [--base main] [--max-rounds 4]
# Prints one final line: LANDED pr=<n> head=<sha7>, or STOPPED pr=<n> <reason> with the facts a human needs
# (merge state, unresolved threads, failing checks). It never loops past --max-rounds and never retries a
# STOPPED cause, so a blocked PR costs one wake, not a watcher that spins.
set -uo pipefail
pr=$1; wt=$2; shift 2
check=""; subject=""; body=""; base=main; max=4
while [ $# -gt 0 ]; do
  case $1 in
    --check) check=$2; shift 2 ;; --subject) subject=$2; shift 2 ;; --body-file) body=$2; shift 2 ;;
    --base) base=$2; shift 2 ;; --max-rounds) max=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 1 ;;
  esac
done
[ -n "$check" ] && [ -n "$subject" ] && [ -f "$body" ] || { echo "usage: land.sh <pr> <worktree> --check <name> --subject <text> --body-file <path>" >&2; exit 1; }
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
stop() { echo "STOPPED pr=$pr $*"; exit 0; }
facts() {
  gh pr view "$pr" --json mergeStateStatus,reviewDecision --jq '"mergeState=" + .mergeStateStatus + " review=" + (.reviewDecision // "none")'
  owner=${repo%/*}; name=${repo#*/}
  gh api graphql -f query="query{repository(owner:\"$owner\",name:\"$name\"){pullRequest(number:$pr){reviewThreads(first:100){nodes{isResolved}}}}}" \
    --jq '"unresolved_threads=" + ([.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved|not)]|length|tostring)'
  gh api "repos/$repo/commits/$(git -C "$wt" rev-parse HEAD)/check-runs" --jq '.check_runs[] | select(.conclusion != "success" and .conclusion != null) | "check " + .name + "=" + .conclusion'
}
for round in $(seq 1 "$max"); do
  git -C "$wt" fetch -q origin
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
    [ -z "$extra" ] || stop "remerge-diff touches: $extra (needs a delta review)"
    git -C "$wt" push -q origin HEAD || stop "push failed"
    gh pr comment "$pr" --body "Carry-over check (automated) for head \`${new:0:7}\`: first parent is the previous head \`${prev:0:7}\`, second parent \`$(git -C "$wt" rev-parse --short "$new^2")\` is on $base, and \`--remerge-diff\` is empty." >/dev/null
  fi
  head=$(git -C "$wt" rev-parse HEAD)
  st=none
  for _ in $(seq 1 120); do
    st=$(gh api "repos/$repo/commits/$head/check-runs" --jq "[.check_runs[]|select(.name==\"$check\")]|if length==0 then \"none\" elif all(.status==\"completed\") then (map(.conclusion)|join(\",\")) else \"running\" end" 2>/dev/null || echo none)
    case "$st" in none|running) sleep 20 ;; *) break ;; esac
  done
  [ "$st" = success ] || stop "$check=$st on ${head:0:7}; $(facts | tr '\n' ' ')"
  cur=""
  for _ in $(seq 1 12); do
    cur=$(gh pr view "$pr" --json headRefOid,mergeStateStatus --jq '.headRefOid+" "+.mergeStateStatus')
    case "$cur" in *UNKNOWN) sleep 10 ;; *) break ;; esac
  done
  case "$cur" in
    "$head CLEAN") gh pr merge "$pr" --squash --match-head-commit "$head" --subject "$subject" --body-file "$body" && { echo "LANDED pr=$pr head=${head:0:7}"; exit 0; } ;;
    "$head BEHIND") echo "round $round: $base moved; merging again" ;;
    "$head BLOCKED"|"$head DIRTY"|"$head UNSTABLE") stop "state=${cur#* } on ${head:0:7}; $(facts | tr '\n' ' ')" ;;
    *) stop "unexpected state '$cur' for ${head:0:7}; $(facts | tr '\n' ' ')" ;;
  esac
done
stop "after $max rounds; $(facts | tr '\n' ' ')"
