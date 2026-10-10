#!/usr/bin/env bash
# PreToolUse hook for SendMessage in an orchestration thread. A message to MAIN must follow the protocol
# (scripts/check-message.sh --up) and go to MAIN's recorded address: its name, or its socket when the name no
# longer resolves, both from .orchestration/thread.md, which MAIN keeps current. A message that breaks either
# rule is denied with the reason, so the thread rewrites it. Every message to MAIN that passes is copied to
# .orchestration/outbox.md, where MAIN's thread.sh check reads it, so a message that never arrives is still read.
# Workers' messages (input with agent_id), and sessions with no state file, pass silently.
set -u
here=$(dirname "$0")
. "$here/../scripts/lib.sh"
input=$(cat)
[ -z "$(printf '%s' "$input" | jq -r '.agent_id // empty')" ] || exit 0
cwd=$(printf '%s' "$input" | jq -r '.cwd // empty')
[ -n "$cwd" ] || exit 0
top=$(toplevel "$cwd") || exit 0
[ -f "$top/.orchestration/state.md" ] || exit 0
main=$(main_name "$top")
sock=$(thread_field "$top" MAIN-SOCKET)
to=$(printf '%s' "$input" | jq -r '.tool_input.to // empty' | sed -E 's/[[:space:]]+\[[^]]*\]$//')
message=$(printf '%s' "$input" | jq -r '.tool_input.message // ""')
to_main=0
{ [ -n "$main" ] && [ "$to" = "$main" ]; } && to_main=1
{ [ -n "$sock" ] && [ "$to" = "$sock" ]; } && to_main=1
if [ "$to_main" = 1 ]; then
  verdict=$(printf '%s' "$message" | "$here/../scripts/check-message.sh" --up) \
    || deny "This message to MAIN breaks the thread protocol: ${verdict#BAD }. Rewrite it: first line 'STATUS: <working|need-decision|blocked|rotating|done> - <summary>', at most 10 lines; a need-decision names Options:, Default:, and 'applies at <UTC>' or owner-before."
  # A resend to the socket after the name failed repeats the last entry; the hash keeps the outbox to one copy.
  outbox="$top/.orchestration/outbox.md"
  hash=$(printf '%s' "$message" | md5sum | cut -c1-12)
  last=$(grep '^=== ' "$outbox" 2>/dev/null | tail -1 | sed -n 's/.* #\([0-9a-f]*\)$/\1/p')
  [ "$last" = "$hash" ] || printf '=== %s to %s #%s\n%s\n\n' "$(utc_now)" "$to" "$hash" "$message" >> "$outbox"
  exit 0
fi
# A status line to any other address means MAIN's address came from somewhere other than the record.
if { [ -n "$main" ] || [ -n "$sock" ]; } && printf '%s\n' "$message" | head -1 | grep -q '^STATUS:'; then
  deny "This reads as a message to MAIN, but $to is not MAIN's recorded address. Send it to \"$main\" (state.sh main); if that name no longer resolves, to ${sock:-the MAIN-SOCKET in .orchestration/thread.md} (state.sh main --socket). Never reuse an address from an earlier message: it goes stale when MAIN restarts or forks."
fi
exit 0
