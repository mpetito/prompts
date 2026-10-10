#!/usr/bin/env bash
# Read the Codex weekly meter from the newest session log and say what the budget rule requires.
#   meter.sh [--switch <percent>]    default 70
# Prints one line: "codex=<used>% resets=<UTC> verdict=<normal|economy|stop>" plus the rule for the verdict.
# The Claude meter is not on disk; record the value from the harness's usage view beside this one.
set -euo pipefail
switch=70
[ "${1:-}" = --switch ] && switch=$2
root=${CODEX_SESSIONS:-$HOME/.codex/sessions}
latest=$(grep -rl --include='*.jsonl' '"used_percent"' "$root" 2>/dev/null | xargs -r ls -t | head -1)
[ -n "$latest" ] || { echo "codex=unknown resets=unknown verdict=unknown (no session log with a meter under $root)"; exit 0; }
read -r used resets < <(grep -h '"used_percent"' "$latest" | tail -1 \
  | jq -r '[.payload.rate_limits.primary.used_percent, .payload.rate_limits.primary.resets_at] | @tsv')
reset_iso=$(date -u -d "@$resets" +%Y-%m-%dT%H:%MZ)
pct=${used%.*}
if [ "$pct" -ge 100 ]; then verdict=stop
elif [ "$pct" -ge "$switch" ]; then verdict=economy
else verdict=normal; fi
echo "codex=${used}% resets=$reset_iso verdict=$verdict (read $(date -u +%Y-%m-%dT%H:%MZ) from $(basename "$latest"))"
case $verdict in
  economy) echo "rule: authors go to the smaller model, drop second reviewers, pause live eval rounds, no new fan-out within 3 h of a limit warning" ;;
  stop) echo "rule: write the resume point, log the reset time, arm wake-at.sh $reset_iso, launch nothing metered" ;;
esac
