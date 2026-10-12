#!/usr/bin/env bash
# Offline checks for the orchestration scripts and hooks, including orchestration-main's thread.sh. Uses a
# throwaway directory with mocked herdr and gh on PATH and real git repositories; needs bash 5, jq,
# python3, git 2.31+ and GNU coreutils.
# No pipefail: each assertion pipes a command that may exit 1 by design into grep, and judges grep.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
thread="$(cd "$here/../orchestration-main/scripts" && pwd)/thread.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
export HOME="$tmp/home" ORCHESTRATION_HOME="$tmp/orch" MOCK_DIR="$tmp/mock"
unset ORCHESTRATION_STATE ORCHESTRATION_DECISIONS CLAUDE_CODE_MESSAGING_SOCKET
# Run inside herdr, the suite must never reach the owner's real session.
for v in $(compgen -e | grep '^HERDR_' || true); do unset "$v"; done
mkdir -p "$HOME" "$MOCK_DIR" "$tmp/bin"
export PATH="$tmp/bin:$PATH"
utc='[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z'

# --- mocks -------------------------------------------------------------------------------------------------
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
cat > "$tmp/bin/herdr" <<'MOCK'
#!/usr/bin/env bash
# A herdr that keeps its agents in $MOCK_DIR/herdr-agents.json and refuses what 0.9.3 refuses.
echo "$*" >> "$MOCK_DIR/herdr.log"
db="$MOCK_DIR/herdr-agents.json"
[ -f "$db" ] || echo '{"result":{"agents":[]}}' > "$db"
err() { printf '{"error":{"code":"%s","message":"%s"}}\n' "$1" "$2" >&2; exit 1; }
put() { jq "$@" "$db" > "$db.tmp" && mv "$db.tmp" "$db"; }
n=$(( $(cat "$MOCK_DIR/herdr.n" 2>/dev/null || echo 0) + 1 )); echo "$n" > "$MOCK_DIR/herdr.n"
case "$1 $2" in
  "agent list") [ "${MOCK_HERDR:-}" = down ] && exit 1; cat "$db" ;;
  "agent get") jq -e --arg a "$3" '.result.agents[] | select(.name == $a) | {result: {agent: (. + {workspace_id: (.pane_id // "" | split(":")[0])})}}' "$db" \
    || err agent_not_found "agent target $3 not found" ;;
  "agent prompt")
    jq -e --arg a "$3" '.result.agents[] | select(.name == $a and .agent_status == "blocked")' "$db" >/dev/null && err agent_blocked "agent $3 is blocked"
    echo '{"result":{"type":"ok"}}' ;;
  "workspace create")
    [[ " $* " == *" --cwd "* && " $* " == *" --no-focus "* ]] || err invalid "the mock wants --cwd and --no-focus"
    printf '{"result":{"workspace":{"workspace_id":"w%s"},"root_pane":{"pane_id":"w%s:p1"}}}\n' "$n" "$n" ;;
  "tab create")
    [ "${MOCK_HERDR:-}" = notab ] && err workspace_not_found "no such workspace"
    ws=$(sed -n 's/.*--workspace \([^ ]*\).*/\1/p' <<<"$*"); [ -n "$ws" ] || err invalid "the mock wants --workspace"
    printf '{"result":{"tab":{"tab_id":"%s:t%s"},"root_pane":{"pane_id":"%s:p%s"}}}\n' "$ws" "$n" "$ws" "$n" ;;
  "agent start")
    name=$3; shift 3; pane=""
    while [ $# -gt 0 ]; do case $1 in --pane) pane=$2; shift 2 ;; --kind|--timeout) shift 2 ;; --) shift; break ;; *) shift ;; esac; done
    [[ $name =~ ^[a-z][a-z0-9_-]{0,31}$ ]] || err invalid_name "agent names must match [a-z][a-z0-9_-]{0,31}"
    [ -n "$pane" ] || err invalid "--pane is required"
    for arg in "$@"; do [[ $arg != *$'\n'* ]] || err invalid_agent_argument "agent arguments cannot be encoded safely for the target shell"; done
    printf '%s\n' "$@" > "$MOCK_DIR/start-$name.args"
    [ "${MOCK_HERDR:-}" = startfail ] && err agent_start_failed "the agent exited"
    state=idle; [ "${MOCK_HERDR:-}" = notready ] && state=blocked
    put --arg a "$name" --arg p "$pane" --arg s "$state" '.result.agents += [{name: $a, agent_status: $s, pane_id: $p}]'
    [ "$state" = idle ] || err agent_not_ready "agent $name is blocked"
    printf '{"result":{"agent":{"name":"%s","pane_id":"%s"}}}\n' "$name" "$pane" ;;
  "pane close")
    [ "${MOCK_HERDR:-}" = closefail ] && err pane_not_found "pane $3 not found"
    put --arg p "$3" '.result.agents |= map(select(.pane_id != $p))'; echo '{"result":{"type":"ok"}}' ;;
  "workspace close") echo '{"result":{"type":"ok"}}' ;;
  *) err unknown "the mock has no $1 $2" ;;
esac
MOCK
chmod +x "$tmp/bin/"*

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

