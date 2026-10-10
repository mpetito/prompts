#!/usr/bin/env bash
# Wait for a new line from someone else in a shared message file (a to-a.md style inbox), ignoring lines
# this writer added itself. Prints the new lines and exits, so run it in the background as a wake source.
#   watch-inbox.sh <file> <own prefix, e.g. "- **[A">  [--minutes <n, default 240>]
set -uo pipefail
file=$1; own=$2; minutes=240
[ "${3:-}" = --minutes ] && minutes=$4
[ -f "$file" ] || { echo "no inbox at $file" >&2; exit 1; }
seen=$(wc -l < "$file")
for _ in $(seq 1 $(( minutes * 4 ))); do
  sleep 15
  [ -f "$file" ] || continue
  total=$(wc -l < "$file")
  if [ "$total" -gt "$seen" ]; then
    new=$(tail -n +"$(( seen + 1 ))" "$file" | grep -v "^${own}" | grep -v '^[[:space:]]*$' || true)
    seen=$total
    [ -z "$new" ] && continue
    echo "INBOX $file $(date -u +%Y-%m-%dT%H:%MZ)"
    echo "$new"
    exit 0
  fi
done
echo "INBOX quiet $file after $minutes min"
