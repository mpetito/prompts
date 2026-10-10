#!/usr/bin/env bash
# Land an approved lane when the build lands locally (LANDING: local in .orchestration/thread.md): check the lane's
# head is the approved commit, merge it --no-ff into orchestration/<build> in the coordination worktree, run the
# check command there, and undo the merge if the check fails. MAIN later brings orchestration/<build> into the base
# with thread.sh integrate.
#   land-local.sh <lane branch> <approved sha> --check "<command>" [--subject "<text>"]
# Run from the coordination worktree. Prints one final line: LANDED lane=<branch> head=<sha7> merge=<sha7>, or
# STOPPED lane=<branch> <reason>. The check's output goes to .orchestration/results/land-<lane>.log.
set -uo pipefail
. "$(dirname "$0")/lib.sh"
usage='usage: land-local.sh <lane branch> <approved sha> --check "<command>" [--subject "<text>"]'
[ $# -ge 2 ] || { echo "$usage" >&2; exit 1; }
lane=$1; sha=$2; shift 2
check=""; subject=""
while [ $# -gt 0 ]; do
  case $1 in
    --check) need_value "$1" $#; check=$2; shift 2 ;;
    --subject) need_value "$1" $#; subject=$2; shift 2 ;;
    *) echo "unknown option $1; $usage" >&2; exit 1 ;;
  esac
done
[ -n "$check" ] || { echo "$usage" >&2; exit 1; }
stop() { echo "STOPPED lane=$lane $*"; exit 0; }
top=$(toplevel "$PWD") || { echo "run land-local.sh from the coordination worktree" >&2; exit 1; }
[ "$(thread_field "$top" LANDING)" = local ] || stop "LANDING is not local in $top/.orchestration/thread.md; land pull requests with land.sh"
branch=$(git -C "$top" symbolic-ref --quiet --short HEAD) || stop "the coordination worktree has a detached HEAD"
[[ $branch == orchestration/* ]] || stop "the coordination worktree is on $branch, not orchestration/<build>"
{ git -C "$top" diff --quiet && git -C "$top" diff --cached --quiet; } || stop "uncommitted changes to tracked files in $top"
head=$(git -C "$top" rev-parse --verify -q "refs/heads/$lane^{commit}") || stop "no branch $lane"
approved=$(git -C "$top" rev-parse --verify -q "$sha^{commit}") || stop "no commit $sha"
[ "$head" = "$approved" ] || stop "head is ${head:0:7}, not the approved ${approved:0:7}; send the new commits to the reviewer as a delta"
git -C "$top" merge-base --is-ancestor "$head" HEAD && stop "${head:0:7} is already on $branch"
before=$(git -C "$top" rev-parse HEAD)
if ! git -C "$top" -c core.editor=true merge -q --no-ff -m "Merge $lane${subject:+: $subject}" "$head" >/dev/null 2>&1; then
  conflicted=$(git -C "$top" diff --name-only --diff-filter=U | tr '\n' ' ')
  git -C "$top" merge --abort >/dev/null 2>&1 || true
  stop "merging into $branch conflicts in: $conflicted(rebase the lane on $branch and review the delta)"
fi
merge=$(git -C "$top" rev-parse HEAD)
mkdir -p "$top/.orchestration/results"
log="$top/.orchestration/results/land-${lane//\//-}.log"
if ! (cd "$top" && bash -c "$check") > "$log" 2>&1; then
  # The tree was clean before the merge, so resetting to it drops only this merge.
  git -C "$top" reset -q --hard "$before"
  stop "check failed on merge ${merge:0:7}, merge undone; output in $log"
fi
echo "LANDED lane=$lane head=${head:0:7} merge=${merge:0:7}"
