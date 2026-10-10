# Shared helpers for the orchestration scripts and hooks. Sourced, not run.
# Times are UTC "YYYY-MM-DDTHH:MMZ" from date -u. Needs GNU date and realpath (coreutils): BSD date has no -d,
# so on macOS install coreutils and put its tools first on PATH.

utc_now() { date -u +%Y-%m-%dT%H:%MZ; }

fmt_utc() { date -u -d "@$1" +%Y-%m-%dT%H:%MZ; }

# to_epoch <UTC time | +<N>m | +<N>h>: print epoch seconds, or name the bad value on stderr and fail.
to_epoch() {
  if [[ $1 =~ ^\+([0-9]+)([mh])$ ]]; then
    local unit=60
    [ "${BASH_REMATCH[2]}" = h ] && unit=3600
    echo $(( $(date -u +%s) + BASH_REMATCH[1] * unit ))
  elif [[ $1 =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}(:[0-9]{2})?Z$ ]]; then
    date -u -d "$1" +%s
  else
    echo "not a UTC time (YYYY-MM-DDTHH:MMZ) or +<N>m / +<N>h: $1" >&2
    return 1
  fi
}

# need_value <option> <remaining argument count>: fail with a usage hint when an option lacks its value.
need_value() {
  [ "$2" -ge 2 ] || { echo "option $1 needs a value" >&2; exit 1; }
}

# The thread's files live in its coordination worktree's untracked .orchestration/ folder, found from any
# directory inside that worktree. toplevel <dir> prints the worktree root, or fails outside git.
toplevel() { git -C "$1" rev-parse --show-toplevel 2>/dev/null; }

# resolve_state <dir> <env var to name in errors>: print the state file, from $ORCHESTRATION_STATE when set,
# else <git toplevel of dir>/.orchestration/state.md. Fails with a message naming the variable.
resolve_state() {
  if [ -n "${ORCHESTRATION_STATE:-}" ]; then echo "$ORCHESTRATION_STATE"; return 0; fi
  local top
  top=$(toplevel "$1") || { echo "$1 is not inside a git worktree; run from the coordination worktree or set $2" >&2; return 1; }
  echo "$top/.orchestration/state.md"
}

# The thread record, .orchestration/thread.md in the coordination worktree: one "Key: value" line per field,
# written by MAIN's thread.sh (launch, rotate, adopt) and read by the thread's scripts and hooks. It is the one
# home for MAIN's address (MAIN, MAIN-SOCKET), the owner's checkout (CHECKOUT) and the build's base and
# landing mode (BASE, BASE-REF, LANE-BASE, LANDING).
thread_field() {
  # thread_field <coordination worktree root> <key>: print the value, or nothing.
  sed -n "s/^$2:[[:space:]]*//p" "$1/.orchestration/thread.md" 2>/dev/null | head -1 | sed -E 's/[[:space:]]+$//'
}

main_name() {
  # main_name <coordination worktree root>: MAIN's session name from the thread record, or from the MAIN: line of
  # a state file written before the record existed.
  local name
  name=$(thread_field "$1" MAIN)
  [ -n "$name" ] || name=$(sed -n 's/^MAIN:[[:space:]]*//p' "$1/.orchestration/state.md" 2>/dev/null | head -1 | sed -E 's/[[:space:]]+$//')
  printf '%s' "$name"
}

owner_checkout() {
  # owner_checkout <coordination worktree root>: the owner's checkout from the record, else the repository's main
  # checkout (the directory holding the common git dir).
  local dir common
  dir=$(thread_field "$1" CHECKOUT)
  if [ -z "$dir" ]; then
    common=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
    dir=$(dirname "$common")
  fi
  realpath -m -- "$dir"
}

worktree_of() {
  # worktree_of <path>: the root of the git worktree holding <path> (which may not exist yet), or nothing.
  local d
  d=$(dirname -- "$1")
  while [ ! -d "$d" ] && [ "$d" != / ]; do d=$(dirname -- "$d"); done
  toplevel "$d" | xargs -r -d '\n' realpath -m --
}

# Hook replies. advise adds a note beside the tool result and leaves the call, and its permission check, as they
# were; deny refuses the call with the reason.
advise() { jq -n --arg c "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'; exit 0; }
deny() { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
