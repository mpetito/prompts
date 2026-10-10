#!/usr/bin/env bash
# Launch one background codex exec lane with a hard timeout and a stripped environment, writing its last message
# to the result file. Run it with the host's background option so its exit wakes the orchestrator.
#   codex-exec.sh <worktree> <brief file> <result file> [--model <id>] [--effort <level>] [--network]
#                 [--timeout <duration, default 2h>] [--strip <VAR>]... [--resume <session id>]
# The prompt is "Read <brief> and follow it; write your result to <result>", so the brief carries everything.
set -euo pipefail
wt=$1; brief=$2; result=$3; shift 3
model=""; effort=""; network=0; timeout_for=2h; strip=(); resume=""
while [ $# -gt 0 ]; do
  case $1 in
    --model) model=$2; shift 2 ;; --effort) effort=$2; shift 2 ;; --network) network=1; shift ;;
    --timeout) timeout_for=$2; shift 2 ;; --strip) strip+=("$2"); shift 2 ;; --resume) resume=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 1 ;;
  esac
done
[ -d "$wt" ] && [ -f "$brief" ] || { echo "worktree or brief missing" >&2; exit 1; }
mkdir -p "$(dirname "$result")"
env_args=()
for v in "${strip[@]}"; do env_args+=(-u "$v"); done
args=(exec --cd "$wt" --sandbox workspace-write --output-last-message "$result")
[ -n "$model" ] && args+=(--model "$model")
[ -n "$effort" ] && args+=(-c "model_reasoning_effort=\"$effort\"")
[ "$network" = 1 ] && args+=(-c sandbox_workspace_write.network_access=true)
[ -n "$resume" ] && args=(exec resume "$resume" --output-last-message "$result")
prompt="Read $brief in full and follow it. Write your final report to $result."
start=$(date -u +%Y-%m-%dT%H:%MZ)
set +e
env "${env_args[@]}" timeout --kill-after=60 "$timeout_for" codex "${args[@]}" - <<< "$prompt" > "${result%.md}.log" 2>&1
code=$?
set -e
case $code in
  0) echo "CODEX done lane=$(basename "$wt") result=$result started=$start" ;;
  124|137) echo "CODEX timeout lane=$(basename "$wt") after $timeout_for; log ${result%.md}.log" ;;
  *) echo "CODEX failed lane=$(basename "$wt") exit=$code; log ${result%.md}.log" ;;
esac
