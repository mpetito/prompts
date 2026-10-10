#!/usr/bin/env bash
# PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit in an orchestration thread and in the workers it
# starts (a worker's input carries agent_id). Writes go to an allowlist: the coordination worktree (except the
# files that configure the thread's own session), the repository's other registered worktrees (the lanes) and temp
# folders. Refused for both: the owner's checkout, which may hold the owner's uncommitted work; configuration
# (settings anywhere, the orchestration registry, the thread record); and everything else, such as the home
# folder. The thread writing in a lane's worktree goes ahead with advice; a worker passes silently.
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
case "$target/" in
  "$top/"*)
    for p in "$raw" "$target"; do
      session_config "$p" "$top" \
        && deny "$p configures the thread's own session (project settings, agents, skills, hooks, .mcp.json or CLAUDE.md in the coordination worktree). Neither the thread nor its workers change it: send MAIN the diff for the owner."
    done
    exit 0 ;;
esac
if build_worktree "$target" "$top"; then
  [ -z "$worker" ] || exit 0
  advise "You wrote $target, in a lane's worktree outside your coordination worktree, $top. That lane's worker owns it: a change there usually goes to the worker as a ruling, so it lands with the worker's tests and review. A deliberate small fix is fine; record it with state.sh log."
fi
scratch_path "$target" && exit 0
deny "$target is outside this build: writes go to the coordination worktree, the repository's lane worktrees and temp folders. If the change belongs elsewhere, such as the owner's home folder or another repository, send MAIN the diff for the owner."
