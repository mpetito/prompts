#!/usr/bin/env bash
# PreToolUse hook for Bash, in the orchestration thread and the workers it starts. Denies, for both, the
# commands that destroyed work in past builds. Advises the thread when it waits in the foreground (workers may:
# their waits deafen no one), and warns when the scratch filesystem is nearly out of inodes. Input: Claude Code's
# hook JSON on stdin; a subagent worker's carries agent_id, and a lane session's hook runs with --lane.
# A command is matched only in command position (start of a line, after ; & | ( or $( , or after
# `sh -c '`), so the same words inside a quoted string, a backtick span or a comment pass.
# The matching is textual, so it catches the commands past builds ran by mistake, not every way to run them; the
# thread is trusted, and this only reminds it.
set -u
. "$(dirname "$0")/../scripts/lib.sh"
input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')
background=$(printf '%s' "$input" | jq -r '.tool_input.run_in_background // false')
worker=$(printf '%s' "$input" | jq -r '.agent_id // empty')
[ "${1:-}" != --lane ] || worker=lane
# A foreground wait shorter than this (a retry backoff, letting a port bind) costs less than a message
# arriving late; anything longer leaves messages from MAIN and lane hand-backs unread while it runs.
foreground_sleep_limit=30
# Lanes fail in confusing ways once /tmp runs out of inodes; 70% leaves room to clean up first.
inode_warn_percent=70
at='(^|[;&|(]|\$\(|-c[[:space:]]+["'"'"'])[[:space:]]*(sudo[[:space:]]+)?'
if printf '%s' "$cmd" | grep -Eq "${at}(pkill|killall)([[:space:]]|$)"; then
  deny "pkill and killall match by pattern or name across every lane on this machine, and have killed the caller's own shell and another lane's server. Stop a process by PID: find it with 'ss -ltnp' or 'pgrep -a', read its command line, then 'kill <pid>'."
fi
if printf '%s' "$cmd" | grep -Eq "${at}git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+worktree[[:space:]]+remove"; then
  deny "Raw worktree removal has deleted lane evidence before it was archived. Use ~/.claude/skills/agent-orchestration/scripts/finish-lane.sh ../<repo>-wt-<lane> <archive dir>, which archives the scratch directory and ignored files such as .eval-runs, refuses while an agent runs there, then removes the worktree. For a throwaway copy, use \`git clone --no-local\` or \`git archive\`, never \`cp -a\` of a worktree."
fi
# Lane evidence lives in the coordination worktree's .orchestration/briefs and results, a lane worktree keeps its
# scratch in .orchestration/tmp until finish-lane.sh archives it, and .orchestration/lanes holds evidence from
# earlier builds.
if printf '%s' "$cmd" | grep -Eq "${at}rm[[:space:]]+(-[a-zA-Z]+[[:space:]]+)*[^[:space:]]*\.orchestration/(briefs|results|lanes|tmp)([/[:space:]]|$)"; then
  deny "Deleting .orchestration/briefs, results, lanes or tmp removes lane evidence. Archive a lane worktree (../<repo>-wt-<lane>) with finish-lane.sh, or move files aside instead."
fi
notes=()
if [ "$background" != true ] && [ -z "$worker" ]; then
  wait_reason=""
  while IFS= read -r m; do
    [[ $m =~ sleep[[:space:]]+([0-9]+)(\.[0-9]+)?([smhd]?) ]] || continue
    secs=${BASH_REMATCH[1]}
    case ${BASH_REMATCH[3]} in m) secs=$(( secs * 60 )) ;; h) secs=$(( secs * 3600 )) ;; d) secs=$(( secs * 86400 )) ;; esac
    [ "$secs" -ge "$foreground_sleep_limit" ] && wait_reason="sleeps ${secs} s in the foreground"
  done < <(printf '%s\n' "$cmd" | grep -oE "${at}sleep[[:space:]]+[0-9]+(\.[0-9]+)?[smhd]?" || true)
  if printf '%s' "$cmd" | grep -Eq "${at}(until|while)([[:space:]]|$)" && printf '%s' "$cmd" | grep -Eq '(^|[^[:alnum:]_-])sleep[[:space:]]'; then
    wait_reason="loops on sleep in the foreground"
  fi
  if printf '%s' "$cmd" | grep -Eq "${at}(bash[[:space:]]+)?[^[:space:]]*mail\.sh[[:space:]]+wait([[:space:]]|$)"; then
    wait_reason="waits on mail in the foreground"
  fi
  if [ -n "$wait_reason" ]; then
    notes+=("This call $wait_reason: until it ends, messages from MAIN and lane hand-backs queue unread. Next time, arm a background timer: ~/.claude/skills/agent-orchestration/scripts/wake-at.sh <UTC|+<N>m> <label> with run_in_background, or watch the condition with Monitor.")
  fi
fi
for fs in /tmp "${TMPDIR:-/tmp}"; do
  use=$(df -iP "$fs" 2>/dev/null | awk 'NR==2 { sub("%", "", $5); print $5 }')
  if [[ ${use:-} =~ ^[0-9]+$ ]] && [ "$use" -ge "$inode_warn_percent" ]; then notes+=("$fs is at ${use}% of its inodes; clean cdk.out* and scratch copies or move TMPDIR to disk before launching more lanes."); break; fi
done
if [ ${#notes[@]} -gt 0 ]; then
  jq -n --arg c "$(printf '%s\n' "${notes[@]}")" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'
fi
exit 0
