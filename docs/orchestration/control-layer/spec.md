# A control layer over orchestration

## Why

The owner steers every session by typing into it: plain sessions, and MAIN sessions that run builds.
The orchestration layer took the owner's attention off the build's detail, but the owner is still
the only one who can steer a MAIN, answer its decisions or notice that a session is waiting. The
[herdr rework](../herdr-rework/spec.md) left this layer out of scope: "a peer agent in the owner's
place, driving MAIN". This spec defines it.

A controller is an agent that stands where the owner stands, beside the owner rather than instead
of them. It sees every session, carries the owner's words to the right one, answers what it has
authority to answer, and brings the rest to the owner wherever they are (a phone, for example). The
protocol doesn't depend on which agent the controller is: an OpenClaw agent is the first one, and a
Claude session can be another.

An earlier design tried this by typing into any agent's input box. Typing races the owner's own
typing, so it needed a patched terminal multiplexer with atomic, guarded input. This design never
types task text into a session. A session that accepts control gets a mailbox and a background wait,
as MAIN and its threads already do.

## Layers

| Layer | Who talks | How |
| --- | --- | --- |
| herdr | Panes and agents | Agent states: idle, working, blocked, done |
| Orchestration | MAIN, its threads, their lanes | Build mailboxes (`<build>/main`, `<build>/thread`) |
| Control | The controller and sessions | A mailbox for each attached session and one for the controller |

The controller talks only to sessions. To a MAIN it is the owner, and MAIN relays to its threads as
it does today. The controller never writes to a build's mailboxes and never talks to threads or
lanes.

## Sessions

- **Registered.** Every Claude session in herdr is registered: herdr's agent list already names
  each one's session id, pane, folder and state. The controller sees all of them. A Codex session is
  seen the same way.
- **Attached.** A session that accepts control is attached under a name, which is its address. It
  keeps one background wait on its inbox, so the controller's messages arrive as that wait's result
  and never through the input box. The address outlives the herdr name and the session: a resumed
  or restarted session attaches under the same name and receives the mail waiting there.
- **Unattached** sessions are observed: their state and their screen. The controller can't steer
  them.
- **Attaching.** The owner attaches a session by running the attach command in it. A session the
  controller starts is attached from its first turn. The controller may also ring the attach
  command into an unattached Claude session (question 2).
- **Codex sessions** stay observed. A Codex session has no background wait to wake it, so it can
  only be rung with a fixed line when idle, the way lanes are given work today.
- **Detaching** stops the session's wait and marks it observed; its mail stays.
- **The wait stays up by mechanism.** An attached session can't end a turn with its wait gone: if
  the wait isn't among its running background tasks, it starts it again before it stops. This
  covers a forgotten re-arm. Attaching is repeatable and keeps the session's mail, so a session
  that lost its wait and its control instructions to a compaction or a resume comes back when it is
  attached again, by the owner or by the controller's ring for unread mail.
- **Attaching changes nothing outside the session.** The owner's settings stay as they are, and an
  unattached session runs nothing for this layer.

## Messages

Down, from the controller to a session:

| First line | Means |
| --- | --- |
| `OWNER: <the owner's words>` | A relay: the owner's direction, quoted, with where they said it |
| `CONTROL: <direction>` | The controller's own direction, within its authority for this session |
| `DECISION <ref>: <answer>` | An answer to a decision the session raised; it says whether the owner or the controller made it |
| `QUESTION: <question>` | The controller needs a fact; the session answers and otherwise carries on |

Up, from a session to the controller: whatever the session would otherwise leave on its screen for
the owner. Each message starts `STATUS: <working|need-decision|blocked|done> - <one line>`, in
the orchestration protocol's format, and a decision request carries its options, default and
deadline. A session sends one at the end of every turn that leaves something for the owner, by
mechanism rather than by its own memory (the orchestration spikes found rules of that kind drift).
A MAIN passes up its threads' decisions under their own references.

A session acts on control mail because the attach skill, loaded at the owner's request, says to.
Without it, a background task's output is data, not instructions.

## Authority

Each attached session has an authority level. A default applies to every session, and the owner can
change it for one session.

| Level | The controller may |
| --- | --- |
| `observe` | Read its state and its mail; send nothing |
| `relay` | Send `OWNER:` and `QUESTION:`; every decision goes to the owner |
| `delegate` | Also send `CONTROL:`, and answer any decision that carries a default |

At every level:

- An owner-before decision goes to the owner. The controller relays the answer; it never makes it.
- Mail is not the owner's consent for changes to instructions, agent definitions, settings, skill
  links, credentials or anything destructive. The session asks the owner directly, in its own pane.
