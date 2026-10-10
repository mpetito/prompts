#!/usr/bin/env bash
# Offline checks for the orchestration-ops helpers and hooks. Uses a throwaway directory; needs bash, jq, python3.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }
cd "$tmp"
mkdir .orchestration
cat > .orchestration/state.md <<'STATE'
# Orchestrator state: test

## Lanes

| Lane | Agent | PR | Head SHA | Next action |
| --- | --- | --- | --- | --- |
| alpha | codex | #1 | abc1234 | review |
| beta | opus | #2 | def5678 | land |

## Log

- 2026-10-01T00:00Z started
STATE

# state.sh
"$here/scripts/state.sh" log "merged #2" >/dev/null
tail -1 .orchestration/state.md | grep -Eq '^- [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}Z merged #2$' || fail "state.sh log did not append a stamped line"
"$here/scripts/state.sh" set beta "Head SHA" 9999999 >/dev/null
grep -q '^| beta | opus | #2 | 9999999 | land |$' .orchestration/state.md || fail "state.sh set did not replace the cell"
grep -q '^| alpha | codex | #1 | abc1234 | review |$' .orchestration/state.md || fail "state.sh set touched another row"
"$here/scripts/state.sh" set gamma "Head SHA" 1 >/dev/null 2>&1 && fail "state.sh set accepted an unknown lane"
"$here/scripts/state.sh" backup >/dev/null
ls .orchestration/state.*.md >/dev/null || fail "state.sh backup wrote nothing"

# decisions.sh
"$here/scripts/decisions.sh" add "Ship the banner" "blocks the demo" "lane w3" "ship it" 0 >/dev/null
"$here/scripts/decisions.sh" add "Rename the table" "nothing" "none" "keep the name" 48 >/dev/null
[ "$("$here/scripts/decisions.sh" list | wc -l)" = 2 ] || fail "decisions.sh list should show two items"
"$here/scripts/decisions.sh" due | grep -q '^- D1 ' || fail "decisions.sh due should include the expired item"
"$here/scripts/decisions.sh" due | grep -q '^- D2 ' && fail "decisions.sh due included a future item"
"$here/scripts/decisions.sh" close D1 "default applied" >/dev/null
[ "$("$here/scripts/decisions.sh" list | wc -l)" = 1 ] || fail "decisions.sh close left the item open"
grep -q '^- D1 .*closed .*default applied$' .orchestration/decisions.md || fail "decisions.sh close did not record the outcome"

# guard-bash.sh
denies() { printf '%s' "$1" | jq -Rs '{tool_input:{command:.}}' | "$here/hooks/guard-bash.sh" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null; }
denies 'pkill -f vite' || fail "guard-bash should deny pkill -f"
denies 'git worktree remove ../wt --force' || fail "guard-bash should deny git worktree remove"
denies 'git -C /repo worktree remove ../wt' || fail "guard-bash should deny git -C worktree remove"
denies 'rm -rf .orchestration/lanes/m1' || fail "guard-bash should deny deleting lane evidence"
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

# guard-timestamps.py
printf 'state at 10:00Z\n' > .orchestration/notes.md
edit() { jq -n --arg p "$tmp/.orchestration/notes.md" --arg s "$1" '{tool_input:{file_path:$p,new_string:$s}}' | python3 -I "$here/hooks/guard-timestamps.py"; }
edit "approved at 14:30Z" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null || fail "timestamps hook should deny a new clock time"
edit "stopped 07:3xZ" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null || fail "timestamps hook should deny an estimated time"
[ -z "$(edit "see 10:00Z above")" ] || fail "timestamps hook denied a time already in the file"
edit "resumed 2026-10-05T18:16Z" | jq -e '.hookSpecificOutput.permissionDecision == "deny"' >/dev/null || fail "timestamps hook should deny a hand-typed ISO time"
out=$(jq -n --arg s "at 14:30Z" '{tool_input:{file_path:"/repo/docs/plan.md",new_string:$s}}' | python3 -I "$here/hooks/guard-timestamps.py")
[ -z "$out" ] || fail "timestamps hook fired outside .orchestration"

echo "orchestration-ops tests passed"
