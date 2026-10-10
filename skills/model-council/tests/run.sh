#!/usr/bin/env bash
# Tests for the council scripts with a mocked codex CLI; no model is called. Run: bash skills/model-council/tests/run.sh
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
failures=0
fail() { echo "FAIL: $1"; failures=$((failures + 1)); }
mkdir -p "$tmp/bin" "$tmp/repo" "$tmp/out"
export PATH="$tmp/bin:$PATH"

cat > "$tmp/bin/codex" <<'MOCK'
#!/usr/bin/env bash
printf '%s\n' "cwd=$PWD" "$@" > "$MOCK_ARGS"
out=""; prev=""
for a in "$@"; do [ "$prev" = --output-last-message ] && out=$a; prev=$a; done
case ${MOCK_CODEX:-ok} in
  ok) echo '{"type":"thread.started","thread_id":"t-123"}'
      printf 'Reasoning here.\nstance: initial\ndisposition: defect\naction: add the tenant id to the cache key\n' > "$out" ;;
  quoted) printf 'stance: initial | agree | revise | hold\ndisposition: <one of>\n...\nstance: hold\ndisposition: false-positive\naction: no change\n' > "$out" ;;
  prose) echo 'I think it is fine.' > "$out" ;;
  fail) exit 3 ;;
  slow) sleep 5 ;;
esac
MOCK
chmod +x "$tmp/bin/codex"
printf 'packet\n' > "$tmp/prompt.md"
export MOCK_ARGS="$tmp/args"
member() { "$here/scripts/codex-member.sh" "$tmp/repo" "$tmp/prompt.md" "$tmp/out/a.md" "$@"; }

# --- codex-member.sh: read-only on a fresh run and on a resumed one ---------------------------------------------
line=$(member --model m1 --effort high)
[[ $line == "MEMBER done member=codex model=m1 session=t-123 stance=initial disposition=defect out="* ]] || fail "fresh run line: $line"
grep -qx 'read-only' "$tmp/args" && grep -qx -- '--sandbox' "$tmp/args" || fail "fresh run lacks --sandbox read-only"
grep -qx 'sandbox_mode="read-only"' "$tmp/args" || fail "fresh run lacks the read-only config override"
grep -qx 'model_reasoning_effort="high"' "$tmp/args" || fail "fresh run dropped the effort"
grep -qx -- '--ignore-user-config' "$tmp/args" || fail "fresh run loaded the user's Codex config"
grep -qx "cwd=$(realpath "$tmp/repo")" "$tmp/args" || fail "fresh run did not start inside the repository"
line=$(member --model m1 --resume t-123)
grep -qx 'resume' "$tmp/args" && grep -qx 't-123' "$tmp/args" || fail "resume did not call codex exec resume <id>"
grep -qx 'sandbox_mode="read-only"' "$tmp/args" || fail "resume dropped the read-only sandbox"
grep -qx 'm1' "$tmp/args" || fail "resume dropped the model"
grep -qx -- '--ignore-user-config' "$tmp/args" || fail "resume loaded the user's Codex config"
grep -qx "cwd=$(realpath "$tmp/repo")" "$tmp/args" || fail "resume did not run inside the repository"
[[ $line == *"session=t-123"* ]] || fail "resume line lost the session: $line"
for run in fresh resume; do
  if [ $run = resume ]; then member --model m1 --resume t-123 >/dev/null; else member --model m1 >/dev/null; fi
  grep -Eq 'workspace-write|danger-full-access|dangerously|--ephemeral|network_access' "$tmp/args" && fail "$run run passed a write, network, bypass or ephemeral flag"
done

# --- codex-member.sh: outcomes -------------------------------------------------------------------------------------
[[ $(MOCK_CODEX=quoted member --model m1) == *"stance=hold disposition=false-positive"* ]] || fail "did not read the last answer block"
[[ $(MOCK_CODEX=prose member --model m1) == "MEMBER malformed"* ]] || fail "an answer without a block was not malformed"
[[ $(MOCK_CODEX=fail member --model m1) == "MEMBER failed"*"exit=3"* ]] || fail "a failing codex was not reported"
[[ $(MOCK_CODEX=slow member --model m1 --timeout 1s) == "MEMBER timeout"* ]] || fail "a slow codex was not reported as a timeout"
member >/dev/null 2>&1 && fail "ran without --model"
member --model opus >/dev/null 2>&1 && fail "accepted an Anthropic model for Codex"

# --- tally.sh ------------------------------------------------------------------------------------------------------
ans() { printf 'Some reasoning.\nstance: %s\ndisposition: %s\naction: %s\ncrux: x\n' "$2" "$3" "$4" > "$tmp/$1"; }
tally() { "$here/scripts/tally.sh" "$tmp/a" "$tmp/b" --exchange "$1"; }
ans a initial defect 'add the tenant id to the cache key'; ans b initial false-positive 'no change'
[[ $(tally 0) == "COUNCIL exchange next=1 of 2"* ]] || fail "blind disagreement did not go to an exchange round"
ans a initial defect 'add the tenant id to the cache key'; ans b initial defect 'partition the cache per tenant'
[[ $(tally 0) == "COUNCIL exchange"* ]] || fail "same disposition, different action was not sent to exchange"
ans a hold defect 'add the tenant id to the cache key'; ans b revise defect 'partition the cache per tenant'
[[ $(tally 2) == "COUNCIL no-consensus reason=round-cap"* ]] || fail "the round cap did not stop persistent disagreement"
ans a hold defect 'x'; ans b hold false-positive 'no change'
[[ $(tally 1) == "COUNCIL no-consensus reason=both-hold"* ]] || fail "hold/hold did not stop the council"
ans a agree defect 'add the tenant id  to the cache key'; ans b hold defect 'add the tenant id to the cache key'
[[ $(tally 1) == "COUNCIL consensus after-exchange=1 disposition=defect"* ]] || fail "identical positions were not consensus"
ans a agree false-positive 'no change'; ans b agree defect 'add the tenant id to the cache key'
[[ $(tally 1) == "COUNCIL exchange next=2"* ]] || fail "crossed agreement was taken as consensus"
ans a initial defect 'x'; : > "$tmp/b"
[[ $(tally 0) == "COUNCIL incomplete"*"no-answer"* ]] || fail "an empty answer was not incomplete"
ans a initial defect 'x'; ans b initial maybe 'x'
[[ $(tally 0) == "COUNCIL incomplete"*"disposition"* ]] || fail "an unknown disposition was not incomplete"
ans a agree defect 'x'; ans b agree defect 'x'
[[ $(tally 0) == "COUNCIL incomplete"*"blind round"* ]] || fail "an exchange stance in the blind round was accepted"
grep -qx 'MAX_EXCHANGE_ROUNDS=2' "$here/scripts/tally.sh" || fail "the round cap is not the single named constant"

[ "$failures" -eq 0 ] && echo "model-council scripts: all tests passed" || { echo "$failures failure(s)"; exit 1; }
