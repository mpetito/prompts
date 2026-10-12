#!/usr/bin/env bash
# Edit the orchestration thread's state file without typing a timestamp by hand.
#   state.sh init <build>                       create .orchestration/ (briefs/, results/) and the skeleton
#   state.sh log "<event>"                      append "- <UTC now> <event>" to the "## Log" section
#   state.sh set <lane> <column> <value>        replace one cell of the "## Lanes" table
#   state.sh resume <file|->                    back up, then replace the RESUME body, stamped "Written: <UTC>"
#   state.sh backup                             copy the file to state.<UTC stamp>.md beside it
#   state.sh thread <key>                       print one field of the thread record (BUILD, BASE, LANE-BASE, ...)
#   state.sh now                                print the UTC stamp the other commands use
# The file is $ORCHESTRATION_STATE when set, else .orchestration/state.md at the root of the git worktree that
# holds the current directory: the build's coordination worktree, ../<repo>-orch-<build>. The build's name, the
# base and the landing mode live in the thread record beside it, .orchestration/thread.md, which MAIN's
# thread.sh writes; read them with "thread".
set -euo pipefail
. "$(dirname "$0")/lib.sh"
now=$(utc_now)
usage() { sed -n '2,13p' "$0" >&2; exit 1; }
resolve() { file=$(resolve_state "$PWD" ORCHESTRATION_STATE) || exit 1; }
need_file() { resolve; [ -f "$file" ] || { echo "no state file at $file; start one with state.sh init" >&2; exit 1; }; }
backup() {
  # Seconds in the stamp, so two backups in one minute (a resume right after a backup) both survive.
  local dest="${file%.md}.$(date -u +%Y%m%dT%H%M%SZ).md"
  cp "$file" "$dest"
  echo "$dest"
}
case "${1:-}" in
  now) echo "$now" ;;
  init)
    [ $# -eq 2 ] || { echo 'usage: state.sh init <build>' >&2; exit 1; }
    resolve
    [ ! -e "$file" ] || { echo "refusing: $file already exists" >&2; exit 1; }
    mkdir -p "$(dirname "$file")/briefs" "$(dirname "$file")/results"
    printf '# Orchestration thread: %s\n\n## Thread\n\nRecord: thread.md (MAIN, base, landing; written by MAIN)\nStarted: %s\n\n## RESUME\n\nWritten: %s\n(nothing yet)\n\n## Lanes\n\n| Lane | Agent | PR | Head SHA | Next action |\n| --- | --- | --- | --- | --- |\n\n## Decisions\n\n## Log\n\n- %s thread started\n' \
      "$2" "$now" "$now" "$now" > "$file"
    echo "initialised $file $now" ;;
  backup)
    need_file
    echo "backed up $file to $(backup)" ;;
  log)
    [ $# -eq 2 ] && [ -n "$2" ] || { echo 'usage: state.sh log "<event>"' >&2; exit 1; }
    need_file
    tmp=$(mktemp "${file}.XXXXXX")
    # Insert at the end of the Log section, before any later section and its blank lines, so the
    # log stays one block wherever the section sits.
    awk -v line="- $now $2" '
      function flush() { while (blanks > 0) { print ""; blanks-- } }
      inlog && /^[[:space:]]*$/ { blanks++; next }
      /^## / { if (inlog) { print line; done = 1; inlog = 0 } flush(); if ($0 ~ /^## Log/) inlog = 1; print; next }
      { flush(); print }
      END { if (!done) { if (!inlog) print "\n## Log\n"; print line } }
    ' "$file" > "$tmp"
    mv "$tmp" "$file"
    echo "logged $now" ;;
  set)
    [ $# -eq 4 ] || { echo 'usage: state.sh set <lane> <column> <value>' >&2; exit 1; }
    need_file
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
        } else if (trim(cells[2]) == lane) {
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
    echo "set $2.$3 $now" ;;
  resume)
    [ $# -eq 2 ] || { echo 'usage: state.sh resume <file|->' >&2; exit 1; }
    need_file
    grep -q '^## RESUME' "$file" || { echo "no ## RESUME section in $file" >&2; exit 1; }
    if [ "$2" = - ]; then body=$(cat); else [ -f "$2" ] || { echo "no file $2" >&2; exit 1; }; body=$(cat "$2"); fi
    # A copied stamp would leave two; the helper writes the only one.
    body=$(printf '%s\n' "$body" | grep -v '^Written:' || true)
    [ -n "$(printf '%s' "$body" | tr -d '[:space:]')" ] || { echo "refusing: empty RESUME" >&2; exit 1; }
    saved=$(backup)
    tmp=$(mktemp "${file}.XXXXXX")
    printf '%s\n' "$body" > "$tmp.body"
    awk -v stamp="Written: $now" -v bodyfile="$tmp.body" '
      /^## / { if (inres) inres = 0; if ($0 ~ /^## RESUME/) { print; print ""; print stamp; while ((getline l < bodyfile) > 0) print l; print ""; inres = 1; next } }
      !inres { print }
    ' "$file" > "$tmp"
    rm -f "$tmp.body"
    mv "$tmp" "$file"
    echo "resume written $now (previous copy $saved)" ;;
  thread)
    [ $# -eq 2 ] || usage
    need_file
    top=$(dirname "$(dirname "$file")")
    value=$(thread_field "$top" "$2")
    [ -n "$value" ] || { echo "no $2 in $top/.orchestration/thread.md" >&2; exit 1; }
    echo "$value" ;;
  *) usage ;;
esac
