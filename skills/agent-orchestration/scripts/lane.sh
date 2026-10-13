#!/usr/bin/env bash
# Start one lane as a herdr agent, Claude or Codex, in a new tab of the build's workspace at the lane's worktree, and
# hand it its brief with a one-line pointer prompt. The thread runs it from its own pane.
#   lane.sh <build> <lane> <lane worktree> <brief file> --kind claude|codex --model <id> [--network]
# The agent is named <build>-<lane> and reports to the thread with
#   mail.sh send <build>/thread --from <build>/<lane> "<STATUS: ... line>"
# Codex runs with --approve-for-me, so its automatic reviewer grants its approvals (commits in the worktree's
# protected git directory among them), and --add-dir on the build's mail folder; --network lets its sandbox reach the
# network. Claude runs the lane agent definition, which carries the guard hooks a subagent worker inherits.
# A non-default ORCHESTRATION_HOME is passed to the lane's tab; Codex's sandbox doesn't see the pane's environment, so
# a Codex lane's brief then gives its send command as ORCHESTRATION_HOME=<home> mail.sh send ....
# Prints one line: LANE <name> pane=<pane> kind=<kind>, BLOCKED <name> <reason> (started, but waiting on a startup
# prompt the owner must answer; send the pointer prompt once it is idle), or FAILED <reason> with exit 1.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
fail() { echo "FAILED $*"; exit 1; }
usage() { sed -n '4p' "$0" >&2; exit 1; }
[ $# -ge 4 ] || usage
build=$1; lane=$2; wt=$3; brief=$4; shift 4
kind=""; model=""; network=0
while [ $# -gt 0 ]; do
  case $1 in
    --kind) need_value "$1" $#; kind=$2; shift 2 ;;
    --model) need_value "$1" $#; model=$2; shift 2 ;;
    --network) network=1; shift ;;
    *) usage ;;
  esac
done
name="$build-$lane"
[[ $name =~ ^[a-z][a-z0-9_-]{0,31}$ ]] || fail "lane agent name $name must match [a-z][a-z0-9_-]{0,31}; shorten the lane name"
[ -n "$model" ] || fail "--model is required: name the lane's model explicitly"
[ -d "$wt" ] || fail "no lane worktree at $wt"
[ -s "$brief" ] || fail "no brief at $brief"
wt=$(realpath "$wt"); brief=$(realpath "$brief")
mail="${ORCHESTRATION_HOME:-$HOME/.orchestration}/mail/$build"
case $kind in
  claude) args=(--agent lane --model "$model") ;;
  codex)
    mkdir -p "$mail"
    args=(--approve-for-me --add-dir "$mail" --model "$model")
    [ "$network" = 0 ] || args+=(-c sandbox_workspace_write.network_access=true) ;;
  *) fail "--kind takes claude or codex, got ${kind:-nothing}" ;;
esac

# herdr <args...> printing herdr's "<code>: <message>" on failure, so a FAILED line carries herdr's own reason.
run() {
  local out
  out=$(herdr "$@" 2>&1) && { printf '%s' "$out"; return 0; }
  printf '%s' "$out" | jq -r '"\(.error.code): \(.error.message)"' 2>/dev/null || printf '%s' "$out"
  return 1
}
ws=$( { herdr agent get "$build" 2>/dev/null || true; } | jq -r '.result.agent.workspace_id // empty')
[ -n "$ws" ] || fail "no live thread named $build to put the lane beside; run lane.sh from the build's thread"
env=(); [ -z "${ORCHESTRATION_HOME:-}" ] || env=(--env "ORCHESTRATION_HOME=$ORCHESTRATION_HOME")
out=$(run tab create --workspace "$ws" --cwd "$wt" --label "$lane" --no-focus "${env[@]}") || fail "herdr tab create: $out"
pane=$(jq -r '.result.root_pane.pane_id' <<<"$out")
if ! out=$(run agent start "$name" --kind "$kind" --pane "$pane" --timeout 120000 -- "${args[@]}"); then
  case $out in
    agent_not_ready:*) echo "BLOCKED $name waiting on a startup prompt: answer it in workspace $build, tab $lane"; exit 0 ;;
    *) herdr pane close "$pane" >/dev/null 2>&1 || true; fail "herdr agent start: $out" ;;
  esac
fi
out=$(run agent prompt "$name" "Read $(native "$brief") and follow it.") || fail "herdr agent prompt: $out"
echo "LANE $name pane=$pane kind=$kind"
