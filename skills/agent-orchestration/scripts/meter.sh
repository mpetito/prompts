#!/usr/bin/env bash
# Read the Codex weekly meter from the newest session log and say what the budget rule requires.
#   meter.sh [--switch <percent>]
# Prints one line: "codex=<used>% resets=<UTC> verdict=<normal|rotate|stop|unknown>", then the rule for
# rotate and stop. The Claude meter is not on disk; read it from the harness's usage view and apply the same rule.
set -euo pipefail
. "$(dirname "$0")/lib.sh"
# Rotate from 70%, keeping the last 30% for finishing the lanes already running. In a past orchestrated build
# (docs/skill-audit/2026-10-09) the coordinators' context re-reads were the largest token cost, so a fresh
# thread lowers the burn rate without lowering any model.
switch=70
while [ $# -gt 0 ]; do
  case $1 in
    --switch) need_value "$1" $#; switch=$2; shift 2 ;;
    *) echo 'usage: meter.sh [--switch <percent>]' >&2; exit 1 ;;
  esac
done
[[ $switch =~ ^[0-9]+$ ]] || { echo "--switch takes a whole percent, got $switch" >&2; exit 1; }
root=${CODEX_SESSIONS:-$HOME/.codex/sessions}
unknown() { echo "codex=unknown resets=unknown verdict=unknown ($1)"; exit 0; }
latest=$(grep -rl --include='*.jsonl' '"used_percent"' "$root" 2>/dev/null | xargs -r ls -t | head -1 || true)
[ -n "$latest" ] || unknown "no session log with a meter under $root"
read -r used resets < <(grep -h '"used_percent"' "$latest" | tail -1 \
  | jq -r '[.payload.rate_limits.primary.used_percent // "", .payload.rate_limits.primary.resets_at // ""] | @tsv' 2>/dev/null) || true
[[ ${used:-} =~ ^[0-9]+(\.[0-9]+)?$ ]] && [[ ${resets:-} =~ ^[0-9]+$ ]] || unknown "no primary meter in $(basename "$latest")"
reset_iso=$(fmt_utc "$resets")
pct=${used%.*}
if [ "$pct" -ge 100 ]; then verdict=stop
elif [ "$pct" -ge "$switch" ]; then verdict=rotate
else verdict=normal; fi
echo "codex=${used}% resets=$reset_iso verdict=$verdict (read $(utc_now) from $(basename "$latest"))"
case $verdict in
  rotate) echo "rule: ask MAIN to rotate this thread (STATUS: working - codex meter at ${used}%; ready to rotate); keep the briefed models and reviewers" ;;
  stop) echo "rule: write the resume point, log the reset time, arm wake-at.sh $reset_iso in the background, launch nothing metered" ;;
esac