# --- state.sh: init, thread, log, resume ----------------------------------------------------------------------
cd "$coord/sub"
"$here/scripts/state.sh" init b1 | grep -Eq "^initialised $coord/.orchestration/state.md $utc$" || fail "state.sh init did not use the worktree root"
s1="$coord/.orchestration/state.md"
[ -d "$coord/.orchestration/briefs" ] && [ -d "$coord/.orchestration/results" ] || fail "state.sh init did not create briefs/ and results/"
[ "$(grep '^#' "$s1" | tr '\n' '|')" = "# Orchestration thread: b1|## Thread|## RESUME|## Lanes|## Decisions|## Log|" ] || fail "state.sh init sections are out of order"
grep -q '^Record: thread.md' "$s1" && grep -Eq "^Started: $utc$" "$s1" && grep -Eq "^Written: $utc$" "$s1" || fail "state.sh init skeleton lines missing"
grep -q '^MAIN:' "$s1" && fail "state.sh init wrote a MAIN line; the thread record is its one home"
"$here/scripts/state.sh" init b1 >/dev/null 2>&1 && fail "state.sh init overwrote an existing file"
"$here/scripts/state.sh" init b1 prompts-9d >/dev/null 2>&1 && fail "state.sh init accepted the old MAIN argument"
printf '%s\n' '# record' 'BUILD: b1' 'CHECKOUT: /x' 'BASE: dev' 'LANE-BASE: orchestration/b1' 'LANDING: local' > "$coord/.orchestration/thread.md"
[ "$("$here/scripts/state.sh" thread LANE-BASE)" = orchestration/b1 ] || fail "state.sh thread did not read a record field"
"$here/scripts/state.sh" thread NOPE >/dev/null 2>&1 && fail "state.sh thread printed a missing field"
"$here/scripts/state.sh" main >/dev/null 2>&1 && fail "state.sh still has a main command"
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
| scripts | - | - | - | brief |

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
# A lane not yet started has "-" cells; the separator row never matches a lane.
"$here/scripts/state.sh" set scripts Agent opus >/dev/null || fail "state.sh set refused a lane whose Agent cell is -"
grep -q '^| scripts | opus | - | - | brief |$' legacy/state.md || fail "state.sh set did not update a lane whose Agent cell was -"
grep -qx '| --- | --- | --- | --- | --- |' legacy/state.md || fail "state.sh set changed the separator row"
grep -q '^| beta | opus | #2 | 9999999 | land |$' legacy/state.md || fail "state.sh set on scripts touched another row"
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

# --- mail.sh -------------------------------------------------------------------------------------------------
mail="$here/scripts/mail.sh"
box="$ORCHESTRATION_HOME/mail"
# herdr_agents <name state>...: the agents the mocked herdr lists.
herdr_agents() { printf '%s\n' "$@" | jq -R 'split(" ") | {name: .[0], agent_status: .[1]}' | jq -s '{result: {agents: .}}' > "$MOCK_DIR/herdr-agents.json"; }
"$mail" send b1/main --from b1/thread "STATUS: working - one" | grep -q '^SENT b1/main ' || fail "mail.sh send did not report SENT"
printf 'STATUS: done - two\n' > "$tmp/m2.md"; "$mail" send b1/main --from b1/thread --file "$tmp/m2.md" >/dev/null
printf 'STATUS: working - three\n' | "$mail" send b1/main --from b1/lane-a >/dev/null
"$mail" send b1/main "no sender" >/dev/null 2>&1 && fail "mail.sh sent without --from"
"$mail" send main --from b1/thread x >/dev/null 2>&1 && fail "mail.sh accepted an address without a build"
"$mail" send b1/main --from b1/thread '  ' >/dev/null 2>&1 && fail "mail.sh sent an empty message"
printf '\n' | "$mail" send b1/main --from b1/thread >/dev/null 2>&1 && fail "mail.sh sent an empty message from stdin"
[ -z "$(ls -A "$box/b1/main/tmp")" ] || fail "mail.sh left a half-written message in tmp/"
"$mail" wait b1/main --timeout 0 | grep -qx 'MAIL 3' || fail "mail.sh wait did not count three messages"
"$mail" read b1/main > "$tmp/read.out"
[ "$(grep '^STATUS' "$tmp/read.out" | tr '\n' ' ')" = "STATUS: working - one STATUS: done - two STATUS: working - three " ] || fail "mail.sh read did not print the messages oldest first: $(cat "$tmp/read.out")"
grep -qx 'From: b1/lane-a' "$tmp/read.out" || fail "mail.sh read lost the sender"
[ "$(ls "$box/b1/main/cur" | wc -l)" = 3 ] && [ -z "$(ls -A "$box/b1/main/new")" ] || fail "mail.sh read did not file the messages"
"$mail" read b1/main | grep -qx 'NO MAIL' || fail "mail.sh read printed old mail again"
"$mail" wait b1/main --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait woke with no mail"
# A quiet message wakes no wait, and the next read prints it.
"$mail" send b1/main --from b1/thread --quiet "STATUS: working - quiet" >/dev/null
"$mail" wait b1/main --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait woke for a quiet message"
"$mail" read b1/main | grep -qx 'STATUS: working - quiet' || fail "mail.sh read skipped a quiet message"
# Two watched threads: a prompt is reported once, and again only after the agent works and blocks anew.
herdr_agents "b1 working" "b2 blocked"
"$mail" wait m/main --watch b1,b2 --timeout 0 | grep -qx 'BLOCKED b2' || fail "mail.sh wait missed a blocked agent"
"$mail" wait m/main --watch b1,b2 --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait reported the same prompt twice"
herdr_agents "b1 working" "b2 working"; "$mail" wait m/main --watch b1,b2 --timeout 0 >/dev/null
herdr_agents "b1 working" "b2 blocked"
"$mail" wait m/main --watch b1,b2 --timeout 0 | grep -qx 'BLOCKED b2' || fail "mail.sh wait missed a second prompt"
# A herdr that can't list its agents says nothing about them; an agent that leaves the list is GONE once.
MOCK_HERDR=down "$mail" wait m/main --watch b1,b2 --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait judged agents while herdr was down"
herdr_agents "b2 blocked"
"$mail" wait m/main --watch b1,b2 --timeout 0 | grep -qx 'GONE b1' || fail "mail.sh wait missed an agent that left"
"$mail" wait m/main --watch b1,b2,b9 --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait reported GONE twice, or for an agent it never saw"
# An idle thread with mail older than five minutes stopped waiting; fresh mail is not yet a sign of that.
herdr_agents "b3 idle"
"$mail" send b3/thread --from b3/lane-a --quiet "STATUS: working - old and quiet" >/dev/null
touch -d '-10 minutes' "$box/b3/thread/new/"*
"$mail" wait b3/main --watch b3=b3/thread --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait called old quiet mail unread"
"$mail" send b3/thread --from b3/main "STEER: fresh" >/dev/null
"$mail" wait b3/main --watch b3=b3/thread --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait called fresh mail unread"
touch -d '-10 minutes' "$box/b3/thread/new/"*
"$mail" wait b3/main --watch b3=b3/thread --timeout 0 | grep -qx 'UNREAD b3 1' || fail "mail.sh wait missed an idle thread with old mail"
"$mail" wait b3/main --watch b3=b3/thread --timeout 0 | grep -qx 'TIMEOUT' || fail "mail.sh wait reported the same unread stretch twice"
herdr_agents "b3 working"; "$mail" wait b3/main --watch b3=b3/thread --timeout 0 >/dev/null
herdr_agents "b3 done"
"$mail" wait b3/main --watch b3=b3/thread --timeout 0 | grep -qx 'UNREAD b3 1' || fail "mail.sh wait missed a second unread stretch"

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

