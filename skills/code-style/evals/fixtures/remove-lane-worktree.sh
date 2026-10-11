#!/usr/bin/env bash
# Removes a lane's worktree and branch once the orchestrator has merged the lane.
# The build's orchestrator agent runs it: remove-lane-worktree.sh <lane>
set -euo pipefail

lane="${1:?usage: remove-lane-worktree.sh <lane>}"
root="$(git rev-parse --show-toplevel)"
wt="$root/.worktrees/$lane"
branch="lane/$lane"
target="$(git -C "$root" branch --show-current)"

if [[ ! -d "$wt" ]]; then
  echo "no worktree at $wt; nothing to remove"
  exit 0
fi

if [[ -n "$(git -C "$wt" status --porcelain --untracked-files=no)" ]]; then
  echo "warning: $wt has uncommitted changes; they will be lost" >&2
fi

git -C "$root" worktree remove --force "$wt"

if git -C "$root" merge-base --is-ancestor "$branch" "$target"; then
  git -C "$root" branch -d "$branch"
else
  echo "warning: $branch is not merged into $target; keeping the branch" >&2
fi

echo "removed $wt"
