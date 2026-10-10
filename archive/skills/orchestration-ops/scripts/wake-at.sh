#!/usr/bin/env bash
# Sleep until a UTC time, then print one line. Run it in the background so its exit wakes the orchestrator.
#   wake-at.sh <UTC time, e.g. 2026-10-09T21:16Z> [<label>]
set -euo pipefail
[ $# -ge 1 ] || { echo "usage: wake-at.sh <UTC time> [label]" >&2; exit 1; }
target=$(date -u -d "$1" +%s)
now=$(date -u +%s)
wait=$(( target - now ))
[ "$wait" -gt 0 ] || wait=0
sleep "$wait"
echo "WAKE ${2:-timer} at $(date -u +%Y-%m-%dT%H:%MZ) (armed for $1)"
