#!/usr/bin/env bash
# PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit in an orchestration thread and in the workers it
# starts. It refuses one thing: a write into the owner's checkout (CHECKOUT in .orchestration/thread.md, else the
# main checkout), which may hold the owner's uncommitted work. A worktree nested inside it, such as a subagent's
# under .claude/worktrees/, is not the checkout. The thread writing anywhere else outside its coordination
# worktree, such as a lane worktree, goes ahead with advice; a worker (input with agent_id) passes silently.
# Outside git, or in a worktree with no .orchestration/state.md, this is not an orchestration thread: silent.
set -u
. "$(dirname "$0")/../scripts/lib.sh"
input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
worker=$(printf '%s' "$input" | jq -r '.agent_id // empty')
[ -n "$path" ] && [ -n "$cwd" ] || exit 0
top=$(toplevel "$cwd") || exit 0
[ -f "$top/.orchestration/state.md" ] || exit 0
top=$(realpath -m -- "$top")
case $path in /*) target=$path ;; *) target="$cwd/$path" ;; esac
target=$(realpath -m -- "$target")
owner=$(owner_checkout "$top" || true)
home_tree=$(worktree_of "$target")
if [ -n "$owner" ] && [ "$owner" != "$top" ] && [ "$home_tree" = "$owner" ]; then
  if [ -n "$worker" ]; then
    deny "$target is in the owner's checkout, $owner, which may hold the owner's uncommitted work. Workers edit only their own lane worktree; make the change there."
  fi
  deny "$target is in the owner's checkout, $owner, which may hold the owner's uncommitted work. Brief a worker to make the change in its lane worktree, or send MAIN the diff for the owner to apply."
fi
[ -z "$worker" ] || exit 0
case "$target/" in "$top/"*) exit 0 ;; esac
advise "You wrote $target, outside your coordination worktree, $top. If it belongs to a lane, that lane's worker owns it: a change there usually goes to the worker as a ruling, so it lands with the worker's tests and review. A deliberate small fix is fine; record it with state.sh log."
