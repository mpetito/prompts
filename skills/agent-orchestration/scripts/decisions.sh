#!/usr/bin/env bash
# The decision queue: one file, one line per open decision, each with a default and a deadline.
#   decisions.sh add "<what>" "<why now>" "<blocks>" "<default>" <UTC | +<N>m | +<N>h | owner-before>
#   decisions.sh list                      print open items, oldest first
#   decisions.sh due                       print open items whose deadline has passed
#   decisions.sh close <id> "<outcome>"    move an item to the Applied section
# An owner-before item (spend, trust roots, production data, safety rules) never applies itself.
# The file is $ORCHESTRATION_DECISIONS when set, else decisions.md beside the state file (state.sh resolves it:
# $ORCHESTRATION_STATE, or .orchestration/ at the root of the current git worktree).
set -euo pipefail
. "$(dirname "$0")/lib.sh"
now=$(utc_now)
ensure() {
  if [ -n "${ORCHESTRATION_DECISIONS:-}" ]; then
    file=$ORCHESTRATION_DECISIONS
  else
    state=$(resolve_state "$PWD" ORCHESTRATION_DECISIONS) || exit 1
    file="$(dirname "$state")/decisions.md"
  fi
  [ -f "$file" ] && return
  mkdir -p "$(dirname "$file")"
  printf '# Decisions\n\nOpen items apply their default at the deadline unless the owner objects. Owner-before items never apply themselves.\n\n## Open\n\n## Applied\n' > "$file"
}
case "${1:-}" in
  add)
    [ $# -eq 6 ] || { echo 'usage: decisions.sh add "<what>" "<why now>" "<blocks>" "<default>" <UTC | +<N>m | +<N>h | owner-before>' >&2; exit 1; }
    if [ "$6" = owner-before ]; then
      when="owner-before: waits for the owner"
      said="owner-before (never applies itself)"
    else
      epoch=$(to_epoch "$6")
      deadline=$(fmt_utc "$epoch")
      when="applies at $deadline unless the owner objects"
      said="applies at $deadline"
    fi
    ensure
    id=$(( $(grep -c '^- D[0-9]' "$file" || true) + 1 ))
    line="- D$id ($now) $2 · why now: $3 · blocks: $4 · default: $5 · $when"
    awk -v l="$line" '/^## Applied/ && !done { print l; print ""; done = 1 } { print }' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
    echo "D$id $said" ;;
  list)
    [ $# -eq 1 ] || { echo 'usage: decisions.sh list' >&2; exit 1; }
    ensure; awk '/^## Open/ { on = 1; next } /^## Applied/ { on = 0 } on && /^- D/' "$file" ;;
  due)
    [ $# -eq 1 ] || { echo 'usage: decisions.sh due' >&2; exit 1; }
    ensure
    # The stamps share one fixed-width format, so a string comparison orders them in time.
    awk -v now="$now" '/^## Open/ { on = 1; next } /^## Applied/ { on = 0 }
      on && /^- D/ { if (match($0, /applies at [0-9T:Z-]+/)) { d = substr($0, RSTART + 11, RLENGTH - 11); if (d <= now) print } }' "$file" ;;
  close)
    [ $# -eq 3 ] || { echo 'usage: decisions.sh close <id> "<outcome>"' >&2; exit 1; }
    ensure
    awk '/^## Open/ { on = 1; next } /^## Applied/ { on = 0 } on' "$file" | grep -q "^- $2 " || { echo "no open item $2" >&2; exit 1; }
    awk -v id="$2" -v out="$3" -v now="$now" '
      /^## Open/ { on = 1 } /^## Applied/ { on = 0 }
      on && index($0, "- " id " ") == 1 { moved = $0 " · closed " now ": " out; next }
      { print }
      END { print moved }' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
    echo "closed $2 $now" ;;
  *) sed -n '2,9p' "$0" >&2; exit 1 ;;
esac
