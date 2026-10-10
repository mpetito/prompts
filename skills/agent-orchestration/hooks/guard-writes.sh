#!/usr/bin/env bash
# PreToolUse hook for Edit, Write, MultiEdit and NotebookEdit. The orchestration thread writes only inside its
# coordination worktree (../<repo>-orch-<build>): the owner's main checkout and the workers' lane worktrees
# (../<repo>-wt-<lane>) belong to others, and a change there goes to a worker. Input: Claude Code's hook JSON
# on stdin. A session outside git, or in a worktree with no .orchestration/state.md, is not an orchestration
# thread, so the hook allows everything silently.
set -u
. "$(dirname "$0")/../scripts/lib.sh"
input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -n "$path" ] && [ -n "$cwd" ] || exit 0
top=$(toplevel "$cwd") || exit 0
[ -f "$top/.orchestration/state.md" ] || exit 0
top=$(realpath -m -- "$top")
case $path in /*) target=$path ;; *) target="$cwd/$path" ;; esac
target=$(realpath -m -- "$target")
case "$target/" in "$top/"*) exit 0 ;; esac
jq -n --arg r "The orchestration thread edits only its coordination worktree, $top. $target is outside it (the owner's checkout, a lane worktree, or elsewhere): brief a worker to make that change in its own worktree." \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
exit 0
