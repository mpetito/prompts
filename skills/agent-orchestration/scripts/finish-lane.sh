#!/usr/bin/env bash
# Retire a lane's worktree without losing its evidence: archive its scratch directory and its ignored files
# (eval runs, logs; not dependency or cache folders) first, refuse while an agent still runs there, then remove
# the worktree and delete the local branch. Ignored files land under <archive dir>/ignored/ at their own paths.
#   finish-lane.sh <lane worktree, e.g. ../<repo>-wt-<lane>> <archive dir> [--scratch <relative path, default .orchestration/tmp>] [--keep-branch]
# Prints one line per step done; refusals go to stderr with exit 1.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
usage='usage: finish-lane.sh <worktree> <archive dir> [--scratch <relative path>] [--keep-branch]'
[ $# -ge 2 ] || { echo "$usage" >&2; exit 1; }
wt=$1; archive=$2; shift 2
scratch=.orchestration/tmp; keep=0
while [ $# -gt 0 ]; do
  case $1 in
    --scratch) need_value "$1" $#; scratch=$2; shift 2 ;;
    --keep-branch) keep=1; shift ;;
    *) echo "unknown option $1; $usage" >&2; exit 1 ;;
  esac
done
[ -d "$wt" ] || { echo "no worktree at $wt" >&2; exit 1; }
archive=$(canon "$archive")
git -C "$wt" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "not a git worktree: $wt" >&2; exit 1; }
# Only inside Herdr can a peer agent be running in the worktree; elsewhere there is nothing to ask.
if command -v herdr >/dev/null && [ "${HERDR_ENV:-}" = 1 ]; then
  # herdr reports absolute working directories in its own platform's form, and a lane's sibling may share its name
  # as a prefix.
  wtc=$(canon "$wt")
  live=$(herdr agent list 2>/dev/null | jq -r '.result.agents[]? | select(.cwd) | [.cwd, .name // .pane_id] | @tsv' \
    | while IFS=$'\t' read -r c name; do case "$(canon "$c")/" in "$wtc/"*) echo "$name" ;; esac; done || true)
  [ -z "$live" ] || { echo "refusing: agent(s) still run in $wt: $live" >&2; exit 1; }
fi
if [ -d "$wt/$scratch" ]; then
  mkdir -p "$archive"
  cp -a "$wt/$scratch/." "$archive/"
  echo "archived $wt/$scratch to $archive"
fi
# A failed listing would archive nothing and still remove the worktree, so it stops everything.
archive_ignored "$wt" "$archive" "$scratch" || exit 1
# Untracked output names the first unignored ancestor, so ".orchestration/" may stand for the scratch dir.
leftover=$(git -C "$wt" status --porcelain | while IFS= read -r line; do
  path=${line:3}
  case "$scratch/" in "$path"*) continue ;; esac
  case "$path" in "$scratch"*) continue ;; esac
  printf '%s\n' "$line"
done)
[ -z "$leftover" ] || { echo "refusing: uncommitted changes in $wt:"; echo "$leftover"; exit 1; } >&2
branch=$(git -C "$wt" rev-parse --abbrev-ref HEAD)
# --show-toplevel would name the worktree itself; the common git dir sits under the main checkout.
main=$(dirname "$(git -C "$wt" rev-parse --path-format=absolute --git-common-dir)")
# --force only skips git's own untracked-file check; the leftover check above already proved that
# nothing but the archived scratch directory is untracked and nothing is modified.
git -C "$main" worktree remove --force "$wt"
echo "removed worktree $wt"
if [ "$keep" = 0 ] && [ "$branch" != HEAD ]; then
  git -C "$main" branch -D "$branch" >/dev/null 2>&1 && echo "deleted branch $branch" || true
fi
