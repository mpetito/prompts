#!/usr/bin/env bash
# Launch, stop, rotate and list orchestration threads: background Claude Code sessions running the orchestrator
# agent, each in its build's coordination worktree, ../<repo>-orch-<build> beside the main checkout, on branch
# orchestration/<build>. The thread keeps its files in that worktree's untracked .orchestration/ folder.
#   thread.sh launch <name> <repo checkout> <brief file> --main <main session name> [--build <build>] [--base <branch>]
#   thread.sh stop <name>
#   thread.sh rotate <name> --main <main session name> [--force]
#   thread.sh list
#   thread.sh decisions
# launch, stop and rotate print one line: LAUNCHED <name> <id>, STOPPED <name> <id>, ROTATED <old> -> <new> <id>,
# or FAILED <reason> with exit 1. list and decisions print one line per thread or item, or NONE.
# MAIN's list of running threads, across repositories, is $ORCHESTRATION_HOME/threads.tsv (default
# ~/.orchestration/threads.tsv), one tab-separated row per thread: name id build repo worktree main launched
set -euo pipefail
. "$(dirname "$0")/../../agent-orchestration/scripts/lib.sh"
# ROTATE makes the thread rewrite RESUME just before it answers "STATUS: rotating"; an older stamp means it never
# answered, and its RESUME may miss recent work.
resume_max_age_minutes=15
home=${ORCHESTRATION_HOME:-$HOME/.orchestration}
reg="$home/threads.tsv"
fail() { echo "FAILED $*"; exit 1; }
usage() { sed -n '2,14p' "$0" >&2; exit 1; }
ensure_registry() {
  mkdir -p "$home"
  [ -f "$reg" ] || printf 'name\tid\tbuild\trepo\tworktree\tmain\tlaunched\n' > "$reg"
}
row_by() { awk -F'\t' -v c="$1" -v v="$2" 'NR > 1 && $c == v' "$reg" 2>/dev/null || true; }
delete_row() {
  awk -F'\t' -v n="$1" 'NR == 1 || $1 != n' "$reg" > "$reg.tmp" && mv "$reg.tmp" "$reg"
}
put_row() {
  # put_row <old name> <row>: replace the row named <old name>, or append when there is none.
  awk -F'\t' -v n="$1" -v r="$2" 'NR > 1 && $1 == n { print r; done = 1; next } { print } END { if (!done) print r }' "$reg" > "$reg.tmp" \
    && mv "$reg.tmp" "$reg"
}
row() { printf '%s\t%s\t%s\t%s\t%s\t%s\t%s' "$@"; }
valid_name() { [[ $1 =~ ^[A-Za-z0-9_-]+$ ]] || fail "$2 '$1' may hold only letters, digits, hyphens and underscores (other sessions address it by name)"; }
claude_env() {
  # A nested session refuses to start while CLAUDECODE marks the parent, and Herdr variables would make the
  # thread treat the caller's terminal pane as its own.
  local args=(-u CLAUDECODE) v
  for v in $(compgen -e | grep '^HERDR_' || true); do args+=(-u "$v"); done
  env "${args[@]}" "$@"
}
start_session() {
  # start_session <name> <worktree> <brief text>: print the new session's short id, or a reason on stderr.
  local out code=0 id
  out=$(cd "$2" && claude_env claude --agent orchestrator --bg --name "$1" "$3" 2>&1) || code=$?
  if printf '%s' "$out" | grep -qi 'workspace not trusted'; then
    echo "workspace not trusted: start the thread from a repository Claude Code trusts (claude: $(printf '%s' "$out" | grep -i -m1 'trusted'))" >&2; return 1
  fi
  if printf '%s' "$out" | grep -qi 'no agent named'; then
    echo "no agent named orchestrator: run setup-skills-link.ps1 so agents/orchestrator.md is linked into ~/.claude/agents" >&2; return 1
  fi
  id=$(printf '%s\n' "$out" | sed -n 's/.*backgrounded[^0-9a-f]*\([0-9a-f]\{8,\}\).*/\1/p' | head -1)
  if [ "$code" -ne 0 ] || [ -z "$id" ]; then
    echo "claude exited $code: $(printf '%s\n' "$out" | grep -m1 . || echo 'no output')" >&2; return 1
  fi
  echo "$id"
}
# brief_text <main> <state> <body>: the header lines, a blank line, then the body. One printf, because a command
# substitution would strip the blank line that separates them.
brief_text() { printf 'MAIN: %s\nSTATE: %s\n\n%s' "$1" "$2" "$3"; }
ensure_worktree() {
  # ensure_worktree <main checkout> <common git dir> <worktree> <build> <base or empty>: reuse the build's
  # coordination worktree or create it from origin/<base>; fail with a reason otherwise.
  local main=$1 common=$2 wt=$3 build=$4 base=$5 branch="orchestration/$4" head
  if [ -e "$wt" ]; then
    local its_common its_top
    its_common=$(git -C "$wt" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)
    its_top=$(git -C "$wt" rev-parse --show-toplevel 2>/dev/null || true)
    if [ -n "$its_common" ] && [ -n "$its_top" ] && [ "$(realpath -m "$its_common")" = "$common" ] \
      && [ "$(realpath -m "$its_top")" = "$wt" ] && [ "$(git -C "$wt" rev-parse --abbrev-ref HEAD)" = "$branch" ]; then
      return 0
    fi
    fail "$wt exists and is not the coordination worktree for build $build (branch $branch of $main); move it aside or pick another --build"
  fi
  git -C "$main" fetch -q origin 2>/dev/null || fail "git fetch origin failed in $main"
  if [ -z "$base" ]; then
    head=$(git -C "$main" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)
    [ -n "$head" ] || { git -C "$main" remote set-head origin --auto >/dev/null 2>&1 || true; head=$(git -C "$main" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true); }
    [ -n "$head" ] || fail "cannot tell origin's default branch in $main; pass --base <branch>"
    base=${head#origin/}
  fi
  git -C "$main" rev-parse --verify -q "origin/$base^{commit}" >/dev/null || fail "no branch origin/$base in $main"
  if git -C "$main" rev-parse --verify -q "refs/heads/$branch" >/dev/null; then
    git -C "$main" worktree add -q "$wt" "$branch" >/dev/null 2>&1 || fail "git worktree add $wt $branch failed"
  else
    # --no-track: the coordination branch must never push to, or pull from, the base by accident.
    git -C "$main" worktree add -q --no-track -b "$branch" "$wt" "origin/$base" >/dev/null 2>&1 || fail "git worktree add $wt from origin/$base failed"
  fi
}

cmd=${1:-}; [ $# -gt 0 ] && shift
case "$cmd" in
  launch)
    [ $# -ge 3 ] || usage
    name=$1; repo=$2; brief=$3; shift 3
    main_name=""; build=""; base=""
    while [ $# -gt 0 ]; do
      case $1 in
        --main) need_value "$1" $#; main_name=$2; shift 2 ;;
        --build) need_value "$1" $#; build=$2; shift 2 ;;
        --base) need_value "$1" $#; base=$2; shift 2 ;;
        *) usage ;;
      esac
    done
    [ -n "$main_name" ] || fail "launch needs --main <main session name>"
    valid_name "$name" "thread name"
    build=${build:-$name}
    valid_name "$build" "build name"
    [ -d "$repo" ] || fail "no repository checkout at $repo"
    [ -s "$brief" ] || fail "no brief at $brief"
    common=$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || fail "$repo is not a git checkout"
    common=$(realpath -m "$common")
    # The main checkout holds the common git dir, so a linked worktree passed here still names the main one.
    main=$(dirname "$common")
    wt="$(dirname "$main")/$(basename "$main")-orch-$build"
    ensure_registry
    [ -z "$(row_by 1 "$name")" ] || fail "a thread named $name is already registered; stop it or pick another name"
    taken=$(row_by 5 "$wt" | cut -f1 | head -1)
    [ -z "$taken" ] || fail "$wt already hosts thread $taken; one running thread per coordination worktree, so stop it or pick another --build"
    ensure_worktree "$main" "$common" "$wt" "$build" "$base"
    mkdir -p "$common/info"
    grep -qxF '.orchestration/' "$common/info/exclude" 2>/dev/null || printf '.orchestration/\n' >> "$common/info/exclude"
    state="$wt/.orchestration/state.md"
    # The row exists before the session starts, so a failed start can be cleaned up by name.
    put_row "$name" "$(row "$name" pending "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    if ! id=$(start_session "$name" "$wt" "$(brief_text "$main_name" "$state" "$(cat "$brief")")" 2>"$reg.err"); then
      delete_row "$name"; reason=$(cat "$reg.err"); rm -f "$reg.err"; fail "$reason"
    fi
    rm -f "$reg.err"
    put_row "$name" "$(row "$name" "$id" "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    echo "LAUNCHED $name $id" ;;
  stop)
    [ $# -eq 1 ] || usage
    found=$(row_by 1 "$1"); [ -n "$found" ] || fail "no thread named $1 in $reg"
    id=$(printf '%s\n' "$found" | cut -f2)
    out=$(claude_env claude stop "$id" 2>&1) || fail "claude stop $id: $(printf '%s\n' "$out" | grep -m1 . || echo 'no output')"
    delete_row "$1"
    echo "STOPPED $1 $id" ;;
  rotate)
    [ $# -ge 1 ] || usage
    old=$1; shift
    main_name=""; force=0
    while [ $# -gt 0 ]; do
      case $1 in
        --main) need_value "$1" $#; main_name=$2; shift 2 ;;
        --force) force=1; shift ;;
        *) usage ;;
      esac
    done
    [ -n "$main_name" ] || fail "rotate needs --main <main session name>"
    found=$(row_by 1 "$old"); [ -n "$found" ] || fail "no thread named $old in $reg"
    IFS=$'\t' read -r _ id build main wt _ _ <<< "$found"
    state="$wt/.orchestration/state.md"
    if [ "$force" = 0 ]; then
      written=$(awk '/^## RESUME/ { r = 1; next } r && /^## / { exit } r && /^Written:/ { sub(/^Written:[ \t]*/, ""); print; exit }' "$state" 2>/dev/null || true)
      [ -n "$written" ] || fail "no RESUME Written: stamp in $state; send ROTATE and wait for 'STATUS: rotating', or pass --force"
      age=$(( ($(date -u +%s) - $(to_epoch "$written")) / 60 ))
      [ "$age" -le "$resume_max_age_minutes" ] \
        || fail "RESUME in $state was written $age min ago (limit $resume_max_age_minutes); send ROTATE and wait for 'STATUS: rotating', or pass --force"
    fi
    if [[ $old =~ ^(.+)-r([0-9]+)$ ]]; then new="${BASH_REMATCH[1]}-r$(( BASH_REMATCH[2] + 1 ))"; else new="$old-r1"; fi
    [ -z "$(row_by 1 "$new")" ] || fail "a thread named $new is already registered; stop it before rotating $old"
    out=$(claude_env claude stop "$id" 2>&1) || fail "claude stop $id: $(printf '%s\n' "$out" | grep -m1 . || echo 'no output')"
    put_row "$old" "$(row "$new" pending "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    brief=$(brief_text "$main_name" "$state" "Resume: read STATE first and continue from its RESUME section without redoing finished work.")
    if ! newid=$(start_session "$new" "$wt" "$brief" 2>"$reg.err"); then
      delete_row "$new"; reason=$(cat "$reg.err"); rm -f "$reg.err"
      fail "$old was stopped but $new did not start: $reason; start it with thread.sh launch"
    fi
    rm -f "$reg.err"
    put_row "$new" "$(row "$new" "$newid" "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    echo "ROTATED $old -> $new $newid" ;;
  list)
    [ $# -eq 0 ] || usage
    rows=$(awk 'NR > 1' "$reg" 2>/dev/null || true)
    [ -n "$rows" ] || { echo NONE; exit 0; }
    live=$(claude_env claude agents --json 2>/dev/null || true)
    printf '%s' "$live" | jq -e 'type == "array"' >/dev/null 2>&1 || live=""
    while IFS=$'\t' read -r name id build main wt main_name launched; do
      status=unknown
      [ -n "$live" ] && status=$(printf '%s' "$live" | jq -r --arg id "$id" '[.[] | select((.sessionId // "") | startswith($id))][0].status // "not-running"')
      echo "$name $id build=$build status=$status main=$main_name worktree=$wt launched=$launched"
    done <<< "$rows"
    ;;
  decisions)
    [ $# -eq 0 ] || usage
    rows=$(awk 'NR > 1' "$reg" 2>/dev/null || true)
    items=""
    while IFS=$'\t' read -r name _ _ _ wt _ _; do
      [ -n "$name" ] || continue
      file="$wt/.orchestration/decisions.md"
      [ -f "$file" ] || continue
      # Sort key first: 0 for owner-before items, 1<deadline> for the rest, so owner-before comes first.
      items+=$(awk -v t="$name" -v why=" · why now: " -v dflt=" · default: " -v dot=" · " '
        /^## Open/ { on = 1; next } /^## / { on = 0 }
        on && match($0, /^- D[0-9]+ \([^)]*\) /) {
          id = substr($0, 3); sub(/ .*/, "", id)
          rest = substr($0, RLENGTH + 1)
          # Separator lengths come from length(), so byte- and character-oriented awks agree on the "·".
          what = rest; i = index(what, why); if (i) what = substr(what, 1, i - 1)
          def = ""; i = index(rest, dflt)
          if (i) { def = substr(rest, i + length(dflt)); j = index(def, dot); if (j) def = substr(def, 1, j - 1) }
          if (match(rest, /applies at [0-9T:Z-]+/)) { when = substr(rest, RSTART + 11, RLENGTH - 11); key = "1" when; tail = "applies at " when }
          else { key = "0"; tail = "owner-before" }
          printf "%s\t%s %s %s | default: %s | %s\n", key, t, id, what, def, tail
        }' "$file")$'\n'
    done <<< "$rows"
    items=$(printf '%s' "$items" | grep . || true)
    [ -n "$items" ] || { echo NONE; exit 0; }
    printf '%s\n' "$items" | sort -t$'\t' -k1,1 | cut -f2- ;;
  *) usage ;;
esac
