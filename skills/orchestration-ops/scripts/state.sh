#!/usr/bin/env bash
# Edit the orchestrator state file without typing a timestamp by hand.
#   state.sh log "<event>"                 append "- <UTC now> <event>" under "## Log"
#   state.sh set <lane> <column> <value>   replace one cell of the "## Lanes" table
#   state.sh backup                        copy the file to state.<UTC stamp>.md beside it
#   state.sh now                           print the UTC stamp the other commands use
# The file is $ORCHESTRATION_STATE, default .orchestration/state.md in the current directory.
set -euo pipefail
file=${ORCHESTRATION_STATE:-.orchestration/state.md}
now=$(date -u +%Y-%m-%dT%H:%MZ)
cmd=${1:-}
case "$cmd" in
  now) echo "$now" ;;
  backup)
    [ -f "$file" ] || { echo "no state file at $file" >&2; exit 1; }
    cp "$file" "${file%.md}.$(date -u +%Y%m%dT%H%MZ).md"
    echo "backed up $file" ;;
  log)
    [ $# -ge 2 ] || { echo "usage: state.sh log \"<event>\"" >&2; exit 1; }
    [ -f "$file" ] || { echo "no state file at $file" >&2; exit 1; }
    grep -q '^## Log' "$file" || printf '\n## Log\n' >> "$file"
    printf -- '- %s %s\n' "$now" "$2" >> "$file"
    echo "logged at $now" ;;
  set)
    [ $# -eq 4 ] || { echo "usage: state.sh set <lane> <column> <value>" >&2; exit 1; }
    [ -f "$file" ] || { echo "no state file at $file" >&2; exit 1; }
    tmp=$(mktemp "${file}.XXXXXX")
    if ! awk -v lane="$2" -v col="$3" -v val="$4" '
      function trim(s) { gsub(/^[ \t]+|[ \t]+$/, "", s); return s }
      /^## Lanes/ { inlanes = 1 }
      inlanes && /^## / && !/^## Lanes/ { inlanes = 0 }
      inlanes && /^\|/ {
        n = split($0, cells, "|")
        if (!header) {
          for (i = 2; i < n; i++) if (trim(cells[i]) == col) target = i
          header = 1
          if (!target) { print "no column " col > "/dev/stderr"; exit 2 }
        } else if (trim(cells[2]) == lane && cells[3] !~ /^[ -]+$/) {
          cells[target] = " " val " "
          line = ""
          for (i = 2; i < n; i++) line = line "|" cells[i]
          $0 = line "|"
          done = 1
        }
      }
      { print }
      END { if (!done) { print "no lane " lane > "/dev/stderr"; exit 3 } }
    ' "$file" > "$tmp"; then rm -f "$tmp"; exit 1; fi
    mv "$tmp" "$file"
    echo "set $2.$3 at $now" ;;
  *) sed -n '2,7p' "$0"; exit 1 ;;
esac
