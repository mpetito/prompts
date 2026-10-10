#!/usr/bin/env bash
# Offline checks for the orchestration scripts and hooks, including orchestration-main's thread.sh. Uses a
# throwaway directory with mocked claude, gh and codex on PATH and real git repositories; needs bash 5, jq,
# python3, git 2.31+ and GNU coreutils.
# No pipefail: each assertion pipes a command that may exit 1 by design into grep, and judges grep.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
thread="$(cd "$here/../orchestration-main/scripts" && pwd)/thread.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
export HOME="$tmp/home" ORCHESTRATION_HOME="$tmp/orch" MOCK_DIR="$tmp/mock"
unset ORCHESTRATION_STATE ORCHESTRATION_DECISIONS HERDR_ENV CLAUDE_CODE_MESSAGING_SOCKET
mkdir -p "$HOME" "$MOCK_DIR" "$tmp/bin"
export PATH="$tmp/bin:$PATH"
utc='[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z'

# --- mocks -------------------------------------------------------------------------------------------------
cat > "$tmp/bin/claude" <<'MOCK'
#!/usr/bin/env bash
echo "$PWD :: $*" >> "$MOCK_DIR/claude.log"
[ -z "${CLAUDECODE:-}" ] || echo "CLAUDECODE leaked" >> "$MOCK_DIR/claude.log"
case "$1" in
  stop) [ "${MOCK_CLAUDE:-}" = fail-stop ] && { echo "no session $2" >&2; exit 1; }; echo "stopped $2"; exit 0 ;;
  agents) cat "$MOCK_DIR/agents.json" 2>/dev/null || echo '[]'; exit 0 ;;
esac
case "${MOCK_CLAUDE:-}" in
  untrusted) echo "Error: Workspace not trusted. Open this folder in claude once to trust it." >&2; exit 1 ;;
  noagent) echo "warning: no agent named orchestrator"; echo "backgrounded · deadbeef · x"; exit 0 ;;
esac
name=""; brief=""
while [ $# -gt 0 ]; do
  case $1 in --agent) shift 2 ;; --bg) shift ;; --name) name=$2; shift 2 ;; *) brief=$1; shift ;; esac
done
printf '%s' "$brief" > "$MOCK_DIR/brief-$name.txt"
id=$(printf '%s' "$name" | md5sum | cut -c1-8)
echo "Starting background service…"; echo "backgrounded · $id · $name"; echo "  claude stop $id      stop this session"
MOCK
cat > "$tmp/bin/gh" <<'MOCK'
#!/usr/bin/env bash
echo "$*" >> "$MOCK_DIR/gh.log"
head=$(git -C "$MOCK_WT" rev-parse HEAD 2>/dev/null || echo none)
case "$1 $2" in
  "repo view") echo "o/r" ;;
  "pr view")
    if [[ $* == *headRefOid,mergeStateStatus* ]]; then echo "$head ${MOCK_MERGE_STATE:-CLEAN}"
    elif [[ $* == *mergeStateStatus,reviewDecision* ]]; then echo "mergeState=${MOCK_MERGE_STATE:-CLEAN} review=APPROVED"
    else cat "$MOCK_DIR/pr-head" 2>/dev/null || echo "$head"; fi ;;
  "pr merge") [ "${MOCK_MERGE_FAIL:-}" = 1 ] && exit 1; echo merged ;;
  "pr comment") echo commented ;;
  "api graphql") if [[ $* == *unresolved_threads=* ]]; then echo unresolved_threads=0; else echo 0; fi ;;
  *)
    if [[ $2 == */check-runs && $* == *'length==0'* ]]; then echo "${MOCK_CHECK:-success}"
    elif [[ $2 == */reviews ]]; then echo "${MOCK_BOT_REVIEWS:-1}"
    fi ;;
esac
MOCK
cat > "$tmp/bin/codex" <<'MOCK'
#!/usr/bin/env bash
case ${MOCK_CODEX:-ok} in
  ok) [ -n "${MOCK_CODEX_ARGS:-}" ] && printf '%s\n' "cwd=$PWD" "$@" > "$MOCK_CODEX_ARGS"
      while [ $# -gt 0 ]; do [ "$1" = --output-last-message ] && echo done > "$2"; shift; done ;;
  fail) exit 3 ;;
  slow) sleep 5 ;;
esac
MOCK
chmod +x "$tmp/bin/"*

