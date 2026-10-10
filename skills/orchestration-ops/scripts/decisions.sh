#!/usr/bin/env bash
# The decision queue: one file, one line per open decision, each with a default and a deadline.
#   decisions.sh add "<what>" "<why now>" "<blocks>" "<default>" <hours>   add an item; the default applies after <hours>
#   decisions.sh list                                                       print open items, oldest first
#   decisions.sh due                                                        print open items whose deadline has passed
#   decisions.sh close <id> "<outcome>"                                     move an item to the Applied section
# The file is $ORCHESTRATION_DECISIONS, default .orchestration/decisions.md.
set -euo pipefail
file=${ORCHESTRATION_DECISIONS:-.orchestration/decisions.md}
now=$(date -u +%Y-%m-%dT%H:%MZ)
ensure() {
  [ -f "$file" ] && return
  mkdir -p "$(dirname "$file")"
  printf '# Decisions\n\nOpen items apply their default at the deadline unless the owner objects. Owner-before classes never apply themselves.\n\n## Open\n\n## Applied\n' > "$file"
}
case "${1:-}" in
  add)
    [ $# -eq 6 ] || { echo 'usage: decisions.sh add "<what>" "<why now>" "<blocks>" "<default>" <hours>' >&2; exit 1; }
    ensure
    id=$(( $(grep -c '^- D[0-9]' "$file" || true) + 1 ))
    deadline=$(date -u -d "+$6 hours" +%Y-%m-%dT%H:%MZ)
    line="- D$id ($now) $2 · why now: $3 · blocks: $4 · default: $5 · applies at $deadline unless you object"
    awk -v l="$line" '/^## Applied/ && !done { print l; print ""; done = 1 } { print }' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
    echo "D$id applies at $deadline" ;;
  list) ensure; awk '/^## Open/ { on = 1; next } /^## Applied/ { on = 0 } on && /^- D/' "$file" ;;
  due)
    ensure
    awk -v now="$now" '/^## Open/ { on = 1; next } /^## Applied/ { on = 0 }
      on && /^- D/ { if (match($0, /applies at [0-9T:Z-]+/)) { d = substr($0, RSTART + 11, RLENGTH - 11); if (d <= now) print } }' "$file" ;;
  close)
    [ $# -eq 3 ] || { echo 'usage: decisions.sh close <id> "<outcome>"' >&2; exit 1; }
    ensure
    grep -q "^- $2 " "$file" || { echo "no open item $2" >&2; exit 1; }
    awk -v id="$2" -v out="$3" -v now="$now" '
      /^## Open/ { on = 1 } /^## Applied/ { on = 0 }
      on && index($0, "- " id " ") == 1 { moved = $0 " · closed " now ": " out; next }
      { print }
      END { print moved }' "$file" > "$file.tmp"
    mv "$file.tmp" "$file"
    echo "closed $2 at $now" ;;
  *) sed -n '2,7p' "$0"; exit 1 ;;
esac
