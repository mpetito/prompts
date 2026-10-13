#!/usr/bin/env bash
# Launch, stop, rotate and list orchestration threads: herdr agents running the orchestrator agent, one per build,
# each named after its build and started in the build's own herdr workspace from its coordination worktree,
# ../<repo>-orch-<build> beside the main checkout, on branch orchestration/<build>. The thread keeps its files in
# that worktree's untracked .orchestration/ folder, and talks to MAIN through the build's mailboxes (mail.sh).
#   thread.sh launch <build> <checkout> <brief file> [--base <branch>] [--landing pr|local]
#   thread.sh stop <build>
#   thread.sh rotate <build> [--force]
#   thread.sh check [--all]
#   thread.sh integrate <build>
#   thread.sh close <build> | --worktree <coordination worktree> [--base <branch>] [--force]
#   thread.sh list
#   thread.sh decisions
# launch, stop, rotate and integrate print one line: LAUNCHED <build> base=<branch>@<sha> landing=<mode>,
# BLOCKED <build> <reason> (launched, but waiting on a startup prompt the owner must answer), STOPPED <build>,
# ROTATED <build>, INTEGRATED <build> <branch>@<sha> (fast-forward|merge), CLOSED <build> archive=<dir>, or
# FAILED <reason> with exit 1. close ends a build: it refuses while the build branch holds work the base lacks,
# archives .orchestration/ and the build's mail under $ORCHESTRATION_HOME/archive/<build>-<stamp>/ and the
# worktree's other ignored files (not dependency or cache folders) under its ignored/, then removes the worktree and
# branch and closes the build's workspace. check prints IDENTITY lines (a repository's local git config sets
# user.name or user.email apart from the global one), or OK; list and decisions print one line per thread or item,
# or NONE.
# A build name is a herdr agent name, [a-z][a-z0-9_-]{0,31}, and a thread keeps it across rotations.
# The base defaults to the checkout's current branch. Landing is pr when the base is on origin with nothing
# unpushed, else local: lanes merge into orchestration/<build>, and integrate brings that branch into the base.
# Each thread's .orchestration/thread.md records its build, the owner's checkout, the base and the landing mode.
# MAIN's list of threads, across repositories, is $ORCHESTRATION_HOME/threads.tsv (default
# ~/.orchestration/threads.tsv), one tab-separated row per thread: build repo worktree workspace launched
set -euo pipefail
. "$(dirname "$0")/../../agent-orchestration/scripts/lib.sh"
# ROTATE makes the thread rewrite RESUME just before it answers "STATUS: rotating"; an older stamp means it never
# answered, and its RESUME may miss recent work.
resume_max_age_minutes=15
home=${ORCHESTRATION_HOME:-$HOME/.orchestration}
reg="$home/threads.tsv"
fail() { echo "FAILED $*"; exit 1; }
usage() { sed -n '2,28p' "$0" >&2; exit 1; }
ensure_registry() {
  mkdir -p "$home"
  [ -f "$reg" ] || printf 'build\trepo\tworktree\tworkspace\tlaunched\n' > "$reg"
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
row() { printf '%s\t%s\t%s\t%s\t%s' "$@"; }
valid_name() { [[ $1 =~ ^[a-z][a-z0-9_-]{0,31}$ ]] || fail "build name '$1' must match [a-z][a-z0-9_-]{0,31}: it is the thread's herdr agent name"; }
herdr_json() {
  # herdr_json <herdr args...>: herdr's JSON reply on stdout; on failure, "<code>: <message>" on stderr and exit 1.
  local out
  if out=$(herdr "$@" 2>&1); then printf '%s' "$out"; return 0; fi
  printf '%s' "$out" | jq -r '"\(.error.code): \(.error.message)"' >&2 2>/dev/null || printf '%s\n' "$out" >&2
  return 1
}
# agent_pane <name>: the pane hosting the live agent with that name, or nothing when there is none.
agent_pane() { { herdr agent get "$1" 2>/dev/null || true; } | jq -r '.result.agent.pane_id // empty'; }
home_env() {
  # The build's workspace doesn't inherit this shell's environment, so a non-default home is passed on.
  [ -z "${ORCHESTRATION_HOME:-}" ] || printf '%s\n' --env "ORCHESTRATION_HOME=$ORCHESTRATION_HOME"
}
new_pane() {
  # new_pane <build> <worktree> <workspace or empty>: a fresh shell pane for the thread, in a new tab of the build's
  # workspace, or in a new workspace when there is none; prints "<pane> <workspace>".
  local out
  local -a env; mapfile -t env < <(home_env)
  if [ -n "$3" ] && out=$(herdr_json tab create --workspace "$3" --cwd "$2" --label "$1" --no-focus "${env[@]}" 2>/dev/null); then
    printf '%s %s\n' "$(jq -r '.result.root_pane.pane_id' <<<"$out")" "$3"; return 0
  fi
  out=$(herdr_json workspace create --cwd "$2" --label "$1" --no-focus "${env[@]}") || return 1
  jq -r '"\(.result.root_pane.pane_id) \(.result.workspace.workspace_id)"' <<<"$out"
}
start_thread() {
  # start_thread <build> <pane> <brief file>: start the orchestrator agent on a one-line prompt naming the brief, since
  # herdr refuses agent arguments it can't encode for the shell (a multi-line brief among them); prints nothing when
  # it is ready, a reason for the owner when it waits on a startup prompt (a folder trust question), or fails with
  # herdr's reason.
  local err
  if err=$(herdr_json agent start "$1" --kind claude --pane "$2" --timeout 120000 -- --agent orchestrator "Read $3 and follow it." 2>&1 >/dev/null); then
    return 0
  fi
  case $err in
    agent_not_ready:*) echo "waiting on a startup prompt: answer it in workspace $1" ;;
    *) echo "$err" >&2; return 1 ;;
  esac
}
identity_warnings() {
  # identity_warnings <repo>: an IDENTITY line for each of user.name and user.email that the repository's local
  # config (the common .git/config, shared by its linked worktrees) sets apart from the global value. A copied
  # worktree's git config once wrote a test identity there, and commits on main took it.
  local key mine global
  for key in user.name user.email; do
    mine=$(git -C "$1" config --local --get "$key" 2>/dev/null || true)
    global=$(git config --global --get "$key" 2>/dev/null || true)
    [ -n "$mine" ] && [ "$mine" != "$global" ] || continue
    echo "IDENTITY $1 $key=$mine (global ${global:-none}): a local git identity; remove it with git -C $1 config --unset $key unless the owner set it"
  done
}
# brief_text <build> <state> <body>: the header lines, a blank line, then the body. One printf, because a command
# substitution would strip the blank line that separates them.
brief_text() { printf 'BUILD: %s\nMAIL: %s/thread is yours; send MAIN %s/main\nSTATE: %s\n\n%s' "$1" "$1" "$1" "$2" "$3"; }
write_record() {
  # write_record <worktree> <build> <checkout> <base> <base ref> <lane base> <landing>
  local file="$1/.orchestration/thread.md"
  mkdir -p "$1/.orchestration"
  printf '%s\n' "# Thread record, written by MAIN's thread.sh launch. The thread reads it and never edits it." \
    "BUILD: $2" "CHECKOUT: $3" "BASE: $4" "BASE-REF: $5" "LANE-BASE: $6" "LANDING: $7" "UPDATED: $(utc_now)" > "$file.tmp"
  mv -f "$file.tmp" "$file"
}
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
    its_top=$(toplevel "$wt" || true)
    if [ -n "$its_common" ] && [ -n "$its_top" ] && [ "$(canon "$its_common")" = "$common" ] \
      && [ "$its_top" = "$wt" ] && [ "$(git -C "$wt" rev-parse --abbrev-ref HEAD)" = "$branch" ]; then
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

