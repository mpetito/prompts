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

# Git for Windows: native tools (git, herdr) report paths as C:/x or C:\x where bash says /c/x, and a native jq.exe
# ends its lines with CRLF unless given -b (jq manual, --binary). canon <path> prints the one absolute form every
# comparison uses: realpath -m of bash's own spelling, resolving a relative path against $PWD. Convert a native
# tool's path with canon where it enters; native tools accept the bash form as an argument. canon_from <dir> <path>
# is canon of <path>, resolving a relative one against <dir> instead; there C:\x and C:/x are absolute too.
# MSYS converts a path argument for a native tool, but not a path inside prose: native <path> is the form to write
# into a prompt or brief an agent reads, C:/x on Windows, which bash and native tools both open.
case ${OSTYPE:-} in
  msys*|cygwin*)
    canon() { realpath -m -- "$(cygpath -u -- "$1")"; }
    canon_from() { local p; p=$(cygpath -u -- "$2"); [[ $p == /* ]] || p="$1/$p"; canon "$p"; }
    native() { cygpath -m -- "$1"; }
    jq() { command jq -b "$@"; } ;;
  *)
    canon() { realpath -m -- "$1"; }
    canon_from() { local p=$2; [[ $p == /* ]] || p="$1/$p"; canon "$p"; }
    native() { printf '%s\n' "$1"; } ;;
esac

# The thread's files live in its coordination worktree's untracked .orchestration/ folder, found from any
# directory inside that worktree. toplevel <dir> prints the worktree root, in canon form, or fails outside git.
toplevel() { local top; top=$(git -C "$1" rev-parse --show-toplevel 2>/dev/null) && canon "$top"; }

# resolve_state <dir> <env var to name in errors>: print the state file, from $ORCHESTRATION_STATE when set,
# else <git toplevel of dir>/.orchestration/state.md. Fails with a message naming the variable.
resolve_state() {
  if [ -n "${ORCHESTRATION_STATE:-}" ]; then echo "$ORCHESTRATION_STATE"; return 0; fi
  local top
  top=$(toplevel "$1") || { echo "$1 is not inside a git worktree; run from the coordination worktree or set $2" >&2; return 1; }
  echo "$top/.orchestration/state.md"
}

# The thread record, .orchestration/thread.md in the coordination worktree: one "Key: value" line per field, written
# by MAIN's thread.sh launch and read by the thread's scripts and hooks: the build (BUILD), the owner's checkout
# (CHECKOUT), and the build's base and landing mode (BASE, BASE-REF, LANE-BASE, LANDING).
record_value() {
  # record_value <file> <key>: the value of the first "<key>: value" line, trimmed, or nothing, also when the file is
  # missing, so callers under set -e and pipefail carry on.
  [ -f "$1" ] || return 0
  awk -v k="$2:" 'index($0, k) == 1 { v = substr($0, length(k) + 1); sub(/^[ \t]+/, "", v); sub(/[ \t]+$/, "", v); print v; exit }' "$1"
}

thread_field() { record_value "$1/.orchestration/thread.md" "$2"; }

# session_top <cwd>: the coordination worktree of this session: the git root of the folder the session started in
# ($CLAUDE_PROJECT_DIR, which a cd never moves), else of <cwd>.
session_top() { toplevel "${CLAUDE_PROJECT_DIR:-$1}"; }

owner_checkouts() {
  # owner_checkouts <coordination worktree root>: the owner's checkouts, one per line: the repository's main checkout
  # (the directory holding the common git dir) and, when the owner works in a linked worktree, the record's CHECKOUT.
  local common dir
  common=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  { dirname -- "$(canon "$common")"
    dir=$(thread_field "$1" CHECKOUT)
    [ -z "$dir" ] || canon "$dir"; } | awk '!seen[$0]++'
}

archive_ignored() {
  # archive_ignored <worktree> <destination> <path prefix to leave out>: copy the files git ignores in <worktree>
  # to <destination>/ignored/<path>, printing "archived ignored <path> to <destination>/ignored" on stdout for
  # each. Dependency and cache folders are rebuilt from the lockfiles, and the caller archives the prefix itself,
  # so both stay behind. git status leaves ignored files out and a forced worktree removal deletes them, so this
  # fails when git can't list them or a copy fails, and the caller must then remove nothing. The last stderr line
  # is the reason: a refusal saying nothing was removed when the listing fails, cp's own message when a copy fails.
  local wt=$1 dest=$2 prefix=$3 listing entry path
  local skip='(^|/)(node_modules|\.venv|venv|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.terraform|cdk\.out[^/]*|\.next|\.turbo|\.cache|dist|build|target)/?$'
  listing=$(mktemp)
  if ! git -C "$wt" status --porcelain=v1 -z --ignored=matching > "$listing"; then
    rm -f "$listing"
    echo "refusing: git status failed in $wt, so its ignored files can't be archived; nothing was removed" >&2
    return 1
  fi
  while IFS= read -r -d '' entry; do
    [ "${entry:0:3}" = '!! ' ] || continue
    path=${entry:3}
    case "$path" in "$prefix"|"$prefix/"*) continue ;; esac
    [[ $path =~ $skip ]] && continue
    { mkdir -p "$dest/ignored" && (cd "$wt" && cp -a --parents -- "${path%/}" "$dest/ignored/"); } || { rm -f "$listing"; return 1; }
    echo "archived ignored $path to $dest/ignored"
  done < "$listing"
  rm -f "$listing"
}

# Hook replies. advise adds a note beside the tool result and leaves the call, and its permission check, as they
# were; deny refuses the call with the reason.
advise() { jq -n --arg c "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$c}}'; exit 0; }
deny() { jq -n --arg r "$1" '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:"deny",permissionDecisionReason:$r}}'; exit 0; }