# --- lane.sh -------------------------------------------------------------------------------------------------
lane="$here/scripts/lane.sh"
mkdir -p "$tmp/lanewt"; printf 'Build the API.\n' > "$tmp/lane-brief.md"
herdr_agents "lb idle"
jq '(.result.agents[] | select(.name == "lb")) += {pane_id: "w7:p1"}' "$MOCK_DIR/herdr-agents.json" > "$tmp/db" && mv "$tmp/db" "$MOCK_DIR/herdr-agents.json"
: > "$MOCK_DIR/herdr.log"
out=$("$lane" lb api "$tmp/lanewt" "$tmp/lane-brief.md" --kind codex --model m1 || true)
[[ $out =~ ^LANE\ lb-api\ pane=w7:p[0-9]+\ kind=codex$ ]] || fail "lane.sh printed: $out"
grep -qx "tab create --workspace w7 --cwd $tmp/lanewt --label api --no-focus" "$MOCK_DIR/herdr.log" || fail "lane.sh did not open a tab for the lane in the thread's workspace: $(cat "$MOCK_DIR/herdr.log")"
[ "$(tr '\n' '|' < "$MOCK_DIR/start-lb-api.args")" = "--approve-for-me|--add-dir|$ORCHESTRATION_HOME/mail/lb|--model|m1|" ] || fail "lane.sh started Codex with: $(cat "$MOCK_DIR/start-lb-api.args")"
[ -d "$ORCHESTRATION_HOME/mail/lb" ] || fail "lane.sh did not create the mail folder it lets Codex write"
grep -qx "agent prompt lb-api Read $tmp/lane-brief.md and follow it." "$MOCK_DIR/herdr.log" || fail "lane.sh did not hand the lane its brief"
"$lane" lb net "$tmp/lanewt" "$tmp/lane-brief.md" --kind codex --model m1 --network >/dev/null
grep -qx 'sandbox_workspace_write.network_access=true' "$MOCK_DIR/start-lb-net.args" || fail "lane.sh --network did not open Codex's sandbox to the network"
"$lane" lb ui "$tmp/lanewt" "$tmp/lane-brief.md" --kind claude --model opus | grep -q '^LANE lb-ui ' || fail "lane.sh did not start a Claude lane"
[ "$(tr '\n' '|' < "$MOCK_DIR/start-lb-ui.args")" = "--agent|lane|--model|opus|" ] || fail "lane.sh started Claude with: $(cat "$MOCK_DIR/start-lb-ui.args")"
"$lane" lb x "$tmp/lanewt" "$tmp/lane-brief.md" --kind claude | grep -q '^FAILED --model is required' || fail "lane.sh started a lane without a model"
"$lane" lb x "$tmp/lanewt" "$tmp/lane-brief.md" --kind gemini --model g | grep -q '^FAILED --kind takes claude or codex' || fail "lane.sh accepted an unknown kind"
"$lane" lb "$(printf 'x%.0s' {1..30})" "$tmp/lanewt" "$tmp/lane-brief.md" --kind claude --model opus | grep -q '^FAILED lane agent name .* must match' || fail "lane.sh accepted a name herdr refuses"
"$lane" nob x "$tmp/lanewt" "$tmp/lane-brief.md" --kind claude --model opus | grep -q '^FAILED no live thread named nob' || fail "lane.sh started a lane with no thread"
: > "$MOCK_DIR/herdr.log"
out=$(MOCK_HERDR=notready "$lane" lb tr "$tmp/lanewt" "$tmp/lane-brief.md" --kind codex --model m1 || true)
[ "$out" = "BLOCKED lb-tr waiting on a startup prompt: answer it in workspace lb, tab tr" ] || fail "lane.sh mishandled a startup prompt: $out"
grep -q '^agent prompt' "$MOCK_DIR/herdr.log" && fail "lane.sh prompted a lane held at a startup prompt"
out=$(MOCK_HERDR=startfail "$lane" lb sf "$tmp/lanewt" "$tmp/lane-brief.md" --kind codex --model m1 || true)
[ "$out" = "FAILED herdr agent start: agent_start_failed: the agent exited" ] && grep -q '^pane close w7:p' "$MOCK_DIR/herdr.log" || fail "lane.sh left the tab of a lane that failed to start: $out"

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
# Inside herdr, a lane named by a relative path is still refused while an agent runs there; a sibling isn't it.
git -C "$tmp/seed" worktree add -q "$tmp/lane4" -b lane-w
printf '{"result":{"agents":[{"name":"t-l4","agent_status":"idle","cwd":"%s/src"},{"name":"t-l40","agent_status":"idle","cwd":"%s0"}]}}' \
  "$(realpath "$tmp/lane4")" "$(realpath "$tmp/lane4")" > "$MOCK_DIR/herdr-agents.json"
