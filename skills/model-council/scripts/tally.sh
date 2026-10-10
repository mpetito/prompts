#!/usr/bin/env bash
# Read both members' answers for one round and print the council's next step, one line:
#   COUNCIL consensus|exchange|no-consensus|incomplete ...
#   tally.sh <answer file> <answer file> --exchange <k>     (k = 0 for the blind round, then 1, 2, ...)
# Consensus is mechanical: the same disposition and the same action text, so the coordinator never judges
# whether two differently worded actions match. It still has to verify the decisive citation.
set -euo pipefail
# Exchange rounds after the blind round. Debate studies find nearly all of the gain in the first exchange and
# flat or falling accuracy after it, with conformity growing; the second round confirms a revised position.
MAX_EXCHANGE_ROUNDS=2
DISPOSITIONS='defect improvement false-positive unnecessary-complexity already-addressed deferred needs-human'
usage='usage: tally.sh <answer file> <answer file> --exchange <k>'
[ $# -eq 4 ] && [ "$3" = --exchange ] || { echo "$usage" >&2; exit 1; }
a=$1; b=$2; k=$4
case $k in ''|*[!0-9]*) echo "--exchange takes a round number; $usage" >&2; exit 1 ;; esac

# The last value of a key: an answer may quote the template before its own block. Whitespace is collapsed.
field() { { grep -iE "^[[:space:]]*$1:" "$2" || true; } | tail -n1 | sed -E 's/^[^:]*:[[:space:]]*//; s/[[:space:]]+/ /g; s/ $//'; }
check() {
  local f=$1 stance disposition
  [ -s "$f" ] || { echo "COUNCIL incomplete member=$f reason=no-answer"; exit 0; }
  stance=$(field stance "$f" | tr '[:upper:]' '[:lower:]')
  disposition=$(field disposition "$f" | tr '[:upper:]' '[:lower:]')
  [ -n "$(field action "$f")" ] || { echo "COUNCIL incomplete member=$f reason=no-action"; exit 0; }
  case " $DISPOSITIONS " in *" $disposition "*) ;; *) echo "COUNCIL incomplete member=$f reason=disposition '$disposition'"; exit 0 ;; esac
  if [ "$k" -eq 0 ]; then [ "$stance" = initial ] || { echo "COUNCIL incomplete member=$f reason=stance '$stance' in the blind round"; exit 0; }
  else case $stance in agree|revise|hold) ;; *) echo "COUNCIL incomplete member=$f reason=stance '$stance'"; exit 0 ;; esac; fi
}
check "$a"; check "$b"
da=$(field disposition "$a" | tr '[:upper:]' '[:lower:]'); db=$(field disposition "$b" | tr '[:upper:]' '[:lower:]')
aa=$(field action "$a"); ab=$(field action "$b")
if [ "$da" = "$db" ] && [ "$aa" = "$ab" ]; then
  echo "COUNCIL consensus after-exchange=$k disposition=$da; verify the decisive citations before reporting it"
elif [ "$k" -ge 1 ] && [ "$(field stance "$a" | tr '[:upper:]' '[:lower:]')" = hold ] && [ "$(field stance "$b" | tr '[:upper:]' '[:lower:]')" = hold ]; then
  echo "COUNCIL no-consensus reason=both-hold after-exchange=$k; report each final position and its crux"
elif [ "$k" -ge "$MAX_EXCHANGE_ROUNDS" ]; then
  echo "COUNCIL no-consensus reason=round-cap after-exchange=$k of $MAX_EXCHANGE_ROUNDS; report each final position and its crux"
else
  echo "COUNCIL exchange next=$((k + 1)) of $MAX_EXCHANGE_ROUNDS; send each member the other's answer, unattributed"
fi
