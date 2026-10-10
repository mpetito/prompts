#!/usr/bin/env bash
# Wait for a PR's gates on one exact head, then print one line. Exits early if the head moves.
#   watch-gates.sh <pr> <full head sha> [--check <name>] [--bot <login regex>] [--minutes <n>]
# Prints: GATES pr=<n> head=<sha7> check=<result|n/a|timeout> bot=<reviewed|n/a|timeout> unresolved_threads=<n>
#     or: MOVED pr=<n> head=<sha7> now=<sha7>
set -uo pipefail
pr=$1; head=$2; shift 2
check=""; bot=""; minutes=25
while [ $# -gt 0 ]; do
  case $1 in
    --check) check=$2; shift 2 ;;
    --bot) bot=$2; shift 2 ;;
    --minutes) minutes=$2; shift 2 ;;
    *) echo "unknown option $1" >&2; exit 1 ;;
  esac
done
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
check_result=""; bot_result=""
for _ in $(seq 1 $(( minutes * 4 ))); do
  cur=$(gh pr view "$pr" --json headRefOid --jq .headRefOid 2>/dev/null || echo "")
  if [ -n "$cur" ] && [ "$cur" != "$head" ]; then echo "MOVED pr=$pr head=${head:0:7} now=${cur:0:7}"; exit 0; fi
  if [ -n "$check" ] && [ -z "$check_result" ]; then
    st=$(gh api "repos/$repo/commits/$head/check-runs" --jq "[.check_runs[] | select(.name==\"$check\")] | if length==0 then \"none\" elif all(.status==\"completed\") then (map(.conclusion)|join(\",\")) else \"running\" end" 2>/dev/null || echo none)
    case "$st" in none|running) ;; *) check_result=$st ;; esac
  fi
  if [ -n "$bot" ] && [ -z "$bot_result" ]; then
    n=$(gh api "repos/$repo/pulls/$pr/reviews" --jq "[.[] | select(.user.login|test(\"$bot\")) | select(.commit_id==\"$head\")] | length" 2>/dev/null || echo 0)
    [ "${n:-0}" -gt 0 ] && bot_result=reviewed
  fi
  { [ -z "$check" ] || [ -n "$check_result" ]; } && { [ -z "$bot" ] || [ -n "$bot_result" ]; } && break
  sleep 15
done
owner=${repo%/*}; name=${repo#*/}
unresolved=$(gh api graphql -f query="query{repository(owner:\"$owner\",name:\"$name\"){pullRequest(number:$pr){reviewThreads(first:100){nodes{isResolved}}}}}" \
  --jq '[.data.repository.pullRequest.reviewThreads.nodes[]|select(.isResolved|not)]|length' 2>/dev/null || echo "?")
check_out=n/a; [ -n "$check" ] && check_out=${check_result:-timeout}
bot_out=n/a; [ -n "$bot" ] && bot_out=${bot_result:-timeout}
echo "GATES pr=$pr head=${head:0:7} check=$check_out bot=$bot_out unresolved_threads=$unresolved"