(cd "$tmp" && HERDR_ENV=1 "$here/scripts/finish-lane.sh" lane4 "$tmp/archive4" 2>&1) | grep -qx "refusing: agent(s) still run in lane4: t-l4" || fail "finish-lane.sh missed an agent in a lane named by a relative path"
jq '.result.agents |= map(select(.name != "t-l4"))' "$MOCK_DIR/herdr-agents.json" > "$tmp/db" && mv "$tmp/db" "$MOCK_DIR/herdr-agents.json"
(cd "$tmp" && HERDR_ENV=1 "$here/scripts/finish-lane.sh" lane4 "$tmp/archive4" >/dev/null 2>&1) && [ ! -d "$tmp/lane4" ] || fail "finish-lane.sh took an agent in a sibling worktree for one in the lane"
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
denies 'rm -rf .orchestration/lanes/lane-b2' || fail "guard-bash should deny deleting lane evidence"
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
  | "$here/hooks/guard-bash.sh" ${LANE:+--lane}; }
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
[ -z "$(LANE=1 bash_note 'sleep 45')" ] || fail "guard-bash advised a lane session on a foreground wait"
bash_note '~/.claude/skills/agent-orchestration/scripts/mail.sh wait b1/thread --timeout 600' | advised 'waits on mail in the foreground' || fail "guard-bash should advise on a foreground mail wait"
[ -z "$(bash_note '~/.claude/skills/agent-orchestration/scripts/mail.sh wait b1/thread' true)" ] || fail "guard-bash noted a background mail wait"
[ -z "$(bash_note '~/.claude/skills/agent-orchestration/scripts/mail.sh read b1/thread')" ] || fail "guard-bash noted a mail read"
[ -z "$(bash_note 'until curl -s localhost; do sleep 2; done' false worker-1)" ] || fail "guard-bash advised a worker's wait loop"
bash_note 'pkill -f vite' false worker-1 | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null || fail "guard-bash let a worker pkill"
bash_note 'git worktree remove ../wt' false worker-1 | jq -r '.hookSpecificOutput.permissionDecisionReason' | grep -q 'git clone --no-local' || fail "guard-bash did not point a worker at a clone for throwaway copies"
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
printf '%s\n' '# record' 'BUILD: b1' "CHECKOUT: $gwapp" > "$gwc/.orchestration/thread.md"
git init -q "$tmp/nostate"
denied() { jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null; }
reason() { jq -r '.hookSpecificOutput.permissionDecisionReason'; }
noted() { jq -e '(.hookSpecificOutput.permissionDecision == null) and (.hookSpecificOutput.additionalContext | test("'"$1"'"))' >/dev/null; }
# with_agent <json>: add agent_id when $AGENT is set, as Claude Code does for a subagent's tool call.
with_agent() { jq --arg a "${AGENT:-}" 'if $a == "" then . else . + {agent_id:$a} end'; }

# --- guard-writes.sh -----------------------------------------------------------------------------------------
writes() { jq -n --arg cwd "$1" --arg p "$2" --arg k "${3:-file_path}" '{cwd:$cwd,tool_input:{($k):$p}}' | with_agent | "$here/hooks/guard-writes.sh" ${LANE:+--lane}; }
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
# A lane session starts in its lane worktree, with no thread files: --lane still guards the owner's checkout.
[ -z "$(writes "$gwl" "$gwapp/a.txt")" ] || fail "guard-writes acted in a session that is neither a thread nor a lane"
LANE=1 writes "$gwl" "$gwapp/a.txt" | reason | grep -q 'Make the change in your own lane worktree' || fail "guard-writes let a lane session write into the owner's checkout"
[ -z "$(LANE=1 writes "$gwl" "$gwl/src/app.ts")" ] || fail "guard-writes noted a lane session in its own worktree"
[ -z "$(LANE=1 writes "$gwl" "$HOME/notes.md")" ] || fail "guard-writes noted a lane session outside the owner's checkout"
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
export ORCHESTRATION_HOME="$tmp/orch"
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
rm -f "$MOCK_DIR/herdr-agents.json" "$MOCK_DIR/herdr.log"
# thread_pane <build>: the pane the mocked herdr hosts the build's thread in.
thread_pane() { jq -r --arg a "$1" '.result.agents[] | select(.name == $a) | .pane_id' "$MOCK_DIR/herdr-agents.json"; }
row_of() { awk -F'\t' -v b="$1" '$1 == b' "$ORCHESTRATION_HOME/threads.tsv"; }
out=$("$thread" launch t-a "$app" "$tmp/brief-a.md" || true)
[[ $out =~ ^LAUNCHED\ t-a\ base=main@[0-9a-f]{7}\ landing=pr$ ]] || fail "thread.sh launch printed: $out"
wta="$tmp/proj/app-orch-t-a"
[ "$(git -C "$wta" rev-parse --abbrev-ref HEAD)" = orchestration/t-a ] || fail "thread.sh did not create the coordination worktree on orchestration/t-a"
[ "$(git -C "$wta" rev-parse HEAD)" = "$(git -C "$app" rev-parse origin/main)" ] || fail "thread.sh did not branch from origin/<current branch>"
rec="$wta/.orchestration/thread.md"
[ "$(sed -n 's/^\([A-Z-]*\): //p' "$rec" | head -6 | tr '\n' '|')" = "t-a|$app|main|origin/main|origin/main|pr|" ] \
  && ! grep -q '^MAIN' "$rec" || fail "thread.sh launch wrote the wrong thread record: $(cat "$rec")"