# --- check-message.sh --------------------------------------------------------------------------------------
cm() { printf '%s' "$2" | "$here/scripts/check-message.sh" "$1"; }
[ "$(cm --up 'STATUS: working - lane A started')" = OK ] || fail "check-message rejected a plain status"
cm --up 'Lane A started' | grep -q '^BAD first line' || fail "check-message accepted a message without STATUS"
cm --up 'STATUS: thinking - hmm' | grep -q '^BAD' || fail "check-message accepted an unknown state"
cm --up 'STATUS: working – en dash' | grep -q '^BAD' || fail "check-message accepted an en dash separator"
cm --up "$(printf 'STATUS: done - x\n%.0s' 1 2 3 4 5 6 7 8 9 10 11)" | grep -q '^BAD 11 lines' || fail "check-message accepted 11 lines"
[ "$(cm --up "$(printf 'STATUS: done - x\n\n\n')")" = OK ] || fail "check-message counted trailing blank lines"
cm --up 'STATUS: need-decision - drink?
Default: tea
applies at 2026-10-10T03:45Z' | grep -q 'without an Options' || fail "check-message accepted a decision without Options"
cm --up 'STATUS: need-decision - drink?
Options: tea | coffee
applies at 2026-10-10T03:45Z' | grep -q 'without a Default' || fail "check-message accepted a decision without Default"
cm --up 'STATUS: need-decision - drink?
Options: tea | coffee
Default: tea' | grep -q "applies at" || fail "check-message accepted a decision without a deadline"
[ "$(cm --up 'STATUS: need-decision - drink?
Options: tea | coffee
Default: tea, applies at 2026-10-10T03:45:10Z')" = OK ] || fail "check-message rejected a deadline with seconds"
[ "$(cm --up 'STATUS: need-decision - spend $40?
Options: yes | no
Default: none, owner-before')" = OK ] || fail "check-message rejected an owner-before decision"
for good in 'STEER: ship signup first' 'DECISION D3: coffee' 'ROTATE' 'ROTATE: write RESUME' 'QUESTION: is lane B blocked?'; do
  [ "$(cm --down "$good")" = OK ] || fail "check-message --down rejected: $good"
done
cm --down 'Please rotate now' | grep -q '^BAD' || fail "check-message --down accepted a free-form message"
cm --up '' | grep -q '^BAD empty' || fail "check-message accepted an empty message"
set +e; printf x | "$here/scripts/check-message.sh" --sideways >/dev/null 2>&1; [ $? -eq 2 ] || fail "check-message accepted an unknown flag"; set -e

# --- state.sh and decisions.sh: resolution from the git worktree ---------------------------------------------
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
mkdir -p "$tmp/plain" "$tmp/coord/sub"
git init -q "$tmp/coord"
coord=$(realpath "$tmp/coord")
out=$(cd "$tmp/plain" && "$here/scripts/state.sh" log x 2>&1) && fail "state.sh worked outside a git worktree"
printf '%s' "$out" | grep -q 'not inside a git worktree.*set ORCHESTRATION_STATE' || fail "state.sh outside git did not name ORCHESTRATION_STATE: $out"
out=$(cd "$tmp/plain" && "$here/scripts/decisions.sh" list 2>&1) && fail "decisions.sh worked outside a git worktree"
printf '%s' "$out" | grep -q 'set ORCHESTRATION_DECISIONS' || fail "decisions.sh outside git did not name ORCHESTRATION_DECISIONS: $out"
out=$(cd "$coord" && "$here/scripts/state.sh" log x 2>&1) && fail "state.sh logged to a missing state file"
printf '%s' "$out" | grep -q "no state file at $coord/.orchestration/state.md" || fail "state.sh did not resolve the worktree root: $out"
"$here/scripts/state.sh" now | grep -Eq "^$utc$" || fail "state.sh now printed the wrong format"

# --- state.sh: init, main, log, resume ----------------------------------------------------------------------
cd "$coord/sub"
"$here/scripts/state.sh" init b1 | grep -Eq "^initialised $coord/.orchestration/state.md $utc$" || fail "state.sh init did not use the worktree root"
s1="$coord/.orchestration/state.md"
[ -d "$coord/.orchestration/briefs" ] && [ -d "$coord/.orchestration/results" ] || fail "state.sh init did not create briefs/ and results/"
[ "$(grep '^#' "$s1" | tr '\n' '|')" = "# Orchestration thread: b1|## Thread|## RESUME|## Lanes|## Decisions|## Log|" ] || fail "state.sh init sections are out of order"
grep -q '^Record: thread.md' "$s1" && grep -Eq "^Started: $utc$" "$s1" && grep -Eq "^Written: $utc$" "$s1" || fail "state.sh init skeleton lines missing"
grep -q '^MAIN:' "$s1" && fail "state.sh init wrote a MAIN line; the thread record is its one home"
"$here/scripts/state.sh" init b1 >/dev/null 2>&1 && fail "state.sh init overwrote an existing file"
"$here/scripts/state.sh" init b1 prompts-9d >/dev/null 2>&1 && fail "state.sh init accepted the old MAIN argument"
"$here/scripts/state.sh" main >/dev/null 2>&1 && fail "state.sh main printed a name with no thread record"
printf '%s\n' '# record' 'MAIN: Main session one' 'MAIN-SOCKET: uds:/tmp/main-1.sock' 'CHECKOUT: /x' 'BASE: dev' 'LANE-BASE: orchestration/b1' 'LANDING: local' > "$coord/.orchestration/thread.md"
[ "$("$here/scripts/state.sh" main)" = 'Main session one' ] || fail "state.sh main did not read MAIN from the thread record"
[ "$("$here/scripts/state.sh" main --socket)" = uds:/tmp/main-1.sock ] || fail "state.sh main --socket did not read MAIN-SOCKET"
[ "$("$here/scripts/state.sh" thread LANE-BASE)" = orchestration/b1 ] || fail "state.sh thread did not read a record field"
"$here/scripts/state.sh" thread NOPE >/dev/null 2>&1 && fail "state.sh thread printed a missing field"
"$here/scripts/state.sh" main --bogus >/dev/null 2>&1 && fail "state.sh main accepted an unknown option"
"$here/scripts/state.sh" log "lane A launched" | grep -Eq "^logged $utc$" || fail "state.sh log printed the wrong line"
tail -1 "$s1" | grep -Eq "^- $utc lane A launched$" || fail "state.sh log did not append to the Log section"
printf 'Lanes A, B done.\nWritten: 1999-01-01T00:00Z\nNext: lane C.\n' | "$here/scripts/state.sh" resume - | grep -q '^resume written' || fail "state.sh resume printed the wrong line"
sed -n '/^## RESUME/,/^## Lanes/p' "$s1" | grep -Eq "^Written: $utc$" || fail "state.sh resume did not stamp Written"
[ "$(grep -c '^Written:' "$s1")" = 1 ] || fail "state.sh resume left a copied Written line"
sed -n '/^## RESUME/,/^## Lanes/p' "$s1" | sed -n 3p | grep -q '^Written:' || fail "Written is not the first line of the RESUME body"
grep -q '^Next: lane C.$' "$s1" && ! grep -q '(nothing yet)' "$s1" || fail "state.sh resume did not replace the body"
grep -q '^## Lanes$' "$s1" && grep -q '^## Log$' "$s1" || fail "state.sh resume damaged later sections"
ls "$coord"/.orchestration/state.*.md >/dev/null 2>&1 || fail "state.sh resume took no backup"
printf '   \n' | "$here/scripts/state.sh" resume - >/dev/null 2>&1 && fail "state.sh resume accepted an empty body"
"$here/scripts/decisions.sh" add "Tea or coffee" "lane B" "lane B" "tea" +2h >/dev/null
[ -f "$coord/.orchestration/decisions.md" ] || fail "decisions.sh did not put decisions.md beside the state file"
cd "$tmp"

# A state file written before thread records existed still names MAIN.
mkdir -p "$tmp/oldstate/.orchestration"; printf '## Thread\n\nMAIN: old-main\n' > "$tmp/oldstate/.orchestration/state.md"
[ "$(ORCHESTRATION_STATE="$tmp/oldstate/.orchestration/state.md" "$here/scripts/state.sh" main)" = old-main ] || fail "state.sh main ignored a legacy MAIN line"

# --- state.sh with an explicit file (the original assertions) ------------------------------------------------
mkdir -p legacy
cat > legacy/state.md <<'STATE'
# Orchestrator state: test

## Lanes

| Lane | Agent | PR | Head SHA | Next action |
| --- | --- | --- | --- | --- |
| alpha | codex | #1 | abc1234 | review |
| beta | opus | #2 | def5678 | land |

## Log

- 2026-10-01T00:00Z started

## Notes

kept below the log
STATE
export ORCHESTRATION_STATE="$tmp/legacy/state.md"
"$here/scripts/state.sh" log "merged #2" >/dev/null
sed -n '/^## Log/,/^## Notes/p' legacy/state.md | grep -Eq "^- $utc merged #2$" || fail "state.sh log did not append a stamped line"
[ "$(sed -n '/^## Log/,/^## Notes/p' legacy/state.md | grep -c '^$')" = 2 ] || fail "state.sh log broke the blank lines around the Log section"
tail -1 legacy/state.md | grep -q 'kept below the log' || fail "state.sh log wrote past a later section"
"$here/scripts/state.sh" set beta "Head SHA" 9999999 >/dev/null
grep -q '^| beta | opus | #2 | 9999999 | land |$' legacy/state.md || fail "state.sh set did not replace the cell"
grep -q '^| alpha | codex | #1 | abc1234 | review |$' legacy/state.md || fail "state.sh set touched another row"
"$here/scripts/state.sh" set gamma "Head SHA" 1 >/dev/null 2>&1 && fail "state.sh set accepted an unknown lane"
"$here/scripts/state.sh" set beta Nope 1 >/dev/null 2>&1 && fail "state.sh set accepted an unknown column"
"$here/scripts/state.sh" backup >/dev/null
ls legacy/state.*.md >/dev/null || fail "state.sh backup wrote nothing"
"$here/scripts/state.sh" log >/dev/null 2>&1 && fail "state.sh log accepted no event"
unset ORCHESTRATION_STATE

# --- decisions.sh ------------------------------------------------------------------------------------------
export ORCHESTRATION_DECISIONS="$tmp/legacy/decisions.md"
"$here/scripts/decisions.sh" add "Ship the banner" "blocks the demo" "lane w3" "ship it" +0m | grep -Eq "^D1 applies at $utc$" || fail "decisions.sh add printed the wrong line"
"$here/scripts/decisions.sh" add "Rename the table" "nothing" "none" "keep the name" +48h >/dev/null
"$here/scripts/decisions.sh" add "Spend 40 USD" "quota" "lane w4" "none" owner-before | grep -q '^D3 owner-before' || fail "decisions.sh add mishandled owner-before"
[ "$("$here/scripts/decisions.sh" list | wc -l)" = 3 ] || fail "decisions.sh list should show three items"
"$here/scripts/decisions.sh" due | grep -q '^- D1 ' || fail "decisions.sh due should include the expired item"
"$here/scripts/decisions.sh" due | grep -q '^- D2 ' && fail "decisions.sh due included a future item"
"$here/scripts/decisions.sh" due | grep -q '^- D3 ' && fail "decisions.sh due included an owner-before item"
"$here/scripts/decisions.sh" close D1 "default applied" >/dev/null
[ "$("$here/scripts/decisions.sh" list | wc -l)" = 2 ] || fail "decisions.sh close left the item open"
grep -q '^- D1 .*closed .*default applied$' legacy/decisions.md || fail "decisions.sh close did not record the outcome"
"$here/scripts/decisions.sh" close D1 again >/dev/null 2>&1 && fail "decisions.sh closed an item twice"
"$here/scripts/decisions.sh" add a b c d tomorrow >/dev/null 2>&1 && fail "decisions.sh accepted a bad deadline"
unset ORCHESTRATION_DECISIONS

# --- wake-at.sh ----------------------------------------------------------------------------------------------
"$here/scripts/wake-at.sh" +0m lane-b | grep -Eq "^WAKE lane-b $utc \(armed for $utc\)$" || fail "wake-at.sh printed the wrong line"
"$here/scripts/wake-at.sh" 2000-01-01T00:00Z | grep -q '^WAKE timer ' || fail "wake-at.sh did not wake at once for a past time"
"$here/scripts/wake-at.sh" soon >/dev/null 2>&1 && fail "wake-at.sh accepted a bad time"

# --- meter.sh ------------------------------------------------------------------------------------------------
export CODEX_SESSIONS="$tmp/sessions"; mkdir -p "$CODEX_SESSIONS"
"$here/scripts/meter.sh" | grep -q '^codex=unknown .*verdict=unknown' || fail "meter.sh without logs should print unknown"
meter_log() { printf '{"payload":{"rate_limits":{"primary":{"used_percent":%s,"resets_at":1791600000}}}}\n' "$1" > "$CODEX_SESSIONS/s.jsonl"; }
meter_log 50; "$here/scripts/meter.sh" | grep -q 'verdict=normal' || fail "meter.sh 50% should be normal"
meter_log 75; [ "$("$here/scripts/meter.sh" | grep -c 'verdict=rotate\|^rule: ask MAIN to rotate')" = 2 ] || fail "meter.sh 75% should be rotate with its rule"
meter_log 100; "$here/scripts/meter.sh" | grep -q 'verdict=stop' || fail "meter.sh 100% should be stop"
printf '{"payload":{"rate_limits":{"secondary":{"used_percent":5}}}}\n' > "$CODEX_SESSIONS/s.jsonl"
"$here/scripts/meter.sh" | grep -q '^codex=unknown .*no primary meter' || fail "meter.sh without a primary meter should print unknown"
"$here/scripts/meter.sh" --switch abc >/dev/null 2>&1 && fail "meter.sh accepted a bad switch"

# --- git fixtures for land.sh, watch-gates.sh and finish-lane.sh -------------------------------------------------
git init -q --bare -b main "$tmp/origin.git"
git clone -q "$tmp/origin.git" "$tmp/seed" 2>/dev/null
(cd "$tmp/seed" && printf 'one\n' > f.txt && printf 'base\n' > g.txt && git add . && git commit -qm init && git push -q origin main)
git clone -q "$tmp/origin.git" "$tmp/wt"
(cd "$tmp/wt" && git checkout -qb feat && printf 'one\nfeat\n' > f.txt && git commit -qam feat && git push -q origin feat)
export MOCK_WT="$tmp/wt" LAND_POLL_SECONDS=0 WATCH_POLL_SECONDS=0
printf 'body\n' > "$tmp/body.md"
land() { "$here/scripts/land.sh" 7 "$tmp/wt" --check ci --subject "feat: x" --body-file "$tmp/body.md" 2>/dev/null; }

# --- land.sh -------------------------------------------------------------------------------------------------
"$here/scripts/land.sh" >/dev/null 2>&1 && fail "land.sh ran without arguments"
"$here/scripts/land.sh" 7 "$tmp/wt" --check >/dev/null 2>&1 && fail "land.sh accepted an option without its value"
land | grep -Eq '^LANDED pr=7 head=[0-9a-f]{7}$' || fail "land.sh did not land a clean PR"
MOCK_MERGE_FAIL=1 land | grep -q '^STOPPED pr=7 merge failed' || fail "land.sh did not stop on a failed merge"
MOCK_CHECK=failure land | grep -q '^STOPPED pr=7 ci=failure' || fail "land.sh did not stop on a failed check"
(cd "$tmp/seed" && printf 'base\nmore\n' > g.txt && git commit -qam base2 && git push -q origin main)
: > "$MOCK_DIR/gh.log"
land | grep -q '^LANDED pr=7' || fail "land.sh did not land after a clean base merge"
grep -q '^pr comment 7 ' "$MOCK_DIR/gh.log" || fail "land.sh did not record the carry-over proof"
[ "$(git -C "$tmp/wt" rev-parse HEAD^2)" = "$(git -C "$tmp/seed" rev-parse HEAD)" ] || fail "land.sh merge has the wrong second parent"
(cd "$tmp/seed" && printf 'one\nclash\n' > f.txt && git commit -qam clash && git push -q origin main)
land | grep -q '^STOPPED pr=7 merge of main conflicts in: f.txt' || fail "land.sh did not stop on a conflicting base"

# --- watch-gates.sh --------------------------------------------------------------------------------------------
sha=$(git -C "$tmp/wt" rev-parse HEAD)
"$here/scripts/watch-gates.sh" 7 abc1234 >/dev/null 2>&1 && fail "watch-gates.sh accepted a short SHA"
"$here/scripts/watch-gates.sh" >/dev/null 2>&1 && fail "watch-gates.sh ran without arguments"
"$here/scripts/watch-gates.sh" 7 "$sha" --check ci --bot copilot --minutes 1 | grep -Eq "^GATES pr=7 head=${sha:0:7} check=success bot=reviewed unresolved_threads=0$" \
  || fail "watch-gates.sh did not report passing gates"
printf '%s\n' 0123456789012345678901234567890123456789 > "$MOCK_DIR/pr-head"
"$here/scripts/watch-gates.sh" 7 "$sha" --check ci --minutes 1 | grep -q "^MOVED pr=7 head=${sha:0:7} now=0123456" || fail "watch-gates.sh did not report a moved head"
rm "$MOCK_DIR/pr-head"

# --- codex-exec.sh ---------------------------------------------------------------------------------------------
printf 'brief\n' > "$tmp/brief.md"
"$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" "$tmp/out/r.md" | grep -q '^CODEX done lane=wt ' || fail "codex-exec.sh did not report done"
[ -s "$tmp/out/r.md" ] || fail "codex-exec.sh did not leave the result file"
MOCK_CODEX=fail "$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" "$tmp/out/r.md" | grep -q '^CODEX failed lane=wt exit=3' || fail "codex-exec.sh did not report failure"
MOCK_CODEX=slow "$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" "$tmp/out/r.md" --timeout 1s | grep -q '^CODEX timeout lane=wt after 1s' || fail "codex-exec.sh did not report a timeout"
"$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" >/dev/null 2>&1 && fail "codex-exec.sh ran without a result file"
# A resumed lane keeps the sandbox, the model and the network setting, and runs from inside its worktree.
MOCK_CODEX_ARGS="$tmp/codex-args" "$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" "$tmp/out/r.md" --resume abc123 --model m1 >/dev/null
grep -qx 'resume' "$tmp/codex-args" || fail "codex-exec.sh --resume did not call codex exec resume"
grep -qx 'sandbox_mode="workspace-write"' "$tmp/codex-args" || fail "codex-exec.sh --resume dropped the sandbox"
grep -qx 'm1' "$tmp/codex-args" || fail "codex-exec.sh --resume dropped the model"
grep -qx "cwd=$(realpath "$tmp/wt")" "$tmp/codex-args" || fail "codex-exec.sh --resume did not run inside the worktree"
grep -q 'network_access' "$tmp/codex-args" && fail "codex-exec.sh --resume enabled the network without --network"
MOCK_CODEX_ARGS="$tmp/codex-args" "$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" "$tmp/out/r.md" --resume abc123 --network >/dev/null
grep -qx 'sandbox_workspace_write.network_access=true' "$tmp/codex-args" || fail "codex-exec.sh --resume dropped --network"
MOCK_CODEX_ARGS="$tmp/codex-args" "$here/scripts/codex-exec.sh" "$tmp/wt" "$tmp/brief.md" "$tmp/out/r.md" >/dev/null
grep -qx 'workspace-write' "$tmp/codex-args" && grep -qx 'sandbox_mode="workspace-write"' "$tmp/codex-args" || fail "codex-exec.sh dropped the sandbox on a fresh lane"

# --- finish-lane.sh (no herdr on PATH) -------------------------------------------------------------------------
git -C "$tmp/seed" worktree add -q "$tmp/lane" -b lane-x
mkdir -p "$tmp/lane/.orchestration/tmp"; printf 'evidence\n' > "$tmp/lane/.orchestration/tmp/note.txt"
# Ignored output: eval runs are evidence, node_modules is not.
printf '.eval-runs/\nnode_modules/\n' >> "$(git -C "$tmp/seed" rev-parse --path-format=absolute --git-common-dir)/info/exclude"
mkdir -p "$tmp/lane/.eval-runs/r1" "$tmp/lane/node_modules/x"
printf 'run\n' > "$tmp/lane/.eval-runs/r1/out.md"; printf 'dep\n' > "$tmp/lane/node_modules/x/i.js"
"$here/scripts/finish-lane.sh" >/dev/null 2>&1 && fail "finish-lane.sh ran without arguments"
printf 'dirty\n' >> "$tmp/lane/g.txt"
"$here/scripts/finish-lane.sh" "$tmp/lane" "$tmp/archive" >/dev/null 2>&1 && fail "finish-lane.sh removed a worktree with uncommitted changes"
git -C "$tmp/lane" checkout -q g.txt
out=$("$here/scripts/finish-lane.sh" "$tmp/lane" "$tmp/archive")
[ -f "$tmp/archive/note.txt" ] || fail "finish-lane.sh did not archive the scratch directory"
[ -f "$tmp/archive/ignored/.eval-runs/r1/out.md" ] || fail "finish-lane.sh did not archive the ignored eval runs"
[ -e "$tmp/archive/ignored/node_modules" ] && fail "finish-lane.sh archived node_modules"
printf '%s' "$out" | grep -q 'archived ignored .eval-runs/' || fail "finish-lane.sh did not report the archived eval runs"
[ ! -d "$tmp/lane" ] || fail "finish-lane.sh did not remove the worktree"
printf '%s' "$out" | grep -q 'deleted branch lane-x' || fail "finish-lane.sh did not delete the lane branch"
# When git can't list the ignored files, nothing is archived or removed.
git -C "$tmp/seed" worktree add -q "$tmp/lane3" -b lane-z
idx="$(git -C "$tmp/lane3" rev-parse --absolute-git-dir)/index"; cp "$idx" "$tmp/lane3.index.bak"; printf 'corrupt' > "$idx"
"$here/scripts/finish-lane.sh" "$tmp/lane3" "$tmp/archive3" 2>&1 | grep -q 'git status failed in .*nothing was removed' || fail "finish-lane.sh carried on when git status failed"
[ -d "$tmp/lane3" ] || fail "finish-lane.sh removed a worktree it could not list"
cp "$tmp/lane3.index.bak" "$idx"

# --- guard-bash.sh -------------------------------------------------------------------------------------------
denies() { jq -n --arg c "$1" --argjson bg "${2:-false}" --arg cwd "${3:-$tmp}" '{cwd:$cwd,tool_input:{command:$c,run_in_background:$bg}}' \
  | "$here/hooks/guard-bash.sh" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null; }
denies 'pkill -f vite' || fail "guard-bash should deny pkill -f"
denies 'git worktree remove ../wt --force' || fail "guard-bash should deny git worktree remove"
denies 'git -C /repo worktree remove ../wt' || fail "guard-bash should deny git -C worktree remove"
denies 'rm -rf .orchestration/lanes/m1' || fail "guard-bash should deny deleting lane evidence"
denies 'rm -rf .orchestration/tmp' || fail "guard-bash should deny deleting a lane's scratch"
denies 'rm -rf ../app-orch-b1/.orchestration/results/lane-a.md' || fail "guard-bash should deny deleting results"
denies "rm -r $coord/.orchestration/briefs" || fail "guard-bash should deny deleting the briefs folder"
denies "rm -r $coord/.orchestration/plan.md" && fail "guard-bash denied deleting a non-evidence file"
denies 'kill 1234' && fail "guard-bash denied kill by pid"
denies 'git worktree add ../wt -b x' && fail "guard-bash denied git worktree add"
denies 'echo pkill-safe-name' && fail "guard-bash denied a harmless word"
denies "printf '%s' 'pkill -f vite' | jq -Rs ." && fail "guard-bash denied the words inside a quoted string"
denies 'cd /x && pkill node' || fail "guard-bash should deny pkill after &&"
denies "sh -c 'pkill -f node'" || fail "guard-bash should deny pkill inside sh -c"
denies 'sudo killall node' || fail "guard-bash should deny sudo killall"
denies 'cat > doc.md <<EOF
| hook | refuses `pkill` |
EOF' && fail "guard-bash denied a backtick-quoted mention"
# Foreground waits: the thread gets advice and the call goes ahead; workers (agent_id) are left alone.
bash_note() { jq -n --arg c "$1" --argjson bg "${2:-false}" --arg a "${3:-}" '{cwd:"/tmp",tool_input:{command:$c,run_in_background:$bg}} + (if $a == "" then {} else {agent_id:$a} end)' \
  | "$here/hooks/guard-bash.sh"; }
advised() { jq -e '(.hookSpecificOutput.permissionDecision == null) and (.hookSpecificOutput.additionalContext | test("'"$1"'"))' >/dev/null; }
bash_note 'sleep 45' | advised 'sleeps 45 s in the foreground' || fail "guard-bash should advise on a 45 s foreground sleep"
bash_note 'sleep 2m && date' | advised 'sleeps 120 s' || fail "guard-bash should advise on a minutes-long foreground sleep"
[ -z "$(bash_note 'sleep 45' true)" ] || fail "guard-bash noted a background sleep"
[ -z "$(bash_note 'sleep 5 && curl localhost:3000')" ] || fail "guard-bash noted a short pause"
bash_note 'until [ -f done.txt ]; do sleep 5; done' | advised 'loops on sleep' || fail "guard-bash should advise on a foreground wait loop"
bash_note 'while ! curl -s localhost; do sleep 2; done' | advised 'loops on sleep' || fail "guard-bash should advise on a foreground while loop"
[ -z "$(bash_note 'until [ -f done.txt ]; do sleep 5; done' true)" ] || fail "guard-bash noted a background wait loop"
[ -z "$(bash_note 'while read -r l; do echo "$l"; done < f')" ] || fail "guard-bash noted a loop that does not sleep"
[ -z "$(bash_note 'echo "until it sleeps"')" ] || fail "guard-bash noted the words inside a quoted string"
[ -z "$(bash_note 'sleep 45' false worker-1)" ] || fail "guard-bash advised a worker on a foreground wait"
[ -z "$(bash_note 'until curl -s localhost; do sleep 2; done' false worker-1)" ] || fail "guard-bash advised a worker's wait loop"
bash_note 'pkill -f vite' false worker-1 | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null || fail "guard-bash let a worker pkill"
bash_note 'git worktree remove ../wt' false worker-1 | jq -r '.hookSpecificOutput.permissionDecisionReason' | grep -q 'plain directory' || fail "guard-bash did not point a worker at plain-directory copies"
jq -n '{tool_input:{command:"sleep 45"}}' | "$here/hooks/guard-bash.sh" | advised 'sleeps 45 s' || fail "guard-bash should advise on a foreground sleep when the input has no cwd"

# --- hooks fixture: the owner's checkout, a coordination worktree, a lane worktree, a nested worktree -----------
git init -q -b main "$HOME/gw/app"
gwapp=$(realpath "$HOME/gw/app")
(cd "$gwapp" && printf 'x\n' > a.txt && git add . && git commit -qm init)
printf '.orchestration/\n' >> "$gwapp/.git/info/exclude"
git -C "$gwapp" worktree add -q "$HOME/gw/app-orch-b" -b orchestration/b
git -C "$gwapp" worktree add -q "$HOME/gw/app-wt-lane-a" -b lane-a
git -C "$gwapp" worktree add -q "$gwapp/.claude/worktrees/agent-x" -b agent-x
gwc=$(realpath "$HOME/gw/app-orch-b"); gwl=$(realpath "$HOME/gw/app-wt-lane-a"); gwn="$gwapp/.claude/worktrees/agent-x"
mkdir -p "$gwc/.orchestration" "$gwc/sub"
printf '# state\n' > "$gwc/.orchestration/state.md"
printf '%s\n' '# record' 'MAIN: Main one' "MAIN-SOCKET: uds:$tmp/main-1.sock" "CHECKOUT: $gwapp" > "$gwc/.orchestration/thread.md"
git init -q "$tmp/nostate"
denied() { jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null; }
reason() { jq -r '.hookSpecificOutput.permissionDecisionReason'; }
noted() { jq -e '(.hookSpecificOutput.permissionDecision == null) and (.hookSpecificOutput.additionalContext | test("'"$1"'"))' >/dev/null; }
# with_agent <json>: add agent_id when $AGENT is set, as Claude Code does for a subagent's tool call.
with_agent() { jq --arg a "${AGENT:-}" 'if $a == "" then . else . + {agent_id:$a} end'; }

# --- guard-writes.sh -----------------------------------------------------------------------------------------
writes() { jq -n --arg cwd "$1" --arg p "$2" --arg k "${3:-file_path}" '{cwd:$cwd,tool_input:{($k):$p}}' | with_agent | "$here/hooks/guard-writes.sh"; }
[ -z "$(writes "$gwc" "$gwc/.orchestration/plan.md")" ] || fail "guard-writes noted a write to .orchestration"
[ -z "$(writes "$gwc/sub" "$gwc/src/app.ts")" ] || fail "guard-writes noted a file inside the coordination worktree"
[ -z "$(writes "$gwc/sub" "../notes.md")" ] || fail "guard-writes noted a relative path inside the worktree"
writes "$gwc" "$gwapp/a.txt" | denied || fail "guard-writes allowed the owner's checkout"
writes "$gwc" "$gwapp/new/dir/b.txt" | denied || fail "guard-writes allowed a new folder in the owner's checkout"
writes "$gwc" "../app/a.txt" | denied || fail "guard-writes allowed a relative path into the owner's checkout"
writes "$gwc" "$gwapp/a.txt" | reason | grep -q "owner's checkout, $gwapp" || fail "guard-writes reason did not name the owner's checkout"
# Elsewhere the thread is trusted: a reminder, never a refusal.
writes "$gwc" "$gwl/src/app.ts" | noted 'outside your coordination worktree' || fail "guard-writes should advise, not refuse, a lane worktree"
writes "$gwc" "/etc/hosts" notebook_path | noted 'outside your coordination worktree' || fail "guard-writes should advise on a notebook outside the worktree"
writes "$gwc" "$gwc/../app-orch-b-evil/x" | noted 'outside your coordination worktree' || fail "guard-writes took a sibling with a shared prefix for its worktree"
[ -z "$(AGENT=w1 writes "$gwc" "$gwl/src/app.ts")" ] || fail "guard-writes noted a worker in its lane worktree"
[ -z "$(AGENT=w1 writes "$gwc" "$HOME/notes.md")" ] || fail "guard-writes noted a worker outside the owner's checkout"
AGENT=w1 writes "$gwc" "$gwapp/a.txt" | denied || fail "guard-writes let a worker write the owner's checkout"
AGENT=w1 writes "$gwc" "$gwapp/a.txt" | reason | grep -q 'Make the change in your own lane worktree' || fail "guard-writes gave a worker the thread's reason"
# The session is the folder it started in: a cd into the owner's checkout changes nothing.
CLAUDE_PROJECT_DIR="$gwc" writes "$gwapp" "$gwapp/a.txt" | denied || fail "guard-writes trusted a cwd moved into the owner's checkout"
# An owner working in a linked worktree is protected through the record's CHECKOUT, and the main checkout always.
sed -i "s#^CHECKOUT: .*#CHECKOUT: $gwl#" "$gwc/.orchestration/thread.md"
writes "$gwc" "$gwl/src/app.ts" | denied || fail "guard-writes ignored the record's CHECKOUT"
writes "$gwc" "$gwapp/a.txt" | denied || fail "guard-writes dropped the main checkout when the record named another"
sed -i '/^CHECKOUT:/d' "$gwc/.orchestration/thread.md"
writes "$gwc" "$gwapp/a.txt" | denied || fail "guard-writes did not fall back to the main checkout"
printf 'CHECKOUT: %s\n' "$gwapp" >> "$gwc/.orchestration/thread.md"
[ -z "$(writes "$tmp/plain" "$gwapp/a.txt")" ] || fail "guard-writes noted a write from outside git"
[ -z "$(writes "$tmp/nostate" "$gwapp/a.txt")" ] || fail "guard-writes noted a write from a worktree with no thread files"

# --- guard-message.sh ----------------------------------------------------------------------------------------
msg() { jq -n --arg cwd "$1" --arg to "$2" --arg m "$3" '{cwd:$cwd,tool_input:{to:$to,message:$m}}' | with_agent | "$here/hooks/guard-message.sh"; }
ob="$gwc/.orchestration/outbox.md"
msg "$gwc" "Main one" "lane A is done" | denied || fail "guard-message allowed a malformed message to MAIN"
msg "$gwc/sub" "Main one [25f79e]" "lane A is done" | denied || fail "guard-message ignored a MAIN address with a ref"
msg "$gwc" "Main one" "lane A is done" | reason | grep -q 'first line must be' || fail "guard-message reason did not carry check-message's reason"
[ ! -f "$ob" ] || fail "guard-message copied a refused message to the outbox"
[ -z "$(msg "$gwc" "Main one" "STATUS: done - lane A merged")" ] || fail "guard-message denied a valid message"
grep -Eq "^=== $utc to Main one #[0-9a-f]{12}$" "$ob" && grep -qx 'STATUS: done - lane A merged' "$ob" || fail "guard-message did not copy the message to the outbox"
# The same message resent to the socket after the name failed goes through and is copied once.
[ -z "$(msg "$gwc" "uds:$tmp/main-1.sock" "STATUS: done - lane A merged")" ] || fail "guard-message denied MAIN's socket"
[ "$(grep -c '^=== ' "$ob")" = 1 ] || fail "guard-message copied a resend twice"
[ -z "$(msg "$gwc" "uds:$tmp/main-1.sock" "STATUS: working - lane B started")" ] || fail "guard-message denied a second message"
[ "$(grep -c '^=== ' "$ob")" = 2 ] || fail "guard-message did not copy a new message"
# A status line to any other address is the stale-address mistake.
msg "$gwc" "uds:/run/stale.sock" "STATUS: working - x" | denied || fail "guard-message allowed a status to a stale socket"
msg "$gwc" "uds:/run/stale.sock" "STATUS: working - x" | reason | grep -q 'state.sh main' || fail "guard-message did not say where MAIN's address is"
msg "$gwc" prompts-9d "STATUS: working - x" | denied || fail "guard-message allowed a status to an old name"
[ "$(grep -c '^=== ' "$ob")" = 2 ] || fail "guard-message copied a refused message"
[ -z "$(msg "$gwc" worker-a "anything goes")" ] || fail "guard-message checked a message to a worker"
CLAUDE_PROJECT_DIR="$gwc" msg "$tmp/plain" "Main one" "lane A is done" | denied || fail "guard-message lost the session after a cd"
[ -z "$(AGENT=w1 msg "$gwc" "Main one" "lane A is done")" ] || fail "guard-message checked a worker's message"
[ -z "$(msg "$tmp/nostate" "Main one" "lane A is done")" ] || fail "guard-message checked a session with no state file"
[ -z "$(msg "$tmp/plain" "Main one" "lane A is done")" ] || fail "guard-message checked a session outside git"

# --- guard-timestamps.py -------------------------------------------------------------------------------------
printf 'state at 10:00Z\n' > "$gwc/.orchestration/notes.md"
edit() { jq -n --arg cwd "${2:-$gwc}" --arg p "${3:-$gwc/.orchestration/notes.md}" --arg s "$1" '{cwd:$cwd,tool_input:{file_path:$p,new_string:$s}}' | with_agent | python3 -I "$here/hooks/guard-timestamps.py"; }
edit "approved at 14:30Z" | noted '14:30Z' || fail "timestamps hook should advise on a new clock time"
edit "stopped 07:3xZ" | noted '07:3xZ' || fail "timestamps hook should advise on an estimated time"
[ -z "$(edit "see 10:00Z above")" ] || fail "timestamps hook noted a time already in the file"
edit "resumed 2026-10-05T18:16Z" | noted '18:16Z' || fail "timestamps hook should advise on a hand-typed ISO time"
[ -z "$(edit "at 14:30Z" "$gwc" "$gwc/docs/plan.md")" ] || fail "timestamps hook fired outside .orchestration"
[ -z "$(edit "at 14:30Z" "$tmp/plain" "$tmp/plain/.orchestration/x.md")" ] || fail "timestamps hook fired outside git"
[ -z "$(AGENT=w1 edit "approved at 14:30Z")" ] || fail "timestamps hook advised a worker"
CLAUDE_PROJECT_DIR="$gwc" edit "approved at 14:30Z" "$tmp/plain" | noted '14:30Z' || fail "timestamps hook lost the session after a cd"

# --- thread.sh -----------------------------------------------------------------------------------------------
export ORCHESTRATION_HOME="$tmp/orch" CLAUDECODE=1 HERDR_PANE_ID=p1 CLAUDE_CODE_MESSAGING_SOCKET="$tmp/main-1.sock"
git init -q --bare -b main "$tmp/app-origin.git"
git clone -q "$tmp/app-origin.git" "$tmp/app-seed" 2>/dev/null
(cd "$tmp/app-seed" && printf 'app\n' > README.md && git add . && git commit -qm init && git push -q origin main \
  && git checkout -qb dev && printf 'dev\n' > DEV.md && git add . && git commit -qm dev && git push -q origin dev)
mkdir -p "$tmp/proj"
git clone -q "$tmp/app-origin.git" "$tmp/proj/app"
app=$(realpath "$tmp/proj/app")
printf 'Build the signup slice.\n' > "$tmp/brief-a.md"
[ "$("$thread" list)" = NONE ] || fail "thread.sh list should print NONE with no registry"
[ "$("$thread" decisions)" = NONE ] || fail "thread.sh decisions should print NONE with no registry"
out=$("$thread" launch t-a "$app" "$tmp/brief-a.md" --main prompts-9d)
[[ $out =~ ^LAUNCHED\ t-a\ [0-9a-f]{8}\ base=main@[0-9a-f]{7}\ landing=pr$ ]] || fail "thread.sh launch printed: $out"
ida=$(printf '%s' "$out" | cut -d' ' -f3)
wta="$tmp/proj/app-orch-t-a"
[ "$(git -C "$wta" rev-parse --abbrev-ref HEAD)" = orchestration/t-a ] || fail "thread.sh did not create the coordination worktree on orchestration/t-a"
[ "$(git -C "$wta" rev-parse HEAD)" = "$(git -C "$app" rev-parse origin/main)" ] || fail "thread.sh did not branch from origin/<current branch>"
rec="$wta/.orchestration/thread.md"
[ "$(sed -n 's/^\(MAIN\|MAIN-SOCKET\|CHECKOUT\|BASE\|BASE-REF\|LANE-BASE\|LANDING\): //p' "$rec" | tr '\n' '|')" = "prompts-9d|uds:$tmp/main-1.sock|$app|main|origin/main|origin/main|pr|" ] \
  || fail "thread.sh launch wrote the wrong thread record: $(cat "$rec")"
[ -z "$(git -C "$wta" config --get branch.orchestration/t-a.merge || true)" ] || fail "thread.sh made the coordination branch track the base"
grep -qxF '.orchestration/' "$app/.git/info/exclude" || fail "thread.sh did not exclude .orchestration/"
[ "$(head -2 "$MOCK_DIR/brief-t-a.txt" | tr '\n' '|')" = "MAIN: prompts-9d|STATE: $wta/.orchestration/state.md|" ] || fail "thread.sh launch brief header is wrong"
grep -q 'Build the signup slice.' "$MOCK_DIR/brief-t-a.txt" || fail "thread.sh launch dropped the brief"
grep -q "^$wta :: --agent orchestrator --bg --name t-a " "$MOCK_DIR/claude.log" || fail "thread.sh did not start the session in the coordination worktree"
grep -q 'CLAUDECODE leaked' "$MOCK_DIR/claude.log" && fail "thread.sh passed CLAUDECODE to claude"
[ "$(awk -F'\t' 'NR==2 {print $1, $2, $3, $4, $5, $6}' "$ORCHESTRATION_HOME/threads.tsv")" = "t-a $ida t-a $app $wta prompts-9d" ] || fail "thread.sh launch registry row is wrong"
# The state file and the hooks work from inside the new worktree, and .orchestration stays untracked.
(cd "$wta" && "$here/scripts/state.sh" init t-a >/dev/null)
[ "$(cd "$wta" && "$here/scripts/state.sh" main --socket)" = "uds:$tmp/main-1.sock" ] || fail "state.sh main --socket did not read the launched record"
[ -z "$(git -C "$wta" status --porcelain)" ] || fail ".orchestration/ shows up as untracked in the coordination worktree"
"$thread" launch t-a "$app" "$tmp/brief-a.md" --main prompts-9d --build other | grep -q '^FAILED a thread named t-a' || fail "thread.sh launched a duplicate name"
"$thread" launch t-x "$app" "$tmp/brief-a.md" --main prompts-9d --build t-a | grep -q "^FAILED $wta already hosts thread t-a" || fail "thread.sh launched a second thread on one worktree"
mkdir -p "$tmp/proj/app-orch-x"
"$thread" launch t-y "$app" "$tmp/brief-a.md" --main prompts-9d --build x | grep -q "^FAILED $tmp/proj/app-orch-x exists and is not the coordination worktree" || fail "thread.sh accepted a foreign path"
"$thread" launch t-z "$tmp/nowhere" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED no repository checkout' || fail "thread.sh launched without a repository"
"$thread" launch t-z "$tmp/plain" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED .* is not a git checkout' || fail "thread.sh launched outside git"
"$thread" launch t-z "$app" "$tmp/brief-a.md" | grep -q '^FAILED launch needs --main' || fail "thread.sh launched without --main"
"$thread" launch "bad name" "$app" "$tmp/brief-a.md" --main m | grep -q '^FAILED thread name' || fail "thread.sh accepted a name with a space"
"$thread" launch t-z "$app" "$tmp/brief-a.md" --main m --base nope | grep -q '^FAILED no branch nope in .* or on origin' || fail "thread.sh accepted a missing base"
"$thread" launch t-z "$app" "$tmp/brief-a.md" --main m --landing push | grep -q '^FAILED --landing takes pr or local' || fail "thread.sh accepted an unknown landing mode"
MOCK_CLAUDE=untrusted "$thread" launch t-u "$app" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED workspace not trusted: start the thread from a repository Claude Code trusts' || fail "thread.sh did not explain an untrusted workspace"
MOCK_CLAUDE=noagent "$thread" launch t-u "$app" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED no agent named orchestrator' || fail "thread.sh did not report a missing agent"
grep -q '^t-u' "$ORCHESTRATION_HOME/threads.tsv" && fail "thread.sh left a registry row for a failed launch"
# A linked worktree passed as the checkout still places the coordination worktree beside the main checkout.
git -C "$app" worktree add -q "$tmp/proj/app-wt-lane-b" -b lane-b
"$thread" launch t-b "$tmp/proj/app-wt-lane-b" "$tmp/brief-a.md" --main prompts-9d --build signup --base dev | grep -q '^LAUNCHED t-b ' || fail "thread.sh did not launch from a linked worktree"
wtb="$tmp/proj/app-orch-signup"
[ -f "$wtb/DEV.md" ] || fail "thread.sh ignored --base dev"
grep -qx "CHECKOUT: $tmp/proj/app-wt-lane-b" "$wtb/.orchestration/thread.md" || fail "thread.sh recorded the main checkout, not the linked worktree it was given"
# list reads live status from claude agents --json by session id prefix.
printf '[{"sessionId":"%s-0000","name":"t-a","status":"busy"}]' "$ida" > "$MOCK_DIR/agents.json"
"$thread" list | grep -q "^t-a $ida build=t-a status=busy main=prompts-9d worktree=$wta " || fail "thread.sh list did not show t-a busy"
"$thread" list | grep -q "^t-b [0-9a-f]* build=signup status=not-running main=prompts-9d worktree=$wtb " || fail "thread.sh list did not mark t-b not running"
# decisions: owner-before first, then by deadline, across threads, read from each worktree's .orchestration/.
(cd "$wta" && "$here/scripts/decisions.sh" add "Tea or coffee" "lane B" "lane B" "tea" +2h >/dev/null)
(cd "$wtb" && "$here/scripts/decisions.sh" add "Banner copy" "demo" "lane C" "short copy" +1h >/dev/null)
(cd "$wtb" && "$here/scripts/decisions.sh" add "Spend 40 USD" "quota" "lane D" "none" owner-before >/dev/null)
out=$("$thread" decisions)
[ "$(printf '%s\n' "$out" | wc -l)" = 3 ] || fail "thread.sh decisions should list three items: $out"
printf '%s\n' "$out" | sed -n 1p | grep -q '^t-b D2 Spend 40 USD | default: none | owner-before$' || fail "thread.sh decisions did not put owner-before first: $out"
printf '%s\n' "$out" | sed -n 2p | grep -Eq "^t-b D1 Banner copy \| default: short copy \| applies at $utc$" || fail "thread.sh decisions misordered by deadline: $out"
printf '%s\n' "$out" | sed -n 3p | grep -Eq "^t-a D1 Tea or coffee \| default: tea \| applies at $utc$" || fail "thread.sh decisions misformatted: $out"
# rotate needs a fresh RESUME stamp unless forced, and stays in the same worktree.
sed -i 's/^Written: .*/Written: 2000-01-01T00:00Z/' "$wta/.orchestration/state.md"
export CLAUDE_CODE_MESSAGING_SOCKET="$tmp/main-2.sock"
"$thread" rotate t-a --main prompts-9d | grep -q '^FAILED RESUME in .* min ago (limit 15)' || fail "thread.sh rotated on a stale RESUME"
"$thread" rotate t-b --main prompts-9d | grep -q '^FAILED no RESUME Written' || fail "thread.sh rotated a thread with no state file"
printf 'Lane A done.\n' | (cd "$wta" && "$here/scripts/state.sh" resume - >/dev/null)
out=$("$thread" rotate t-a --main prompts-9d)
[[ $out =~ ^ROTATED\ t-a\ -\>\ t-a-r1\ [0-9a-f]{8}$ ]] || fail "thread.sh rotate printed: $out"
grep -q "stop $ida" "$MOCK_DIR/claude.log" || fail "thread.sh rotate did not stop the old session"
grep -q "^$wta :: --agent orchestrator --bg --name t-a-r1 " "$MOCK_DIR/claude.log" || fail "thread.sh rotate left the coordination worktree"
grep -q '^Resume: read STATE first and continue from its RESUME section without redoing finished work.$' "$MOCK_DIR/brief-t-a-r1.txt" || fail "thread.sh rotate brief is wrong"
[ "$(awk -F'\t' '$1=="t-a-r1" {print $3, $5}' "$ORCHESTRATION_HOME/threads.tsv")" = "t-a $wta" ] || fail "thread.sh rotate changed the build or worktree"
grep -qx "MAIN-SOCKET: uds:$tmp/main-2.sock" "$rec" && grep -qx 'LANDING: pr' "$rec" || fail "thread.sh rotate did not refresh MAIN's socket, or lost the rest of the record"
grep -q '^t-a	' "$ORCHESTRATION_HOME/threads.tsv" && fail "thread.sh rotate left the old row"
"$thread" rotate t-a-r1 --main prompts-9d --force | grep -q '^ROTATED t-a-r1 -> t-a-r2 ' || fail "thread.sh rotate --force did not increment the suffix"
out=$("$thread" stop t-b)
[[ $out =~ ^STOPPED\ t-b\ [0-9a-f]{8}$ ]] || fail "thread.sh stop printed: $out"
grep -q '^t-b	' "$ORCHESTRATION_HOME/threads.tsv" && fail "thread.sh stop left the row"
[ -d "$wtb/.git" ] || [ -f "$wtb/.git" ] || fail "thread.sh stop removed the coordination worktree"
"$thread" stop t-b | grep -q '^FAILED no thread named t-b' || fail "thread.sh stopped an unknown thread"
"$thread" launch t-b2 "$app" "$tmp/brief-a.md" --main prompts-9d --build signup | grep -q '^LAUNCHED t-b2 ' || fail "thread.sh did not reuse the existing coordination worktree"
MOCK_CLAUDE=fail-stop "$thread" stop t-a-r2 | grep -q '^FAILED claude stop' || fail "thread.sh hid a failed stop"
grep -q '^t-a-r2	' "$ORCHESTRATION_HOME/threads.tsv" || fail "thread.sh dropped the row after a failed stop"

# --- thread.sh: started from a branch ------------------------------------------------------------------------
# The base defaults to the checkout's current branch; an unpushed branch lands locally.
git -C "$app" checkout -q -b feat-x
(cd "$app" && printf 'feat\n' > FEAT.md && git add . && git commit -qm feat)
out=$("$thread" launch t-c "$app" "$tmp/brief-a.md" --main prompts-9d --build c)
[[ $out =~ ^LAUNCHED\ t-c\ [0-9a-f]{8}\ base=feat-x@[0-9a-f]{7}\ landing=local$ ]] || fail "thread.sh did not launch from the current, unpushed branch: $out"
wtc="$tmp/proj/app-orch-c"
[ "$(git -C "$wtc" rev-parse HEAD)" = "$(git -C "$app" rev-parse feat-x)" ] || fail "thread.sh did not branch from the local feat-x"
grep -qx 'LANE-BASE: orchestration/c' "$wtc/.orchestration/thread.md" && grep -qx 'BASE-REF: feat-x' "$wtc/.orchestration/thread.md" || fail "thread.sh recorded the wrong base for a local build"
"$thread" launch t-d "$app" "$tmp/brief-a.md" --main m --build d --landing pr | grep -q '^FAILED --landing pr needs feat-x on origin with nothing unpushed' || fail "thread.sh accepted pr landing for an unpushed branch"
git -C "$app" checkout -q --detach
"$thread" launch t-d "$app" "$tmp/brief-a.md" --main m --build d | grep -q '^FAILED .* is on a detached HEAD; pass --base' || fail "thread.sh guessed a base on a detached HEAD"
git -C "$app" checkout -q main
# A branch on origin with unpushed local commits starts from the local branch and lands locally.
git -C "$app" checkout -q -b dev origin/dev
(cd "$app" && printf 'local\n' > LOCAL.md && git add . && git commit -qm local)
out=$("$thread" launch t-e "$app" "$tmp/brief-a.md" --main m --build e)
[[ $out == *"base=dev@"*" landing=local" ]] && [ -f "$tmp/proj/app-orch-e/LOCAL.md" ] || fail "thread.sh dropped unpushed commits on a branch that is on origin: $out"
"$thread" stop t-e >/dev/null
git -C "$app" checkout -q main
# A local branch behind origin starts from origin, which has the newer commits.
(cd "$tmp/app-seed" && git checkout -q main && printf 'more\n' > MORE.md && git add . && git commit -qm more && git push -q origin main)
out=$("$thread" launch t-d "$app" "$tmp/brief-a.md" --main m --build d)
[[ $out == *"landing=pr" ]] && [ -f "$tmp/proj/app-orch-d/MORE.md" ] || fail "thread.sh did not start a stale local branch from origin: $out"
# No origin at all, then an origin that can't be fetched: both land locally, and the second warns.
git init -q -b trunk "$tmp/proj/solo"
(cd "$tmp/proj/solo" && printf 's\n' > s.txt && git add . && git commit -qm s)
out=$("$thread" launch t-s "$tmp/proj/solo" "$tmp/brief-a.md" --main m --build s1)
[[ $out == *"base=trunk@"*" landing=local" ]] || fail "thread.sh did not land locally without an origin: $out"
git -C "$tmp/proj/solo" remote add origin "$tmp/no-such-origin.git"
out=$("$thread" launch t-s2 "$tmp/proj/solo" "$tmp/brief-a.md" --main m --build s2 2>"$tmp/s2.err")
[[ $out == *"landing=local" ]] && grep -q 'warning: git fetch origin failed' "$tmp/s2.err" || fail "thread.sh did not carry on past a failed fetch: $out"

# --- thread.sh check and adopt: MAIN's address moved --------------------------------------------------------
# MAIN restarts with a new socket; every thread so far recorded main-2.
export CLAUDE_CODE_MESSAGING_SOCKET="$tmp/main-3.sock"
(cd "$app" && "$thread" check) | tee "$tmp/check.out" | grep -q '^MOVED t-c main=prompts-9d recorded=uds:'"$tmp"'/main-2.sock this=uds:'"$tmp"'/main-3.sock' || fail "thread.sh check did not report that MAIN moved: $(cat "$tmp/check.out")"
(cd "$app" && "$thread" check) | grep -q '^MOVED t-s ' && fail "thread.sh check reported another repository's thread"
(cd "$tmp/plain" && "$thread" check) | grep -q '^MOVED t-s ' || fail "thread.sh check outside git did not cover every thread"
(cd "$app" && "$thread" check --all) | grep -q '^MOVED t-s ' || fail "thread.sh check --all did not cover every thread"
out=$("$thread" adopt t-c --main 'Main two')
[ "$out" = "ADOPTED t-c main=Main two socket=uds:$tmp/main-3.sock" ] || fail "thread.sh adopt printed: $out"
grep -qx 'MAIN: Main two' "$wtc/.orchestration/thread.md" && grep -qx "MAIN-SOCKET: uds:$tmp/main-3.sock" "$wtc/.orchestration/thread.md" || fail "thread.sh adopt did not rewrite the record"
grep -qx 'LANE-BASE: orchestration/c' "$wtc/.orchestration/thread.md" || fail "thread.sh adopt lost the rest of the record"
[ "$(awk -F'\t' '$1=="t-c" {print $6}' "$ORCHESTRATION_HOME/threads.tsv")" = 'Main two' ] || fail "thread.sh adopt did not update the registry"
(cd "$app" && "$thread" check) | grep -q '^MOVED t-c ' && fail "thread.sh check still reported t-c after adopt"
"$thread" adopt t-c | grep -q '^FAILED adopt needs --main' || fail "thread.sh adopted without a name"
"$thread" adopt t-nope --main x | grep -q '^FAILED no thread named t-nope' || fail "thread.sh adopted an unknown thread"
# The inbox shows each outbox entry once, without its hash.
printf '=== 2026-10-10T13:46Z to Main two #0123456789ab\nSTATUS: done - c merged\nCheck: README\n\n' > "$wtc/.orchestration/outbox.md"
out=$(cd "$tmp/plain" && "$thread" check --all)
printf '%s\n' "$out" | grep -qx 'INBOX t-c 2026-10-10T13:46Z to Main two' && printf '%s\n' "$out" | grep -qx '  Check: README' || fail "thread.sh check did not show the outbox: $out"
(cd "$tmp/plain" && "$thread" check --all) | grep -q '^INBOX t-c' && fail "thread.sh check showed an outbox entry twice"
printf '=== 2026-10-10T14:00Z to Main two #ba9876543210\nSTATUS: working - d1\n\n' >> "$wtc/.orchestration/outbox.md"
(cd "$tmp/plain" && "$thread" check --all) | grep -q '^INBOX t-c 2026-10-10T14:00Z' || fail "thread.sh check missed a new outbox entry"
for t in t-a-r2 t-b2 t-d t-s t-s2; do "$thread" adopt "$t" --main 'Main two' >/dev/null; done
[ "$(cd "$tmp/plain" && "$thread" check --all)" = OK ] || fail "thread.sh check did not print OK with nothing to catch up on"
# A thread with no record at all (launched before records existed) is reported, not fatal.
mkdir -p "$tmp/proj/legacy-orch/.orchestration"
printf 't-old\tdeadbeef\told\t%s\t%s\tm\t2026-10-10T00:00Z\n' "$app" "$tmp/proj/legacy-orch" >> "$ORCHESTRATION_HOME/threads.tsv"
(cd "$app" && "$thread" check) | grep -q '^MOVED t-old main=m recorded=none' || fail "thread.sh check failed on a thread with no record"
"$thread" stop t-old >/dev/null

# --- land-local.sh -------------------------------------------------------------------------------------------
git -C "$app" worktree add -q "$tmp/proj/app-wt-l1" -b lane/l1 orchestration/c
(cd "$tmp/proj/app-wt-l1" && printf 'l1\n' > L1.md && git add . && git commit -qm l1)
l1=$(git -C "$app" rev-parse lane/l1)
ll() { (cd "$wtc" && "$here/scripts/land-local.sh" "$@"); }
ll lane/l1 HEAD~1 --check true | grep -q "^STOPPED lane=lane/l1 head is ${l1:0:7}, not the approved" || fail "land-local.sh landed an unapproved head"
before=$(git -C "$wtc" rev-parse HEAD)
ll lane/l1 "$l1" --check 'exit 3' | grep -q '^STOPPED lane=lane/l1 check failed on merge .*, merge undone' || fail "land-local.sh kept a merge whose check failed"
[ "$(git -C "$wtc" rev-parse HEAD)" = "$before" ] || fail "land-local.sh did not undo the failed merge"
out=$(ll lane/l1 "$l1" --check 'test -f L1.md' --subject 'feat: l1')
[[ $out =~ ^LANDED\ lane=lane/l1\ head=${l1:0:7}\ merge=[0-9a-f]{7}$ ]] || fail "land-local.sh printed: $out"
[ "$(git -C "$wtc" rev-parse HEAD^2)" = "$l1" ] && [ "$(git -C "$wtc" log -1 --format=%s)" = 'Merge lane/l1: feat: l1' ] || fail "land-local.sh did not make a --no-ff merge of the approved head"
ll lane/l1 "$l1" --check true | grep -q 'is already on orchestration/c' || fail "land-local.sh merged a lane twice"
ll lane/none abc --check true | grep -q '^STOPPED lane=lane/none no branch' || fail "land-local.sh accepted a missing branch"
(cd "$wta" && "$here/scripts/land-local.sh" lane/l1 "$l1" --check true) | grep -q 'LANDING is not local' || fail "land-local.sh ran in a pull-request build"
ll lane/l1 "$l1" >/dev/null 2>&1 && fail "land-local.sh ran without --check"

# --- thread.sh integrate -------------------------------------------------------------------------------------
"$thread" integrate t-c | grep -q '^FAILED .* is on main, not feat-x' || fail "thread.sh integrated into the wrong branch"
git -C "$app" checkout -q feat-x
out=$("$thread" integrate t-c)
[[ $out =~ ^INTEGRATED\ t-c\ feat-x@[0-9a-f]{7}\ \(fast-forward\)$ ]] && [ -f "$app/L1.md" ] || fail "thread.sh integrate did not fast-forward: $out"
(cd "$app" && printf 'owner\n' > OWNER.md && git add . && git commit -qm owner)
(cd "$wtc" && printf 'c2\n' > C2.md && git add C2.md && git commit -qm c2)
out=$("$thread" integrate t-c)
[[ $out == *"(merge)" ]] && [ -f "$app/C2.md" ] && [ -f "$app/OWNER.md" ] || fail "thread.sh integrate did not merge a moved base: $out"
(cd "$app" && printf 'a\n' > CLASH.md && git add . && git commit -qm a)
(cd "$wtc" && printf 'b\n' > CLASH.md && git add CLASH.md && git commit -qm b)
"$thread" integrate t-c | grep -q '^FAILED merging orchestration/c into feat-x conflicts in: CLASH.md' || fail "thread.sh integrate hid a conflict"
[ -z "$(git -C "$app" status --porcelain --untracked-files=no)" ] || fail "thread.sh integrate left a half-done merge"
printf 'dirty\n' >> "$app/FEAT.md"
"$thread" integrate t-c | grep -q '^FAILED .* has uncommitted changes' || fail "thread.sh integrated over uncommitted changes"
git -C "$app" checkout -q FEAT.md
"$thread" integrate t-d | grep -q '^FAILED t-d lands by pull request' || fail "thread.sh integrated a pull-request build"
sed -i "s#^CHECKOUT: .*#CHECKOUT: $tmp/proj/solo#" "$wtc/.orchestration/thread.md"
"$thread" integrate t-c | grep -q "^FAILED $tmp/proj/solo is not a checkout of $app" || fail "thread.sh integrated into another repository"

# --- thread.sh close ------------------------------------------------------------------------------------------
# t-c's branch still holds the CLASH commit that integrate refused, so close refuses too.
"$thread" close t-c | grep -q '^FAILED orchestration/c holds work that feat-x lacks in: CLASH.md' || fail "thread.sh closed a build with unlanded work"
[ -d "$wtc" ] || fail "thread.sh close removed a worktree it refused to close"
idc=$(awk -F'\t' '$1=="t-c" {print $2}' "$ORCHESTRATION_HOME/threads.tsv")
out=$("$thread" close t-c --force)
[[ $out =~ ^CLOSED\ c\ archive=$ORCHESTRATION_HOME/archive/c-[0-9T]+Z\ lanes\ still\ present:\ .*app-wt-l1 ]] || fail "thread.sh close printed: $out"
arch=${out#*archive=}; arch=${arch%% *}
[ -f "$arch/thread.md" ] && [ -f "$arch/outbox.md" ] || fail "thread.sh close did not archive .orchestration"
[ ! -e "$wtc" ] && ! git -C "$app" rev-parse --verify -q orchestration/c >/dev/null || fail "thread.sh close left the worktree or the branch"
grep -q '^t-c	' "$ORCHESTRATION_HOME/threads.tsv" && fail "thread.sh close left the registry row"
grep -q "stop $idc" "$MOCK_DIR/claude.log" && grep -q "rm $idc" "$MOCK_DIR/claude.log" || fail "thread.sh close did not stop and remove the session"
# A pull-request build whose work landed by squash: different commits, same files on the base.
wtd="$tmp/proj/app-orch-d"
(cd "$wtd" && printf 'plan\n' > PLAN.md && git add PLAN.md && git commit -qm plan)
"$thread" close t-d | grep -q '^FAILED orchestration/d holds work that origin/main lacks in: PLAN.md' || fail "thread.sh closed a pull-request build before its work landed"
(cd "$tmp/app-seed" && git pull -q origin main && printf 'plan\n' > PLAN.md && git add PLAN.md && git commit -qm "plan (#9)" && git push -q origin main)
"$thread" close t-d | grep -q '^CLOSED d ' || fail "thread.sh did not recognise squash-landed work"
# A build the registry no longer lists closes by its worktree, with the base given.
git -C "$app" worktree add -q -b orchestration/z "$tmp/proj/app-orch-z" main
"$thread" close --worktree "$tmp/proj/app-orch-z" | tee "$tmp/z.out" | grep -q '^FAILED no record of .* base; pass --base' || fail "thread.sh closed an unrecorded build without a base: $(cat "$tmp/z.out")"
"$thread" close --worktree "$tmp/proj/app-orch-z" --base main | grep -q '^CLOSED z ' || fail "thread.sh did not close an unregistered build"
"$thread" close --worktree "$app" | grep -q 'is on .*, not orchestration/<build>' || fail "thread.sh closed a checkout that is not a coordination worktree"
"$thread" close t-nope | grep -q '^FAILED no thread named t-nope' || fail "thread.sh closed an unknown thread"

echo "orchestration tests passed"
