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
record_value() {
  # record_value <file> <key>: the value of the first "<key>: value" line, trimmed, or nothing. The key is matched as
  # plain text, never as a pattern or script, and a missing file prints nothing rather than failing, so callers
  # under set -e and pipefail survive it.
  [ -f "$1" ] || return 0
  awk -v k="$2:" 'index($0, k) == 1 { v = substr($0, length(k) + 1); sub(/^[ \t]+/, "", v); sub(/[ \t]+$/, "", v); print v; exit }' "$1"
}

thread_field() {
  # thread_field <coordination worktree root> <key>: print the value, or nothing.
  record_value "$1/.orchestration/thread.md" "$2"
}

main_name() {
  # main_name <coordination worktree root>: MAIN's session name from the thread record, or from the MAIN: line of
  # a state file written before the record existed.
  local name
  name=$(thread_field "$1" MAIN)
  [ -n "$name" ] || name=$(record_value "$1/.orchestration/state.md" MAIN)
  printf '%s' "$name"
}

# session_top <cwd>: the coordination worktree of this session: the git root of the folder the session started in
# ($CLAUDE_PROJECT_DIR, which a cd never moves), else of <cwd>.
session_top() { toplevel "${CLAUDE_PROJECT_DIR:-$1}"; }

main_record() {
  # main_record <coordination worktree root>: MAIN's own copy of the thread record, which thread.sh keeps under
  # $ORCHESTRATION_HOME/records/ out of the thread's reach (the hooks refuse writes there).
  printf '%s/records/%s.md' "${ORCHESTRATION_HOME:-$HOME/.orchestration}" "$(printf '%s' "$1" | md5sum | cut -c1-16)"
}

owner_checkouts() {
  # owner_checkouts <coordination worktree root>: every checkout to protect, one per line: the repository's main
  # checkout (the directory holding the common git dir), which the thread cannot redirect, and the CHECKOUT in MAIN's
  # copy of the record, for an owner working in a linked worktree. The worktree's copy is only a fallback, when MAIN
  # keeps none: the thread can delete and rewrite that one.
  local common dir
  common=$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || return 1
  { dirname -- "$(realpath -m -- "$common")"
    dir=$(record_value "$(main_record "$1")" CHECKOUT)
    [ -n "$dir" ] || [ -f "$(main_record "$1")" ] || dir=$(thread_field "$1" CHECKOUT)
    [ -z "$dir" ] || realpath -m -- "$dir"; } | awk '!seen[$0]++'
}

registered_worktree() {
  # registered_worktree <dir> <any worktree of the repository>: true when <dir> is one of the repository's worktrees.
  git -C "$2" worktree list --porcelain 2>/dev/null | sed -n 's/^worktree //p' | xargs -r -d '\n' realpath -m -- \
    | grep -qxF -- "$1"
}

in_checkout() {
  # in_checkout <target> <checkout>: true when <target> is inside <checkout> and not inside a subagent's worktree
  # nested in it (a registered worktree under <checkout>/.claude/worktrees/). Fails closed: a path git cannot
  # place there counts as inside, and so does any other worktree nested in the checkout, wherever registered.
  local tree
  case "$1/" in "$2/"*) ;; *) return 1 ;; esac
  tree=$(worktree_of "$1")
  [ -n "$tree" ] || return 0
  case "$tree/" in "$2/.claude/worktrees/"?*) ;; *) return 0 ;; esac
  registered_worktree "$tree" "$2" && return 1
  return 0
}

config_file() {
  # config_file <path> <coordination worktree root>: true for files that configure Claude Code, Codex or the
  # orchestration: settings files anywhere, ~/.claude.json, ~/.codex/, the registry, and the thread record.
  local orch
  orch=$(realpath -m -- "${ORCHESTRATION_HOME:-$HOME/.orchestration}")
  case "$1" in
    */.claude/settings.json|*/.claude/settings.local.json|"$HOME/.claude.json"|*/.codex|*/.codex/*) return 0 ;;
    "$orch"|"$orch/"*|"$2/.orchestration/thread.md") return 0 ;;
  esac
  return 1
}

session_config() {
  # session_config <path> <coordination worktree root>: true for files in the coordination worktree that configure
  # the thread's own session: project settings, agents, skills, commands and hooks under .claude/, .mcp.json and
  # CLAUDE.md. A project agent named orchestrator would replace the one that carries these hooks. Subagents'
  # worktrees under .claude/worktrees/ are not configuration; the caller checks them first.
  case "$1" in
    "$2/.claude"|"$2/.claude/"*|"$2/.mcp.json"|"$2/CLAUDE.md"|"$2/CLAUDE.local.md") return 0 ;;
  esac
  return 1
}

build_worktree() {
  # build_worktree <path> <coordination worktree root> <main checkout>: true when <path> is inside a worktree the
  # build uses: a lane's, beside the main checkout as <repo>-wt-<lane>, or a subagent's, under .claude/worktrees/ of
  # the main checkout or of the coordination worktree. Both the place and git's registration count: the thread can
  # register a worktree anywhere with git worktree add, so registration alone grants nothing.
  local tree lanes
  tree=$(worktree_of "$1")
  [ -n "$tree" ] || return 1
  lanes="$(dirname -- "$3")/$(basename -- "$3")-wt-"
  case "$tree" in
    "$lanes"?*) case "${tree#"$lanes"}" in */*) return 1 ;; esac ;;
    "$3/.claude/worktrees/"?*|"$2/.claude/worktrees/"?*) ;;
    *) return 1 ;;
  esac
  registered_worktree "$tree" "$2"
}

scratch_path() {
  # scratch_path <path>: true under a temp folder (/tmp, /var/tmp, $TMPDIR), outside the home folder.
  local home tmpdir
  home=$(realpath -m -- "$HOME"); tmpdir=$(realpath -m -- "${TMPDIR:-/tmp}")
  case "$1/" in "$home/"*) return 1 ;; esac
  case "$1/" in /tmp/*|/var/tmp/*|"$tmpdir/"*) return 0 ;; esac
  return 1
}

worktree_of() {
  # worktree_of <path>: the root of the git worktree holding <path> (which may not exist yet), or nothing.
  local d
  d=$(dirname -- "$1")
  while [ ! -d "$d" ] && [ "$d" != / ]; do d=$(dirname -- "$d"); done
  toplevel "$d" | xargs -r -d '\n' realpath -m --
}

# Hook replies. advise adds a note beside the tool result and leaves the call, and its permission check, as they
# were; deny refuses the call with the reason. Neither needs jq, so a hook can still refuse when jq is missing.
json_string() {
  local s=$1
  s=${s//\\/\\\\}; s=${s//\"/\\\"}; s=${s//$'\n'/\\n}; s=${s//$'\r'/\\r}; s=${s//$'\t'/\\t}
  s=$(printf '%s' "$s" | tr -d '\000-\010\013\014\016-\037')
  printf '"%s"' "$s"
}
advise() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":%s}}\n' "$(json_string "$1")"; exit 0; }
deny() { printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":%s}}\n' "$(json_string "$1")"; exit 0; }
# require_jq: the hooks read their input with jq; without it every field would read as empty and the hook would
# allow everything, so refuse instead.
require_jq() { command -v jq >/dev/null 2>&1 || deny "jq is not installed, so this orchestration hook cannot read the tool call; it refuses rather than allows. Install jq."; }