[ -z "$(git -C "$wta" config --get branch.orchestration/t-a.merge || true)" ] || fail "thread.sh made the coordination branch track the base"
grep -qxF '.orchestration/' "$app/.git/info/exclude" || fail "thread.sh did not exclude .orchestration/"
# One workspace per build, opened at the coordination worktree without taking the owner's focus.
grep -qx "workspace create --cwd $wta --label t-a --no-focus --env ORCHESTRATION_HOME=$ORCHESTRATION_HOME" "$MOCK_DIR/herdr.log" \
  || fail "thread.sh did not open the build's workspace at its worktree without focus: $(cat "$MOCK_DIR/herdr.log")"
wsa=$(row_of t-a | cut -f4)
[ "$(row_of t-a | cut -f1-3)" = "t-a	$app	$wta" ] && [[ $wsa =~ ^w[0-9]+$ ]] || fail "thread.sh launch registry row is wrong: $(row_of t-a)"
[ "$(thread_pane t-a)" = "$wsa:p1" ] || fail "thread.sh did not start the thread in the workspace's root pane"
[ "$(tr '\n' '|' < "$MOCK_DIR/start-t-a.args")" = "--agent|orchestrator|Read $wta/.orchestration/launch-brief.md and follow it.|" ] \
  || fail "thread.sh started the wrong agent or prompt: $(cat "$MOCK_DIR/start-t-a.args")"
[ "$(head -3 "$wta/.orchestration/launch-brief.md" | tr '\n' '|')" = "BUILD: t-a|MAIL: t-a/thread is yours; send MAIN t-a/main|STATE: $wta/.orchestration/state.md|" ] \
  || fail "thread.sh wrote the wrong brief header: $(head -3 "$wta/.orchestration/launch-brief.md")"
grep -q 'Build the signup slice.' "$wta/.orchestration/launch-brief.md" || fail "thread.sh launch dropped the brief"
# The state file and the hooks work from inside the new worktree, and .orchestration stays untracked.
(cd "$wta" && "$here/scripts/state.sh" init t-a >/dev/null)
[ "$(cd "$wta" && "$here/scripts/state.sh" thread BUILD)" = t-a ] || fail "state.sh thread did not read BUILD from the launched record"
[ -z "$(git -C "$wta" status --porcelain)" ] || fail ".orchestration/ shows up as untracked in the coordination worktree"
"$thread" launch t-a "$app" "$tmp/brief-a.md" | grep -q '^FAILED a thread for build t-a is already registered' || fail "thread.sh launched a duplicate build"
jq '.result.agents += [{name: "held", agent_status: "idle", pane_id: "w0:p9"}]' "$MOCK_DIR/herdr-agents.json" > "$tmp/db" && mv "$tmp/db" "$MOCK_DIR/herdr-agents.json"
"$thread" launch held "$app" "$tmp/brief-a.md" | grep -q '^FAILED a live herdr agent is already named held' || fail "thread.sh took a name a live agent holds"
mkdir -p "$tmp/proj/app-orch-x"
"$thread" launch x "$app" "$tmp/brief-a.md" | grep -q "^FAILED $tmp/proj/app-orch-x exists and is not the coordination worktree" || fail "thread.sh accepted a foreign path"
"$thread" launch t-z "$tmp/nowhere" "$tmp/brief-a.md" | grep -q '^FAILED no repository checkout' || fail "thread.sh launched without a repository"
"$thread" launch t-z "$tmp/plain" "$tmp/brief-a.md" | grep -q '^FAILED .* is not a git checkout' || fail "thread.sh launched outside git"
for bad in "bad name" Upper 1st "$(printf 'a%.0s' {1..33})"; do
  "$thread" launch "$bad" "$app" "$tmp/brief-a.md" | grep -q '^FAILED build name .* must match' || fail "thread.sh accepted the build name '$bad'"
