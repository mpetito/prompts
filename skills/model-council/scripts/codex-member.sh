#!/usr/bin/env bash
# Run the Codex council member once, read-only, on a prompt file, and print one line:
#   MEMBER done|failed|timeout|malformed member=codex model=<id> session=<id> ...
#   codex-member.sh <repo> <prompt file> <answer file> --model <id> [--effort <level>] [--resume <session id>]
#                   [--timeout <duration, default 20m>]
# Run it with the host's background option so its exit wakes the coordinator. The event stream goes to
# <answer file without .md>.jsonl; pass the printed session to --resume for the member's next round.
set -euo pipefail
usage='usage: codex-member.sh <repo> <prompt file> <answer file> --model <id> [--effort <level>] [--resume <session id>] [--timeout <duration>]'
[ $# -ge 3 ] || { echo "$usage" >&2; exit 1; }
repo=$1; prompt=$2; out=$3; shift 3
model=""; effort=""; resume=""; timeout_for=20m
while [ $# -gt 0 ]; do
  [ $# -ge 2 ] || { echo "$1 needs a value; $usage" >&2; exit 1; }
  case $1 in
    --model) model=$2 ;;
    --effort) effort=$2 ;;
    --resume) resume=$2 ;;
    --timeout) timeout_for=$2 ;;
    *) echo "unknown option $1; $usage" >&2; exit 1 ;;
  esac
  shift 2
done
[ -n "$model" ] || { echo "--model is required: pick a high-capability model from 'codex debug models'" >&2; exit 1; }
case ${model,,} in
  *opus*|*sonnet*|*haiku*|*fable*|*claude*) echo "$model is an Anthropic model; the Codex member needs a Codex model ID" >&2; exit 1 ;;
esac
[ -d "$repo" ] || { echo "no repository at $repo" >&2; exit 1; }
[ -f "$prompt" ] || { echo "no prompt at $prompt" >&2; exit 1; }
command -v codex >/dev/null || { echo "codex is not on PATH" >&2; exit 1; }
mkdir -p "$(dirname "$out")"
repo=$(realpath "$repo"); prompt=$(realpath "$prompt"); out=$(realpath -m "$out")
events=${out%.md}.jsonl
rm -f "$out"  # a stale answer from an earlier run must not survive this one

# Read-only on both paths. `codex exec resume` takes no --sandbox or --cd, so the sandbox is also a config
# override and the command runs from inside the repository; without both, a resumed member runs under the
# user's own Codex default. --ignore-user-config skips $CODEX_HOME/config.toml (auth still loads), so a
# member does not depend on the user's servers, plugins or defaults. Never --ephemeral: nothing to resume.
opts=(--ignore-user-config -c 'sandbox_mode="read-only"' --model "$model" --json --output-last-message "$out")
[ -n "$effort" ] && opts+=(-c "model_reasoning_effort=\"$effort\"")
if [ -n "$resume" ]; then args=(exec resume "$resume" "${opts[@]}" -)
else args=(exec --cd "$repo" --sandbox read-only "${opts[@]}" -); fi

set +e
(cd "$repo" && timeout --kill-after=30 "$timeout_for" codex "${args[@]}" < "$prompt") > "$events" 2> "${out%.md}.log"
code=$?
set -e

session=$resume
[ -n "$session" ] || session=$(grep -o '"thread_id": *"[^"]*"' "$events" | head -n1 | sed -E 's/.*"([^"]*)"$/\1/' || true)
line="member=codex model=$model session=${session:-none}"
# A failed or timed-out member leaves no answer file, so tally.sh can never count it.
case $code in
  0) ;;
  124|137) rm -f "$out"; echo "MEMBER timeout $line after $timeout_for; log ${out%.md}.log"; exit 0 ;;
  *) rm -f "$out"; echo "MEMBER failed $line exit=$code; log ${out%.md}.log"; exit 0 ;;
esac

# The last value of a key: the answer may quote the template before its own block.
field() { { grep -iE "^[[:space:]]*$1:" "$out" 2>/dev/null || true; } | tail -n1 | sed -E 's/^[^:]*:[[:space:]]*//; s/[[:space:]]+$//'; }
stance=$(field stance); disposition=$(field disposition)
if [ ! -s "$out" ] || [ -z "$stance" ] || [ -z "$disposition" ]; then
  echo "MEMBER malformed $line out=$out (no answer block)"; exit 0
fi
echo "MEMBER done $line stance=$stance disposition=$disposition out=$out"
