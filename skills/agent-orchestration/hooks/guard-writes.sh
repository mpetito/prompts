#!/usr/bin/env bash
# PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit in an orchestration thread and the workers it starts (a
# subagent worker's input carries agent_id; a lane session's hook runs with --lane). A reminder, not a boundary: the
# thread is trusted, and could write any file through Bash anyway. It refuses the one write a reminder would come too
# late for, into the owner's checkout, which may hold their uncommitted work; and it advises the thread when it writes
# outside its coordination worktree, where a change usually belongs to a worker. A session that is neither a lane
# nor started where a thread record or state file is, is not a thread: silent.
set -u
. "$(dirname "$0")/../scripts/lib.sh"
input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
worker=$(printf '%s' "$input" | jq -r '.agent_id // empty')
lane=""; [ "${1:-}" != --lane ] || { lane=1; worker=lane; }
[ -n "$path" ] && [ -n "$cwd" ] || exit 0
top=$(session_top "$cwd") || exit 0
# A lane session starts in its own worktree, which holds no thread files; its owner's checkout is the repository's.
[ -n "$lane" ] || [ -f "$top/.orchestration/thread.md" ] || [ -f "$top/.orchestration/state.md" ] || exit 0
top=$(realpath -m -- "$top")
case $path in /*) target=$path ;; *) target="$cwd/$path" ;; esac
target=$(realpath -m -- "$target")
while IFS= read -r owner; do
  [ -n "$owner" ] && [ "$owner" != "$top" ] || continue
  case "$target/" in "$owner/"*) ;; *) continue ;; esac
  if [ -n "$worker" ]; then
    deny "$target is in the owner's checkout, $owner, which may hold their uncommitted work. Make the change in your own lane worktree."
  fi
  deny "$target is in the owner's checkout, $owner, which may hold their uncommitted work. Brief a worker to make the change in a lane worktree, or send MAIN the diff for the owner."
done < <(owner_checkouts "$top" || true)
[ -z "$worker" ] || exit 0
case "$target/" in "$top/"*) exit 0 ;; esac
advise "You wrote $target, outside your coordination worktree, $top. Code belongs to the lane workers: a change in a lane's worktree usually goes to its worker as a ruling, so it lands with their tests and review. A deliberate small fix is fine; record it with state.sh log."