done
"$thread" launch t-z "$app" "$tmp/brief-a.md" --base nope | grep -q '^FAILED no branch nope in .* or on origin' || fail "thread.sh accepted a missing base"
"$thread" launch t-z "$app" "$tmp/brief-a.md" --landing push | grep -q '^FAILED --landing takes pr or local' || fail "thread.sh accepted an unknown landing mode"
# A thread held at a startup prompt is launched and reported; a thread that fails to start leaves nothing behind.
out=$(MOCK_HERDR=notready "$thread" launch t-u "$app" "$tmp/brief-a.md" || true)
[ "$out" = "BLOCKED t-u waiting on a startup prompt: answer it in workspace t-u" ] && [ -n "$(row_of t-u)" ] || fail "thread.sh launch mishandled a startup prompt: $out"
"$thread" stop t-u >/dev/null
out=$(MOCK_HERDR=startfail "$thread" launch t-f "$app" "$tmp/brief-a.md" || true)
[ "$out" = "FAILED herdr agent start: agent_start_failed: the agent exited" ] || fail "thread.sh launch printed: $out"
[ -z "$(row_of t-f)" ] && grep -q "^workspace close w" "$MOCK_DIR/herdr.log" || fail "thread.sh left a row or a workspace behind after a failed start"
# A linked worktree passed as the checkout still places the coordination worktree beside the main checkout.
git -C "$app" worktree add -q "$tmp/proj/app-wt-lane-b" -b lane-b
"$thread" launch signup "$tmp/proj/app-wt-lane-b" "$tmp/brief-a.md" --base dev | grep -q '^LAUNCHED signup ' || fail "thread.sh did not launch from a linked worktree"
wtb="$tmp/proj/app-orch-signup"
[ -f "$wtb/DEV.md" ] || fail "thread.sh ignored --base dev"
grep -qx "CHECKOUT: $tmp/proj/app-wt-lane-b" "$wtb/.orchestration/thread.md" || fail "thread.sh recorded the main checkout, not the linked worktree it was given"
# list reads each thread's status from herdr.
jq '(.result.agents[] | select(.name == "t-a") | .agent_status) = "working"' "$MOCK_DIR/herdr-agents.json" > "$tmp/db" && mv "$tmp/db" "$MOCK_DIR/herdr-agents.json"
herdr pane close "$(thread_pane signup)" >/dev/null
"$thread" list | grep -q "^t-a status=working workspace=$wsa worktree=$wta " || fail "thread.sh list did not show t-a working"
"$thread" list | grep -q "^signup status=not-running workspace=w[0-9]* worktree=$wtb " || fail "thread.sh list did not mark signup not running"
# decisions: owner-before first, then by deadline, across threads, read from each worktree's .orchestration/.
(cd "$wta" && "$here/scripts/decisions.sh" add "Tea or coffee" "lane B" "lane B" "tea" +2h >/dev/null)
(cd "$wtb" && "$here/scripts/decisions.sh" add "Banner copy" "demo" "lane C" "short copy" +1h >/dev/null)
(cd "$wtb" && "$here/scripts/decisions.sh" add "Spend 40 USD" "quota" "lane D" "none" owner-before >/dev/null)
out=$("$thread" decisions || true)
[ "$(printf '%s\n' "$out" | wc -l)" = 3 ] || fail "thread.sh decisions should list three items: $out"
printf '%s\n' "$out" | sed -n 1p | grep -q '^signup D2 Spend 40 USD | default: none | owner-before$' || fail "thread.sh decisions did not put owner-before first: $out"
printf '%s\n' "$out" | sed -n 2p | grep -Eq "^signup D1 Banner copy \| default: short copy \| applies at $utc$" || fail "thread.sh decisions misordered by deadline: $out"
printf '%s\n' "$out" | sed -n 3p | grep -Eq "^t-a D1 Tea or coffee \| default: tea \| applies at $utc$" || fail "thread.sh decisions misformatted: $out"
# rotate needs a fresh RESUME stamp unless forced, keeps the name, and replaces the thread in the build's workspace.
sed -i 's/^Written: .*/Written: 2000-01-01T00:00Z/' "$wta/.orchestration/state.md"
"$thread" rotate t-a | grep -q '^FAILED RESUME in .* min ago (limit 15)' || fail "thread.sh rotated on a stale RESUME"
"$thread" rotate signup | grep -q '^FAILED no RESUME Written' || fail "thread.sh rotated a thread with no state file"
printf 'Lane A done.\n' | (cd "$wta" && "$here/scripts/state.sh" resume - >/dev/null)
olda=$(thread_pane t-a)
[ "$("$thread" rotate t-a)" = "ROTATED t-a" ] || fail "thread.sh rotate did not print ROTATED t-a"
grep -qx "tab create --workspace $wsa --cwd $wta --label t-a --no-focus --env ORCHESTRATION_HOME=$ORCHESTRATION_HOME" "$MOCK_DIR/herdr.log" || fail "thread.sh rotate did not open the new thread in the build's workspace"
newa=$(thread_pane t-a)
grep -qx "pane close $olda" "$MOCK_DIR/herdr.log" && [ -n "$newa" ] && [ "$newa" != "$olda" ] || fail "thread.sh rotate did not replace the old pane: old=$olda new=$newa"
grep -qx "Read $wta/.orchestration/rotate-brief.md and follow it." "$MOCK_DIR/start-t-a.args" \
  && grep -qx 'Resume: read STATE first and continue from its RESUME section without redoing finished work.' "$wta/.orchestration/rotate-brief.md" \
  || fail "thread.sh rotate brief is wrong"
[ "$(row_of t-a | cut -f1-4)" = "t-a	$app	$wta	$wsa" ] || fail "thread.sh rotate changed the build, worktree or workspace: $(row_of t-a)"
# A thread whose agent and workspace are gone restarts in a new workspace.
out=$(MOCK_HERDR=notab "$thread" rotate signup --force || true)
[ "$out" = "ROTATED signup" ] && [ -n "$(thread_pane signup)" ] || fail "thread.sh rotate --force did not restart a stopped thread: $out"
"$thread" list | grep -q "^signup status=idle workspace=w[0-9]* " || fail "thread.sh rotate did not record the new workspace"
MOCK_HERDR=closefail "$thread" stop signup | grep -q '^FAILED herdr pane close .*: pane_not_found' || fail "thread.sh hid a failed stop"
[ -n "$(row_of signup)" ] || fail "thread.sh dropped the row after a failed stop"
[ "$("$thread" stop signup)" = "STOPPED signup" ] || fail "thread.sh stop did not print STOPPED signup"
[ -z "$(row_of signup)" ] && [ -z "$(thread_pane signup)" ] || fail "thread.sh stop left the row or the agent"
[ -d "$wtb/.git" ] || [ -f "$wtb/.git" ] || fail "thread.sh stop removed the coordination worktree"
"$thread" stop signup | grep -q '^FAILED no thread for build signup' || fail "thread.sh stopped an unknown thread"
"$thread" launch signup "$app" "$tmp/brief-a.md" | grep -q '^LAUNCHED signup ' || fail "thread.sh did not reuse the existing coordination worktree"