cmd=${1:-}; [ $# -gt 0 ] && shift
case "$cmd" in
  launch)
    [ $# -ge 3 ] || usage
    build=$1; repo=$2; brief=$3; shift 3
    base=""; want=""
    while [ $# -gt 0 ]; do
      case $1 in
        --base) need_value "$1" $#; base=$2; shift 2 ;;
        --landing) need_value "$1" $#; want=$2; shift 2 ;;
        *) usage ;;
      esac
    done
    valid_name "$build"
    [ -d "$repo" ] || fail "no repository checkout at $repo"
    [ -s "$brief" ] || fail "no brief at $brief"
    common=$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir 2>/dev/null) || fail "$repo is not a git checkout"
    common=$(canon "$common")
    checkout=$(toplevel "$repo")
    # The main checkout holds the common git dir, so a linked worktree passed here still names the main one.
    main=$(dirname "$common")
    wt="$(dirname "$main")/$(basename "$main")-orch-$build"
    if [ -z "$base" ]; then
      base=$(git -C "$repo" symbolic-ref --quiet --short HEAD 2>/dev/null) || fail "$repo is on a detached HEAD; pass --base <branch>"
    fi
    ensure_registry
    [ -z "$(row_by 1 "$build")" ] || fail "a thread for build $build is already registered; stop or close it, or pick another build name"
    [ -z "$(agent_pane "$build")" ] || fail "a live herdr agent is already named $build; pick another build name"
    pick_base "$main" "$base" "$want"
    ensure_worktree "$main" "$common" "$wt" "$build" "$base_ref"
    mkdir -p "$common/info"
    grep -qxF '.orchestration/' "$common/info/exclude" 2>/dev/null || printf '.orchestration/\n' >> "$common/info/exclude"
    if [ "$landing" = pr ]; then lane_base=$base_ref; else lane_base="orchestration/$build"; fi
    write_record "$wt" "$build" "$checkout" "$base" "$base_ref" "$lane_base" "$landing"
    read -r pane ws < <(new_pane "$build" "$wt" "" 2>"$reg.err") || { reason=$(cat "$reg.err"); rm -f "$reg.err"; fail "herdr workspace create: $reason"; }
    rm -f "$reg.err"
    # The row exists before the agent starts, so a thread waiting on a startup prompt is still known by name.
    put_row "$build" "$(row "$build" "$main" "$wt" "$ws" "$(utc_now)")"
    brief_text "$build" "$wt/.orchestration/state.md" "$(cat "$brief")" > "$wt/.orchestration/launch-brief.md"
    if ! waiting=$(start_thread "$build" "$pane" "$wt/.orchestration/launch-brief.md" 2>"$reg.err"); then
      reason=$(cat "$reg.err"); rm -f "$reg.err"
      delete_row "$build"; herdr workspace close "$ws" >/dev/null 2>&1 || true
      fail "herdr agent start: $reason"
    fi
    rm -f "$reg.err"
    [ -z "$waiting" ] || { echo "BLOCKED $build $waiting"; exit 0; }
    echo "LAUNCHED $build base=$base@$(git -C "$main" rev-parse --short "$base_ref") landing=$landing" ;;
  stop)
    [ $# -eq 1 ] || usage
    [ -n "$(row_by 1 "$1")" ] || fail "no thread for build $1 in $reg"
    pane=$(agent_pane "$1")
    [ -z "$pane" ] || herdr_json pane close "$pane" >/dev/null 2>"$reg.err" || { reason=$(cat "$reg.err"); rm -f "$reg.err"; fail "herdr pane close $pane: $reason"; }
    rm -f "$reg.err"
    delete_row "$1"
    echo "STOPPED $1" ;;
  rotate)
    [ $# -ge 1 ] || usage
    build=$1; shift; force=0
    while [ $# -gt 0 ]; do
      case $1 in --force) force=1; shift ;; *) usage ;; esac
    done
    found=$(row_by 1 "$build"); [ -n "$found" ] || fail "no thread for build $build in $reg"
    IFS=$'\t' read -r _ main wt ws _ <<< "$found"
    state="$wt/.orchestration/state.md"
    if [ "$force" = 0 ]; then
      written=$(awk '/^## RESUME/ { r = 1; next } r && /^## / { exit } r && /^Written:/ { sub(/^Written:[ \t]*/, ""); print; exit }' "$state" 2>/dev/null || true)
      [ -n "$written" ] || fail "no RESUME Written: stamp in $state; send ROTATE and wait for 'STATUS: rotating', or pass --force"
      age=$(( ($(date -u +%s) - $(to_epoch "$written")) / 60 ))
      [ "$age" -le "$resume_max_age_minutes" ] \
        || fail "RESUME in $state was written $age min ago (limit $resume_max_age_minutes); send ROTATE and wait for 'STATUS: rotating', or pass --force"
    fi
    old=$(agent_pane "$build")
    # The new pane opens first, so closing the old one never leaves the build's workspace empty.
    read -r pane ws < <(new_pane "$build" "$wt" "$ws" 2>"$reg.err") || { reason=$(cat "$reg.err"); rm -f "$reg.err"; fail "no pane for the new thread: $reason"; }
    rm -f "$reg.err"
    if [ -n "$old" ]; then
      herdr pane close "$old" >/dev/null 2>&1 || true
      [ -z "$(agent_pane "$build")" ] || { herdr pane close "$pane" >/dev/null 2>&1 || true; fail "the old thread still runs in $old, so nothing was started; close it, then rotate again"; }
    fi
    put_row "$build" "$(row "$build" "$main" "$wt" "$ws" "$(utc_now)")"
    brief_text "$build" "$state" "Resume: read STATE first and continue from its RESUME section without redoing finished work." \
      > "$wt/.orchestration/rotate-brief.md"
    if ! waiting=$(start_thread "$build" "$pane" "$wt/.orchestration/rotate-brief.md" 2>"$reg.err"); then
      reason=$(cat "$reg.err"); rm -f "$reg.err"; herdr pane close "$pane" >/dev/null 2>&1 || true
      fail "the new thread did not start: $reason; ${old:+the old one was closed; }run thread.sh rotate $build --force"
    fi
    rm -f "$reg.err"
    [ -z "$waiting" ] || { echo "BLOCKED $build $waiting"; exit 0; }
    echo "ROTATED $build" ;;
  check)
    all=0
    if [ "${1:-}" = --all ]; then all=1; shift; fi
    [ $# -eq 0 ] || usage
    rows=$(awk 'NR > 1' "$reg" 2>/dev/null || true)
    [ -n "$rows" ] || { echo NONE; exit 0; }
    # Only this repository's threads, unless --all or outside git: other main sessions own the rest.
    here=""
    if [ "$all" = 0 ] && c=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null); then here=$(dirname "$(canon "$c")"); fi
    printed=0
    while IFS= read -r repo; do
      [ -n "$repo" ] || continue
      out=$(identity_warnings "$repo")
      if [ -n "$out" ]; then printf '%s\n' "$out"; printed=1; fi
    done < <(printf '%s\n' "$rows" | cut -f2 | awk -v h="$here" 'h == "" || $0 == h' | sort -u)
    [ "$printed" = 1 ] || echo OK ;;
  integrate)
    [ $# -eq 1 ] || usage
    found=$(row_by 1 "$1"); [ -n "$found" ] || fail "no thread for build $1 in $reg"
    IFS=$'\t' read -r build repo wt _ _ <<< "$found"
    landing=$(thread_field "$wt" LANDING); base=$(thread_field "$wt" BASE); checkout=$(thread_field "$wt" CHECKOUT)
    [ "$landing" = local ] || fail "$1 lands by pull request (LANDING: ${landing:-unknown}), so its base moves on origin; pull it instead"
    [ -n "$base" ] && [ -d "$checkout" ] || fail "no BASE or CHECKOUT in $wt/.orchestration/thread.md"
    [ "$(canon "$(git -C "$checkout" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)")" \
      = "$(canon "$(git -C "$repo" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)")" ] \
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
  close)
    name=""; wt=""; base=""; force=0
    while [ $# -gt 0 ]; do
      case $1 in
        --worktree) need_value "$1" $#; wt=$2; shift 2 ;;
        --base) need_value "$1" $#; base=$2; shift 2 ;;
        --force) force=1; shift ;;
        -*) usage ;;
        *) [ -z "$name" ] || usage; name=$1; shift ;;
      esac
    done
    [ -n "$name" ] || [ -n "$wt" ] || usage
    ws=""
    if [ -n "$name" ]; then
      found=$(row_by 1 "$name"); [ -n "$found" ] || fail "no thread for build $name in $reg; for a build the registry no longer lists, pass --worktree <coordination worktree>"
      IFS=$'\t' read -r _ _ wt ws _ <<< "$found"
    fi
    wt=$(canon "$wt")
    [ -d "$wt" ] || fail "no coordination worktree at $wt"
    branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null) || fail "$wt has a detached HEAD; it is not a coordination worktree"
    [[ $branch == orchestration/* ]] || fail "$wt is on $branch, not orchestration/<build>; it is not a coordination worktree"
    build=${branch#orchestration/}
    repo=$(dirname "$(canon "$(git -C "$wt" rev-parse --path-format=absolute --git-common-dir)")")
    [ "$wt" = "$(dirname "$repo")/$(basename "$repo")-orch-$build" ] || fail "$wt is not $(basename "$repo")-orch-$build beside $repo"
    [ -n "$base" ] || base=$(thread_field "$wt" BASE)
    landing=$(thread_field "$wt" LANDING)
    if [ "$force" = 0 ]; then
      [ -z "$(git -C "$wt" status --porcelain --untracked-files=no)" ] || fail "$wt has uncommitted changes to tracked files; land them, or pass --force"
      [ -n "$base" ] || fail "no record of $wt's base; pass --base <branch>, or --force"
      ref="refs/heads/$base"
      if [ "$landing" = pr ] || ! git -C "$repo" rev-parse --verify -q "$ref" >/dev/null; then
        git -C "$repo" fetch -q origin 2>/dev/null || true; ref="refs/remotes/origin/$base"
      fi
      git -C "$repo" rev-parse --verify -q "$ref" >/dev/null || fail "no branch $base to compare $branch with; pass --base <branch>, or --force"
      # Landed means an ancestor of the base, or, after a squash merge, every file the branch changed as it is on the base.
      if ! git -C "$repo" merge-base --is-ancestor "$branch" "$ref"; then
        fork=$(git -C "$repo" merge-base "$branch" "$ref"); unlanded=""
        while IFS= read -r -d '' f; do
          [ "$(git -C "$repo" rev-parse -q --verify "$branch:$f" || echo none)" = "$(git -C "$repo" rev-parse -q --verify "$ref:$f" || echo none)" ] \
            || unlanded+="$f "
        done < <(git -C "$repo" diff -z --name-only "$fork" "$branch")
        [ -z "$unlanded" ] || fail "$branch holds work that ${ref#refs/*/} lacks in: $unlanded(integrate or land it, or pass --force)"
      fi
    fi
    [ -n "$ws" ] || ws=$( { herdr agent get "$build" 2>/dev/null || true; } | jq -r '.result.agent.workspace_id // empty')
    # Closing the workspace ends the thread and any lane still in it, so none sends mail after the archive.
    [ -z "$ws" ] || herdr workspace close "$ws" >/dev/null 2>&1 || true
    pane=$(agent_pane "$build")
    [ -z "$pane" ] || herdr pane close "$pane" >/dev/null 2>&1 || true
    archive="$home/archive/$build-$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p "$archive"
    [ ! -d "$wt/.orchestration" ] || cp -a "$wt/.orchestration/." "$archive/"
    [ ! -d "$home/mail/$build" ] || mv "$home/mail/$build" "$archive/mail"
    # The forced removal deletes what git ignores (eval runs, agent memory), so archive it first. stdout carries
    # only the CLOSED or FAILED line, so the per-file lines and git's own diagnostics are dropped.
    reason=$(archive_ignored "$wt" "$archive" .orchestration 2>&1 >/dev/null) || fail "${reason##*$'\n'} (archive at $archive)"
    git -C "$repo" worktree remove --force "$wt" || fail "git worktree remove $wt failed; the archive is at $archive"
    git -C "$repo" branch -D "$branch" >/dev/null 2>&1 || true
    [ -z "$name" ] || delete_row "$name"
    # git lists worktrees in its own path form, so each is matched in canon form.
    lanes=$(git -C "$repo" worktree list --porcelain | sed -n 's/^worktree //p' | while IFS= read -r p; do canon "$p"; done \
      | sed -n "s#^\($(dirname "$repo")/$(basename "$repo")-wt-[^/]*\)\$#\1#p" | tr '\n' ' ')
    echo "CLOSED $build archive=$archive${lanes:+ lanes still present: $lanes}" ;;
  list)
    [ $# -eq 0 ] || usage
    rows=$(awk 'NR > 1' "$reg" 2>/dev/null || true)
    [ -n "$rows" ] || { echo NONE; exit 0; }
    agents=$(herdr agent list 2>/dev/null || true)
    while IFS=$'\t' read -r build _ wt ws launched; do
      status=unknown
      [ -z "$agents" ] || status=$(jq -r --arg b "$build" '[.result.agents[] | select(.name == $b)][0].agent_status // "not-running"' <<<"$agents")
      echo "$build status=$status workspace=$ws worktree=$wt launched=$launched"
    done <<< "$rows"
    ;;
  decisions)
    [ $# -eq 0 ] || usage
    rows=$(awk 'NR > 1' "$reg" 2>/dev/null || true)
    items=""
    while IFS=$'\t' read -r name _ wt _ _; do
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
