#!/usr/bin/env bash
# PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit in an orchestration thread and in the workers it
# starts (a worker's input carries agent_id). For both it refuses two things: a write into the owner's checkout,
# which may hold the owner's uncommitted work, and a write to configuration (Claude Code or Codex settings, the
# orchestration registry, the thread record). The thread writing anywhere else outside its coordination worktree,
# such as a lane worktree, goes ahead with advice; a worker passes silently.
# The session is identified from the folder it started in ($CLAUDE_PROJECT_DIR), so a cd changes nothing. A path
# counts as the owner's checkout unless git places it in one of the repository's linked worktrees nested there.
set -u
. "$(dirname "$0")/../scripts/lib.sh"
input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
worker=$(printf '%s' "$input" | jq -r '.agent_id // empty')
[ -n "$path" ] && [ -n "$cwd" ] || exit 0
case $path in /*) raw=$path ;; *) raw="$cwd/$path" ;; esac
raw=$(realpath -ms -- "$raw")
target=$(realpath -m -- "$raw")
top=$(session_top "$cwd" | xargs -r -d '\n' realpath -m --)
for p in "$raw" "$target"; do
  if config_file "$p" "${top:-/nonexistent}"; then
    deny "$p configures Claude Code, Codex or this orchestration (settings, the registry, the thread record). Neither the thread nor its workers edit it: send MAIN the diff, and MAIN applies it once the owner approves."
  fi
done
[ -n "$top" ] || exit 0
[ -f "$top/.orchestration/thread.md" ] || [ -f "$top/.orchestration/state.md" ] || exit 0
if ! owners=$(owner_checkouts "$top"); then
  case "$target/" in "$top/"*) exit 0 ;; esac
  deny "git could not name the owner's checkout from $top, so a write outside the coordination worktree is refused."
fi
while IFS= read -r owner; do
  [ -n "$owner" ] && [ "$owner" != "$top" ] || continue
  in_checkout "$target" "$owner" || continue
  if [ -n "$worker" ]; then
    deny "$target is in the owner's checkout, $owner, which may hold the owner's uncommitted work. Workers edit only their own lane worktree; make the change there."
  fi
  deny "$target is in the owner's checkout, $owner, which may hold the owner's uncommitted work. Brief a worker to make the change in its lane worktree, or send MAIN the diff for the owner to apply."
done <<< "$owners"
[ -z "$worker" ] || exit 0
case "$target/" in "$top/"*) exit 0 ;; esac
advise "You wrote $target, outside your coordination worktree, $top. If it belongs to a lane, that lane's worker owns it: a change there usually goes to the worker as a ruling, so it lands with the worker's tests and review. A deliberate small fix is fine; record it with state.sh log."