# --- thread.sh: started from a branch ------------------------------------------------------------------------
# The base defaults to the checkout's current branch; an unpushed branch lands locally.
git -C "$app" checkout -q -b feat-x
(cd "$app" && printf 'feat\n' > FEAT.md && git add . && git commit -qm feat)
out=$("$thread" launch c "$app" "$tmp/brief-a.md" || true)
[[ $out =~ ^LAUNCHED\ c\ base=feat-x@[0-9a-f]{7}\ landing=local$ ]] || fail "thread.sh did not launch from the current, unpushed branch: $out"
wtc="$tmp/proj/app-orch-c"
[ "$(git -C "$wtc" rev-parse HEAD)" = "$(git -C "$app" rev-parse feat-x)" ] || fail "thread.sh did not branch from the local feat-x"
grep -qx 'LANE-BASE: orchestration/c' "$wtc/.orchestration/thread.md" && grep -qx 'BASE-REF: feat-x' "$wtc/.orchestration/thread.md" || fail "thread.sh recorded the wrong base for a local build"
"$thread" launch d "$app" "$tmp/brief-a.md" --landing pr | grep -q '^FAILED --landing pr needs feat-x on origin with nothing unpushed' || fail "thread.sh accepted pr landing for an unpushed branch"
git -C "$app" checkout -q --detach
"$thread" launch d "$app" "$tmp/brief-a.md" | grep -q '^FAILED .* is on a detached HEAD; pass --base' || fail "thread.sh guessed a base on a detached HEAD"
git -C "$app" checkout -q main
# A branch on origin with unpushed local commits starts from the local branch and lands locally.
git -C "$app" checkout -q -b dev origin/dev
(cd "$app" && printf 'local\n' > LOCAL.md && git add . && git commit -qm local)
out=$("$thread" launch e "$app" "$tmp/brief-a.md" || true)
[[ $out == *"base=dev@"*" landing=local" ]] && [ -f "$tmp/proj/app-orch-e/LOCAL.md" ] || fail "thread.sh dropped unpushed commits on a branch that is on origin: $out"
"$thread" stop e >/dev/null
git -C "$app" checkout -q main
# A local branch behind origin starts from origin, which has the newer commits.
(cd "$tmp/app-seed" && git checkout -q main && printf 'more\n' > MORE.md && git add . && git commit -qm more && git push -q origin main)
out=$("$thread" launch d "$app" "$tmp/brief-a.md" || true)
[[ $out == *"landing=pr" ]] && [ -f "$tmp/proj/app-orch-d/MORE.md" ] || fail "thread.sh did not start a stale local branch from origin: $out"
# No origin at all, then an origin that can't be fetched: both land locally, and the second warns.
git init -q -b trunk "$tmp/proj/solo"
(cd "$tmp/proj/solo" && printf 's\n' > s.txt && git add . && git commit -qm s)
out=$("$thread" launch s1 "$tmp/proj/solo" "$tmp/brief-a.md" || true)
[[ $out == *"base=trunk@"*" landing=local" ]] || fail "thread.sh did not land locally without an origin: $out"
git -C "$tmp/proj/solo" remote add origin "$tmp/no-such-origin.git"
out=$("$thread" launch s2 "$tmp/proj/solo" "$tmp/brief-a.md" 2>"$tmp/s2.err" || true)
[[ $out == *"landing=local" ]] && grep -q 'warning: git fetch origin failed' "$tmp/s2.err" || fail "thread.sh did not carry on past a failed fetch: $out"

# --- thread.sh check: local git identities ----------------------------------------------------------------------
[ "$(cd "$tmp/plain" && "$thread" check --all)" = OK ] || fail "thread.sh check did not print OK with nothing to report"
# A local git identity that differs from the global one is reported once per repository; an equal one is not.
printf '[user]\n\temail = owner@example.com\n' > "$HOME/.gitconfig"
git -C "$app" config user.email test@example.com
out=$(cd "$tmp/plain" && "$thread" check --all)
[ "$(printf '%s\n' "$out" | grep -c '^IDENTITY ')" = 1 ] && printf '%s\n' "$out" | grep -q "^IDENTITY $app user.email=test@example.com (global owner@example.com): " \
  || fail "thread.sh check did not report a local git identity once: $out"
(cd "$app" && "$thread" check) | grep -q "^IDENTITY $app " || fail "thread.sh check missed this repository's identity"
[ "$(cd "$tmp/proj/solo" && "$thread" check)" = OK ] || fail "thread.sh check reported another repository's identity"
git -C "$app" config user.name tester
(cd "$tmp/plain" && "$thread" check --all) | grep -q "^IDENTITY $app user.name=tester (global none): " || fail "thread.sh check did not report a local name with no global one"
git -C "$app" config --unset user.name
git -C "$app" config user.email owner@example.com
[ "$(cd "$tmp/plain" && "$thread" check --all)" = OK ] || fail "thread.sh check reported a local identity equal to the global one"
git -C "$app" config --unset user.email
rm "$HOME/.gitconfig"

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
"$thread" integrate c | grep -q '^FAILED .* is on main, not feat-x' || fail "thread.sh integrated into the wrong branch"
git -C "$app" checkout -q feat-x
out=$("$thread" integrate c || true)
[[ $out =~ ^INTEGRATED\ c\ feat-x@[0-9a-f]{7}\ \(fast-forward\)$ ]] && [ -f "$app/L1.md" ] || fail "thread.sh integrate did not fast-forward: $out"
(cd "$app" && printf 'owner\n' > OWNER.md && git add . && git commit -qm owner)
(cd "$wtc" && printf 'c2\n' > C2.md && git add C2.md && git commit -qm c2)
out=$("$thread" integrate c || true)
[[ $out == *"(merge)" ]] && [ -f "$app/C2.md" ] && [ -f "$app/OWNER.md" ] || fail "thread.sh integrate did not merge a moved base: $out"
(cd "$app" && printf 'a\n' > CLASH.md && git add . && git commit -qm a)
(cd "$wtc" && printf 'b\n' > CLASH.md && git add CLASH.md && git commit -qm b)
"$thread" integrate c | grep -q '^FAILED merging orchestration/c into feat-x conflicts in: CLASH.md' || fail "thread.sh integrate hid a conflict"
[ -z "$(git -C "$app" status --porcelain --untracked-files=no)" ] || fail "thread.sh integrate left a half-done merge"
printf 'dirty\n' >> "$app/FEAT.md"
"$thread" integrate c | grep -q '^FAILED .* has uncommitted changes' || fail "thread.sh integrated over uncommitted changes"
git -C "$app" checkout -q FEAT.md
"$thread" integrate d | grep -q '^FAILED d lands by pull request' || fail "thread.sh integrated a pull-request build"
sed -i "s#^CHECKOUT: .*#CHECKOUT: $tmp/proj/solo#" "$wtc/.orchestration/thread.md"
"$thread" integrate c | grep -q "^FAILED $tmp/proj/solo is not a checkout of $app" || fail "thread.sh integrated into another repository"

