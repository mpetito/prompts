#!/usr/bin/env bash
# Launch one background codex exec lane with a hard timeout and a stripped environment, writing its last message
# to the result file. Run it with the host's background option so its exit wakes the orchestrator.
#   codex-exec.sh <lane worktree, e.g. ../<repo>-wt-<lane>> <brief file> <result file> [--model <id>] [--effort <level>] [--network]
#                 [--timeout <duration, default 2h>] [--strip <VAR>]... [--resume <session id>]
# The prompt is "Read <brief> and follow it; write your result to <result>", so the brief carries everything.
# Prints one line: CODEX done|timeout|failed lane=<worktree name> ...
set -euo pipefail
. "$(dirname "$0")/lib.sh"
usage='usage: codex-exec.sh <worktree> <brief file> <result file> [--model <id>] [--effort <level>] [--network] [--timeout <duration>] [--strip <VAR>]... [--resume <session id>]'
[ $# -ge 3 ] || { echo "$usage" >&2; exit 1; }
wt=$1; brief=$2; result=$3; shift 3
# Two hours: twice the hour of agent time a lane is meant to take; past that the brief was too large and a
# narrower resume costs less than more waiting.
timeout_for=2h
# Grace between TERM and KILL, so a lane that is already shutting down is not killed mid-write.
kill_after=60
model=""; effort=""; network=0; strip=(); resume=""
while [ $# -gt 0 ]; do
  case $1 in
    --model) need_value "$1" $#; model=$2; shift 2 ;;
    --effort) need_value "$1" $#; effort=$2; shift 2 ;;
    --network) network=1; shift ;;
    --timeout) need_value "$1" $#; timeout_for=$2; shift 2 ;;
    --strip) need_value "$1" $#; strip+=("$2"); shift 2 ;;
    --resume) need_value "$1" $#; resume=$2; shift 2 ;;
    *) echo "unknown option $1; $usage" >&2; exit 1 ;;
  esac
done
[ -d "$wt" ] || { echo "no worktree at $wt" >&2; exit 1; }
[ -f "$brief" ] || { echo "no brief at $brief" >&2; exit 1; }
command -v codex >/dev/null || { echo "codex is not on PATH" >&2; exit 1; }
mkdir -p "$(dirname "$result")"
# Codex reads both paths from inside the worktree, so they must not depend on the caller's directory.
wt=$(realpath "$wt"); brief=$(realpath "$brief"); result=$(realpath -m "$result")
env_args=()
for v in "${strip[@]}"; do env_args+=(-u "$v"); done
# The same sandbox, model and network setting for a fresh lane and a resumed one. `codex exec resume` takes
# no --sandbox or --cd, so the sandbox is a config override and the command runs from inside the worktree;
# without them a resumed lane ran under the user's own Codex default.
opts=(-c 'sandbox_mode="workspace-write"' --output-last-message "$result")
[ -n "$model" ] && opts+=(--model "$model")
[ -n "$effort" ] && opts+=(-c "model_reasoning_effort=\"$effort\"")
[ "$network" = 1 ] && opts+=(-c sandbox_workspace_write.network_access=true)
if [ -n "$resume" ]; then args=(exec resume "$resume" "${opts[@]}")
else args=(exec --cd "$wt" --sandbox workspace-write "${opts[@]}"); fi
prompt="Read $brief in full and follow it. Write your final report to $result."
start=$(utc_now)
set +e
(cd "$wt" && env "${env_args[@]}" timeout --kill-after="$kill_after" "$timeout_for" codex "${args[@]}" - <<< "$prompt") > "${result%.md}.log" 2>&1
code=$?
set -e
case $code in
  0) echo "CODEX done lane=$(basename "$wt") result=$result started=$start" ;;
  124|137) echo "CODEX timeout lane=$(basename "$wt") after $timeout_for; log ${result%.md}.log" ;;
  *) echo "CODEX failed lane=$(basename "$wt") exit=$code; log ${result%.md}.log" ;;
esac
