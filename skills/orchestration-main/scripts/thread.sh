#!/usr/bin/env bash
# Launch, stop, rotate and list orchestration threads: background Claude Code sessions running the orchestrator
# agent, each in its build's coordination worktree, ../<repo>-orch-<build> beside the main checkout, on branch
# orchestration/<build>. The thread keeps its files in that worktree's untracked .orchestration/ folder.
#   thread.sh launch <name> <checkout> <brief file> --main <your session name> [--build <b>] [--base <branch>] [--landing pr|local]
#   thread.sh stop <name>
#   thread.sh rotate <name> --main <your session name> [--force]
#   thread.sh adopt <name> --main <your session name>
#   thread.sh check [--all]
#   thread.sh integrate <name>
#   thread.sh list
#   thread.sh decisions
# launch, stop, rotate, adopt and integrate print one line: LAUNCHED <name> <id> base=<branch>@<sha> landing=<mode>,
# STOPPED <name> <id>, ROTATED <old> -> <new> <id>, ADOPTED <name> main=<name> socket=<address>,
# INTEGRATED <name> <branch>@<sha> (fast-forward|merge), or FAILED <reason> with exit 1. check prints MOVED and
# INBOX lines, or OK; list and decisions print one line per thread or item, or NONE.
# The base defaults to the checkout's current branch. Landing is pr when the base is on origin with nothing
# unpushed, else local: lanes merge into orchestration/<build>, and integrate brings that branch into the base.
# Each thread's .orchestration/thread.md records MAIN's name and socket ($CLAUDE_CODE_MESSAGING_SOCKET), the
# owner's checkout, the base and the landing mode. A session's name can change with its title and its socket
# with a restart or fork, so MAIN runs check on every wake and adopt when it has moved. The copy in the worktree
# is within the thread's reach, so MAIN keeps its own in $ORCHESTRATION_HOME/records/ and acts only on that.
# MAIN's list of threads, across repositories, is $ORCHESTRATION_HOME/threads.tsv (default
# ~/.orchestration/threads.tsv), one tab-separated row per thread: name id build repo worktree main launched
set -euo pipefail
. "$(dirname "$0")/../../agent-orchestration/scripts/lib.sh"
# ROTATE makes the thread rewrite RESUME just before it answers "STATUS: rotating"; an older stamp means it never
# answered, and its RESUME may miss recent work.
resume_max_age_minutes=15
home=${ORCHESTRATION_HOME:-$HOME/.orchestration}
reg="$home/threads.tsv"
fail() { echo "FAILED $*"; exit 1; }
usage() { sed -n '2,24p' "$0" >&2; exit 1; }
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
# This session's own inbox address, as SendMessage takes it; empty where Claude Code exports no socket.
main_socket() { [ -z "${CLAUDE_CODE_MESSAGING_SOCKET:-}" ] || printf 'uds:%s' "$CLAUDE_CODE_MESSAGING_SOCKET"; }
main_copy() { printf '%s/records/%s.md' "$home" "$(printf '%s' "$1" | md5sum | cut -c1-16)"; }
publish_record() {
  # publish_record <worktree>: copy MAIN's record over the worktree's, undoing any change made there.
  mkdir -p "$1/.orchestration"
  cp "$(main_copy "$1")" "$1/.orchestration/thread.md.tmp" && mv "$1/.orchestration/thread.md.tmp" "$1/.orchestration/thread.md"
}
write_record() {
  # write_record <worktree> <main name> <checkout> <base> <base ref> <lane base> <landing>
  local copy
  copy=$(main_copy "$1")
  mkdir -p "$(dirname "$copy")"
  printf '%s\n' "# Thread record, written by MAIN's thread.sh (launch, rotate, adopt). The thread reads it and never edits it." \
    "MAIN: $2" "MAIN-SOCKET: $(main_socket)" "CHECKOUT: $3" "BASE: $4" "BASE-REF: $5" "LANE-BASE: $6" "LANDING: $7" \
    "UPDATED: $(utc_now)" > "$copy.tmp"
  mv "$copy.tmp" "$copy"
  publish_record "$1"
}
set_main() {
  # set_main <worktree> <main name> <checkout>: point MAIN's record at this session and publish it; a thread started
  # before records existed gets one with what the registry knows, and no base or landing mode.
  local copy
  copy=$(main_copy "$1")
  if [ ! -f "$copy" ]; then write_record "$1" "$2" "$3" "" "" "" ""; return 0; fi
  awk -v m="$2" -v s="$(main_socket)" -v u="$(utc_now)" '
    /^MAIN:/ { print "MAIN: " m; next } /^MAIN-SOCKET:/ { print "MAIN-SOCKET: " s; next }
    /^UPDATED:/ { print "UPDATED: " u; next } { print }' "$copy" > "$copy.tmp"
  mv "$copy.tmp" "$copy"
  publish_record "$1"
}
# record_field <worktree> <key>: a field from MAIN's own copy of the thread's record.
record_field() { sed -n "s/^$2:[[:space:]]*//p" "$(main_copy "$1")" 2>/dev/null | head -1 | sed -E 's/[[:space:]]+$//'; }
pick_base() {
  # pick_base <main checkout> <base branch> <requested landing or empty>: set base_ref and landing. origin/<base>
  # when the local branch has nothing unpushed (or is absent), else the local branch; landing follows: pr from
  # origin, local otherwise.
  local main=$1 base=$2 want=$3 local_ok=0 remote_ok=0 auto
  if git -C "$main" remote get-url origin >/dev/null 2>&1; then
    git -C "$main" fetch -q origin 2>/dev/null || echo "warning: git fetch origin failed in $main; using the refs already there" >&2
  fi
  git -C "$main" rev-parse --verify -q "refs/heads/$base^{commit}" >/dev/null && local_ok=1
  git -C "$main" rev-parse --verify -q "refs/remotes/origin/$base^{commit}" >/dev/null && remote_ok=1
  [ "$local_ok" = 1 ] || [ "$remote_ok" = 1 ] || fail "no branch $base in $main or on origin"
  if [ "$remote_ok" = 1 ] && { [ "$local_ok" = 0 ] || git -C "$main" merge-base --is-ancestor "refs/heads/$base" "refs/remotes/origin/$base"; }; then
    base_ref="origin/$base"; auto=pr
  else
    base_ref=$base; auto=local
  fi
  case $want in
    "") landing=$auto ;;
    local) landing=local ;;
    pr) [ "$auto" = pr ] || fail "--landing pr needs $base on origin with nothing unpushed; push it, or use --landing local"
        landing=pr ;;
    *) fail "--landing takes pr or local, got $want" ;;
  esac
}
ensure_worktree() {
  # ensure_worktree <main checkout> <common git dir> <worktree> <build> <base ref>: reuse the build's coordination
  # worktree or create it from <base ref>; fail with a reason otherwise.
  local main=$1 common=$2 wt=$3 build=$4 base_ref=$5 branch="orchestration/$4"
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
  if git -C "$main" rev-parse --verify -q "refs/heads/$branch" >/dev/null; then
    git -C "$main" worktree add -q "$wt" "$branch" >/dev/null 2>&1 || fail "git worktree add $wt $branch failed"
  else
    # --no-track: the coordination branch must never push to, or pull from, the base by accident.
    git -C "$main" worktree add -q --no-track -b "$branch" "$wt" "$base_ref" >/dev/null 2>&1 || fail "git worktree add $wt from $base_ref failed"
  fi
}
inbox() {
  # inbox <worktree> <thread name>: print the thread's outbox entries not shown before, then remember the count.
  # The thread's message hook copies every message to MAIN there, so one that never arrived is still read.
  local file="$1/.orchestration/outbox.md" mark seen total
  [ -f "$file" ] || return 0
  mkdir -p "$home/seen"
  mark="$home/seen/$(printf '%s' "$1" | md5sum | cut -c1-16)"
  seen=$(cat "$mark" 2>/dev/null || echo 0)
  total=$(grep -c '^=== ' "$file" || true)
  [ "$total" -ge "$seen" ] || seen=0
  [ "$total" -gt "$seen" ] || return 0
  awk -v skip="$seen" -v t="$2" '
    /^=== / { n++; on = (n > skip); if (on) { sub(/^=== /, ""); sub(/ #[0-9a-f]+$/, ""); print "INBOX " t " " $0 } next }
    on && NF { print "  " $0 }' "$file"
  echo "$total" > "$mark"
}

cmd=${1:-}; [ $# -gt 0 ] && shift
case "$cmd" in
  launch)
    [ $# -ge 3 ] || usage
    name=$1; repo=$2; brief=$3; shift 3
    main_name=""; build=""; base=""; want=""
    while [ $# -gt 0 ]; do
      case $1 in
        --main) need_value "$1" $#; main_name=$2; shift 2 ;;
        --build) need_value "$1" $#; build=$2; shift 2 ;;
        --base) need_value "$1" $#; base=$2; shift 2 ;;
        --landing) need_value "$1" $#; want=$2; shift 2 ;;
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
    checkout=$(realpath -m "$(git -C "$repo" rev-parse --show-toplevel)")
    # The main checkout holds the common git dir, so a linked worktree passed here still names the main one.
    main=$(dirname "$common")
    wt="$(dirname "$main")/$(basename "$main")-orch-$build"
    if [ -z "$base" ]; then
      base=$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null) || fail "$repo is on a detached HEAD; pass --base <branch>"
    fi
    ensure_registry
    [ -z "$(row_by 1 "$name")" ] || fail "a thread named $name is already registered; stop it or pick another name"
    taken=$(row_by 5 "$wt" | cut -f1 | head -1)
    [ -z "$taken" ] || fail "$wt already hosts thread $taken; one running thread per coordination worktree, so stop it or pick another --build"
    pick_base "$main" "$base" "$want"
    ensure_worktree "$main" "$common" "$wt" "$build" "$base_ref"
    mkdir -p "$common/info"
    grep -qxF '.orchestration/' "$common/info/exclude" 2>/dev/null || printf '.orchestration/\n' >> "$common/info/exclude"
    if [ "$landing" = pr ]; then lane_base=$base_ref; else lane_base="orchestration/$build"; fi
    write_record "$wt" "$main_name" "$checkout" "$base" "$base_ref" "$lane_base" "$landing"
    state="$wt/.orchestration/state.md"
    # The row exists before the session starts, so a failed start can be cleaned up by name.
    put_row "$name" "$(row "$name" pending "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    if ! id=$(start_session "$name" "$wt" "$(brief_text "$main_name" "$state" "$(cat "$brief")")" 2>"$reg.err"); then
      delete_row "$name"; reason=$(cat "$reg.err"); rm -f "$reg.err"; fail "$reason"
    fi
    rm -f "$reg.err"
    put_row "$name" "$(row "$name" "$id" "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    echo "LAUNCHED $name $id base=$base@$(git -C "$main" rev-parse --short "$base_ref") landing=$landing" ;;
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
    set_main "$wt" "$main_name" "$main"
    put_row "$old" "$(row "$new" pending "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    brief=$(brief_text "$main_name" "$state" "Resume: read STATE first and continue from its RESUME section without redoing finished work.")
    if ! newid=$(start_session "$new" "$wt" "$brief" 2>"$reg.err"); then
      delete_row "$new"; reason=$(cat "$reg.err"); rm -f "$reg.err"
      fail "$old was stopped but $new did not start: $reason; start it with thread.sh launch"
    fi
    rm -f "$reg.err"
    put_row "$new" "$(row "$new" "$newid" "$build" "$main" "$wt" "$main_name" "$(utc_now)")"
    echo "ROTATED $old -> $new $newid" ;;
  adopt)
    [ $# -ge 1 ] || usage
    t=$1; shift; main_name=""
    while [ $# -gt 0 ]; do
      case $1 in --main) need_value "$1" $#; main_name=$2; shift 2 ;; *) usage ;; esac
    done
    [ -n "$main_name" ] || fail "adopt needs --main <your session name>"
    found=$(row_by 1 "$t"); [ -n "$found" ] || fail "no thread named $t in $reg"
    IFS=$'\t' read -r _ id build main wt _ launched <<< "$found"
    set_main "$wt" "$main_name" "$main"
    put_row "$t" "$(row "$t" "$id" "$build" "$main" "$wt" "$main_name" "$launched")"
    sock=$(main_socket)
    echo "ADOPTED $t main=$main_name socket=${sock:-none}" ;;
  check)
    all=0
    if [ "${1:-}" = --all ]; then all=1; shift; fi
    [ $# -eq 0 ] || usage
    rows=$(awk 'NR > 1' "$reg" 2>/dev/null || true)
    [ -n "$rows" ] || { echo NONE; exit 0; }
    # Only this repository's threads, unless --all or outside git: other main sessions own the rest.
    here=""
    if [ "$all" = 0 ] && c=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null); then here=$(dirname "$(realpath -m "$c")"); fi
    sock=$(main_socket); printed=0
    while IFS=$'\t' read -r name _ _ repo wt main_name _; do
      [ -n "$name" ] || continue
      [ -z "$here" ] || [ "$repo" = "$here" ] || continue
      copy=$(main_copy "$wt")
      if [ -f "$copy" ] && ! cmp -s "$copy" "$wt/.orchestration/thread.md"; then
        echo "CHANGED $name: its thread record differs from yours; restore it with thread.sh adopt $name --main <your name>"
        printed=1
      fi
      if [ -f "$copy" ]; then rec=$(record_field "$wt" MAIN-SOCKET); else rec=$(thread_field "$wt" MAIN-SOCKET); fi
      if [ -n "$sock" ] && [ "$rec" != "$sock" ]; then
        echo "MOVED $name main=$main_name recorded=${rec:-none} this=$sock: if you are its main session now, run thread.sh adopt $name --main <your name>"
        printed=1
      fi
      out=$(inbox "$wt" "$name")
      if [ -n "$out" ]; then printf '%s\n' "$out"; printed=1; fi
    done <<< "$rows"
    [ "$printed" = 1 ] || echo OK ;;
  integrate)
    [ $# -eq 1 ] || usage
    found=$(row_by 1 "$1"); [ -n "$found" ] || fail "no thread named $1 in $reg"
    IFS=$'\t' read -r _ _ build repo wt _ _ <<< "$found"
    [ -f "$(main_copy "$wt")" ] || fail "no record of $1 in $home/records; it was launched before records existed, so integrate by hand"
    landing=$(record_field "$wt" LANDING); base=$(record_field "$wt" BASE); checkout=$(record_field "$wt" CHECKOUT)
    [ "$landing" = local ] || fail "$1 lands by pull request (LANDING: ${landing:-unknown}), so its base moves on origin; pull it instead"
    [ -n "$base" ] && [ -d "$checkout" ] || fail "no BASE or CHECKOUT in $(main_copy "$wt")"
    [ "$(realpath -m "$(git -C "$checkout" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)")" \
      = "$(realpath -m "$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)")" ] \
      || fail "$checkout is not a checkout of $repo"
    cur=$(git -C "$checkout" symbolic-ref --quiet --short HEAD 2>/dev/null || echo 'a detached HEAD')
    [ "$cur" = "$base" ] || fail "$checkout is on $cur, not $base; check out $base there first"
    { git -C "$checkout" diff --quiet && git -C "$checkout" diff --cached --quiet; } \
      || fail "$checkout has uncommitted changes to tracked files; commit or stash them first"
    src="orchestration/$build"
    if git -C "$checkout" merge -q --ff-only "$src" >/dev/null 2>&1; then how=fast-forward
    elif git -C "$checkout" -c core.editor=true merge -q --no-ff --no-edit "$src" >/dev/null 2>&1; then how=merge
    else
      conflicted=$(git -C "$checkout" diff --name-only --diff-filter=U | tr '\n' ' ')
      git -C "$checkout" merge --abort >/dev/null 2>&1 || true
      fail "merging $src into $base conflicts in: $conflicted"
    fi
    echo "INTEGRATED $1 $base@$(git -C "$checkout" rev-parse --short HEAD) ($how)" ;;
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