# --- thread.sh close ------------------------------------------------------------------------------------------
# c's branch still holds the CLASH commit that integrate refused, so close refuses too.
"$thread" close c | grep -q '^FAILED orchestration/c holds work that feat-x lacks in: CLASH.md' || fail "thread.sh closed a build with unlanded work"
[ -d "$wtc" ] || fail "thread.sh close removed a worktree it refused to close"
# Files git ignores in the coordination worktree are evidence too, except dependency folders.
printf '.eval-runs/\n.claude/agent-memory/\nnode_modules/\n' >> "$app/.git/info/exclude"
mkdir -p "$wtc/.eval-runs/r1" "$wtc/.claude/agent-memory" "$wtc/node_modules/x"
printf 'run\n' > "$wtc/.eval-runs/r1/out.md"; printf 'memory\n' > "$wtc/.claude/agent-memory/x.md"; printf 'dep\n' > "$wtc/node_modules/x/i.js"
"$here/scripts/mail.sh" send c/main --from c/thread "STATUS: done - c" >/dev/null
panec=$(thread_pane c); wsc=$(row_of c | cut -f4)
out=$("$thread" close c --force || true)
[[ $out =~ ^CLOSED\ c\ archive=$ORCHESTRATION_HOME/archive/c-[0-9T]+Z\ lanes\ still\ present:\ .*app-wt-l1 ]] || fail "thread.sh close printed: $out"
arch=${out#*archive=}; arch=${arch%% *}
[ -f "$arch/thread.md" ] || fail "thread.sh close did not archive .orchestration"
[ -n "$(ls "$arch/mail/main/new")" ] && [ ! -e "$ORCHESTRATION_HOME/mail/c" ] || fail "thread.sh close did not move the build's mail into the archive"
[ -f "$arch/ignored/.eval-runs/r1/out.md" ] && [ -f "$arch/ignored/.claude/agent-memory/x.md" ] || fail "thread.sh close did not archive the ignored files"
[ -e "$arch/ignored/node_modules" ] && fail "thread.sh close archived node_modules"
[ -e "$arch/ignored/.orchestration" ] && fail "thread.sh close archived .orchestration twice"
[ ! -e "$wtc" ] && ! git -C "$app" rev-parse --verify -q orchestration/c >/dev/null || fail "thread.sh close left the worktree or the branch"
[ -z "$(row_of c)" ] || fail "thread.sh close left the registry row"
grep -qx "pane close $panec" "$MOCK_DIR/herdr.log" && grep -qx "workspace close $wsc" "$MOCK_DIR/herdr.log" || fail "thread.sh close did not close the thread's pane and the build's workspace"
# A pull-request build whose work landed by squash: different commits, same files on the base.
wtd="$tmp/proj/app-orch-d"
(cd "$wtd" && printf 'plan\n' > PLAN.md && git add PLAN.md && git commit -qm plan)
"$thread" close d | grep -q '^FAILED orchestration/d holds work that origin/main lacks in: PLAN.md' || fail "thread.sh closed a pull-request build before its work landed"
(cd "$tmp/app-seed" && git pull -q origin main && printf 'plan\n' > PLAN.md && git add PLAN.md && git commit -qm "plan (#9)" && git push -q origin main)
"$thread" close d | grep -q '^CLOSED d ' || fail "thread.sh did not recognise squash-landed work"
# A build the registry no longer lists closes by its worktree, with the base given.
git -C "$app" worktree add -q -b orchestration/z "$tmp/proj/app-orch-z" main
"$thread" close --worktree "$tmp/proj/app-orch-z" | tee "$tmp/z.out" | grep -q '^FAILED no record of .* base; pass --base' || fail "thread.sh closed an unrecorded build without a base: $(cat "$tmp/z.out")"
# When git can't list the ignored files, close keeps the worktree.
idx="$(git -C "$tmp/proj/app-orch-z" rev-parse --absolute-git-dir)/index"; cp "$idx" "$tmp/z.index.bak"; printf 'corrupt' > "$idx"
out=$("$thread" close --worktree "$tmp/proj/app-orch-z" --base main --force || true)
[[ $out =~ ^FAILED\ refusing:\ git\ status\ failed\ in\ .*app-orch-z.*nothing\ was\ removed\ \(archive\ at\ [^$'\n']*\)$ ]] || fail "thread.sh close carried on, or printed more than one line, when git status failed: $out"
[ -d "$tmp/proj/app-orch-z" ] || fail "thread.sh close removed a worktree it could not list"
cp "$tmp/z.index.bak" "$idx"
"$thread" close --worktree "$tmp/proj/app-orch-z" --base main | grep -q '^CLOSED z ' || fail "thread.sh did not close an unregistered build"
"$thread" close --worktree "$app" | grep -q 'is on .*, not orchestration/<build>' || fail "thread.sh closed a checkout that is not a coordination worktree"
"$thread" close t-nope | grep -q '^FAILED no thread for build t-nope' || fail "thread.sh closed an unknown thread"

echo "orchestration tests passed"
