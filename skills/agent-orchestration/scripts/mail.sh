#!/usr/bin/env bash
# A build's mailboxes, one maildir per box under $ORCHESTRATION_HOME/mail (default ~/.orchestration/mail), addressed
# <build>/<box>: main is what MAIN reads for the build, thread is the thread's inbox.
#   mail.sh send <build>/<box> --from <build>/<box or lane> [--quiet] [<text> | --file <path>]   the body is stdin when
#                                                                                       neither; never empty
#   mail.sh read <build>/<box>
#   mail.sh wait <build>/<box> [--watch <agent>[=<build>/<box>],...] [--timeout <seconds, default 3600>]
# send prints SENT <to> <file>. A quiet message wakes no wait; the next read prints it with the rest. read prints each
# new message, oldest first, after a "=== <file>" line, and files it, or prints NO MAIL. wait checks every 2 s and
# prints one line, then exits 0:
#   MAIL <n>            the box holds n unread messages that are not quiet
#   BLOCKED <agent>     a watched agent entered herdr's blocked state (a permission or question prompt); once per prompt
#   GONE <agent>        a watched agent left herdr's agent list
#   UNREAD <agent> <n>  a watched agent sits idle while its own box (after the =) holds n messages, not quiet, older
#                       than 5 minutes, so it stopped waiting; once until it works again
#   TIMEOUT
# A message is written to tmp/ and renamed into new/, so a reader never sees half of one; read moves it to cur/.
# A waiter keeps what it last saw of each watched agent in <box>/.watch/<agent>: "<herdr state> <unread reported>".
set -euo pipefail
. "$(dirname "$0")/lib.sh"
root=${ORCHESTRATION_HOME:-$HOME/.orchestration}/mail
# Mail sits unread this long before an idle receiver counts as not waiting: longer than any turn spent between
# reading mail and starting the next wait.
unread_after_minutes=5
usage() { sed -n '4,7p' "$0" >&2; exit 1; }

box_dir() {
  # box_dir <build>/<box>: the box's folder, created on first use; the names follow herdr's agent-name pattern.
  [[ $1 =~ ^[a-z][a-z0-9_-]{0,31}/[a-z][a-z0-9_-]{0,31}$ ]] || { echo "not a <build>/<box> address: $1" >&2; exit 1; }
  mkdir -p "$root/$1"/{tmp,new,cur,.watch}
  echo "$root/$1"
}

# count <box dir> [find tests]: unread messages; waking counts leave quiet ones out.
count() { find "$1/new" -type f "${@:2}" | wc -l; }
waking() { count "$1" ! -name '*.quiet.md' "${@:2}"; }

send() {
  local to=$1 from="" text="" file="" quiet="" dir name body
  shift
  while [ $# -gt 0 ]; do
    case $1 in
      --from) need_value "$1" $#; from=$2; shift 2 ;;
      --file) need_value "$1" $#; file=$2; shift 2 ;;
      --quiet) quiet=.quiet; shift ;;
      --*) usage ;;
      # One argument is the whole message: an unquoted one would arrive as its last word.
      *) [ -z "$text" ] || usage; text=$1; shift ;;
    esac
  done
  [ -n "$from" ] || usage
  if [ -n "$file" ]; then body=$(cat -- "$file"); elif [ -n "$text" ]; then body=$text; else body=$(cat); fi
  [[ $body =~ [^[:space:]] ]] || { echo "refusing an empty message to $to" >&2; exit 1; }
  dir=$(box_dir "$to")
  # Nanoseconds keep same-second messages in the order they were sent.
  name="$(date -u +%Y%m%dT%H%M%S.%NZ)-$$$quiet.md"
  printf 'From: %s\nDate: %s\n\n%s\n' "$from" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$body" > "$dir/tmp/$name"
  mv "$dir/tmp/$name" "$dir/new/$name"
  echo "SENT $to $name"
}

read_box() {
  local dir f
  dir=$(box_dir "$1")
  [ "$(count "$dir")" -gt 0 ] || { echo "NO MAIL"; return 0; }
  for f in "$dir"/new/*; do
    printf '=== %s\n' "$(basename "$f")"; cat -- "$f"; echo
    mv "$f" "$dir/cur/"
  done
}

watch_once() {
  # watch_once <box dir> <watch list>: print the first watched agent's news and return 0, or return 1. Nothing is
  # judged when herdr can't list its agents, so a herdr hiccup never reads as every agent gone.
  local dir=$1 list states spec agent inbox state last flag unread
  list=$(herdr agent list 2>/dev/null) || return 1
  states=$(jq -r '.result.agents[] | select(.name) | "\(.name) \(.agent_status)"' <<<"$list")
  for spec in ${2//,/ }; do
    agent=${spec%%=*}; inbox=""
    [ "$spec" = "$agent" ] || inbox=${spec#*=}
    state=$(awk -v a="$agent" '$1 == a { print $2 }' <<<"$states")
    state=${state:-gone}
    last=""; flag=0
    [ -f "$dir/.watch/$agent" ] && read -r last flag < "$dir/.watch/$agent"
    [ "$state" = working ] && flag=0
    unread=0
    if [ -n "$inbox" ] && [ "$flag" = 0 ] && { [ "$state" = idle ] || [ "$state" = done ]; }; then
      unread=$(waking "$(box_dir "$inbox")" -mmin "+$unread_after_minutes")
      [ "$unread" -eq 0 ] || flag=1
    fi
    echo "$state $flag" > "$dir/.watch/$agent"
    if [ "$state" = blocked ] && [ "$last" != blocked ]; then echo "BLOCKED $agent"; return 0; fi
    if [ "$state" = gone ] && [ -n "$last" ] && [ "$last" != gone ]; then echo "GONE $agent"; return 0; fi
    if [ "$unread" -gt 0 ]; then echo "UNREAD $agent $unread"; return 0; fi
  done
  return 1
}

wait_box() {
  local dir watch="" timeout=3600 end n
  dir=$(box_dir "$1")
  shift
  while [ $# -gt 0 ]; do
    case $1 in
      --watch) need_value "$1" $#; watch=$2; shift 2 ;;
      --timeout) need_value "$1" $#; timeout=$2; shift 2 ;;
      *) usage ;;
    esac
  done
  end=$(( $(date +%s) + timeout ))
  while :; do
    n=$(waking "$dir")
    [ "$n" -eq 0 ] || { echo "MAIL $n"; return 0; }
    [ -z "$watch" ] || ! watch_once "$dir" "$watch" || return 0
    [ "$(date +%s)" -lt "$end" ] || { echo TIMEOUT; return 0; }
    sleep 2
  done
}

[ $# -ge 2 ] || usage
cmd=$1; shift
case $cmd in
  send) send "$@" ;;
  read) [ $# -eq 1 ] || usage; read_box "$1" ;;
  wait) wait_box "$@" ;;
  *) usage ;;
esac
