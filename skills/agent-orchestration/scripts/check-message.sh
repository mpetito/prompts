#!/usr/bin/env bash
# Check one cross-session message against the two-thread protocol. The message comes on stdin.
#   check-message.sh [--up | --down]
# --up (default): orchestration thread to MAIN. First line "STATUS: <working|need-decision|blocked|rotating|done> - <summary>",
#   at most 10 lines; a need-decision also names "Options:", "Default:", and "applies at <UTC>" or "owner-before".
# --down: MAIN to the thread. First line starts with "STEER:", "DECISION <id>:", "ROTATE" or "QUESTION:".
# Prints OK, or BAD <reason>; exits 0 or 1 (2 on a usage error).
set -euo pipefail
# Ten lines: a status the owner-facing thread can relay in one glance; anything longer belongs in a file
# the message points to. Messages queue and are read whole, so length is paid on every wake.
max_up_lines=10
mode=up
case "${1:-}" in
  ""|--up) ;;
  --down) mode=down ;;
  *) echo 'usage: check-message.sh [--up | --down] < message' >&2; exit 2 ;;
esac
[ $# -le 1 ] || { echo 'usage: check-message.sh [--up | --down] < message' >&2; exit 2; }
# Trailing blank lines are formatting, not content; drop them before counting.
msg=$(cat | sed -e :a -e '/^[[:space:]]*$/{$d;N;ba' -e '}')
bad() { echo "BAD $*"; exit 1; }
[ -n "$(printf '%s' "$msg" | tr -d '[:space:]')" ] || bad "empty message"
first=$(printf '%s\n' "$msg" | head -1)
if [ "$mode" = down ]; then
  [[ $first =~ ^(STEER:|DECISION[[:space:]]+[^[:space:]:]+:|ROTATE([[:space:]:]|$)|QUESTION:) ]] \
    || bad "first line must start with STEER:, DECISION <id>:, ROTATE or QUESTION:, got: ${first:0:80}"
  echo OK; exit 0
fi
[[ $first =~ ^STATUS:\ (working|need-decision|blocked|rotating|done)\ -\ [^[:space:]] ]] \
  || bad "first line must be 'STATUS: <working|need-decision|blocked|rotating|done> - <summary>', got: ${first:0:80}"
lines=$(printf '%s\n' "$msg" | wc -l)
[ "$lines" -le "$max_up_lines" ] || bad "$lines lines; at most $max_up_lines, with detail in a file the message names"
if [[ $first =~ ^STATUS:\ need-decision ]]; then
  printf '%s\n' "$msg" | grep -Eq '(^|[[:space:]])Options:' || bad "need-decision without an Options: line"
  printf '%s\n' "$msg" | grep -Eq '(^|[[:space:]])Default:' || bad "need-decision without a Default: line"
  printf '%s\n' "$msg" | grep -Eq 'applies at [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z|owner-before' \
    || bad "need-decision without 'applies at <UTC>' or owner-before"
fi
echo OK
