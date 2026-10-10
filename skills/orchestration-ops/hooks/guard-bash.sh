#!/usr/bin/env bash
# PreToolUse hook for Bash. Denies the commands that cost the most in past builds and warns when the
# scratch filesystem is nearly out of inodes. Input: Claude Code's hook JSON on stdin.
# A command is matched only in command position (start of a line, after ; & | ( or $( , or after
# `sh -c '`), so the same words inside a quoted string, a backtick span or a comment pass.
set -u
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
deny() {
  jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'
  exit 0
}
at='(^|[;&|(]|\$\(|-c[[:space:]]+["'"'"'])[[:space:]]*(sudo[[:space:]]+)?'
if printf '%s' "$cmd" | grep -Eq "${at}(pkill|killall)([[:space:]]|$)"; then
  deny "pkill and killall match by pattern or name across every lane on this machine, and have killed the caller's own shell and another lane's server. Stop a process by PID: find it with 'ss -ltnp' or 'pgrep -a', read its command line, then 'kill <pid>'."
fi
if printf '%s' "$cmd" | grep -Eq "${at}git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+worktree[[:space:]]+remove"; then
  deny "Raw worktree removal has deleted lane evidence before it was archived. Use the orchestration-ops finish-lane.sh script, which archives the scratch directory, refuses while an agent runs there, then removes the worktree."
fi
if printf '%s' "$cmd" | grep -Eq "${at}rm[[:space:]]+(-[a-zA-Z]+[[:space:]]+)*[^[:space:]]*\.orchestration/(lanes|tmp)([/[:space:]]|$)"; then
  deny "Deleting under .orchestration/lanes or .orchestration/tmp removes lane evidence. Archive it with finish-lane.sh or move it aside instead."
fi
warn=""
for fs in /tmp "${TMPDIR:-/tmp}"; do
  use=$(df -iP "$fs" 2>/dev/null | awk 'NR==2 { sub("%", "", $5); print $5 }')
  if [ -n "${use:-}" ] && [ "$use" -ge 70 ]; then warn="$fs is at ${use}% of its inodes; clean cdk.out* and scratch copies or move TMPDIR to disk before launching more lanes."; break; fi
done
if [ -n "$warn" ]; then
  jq -n --arg c "$warn" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'
fi
exit 0