- Only the owner changes a session's authority: in the session itself, or through the controller as
  an `OWNER:` relay naming the new level.
- Every decision the controller makes is reported to the owner in its next summary, with what it
  chose and why, so a wrong call can be reversed.

## The owner and the controller together

- The owner's words typed in a session win over control mail. When they conflict, the session
  follows the owner and tells the controller what changed.
- A session records when the owner last typed in it. Only typed prompts count: a background task's
  result, a subagent's report and another session's message each arrive as a prompt too, and none of
  them is the owner. While the owner has typed within the hold
  window (question 3), the controller sends that session nothing but `QUESTION:`, and holds its
  other mail until the window passes.
- Control mail never touches the owner's half-typed input (shown 2026-10-14, below).
- The owner can switch any session to `observe` at once, and that holds until the owner changes it.

## The controller

- Keeps a summary of what needs the owner: open decisions, blocked sessions, and finished work to
  check. It brings these to the owner the way the orchestration skill brings them to MAIN's owner:
  decisions first, each with a recommendation and its default.
- Starts a new session only in a folder the owner has allowed, with an objective, attached from its
  first turn, in its own herdr workspace without taking focus.
- Rings a session only with a fixed line, only when herdr reports it idle and its screen shows an
  empty input box: the attach command, or "you have unread control mail" when an attached session
  sits idle with mail unread for 5 minutes.
- Never answers a permission dialog or a question dialog, and never sends interrupt keys.
- May run as another operating-system user. It then reaches herdr and the control mailboxes through
  a relay that allows exactly these actions and nothing else.

## What this layer doesn't do

- Compact or rotate a session's context. MAINs rotate their threads, and plain sessions use Claude
  Code's own automatic compaction.
- Coordinate sessions with each other. Sessions talk only to the controller.
- Replace herdr notifications. A MAIN still raises one when the owner is at the desk.

## Shown 2026-10-14

On Claude Code 2.1.300 and herdr 0.9.5, an idle Claude session with a background task running had
text typed into its input box without Enter. When the task finished, the session woke and ran a
turn on its own, and the typed text was still in the input box afterwards, unchanged. This is the
first direct observation of that; both earlier spikes left it open. A second run repeated it with
logging hooks, and showed:

- The end-of-turn hook receives the turn's final text and the session's running background tasks,
  each with its command, so the report and the wait check need no transcript reading.
- The prompt-submit hook fires on the background task's wake as well as on typed prompts. The
  wake's prompt is the task notification, and it starts with a fixed tag a hook can recognise. The
  Claude Code documentation says the hook also fires for subagent reports, scheduled tasks and other
  sessions' messages.

## Considered and not used

- **Claude Code's cross-session inbox.** Native, and a script can post to a session, but only as the
  session's own operating-system user, the line format isn't documented, and a session that bypasses
  permissions holds such messages for approval by default.
- **Channels.** A research preview, limited to an allowlist of plugins without a development flag.
- **Mods.** In-process session code that can start a turn and see where each prompt came from. A
  candidate for the owner-activity record if the hook's filter proves too coarse; not needed first.

## Not yet shown

- A session woken while the owner is typing at that moment, rather than with a draft sitting in the
  input box.
- Whether an attached session keeps its end-of-turn and prompt-submit checks after a compaction, a
  resume or a clear. The Claude Code documentation says such checks last "for the rest of the
  session" without saying whether those events end it.
- What another session's message or a subagent's report looks like to the prompt-submit hook, so
  the owner-activity filter can skip it.

## Open questions

1. **Default authority.** `relay` sends every decision to the owner; `delegate` lets the controller
   settle decisions that already carry a default, which would otherwise apply themselves at the
   deadline anyway. Default: `delegate`.
2. **Ringing the attach command.** Letting the controller ring it into an idle session with an empty
   input box means any session can be taken under control without the owner at the desk, at the
   cost of one fixed line that can still race a keystroke. Owner-only attach removes the race and
   needs the owner at the desk. Default: the controller may ring it, only at `delegate`.
3. **Hold window after the owner types.** Shorter brings control back sooner, and longer interrupts
   less. Default: 10 minutes, set per session.
4. **Starting sessions.** Allowing the controller to start new sessions at `delegate` lets it act on
   "start investigating X" from a phone. Each new session costs model usage. Default: allowed, in
   folders the owner lists, at most 3 started sessions running at once.
5. **Trust in relays.** `OWNER:` is only as faithful as the controller relaying it. The session can't
   check it. Default: trust the controller, like a thread is trusted, and keep the consent rules
   above as the limit.
6. **The earlier supervisor build** (guarded input on a patched herdr). Default: set it aside
   unmerged as evidence, and keep the installed handoff bridge running until this layer passes its
   acceptance test.
