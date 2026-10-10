#!/usr/bin/env bash
# Sleep until a UTC time, then print one line. Run it with the Bash tool's run_in_background so its exit
# wakes the thread; a foreground wait leaves messages and hand-backs unread until it ends.
#   wake-at.sh <UTC time YYYY-MM-DDTHH:MMZ | +<N>m | +<N>h> [<label>]
# Prints: WAKE <label> <UTC now> (armed for <UTC target>)
set -euo pipefail
. "$(dirname "$0")/lib.sh"
[ $# -ge 1 ] && [ $# -le 2 ] || { echo 'usage: wake-at.sh <UTC time | +<N>m | +<N>h> [label]' >&2; exit 1; }
target=$(to_epoch "$1")
wait=$(( target - $(date -u +%s) ))
[ "$wait" -gt 0 ] || wait=0
sleep "$wait"
echo "WAKE ${2:-timer} $(utc_now) (armed for $(fmt_utc "$target"))"
