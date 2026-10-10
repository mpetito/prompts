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
unset ORCHESTRATION_STATE ORCHESTRATION_DECISIONS HERDR_ENV
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
  ok) while [ $# -gt 0 ]; do [ "$1" = --output-last-message ] && echo done > "$2"; shift; done ;;
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
"$here/scripts/state.sh" init b1 prompts-9d | grep -Eq "^initialised $coord/.orchestration/state.md $utc$" || fail "state.sh init did not use the worktree root"
s1="$coord/.orchestration/state.md"
[ -d "$coord/.orchestration/briefs" ] && [ -d "$coord/.orchestration/results" ] || fail "state.sh init did not create briefs/ and results/"
[ "$(grep '^#' "$s1" | tr '\n' '|')" = "# Orchestration thread: b1|## Thread|## RESUME|## Lanes|## Decisions|## Log|" ] || fail "state.sh init sections are out of order"
grep -q '^MAIN: prompts-9d$' "$s1" && grep -Eq "^Started: $utc$" "$s1" && grep -Eq "^Written: $utc$" "$s1" || fail "state.sh init skeleton lines missing"
"$here/scripts/state.sh" init b1 prompts-9d >/dev/null 2>&1 && fail "state.sh init overwrote an existing file"
[ "$("$here/scripts/state.sh" main)" = prompts-9d ] || fail "state.sh main did not print the MAIN name"
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

# --- finish-lane.sh (no herdr on PATH) -------------------------------------------------------------------------
git -C "$tmp/seed" worktree add -q "$tmp/lane" -b lane-x
mkdir -p "$tmp/lane/.orchestration/tmp"; printf 'evidence\n' > "$tmp/lane/.orchestration/tmp/note.txt"
"$here/scripts/finish-lane.sh" >/dev/null 2>&1 && fail "finish-lane.sh ran without arguments"
printf 'dirty\n' >> "$tmp/lane/g.txt"
"$here/scripts/finish-lane.sh" "$tmp/lane" "$tmp/archive" >/dev/null 2>&1 && fail "finish-lane.sh removed a worktree with uncommitted changes"
git -C "$tmp/lane" checkout -q g.txt
out=$("$here/scripts/finish-lane.sh" "$tmp/lane" "$tmp/archive")
[ -f "$tmp/archive/note.txt" ] || fail "finish-lane.sh did not archive the scratch directory"
[ ! -d "$tmp/lane" ] || fail "finish-lane.sh did not remove the worktree"
printf '%s' "$out" | grep -q 'deleted branch lane-x' || fail "finish-lane.sh did not delete the lane branch"

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
denies 'sleep 45' || fail "guard-bash should deny a 45 s foreground sleep"
denies 'sleep 2m && date' || fail "guard-bash should deny a minutes-long foreground sleep"
denies 'sleep 45' true && fail "guard-bash denied a background sleep"
denies 'sleep 5 && curl localhost:3000' && fail "guard-bash denied a short pause"
denies 'until [ -f done.txt ]; do sleep 5; done' || fail "guard-bash should deny a foreground wait loop"
denies 'while ! curl -s localhost; do sleep 2; done' || fail "guard-bash should deny a foreground while loop"
denies 'until [ -f done.txt ]; do sleep 5; done' true && fail "guard-bash denied a background wait loop"
denies 'while read -r l; do echo "$l"; done < f' && fail "guard-bash denied a loop that does not sleep"
denies 'echo "until it sleeps"' && fail "guard-bash denied the words inside a quoted string"
jq -n '{tool_input:{command:"sleep 45"}}' | "$here/hooks/guard-bash.sh" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null \
  || fail "guard-bash should deny a foreground sleep when the input has no cwd"

# --- guard-writes.sh -----------------------------------------------------------------------------------------
# $coord is a coordination worktree with .orchestration/state.md; $tmp/plain is outside git; $tmp/nostate is a
# git repository without a state file.
git init -q "$tmp/nostate"
writes() { jq -n --arg cwd "$1" --arg p "$2" --arg k "${3:-file_path}" '{cwd:$cwd,tool_input:{($k):$p}}' | "$here/hooks/guard-writes.sh"; }
denied() { jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null; }
[ -z "$(writes "$coord" "$coord/.orchestration/plan.md")" ] || fail "guard-writes denied a write to .orchestration"
[ -z "$(writes "$coord/sub" "$coord/src/app.ts")" ] || fail "guard-writes denied a file inside the coordination worktree"
[ -z "$(writes "$coord/sub" "../notes.md")" ] || fail "guard-writes denied a relative path inside the worktree"
writes "$coord" "$tmp/app/src/app.ts" | denied || fail "guard-writes allowed the owner's checkout"
writes "$coord" "$tmp/app-wt-lane-a/src/app.ts" | denied || fail "guard-writes allowed a lane worktree"
writes "$coord" "../app/src/app.ts" | denied || fail "guard-writes allowed a relative path out of the worktree"
writes "$coord" "$coord/../coord-evil/x" | denied || fail "guard-writes allowed a sibling with a shared prefix"
writes "$coord" "/etc/hosts" notebook_path | denied || fail "guard-writes allowed a notebook outside the worktree"
writes "$coord" "$tmp/app/x" | jq -r '.hookSpecificOutput.permissionDecisionReason' | grep -q "edits only its coordination worktree, $coord" || fail "guard-writes reason did not name the worktree"
[ -z "$(writes "$tmp/plain" "$tmp/app/x")" ] || fail "guard-writes denied a write from outside git"
[ -z "$(writes "$tmp/nostate" "$tmp/app/x")" ] || fail "guard-writes denied a write from a worktree with no state file"

# --- guard-message.sh ----------------------------------------------------------------------------------------
msg() { jq -n --arg cwd "$1" --arg to "$2" --arg m "$3" '{cwd:$cwd,tool_input:{to:$to,message:$m}}' | "$here/hooks/guard-message.sh"; }
msg "$coord" prompts-9d "lane A is done" | denied || fail "guard-message allowed a malformed message to MAIN"
msg "$coord/sub" "prompts-9d [25f79e]" "lane A is done" | denied || fail "guard-message ignored a MAIN address with a ref"
msg "$coord" prompts-9d "lane A is done" | jq -r '.hookSpecificOutput.permissionDecisionReason' | grep -q 'first line must be' || fail "guard-message reason did not carry check-message's reason"
[ -z "$(msg "$coord" prompts-9d "STATUS: done - lane A merged")" ] || fail "guard-message denied a valid message"
[ -z "$(msg "$coord" worker-a "anything goes")" ] || fail "guard-message checked a message to a worker"
[ -z "$(msg "$tmp/nostate" prompts-9d "lane A is done")" ] || fail "guard-message checked a session with no state file"
[ -z "$(msg "$tmp/plain" prompts-9d "lane A is done")" ] || fail "guard-message checked a session outside git"

# --- guard-timestamps.py -------------------------------------------------------------------------------------
printf 'state at 10:00Z\n' > "$coord/.orchestration/notes.md"
edit() { jq -n --arg cwd "${2:-$coord}" --arg p "${3:-$coord/.orchestration/notes.md}" --arg s "$1" '{cwd:$cwd,tool_input:{file_path:$p,new_string:$s}}' | python3 -I "$here/hooks/guard-timestamps.py"; }
edit "approved at 14:30Z" | denied || fail "timestamps hook should deny a new clock time"
edit "stopped 07:3xZ" | denied || fail "timestamps hook should deny an estimated time"
[ -z "$(edit "see 10:00Z above")" ] || fail "timestamps hook denied a time already in the file"
edit "resumed 2026-10-05T18:16Z" | denied || fail "timestamps hook should deny a hand-typed ISO time"
[ -z "$(edit "at 14:30Z" "$coord" "$coord/docs/plan.md")" ] || fail "timestamps hook fired outside .orchestration"
[ -z "$(edit "at 14:30Z" "$tmp/plain" "$tmp/plain/.orchestration/x.md")" ] || fail "timestamps hook fired outside git"

# --- thread.sh -----------------------------------------------------------------------------------------------
export ORCHESTRATION_HOME="$tmp/orch" CLAUDECODE=1 HERDR_PANE_ID=p1
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
[[ $out =~ ^LAUNCHED\ t-a\ [0-9a-f]{8}$ ]] || fail "thread.sh launch printed: $out"
ida=${out##* }
wta="$tmp/proj/app-orch-t-a"
[ "$(git -C "$wta" rev-parse --abbrev-ref HEAD)" = orchestration/t-a ] || fail "thread.sh did not create the coordination worktree on orchestration/t-a"
[ "$(git -C "$wta" rev-parse HEAD)" = "$(git -C "$app" rev-parse origin/main)" ] || fail "thread.sh did not branch from origin's default branch"
[ -z "$(git -C "$wta" config --get branch.orchestration/t-a.merge || true)" ] || fail "thread.sh made the coordination branch track the base"
grep -qxF '.orchestration/' "$app/.git/info/exclude" || fail "thread.sh did not exclude .orchestration/"
[ "$(head -2 "$MOCK_DIR/brief-t-a.txt" | tr '\n' '|')" = "MAIN: prompts-9d|STATE: $wta/.orchestration/state.md|" ] || fail "thread.sh launch brief header is wrong"
grep -q 'Build the signup slice.' "$MOCK_DIR/brief-t-a.txt" || fail "thread.sh launch dropped the brief"
grep -q "^$wta :: --agent orchestrator --bg --name t-a " "$MOCK_DIR/claude.log" || fail "thread.sh did not start the session in the coordination worktree"
grep -q 'CLAUDECODE leaked' "$MOCK_DIR/claude.log" && fail "thread.sh passed CLAUDECODE to claude"
[ "$(awk -F'\t' 'NR==2 {print $1, $2, $3, $4, $5, $6}' "$ORCHESTRATION_HOME/threads.tsv")" = "t-a $ida t-a $app $wta prompts-9d" ] || fail "thread.sh launch registry row is wrong"
# The state file and the hooks work from inside the new worktree, and .orchestration stays untracked.
(cd "$wta" && "$here/scripts/state.sh" init t-a prompts-9d >/dev/null)
[ -z "$(git -C "$wta" status --porcelain)" ] || fail ".orchestration/ shows up as untracked in the coordination worktree"
"$thread" launch t-a "$app" "$tmp/brief-a.md" --main prompts-9d --build other | grep -q '^FAILED a thread named t-a' || fail "thread.sh launched a duplicate name"
"$thread" launch t-x "$app" "$tmp/brief-a.md" --main prompts-9d --build t-a | grep -q "^FAILED $wta already hosts thread t-a" || fail "thread.sh launched a second thread on one worktree"
mkdir -p "$tmp/proj/app-orch-x"
"$thread" launch t-y "$app" "$tmp/brief-a.md" --main prompts-9d --build x | grep -q "^FAILED $tmp/proj/app-orch-x exists and is not the coordination worktree" || fail "thread.sh accepted a foreign path"
"$thread" launch t-z "$tmp/nowhere" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED no repository checkout' || fail "thread.sh launched without a repository"
"$thread" launch t-z "$tmp/plain" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED .* is not a git checkout' || fail "thread.sh launched outside git"
"$thread" launch t-z "$app" "$tmp/brief-a.md" | grep -q '^FAILED launch needs --main' || fail "thread.sh launched without --main"
"$thread" launch "bad name" "$app" "$tmp/brief-a.md" --main m | grep -q '^FAILED thread name' || fail "thread.sh accepted a name with a space"
"$thread" launch t-z "$app" "$tmp/brief-a.md" --main m --base nope | grep -q '^FAILED no branch origin/nope' || fail "thread.sh accepted a missing base"
MOCK_CLAUDE=untrusted "$thread" launch t-u "$app" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED workspace not trusted: start the thread from a repository Claude Code trusts' || fail "thread.sh did not explain an untrusted workspace"
MOCK_CLAUDE=noagent "$thread" launch t-u "$app" "$tmp/brief-a.md" --main prompts-9d | grep -q '^FAILED no agent named orchestrator' || fail "thread.sh did not report a missing agent"
grep -q '^t-u' "$ORCHESTRATION_HOME/threads.tsv" && fail "thread.sh left a registry row for a failed launch"
# A linked worktree passed as the checkout still places the coordination worktree beside the main checkout.
git -C "$app" worktree add -q "$tmp/proj/app-wt-lane-b" -b lane-b
"$thread" launch t-b "$tmp/proj/app-wt-lane-b" "$tmp/brief-a.md" --main prompts-9d --build signup --base dev | grep -q '^LAUNCHED t-b ' || fail "thread.sh did not launch from a linked worktree"
wtb="$tmp/proj/app-orch-signup"
[ -f "$wtb/DEV.md" ] || fail "thread.sh ignored --base dev"
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
"$thread" rotate t-a --main prompts-9d | grep -q '^FAILED RESUME in .* min ago (limit 15)' || fail "thread.sh rotated on a stale RESUME"
"$thread" rotate t-b --main prompts-9d | grep -q '^FAILED no RESUME Written' || fail "thread.sh rotated a thread with no state file"
printf 'Lane A done.\n' | (cd "$wta" && "$here/scripts/state.sh" resume - >/dev/null)
out=$("$thread" rotate t-a --main prompts-9d)
[[ $out =~ ^ROTATED\ t-a\ -\>\ t-a-r1\ [0-9a-f]{8}$ ]] || fail "thread.sh rotate printed: $out"
grep -q "stop $ida" "$MOCK_DIR/claude.log" || fail "thread.sh rotate did not stop the old session"
grep -q "^$wta :: --agent orchestrator --bg --name t-a-r1 " "$MOCK_DIR/claude.log" || fail "thread.sh rotate left the coordination worktree"
grep -q '^Resume: read STATE first and continue from its RESUME section without redoing finished work.$' "$MOCK_DIR/brief-t-a-r1.txt" || fail "thread.sh rotate brief is wrong"
[ "$(awk -F'\t' '$1=="t-a-r1" {print $3, $5}' "$ORCHESTRATION_HOME/threads.tsv")" = "t-a $wta" ] || fail "thread.sh rotate changed the build or worktree"
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

echo "orchestration tests passed"
