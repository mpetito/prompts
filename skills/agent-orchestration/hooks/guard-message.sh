#!/usr/bin/env bash
# PreToolUse hook for SendMessage. A message from the orchestration thread to its MAIN session must follow the
# protocol (scripts/check-message.sh --up); one that does not is denied with the reason, so the thread rewrites
# it. MAIN is the "MAIN:" line of .orchestration/state.md at the root of the session's git worktree. Messages to
# anyone else, and sessions without that state file, pass silently. Input: Claude Code's hook JSON on stdin.
set -u
here=$(dirname "$0")
. "$here/../scripts/lib.sh"
input=$(cat)
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[ -n "$cwd" ] || exit 0
top=$(toplevel "$cwd") || exit 0
main=$(sed -n 's/^MAIN:[[:space:]]*//p' "$top/.orchestration/state.md" 2>/dev/null | head -1 | sed -E 's/[[:space:]]+$//')
to=$(printf '%s' "$input" | jq -r '.tool_input.to // empty' | sed -E 's/[[:space:]]+\[[^]]*\]$//')
[ -n "$main" ] && [ "$to" = "$main" ] || exit 0
verdict=$(printf '%s' "$input" | jq -r '.tool_input.message // ""' | "$here/../scripts/check-message.sh" --up) && exit 0
jq -n --arg r "This message to MAIN ($main) breaks the thread protocol: ${verdict#BAD }. Rewrite it: first line 'STATUS: <working|need-decision|blocked|rotating|done> - <summary>', at most 10 lines; a need-decision names Options:, Default:, and 'applies at <UTC>' or owner-before." \
  '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
exit 0
