# Control protocol

Protocol version: 1

How a controller and the sessions attached to it talk: the addresses, the messages, what each
authority level permits, and every subcommand of `ctl.py` with every line it prints. The controller
(an OpenClaw adapter through its relay, or a Claude session) uses only the controller subcommands.
An attached session uses the session subcommands and two mail.py commands. The session's hooks use
what [What the hooks call](#what-the-hooks-call) names, and nothing else.

`ctl.py` means `python3 "$HOME/.claude/skills/control-attach/scripts/ctl.py"` and `mail.py` means
`python3 "$HOME/.claude/skills/agent-orchestration/scripts/mail.py"`, written in full in a command.

## Contents

- Addresses and files
- Messages
- Authority
- The owner and the controller together
- Session subcommands
- Controller subcommands
- What the hooks call

## Addresses and files

`<home>` is `$ORCHESTRATION_HOME`, else `~/.orchestration`. Everything below lives under
`<home>/control/`.

- **A name** is an attached session's address. It matches `[a-z][a-z0-9_-]{0,31}`, herdr's
  agent-name pattern and mail.py's box pattern, and `attach` names the session's herdr agent after
  it. `owner` is reserved: it is the controller's address.
- **Mail** is mail.py's maildir with `--home <home>/control`, so the boxes are under
  `<home>/control/mail/`:
  - `<name>/in`: the session's inbox. The controller sends there `--from owner`.
  - `owner/in`: the controller's inbox. A session sends there `--from <name>`.
  Mail outlives the session and the attachment: nothing in this protocol deletes it.
- **A record**, `sessions/<name>.json`, one per name ever attached or started, written only by
  `ctl.py`. It holds exactly:

  | Field | Value |
  | --- | --- |
  | `pane` | The herdr pane id the session attached from, or `start` started it in |
  | `session` | herdr's session id for the pane's agent (`agent_session.value`) when `attach` last ran, or `""` before it |
  | `authority` | `observe`, `relay` or `delegate` |
  | `hold` | The hold window in minutes, a whole number, 0 for none |
  | `typed` | When the owner last typed a prompt in the session, UTC `YYYY-MM-DDTHH:MMZ`, or `""` |
  | `attached` | `true` from `attach` until `detach`, or until another name attaches from the same pane |
  | `started` | `true` when `start` started the session; it never changes after |

  A `/clear` keeps the pane and the herdr name but changes the session id and drops the session's
  hooks, so `session` is the only sign that a cleared session needs attaching again. A session's own
  subcommands find its record by `HERDR_PANE_ID`: the record that is `attached` with that `pane`.
- **A record's session** is an agent in the record's `pane`, or, while the record is attached, an
  agent with its `session` id, which a moved pane keeps. herdr gives an exited session's name to
  whichever agent asks for it next, so a name alone never ties an agent to a record. An agent's
  records: a named agent's is its name's record, when it is that record's session. An unnamed
  agent's (herdr cleared the name, or never gave one) is the attached record it is the session of,
  else every record it is: one pane can hold a record for each name it was detached or started
  under.
- **The folders file**, `folders`, written by the owner and never by `ctl.py`: one absolute folder
  per line, blank lines ignored. `start` uses a folder only when it is a listed one or inside one.
  Without the file, `start` refuses.
- **The defaults**: authority `delegate`, hold 10 minutes (spec questions 1 and 3). The default
  authority is fixed, not a setting: the owner changes one session's level, never the default.
- Times are UTC, `YYYY-MM-DDTHH:MMZ`.

## Messages

Every message is mail: plain text, never empty, its first line saying it all.

Down, from the controller to `<name>/in`, sent only by `ctl.py send` (and `start`, below):

| First line | Means | Quiet |
| --- | --- | --- |
| `OWNER: <the owner's words>` | A relay of the owner's direction, quoted, with where they said it | no |
| `CONTROL: <direction>` | The controller's own direction, within its authority | no |
| `DECISION <ref>: <answer>` | An answer to decision `<ref>`; the second line is `By: owner` or `By: controller` | no |
| `QUESTION: <question>` | The controller needs a fact; the session answers and otherwise carries on | no |

- The session acts on these because the control-attach skill says to. The owner's typed words win
  over any of them: the session follows the owner and says what changed in its next report.
- A session refuses a `DECISION` with `By: controller` for a decision it raised as owner-before, and
  raises it again. Only the session knows which of its decisions are owner-before, so no script
  tracks it.

Up, from a session to `owner/in`: the turn's final text, unchanged, sent by `ctl.py report` at the
end of every turn; and an answer to a `QUESTION:`, which the session sends at once, waking, and then
carries on:

```bash
python3 "<mail.py>" send owner/in --home "<home>/control" --from <name> "STATUS: working - <answer>"
```

An answer is never quiet. Each up message's first line is, in the orchestration protocol's format,

```text
STATUS: <working|need-decision|blocked|done> - <one line>
```

| State | When | Quiet |
| --- | --- | --- |
| `working` | Progress, a steer acted on, a decision applied | yes, except an answer to `QUESTION:`, sent with mail.py (above) |
| `need-decision` | The owner or the controller must choose; a decision request follows | no |
| `blocked` | Nothing can move without the owner or the controller; say what would unblock it | no |
| `done` | The work asked for is finished; list what the owner should check | no |

A report whose first line is anything else is sent too, quiet. A decision request is the
orchestration protocol's:

```text
STATUS: need-decision - D3 payment provider for checkout
Question: Stripe or Paddle for the first checkout slice?
Options: Stripe (cards today, tax later) | Paddle (merchant of record, 2 days more)
Default: Stripe, applies at 2026-10-10T18:00Z
Blocks: the checkout work only
```

An owner-before decision has `Default: none, owner-before`. `<ref>` is one token without spaces or
`:`. A MAIN passes up a thread's decision as `<build>/D<n>`, so two builds' `D3`s stay apart, and
relays the answer to the thread as `DECISION D<n>: …`.

## Authority

| Level | The controller may send |
| --- | --- |
| `observe` | Nothing. It reads the session's state and screen, and its mail |
| `relay` | `OWNER:`, `QUESTION:`, and a `DECISION` the owner made (`--owner`) |
| `delegate` | Also `CONTROL:`, and a `DECISION` it made itself, for a decision that carries a default |

`ctl.py send` refuses what the level doesn't permit. At every level:

- An owner-before decision goes to the owner. The controller relays the answer; it never makes it.
- Mail is not the owner's consent for changes to instructions, agent definitions, settings, skill
  links, credentials or anything destructive. The session asks the owner directly, in its own pane.
- Only the owner changes a session's level: in the session itself, or through the controller as an
  `OWNER:` relay naming the level. The session runs `ctl.py authority <level>` either way.
- Every decision the controller makes goes to the owner in its next summary, with what it chose and
  why.

## The owner and the controller together

- **The hold window.** `typed` records each prompt the owner types in an attached session. Until
  `hold` minutes after it, `send` refuses everything but `QUESTION:` with `HELD <until>`, and the
  controller sends it again after `<until>`. `typed` keeps the minute, so the window ends to the
  minute, up to 59 seconds before a full `hold` from the keystroke. A task notification, a
  subagent's report, another session's message and a ring line are not the owner typing; `typed`
  alone decides that.
- **Rings.** The controller types into a pane only a fixed line, only when herdr reports the agent
  `idle` or `done` and its visible input line is empty: `/control-attach <name>` into a Claude
  agent, `Read <file> and follow it.` into a Codex agent. Nothing else is ever typed, never into a
  session at `observe`, and no key is sent to a dialog. The input line is the screen's last line
  opening with Claude's `❯` or Codex's `›`, with the lines between it and the rule that closes
  Claude's input box, where a draft goes on. Dim text there, a placeholder or a suggested prompt,
  is not typing, and a screen that shows no input line is not known to be empty.
- **A ring never changes a level.** Into a record's session, a ring attaches only one of the
  agent's records' names: under another name the session would take that name's level, and only
  the owner sets one.
- **Never into orchestration's agents.** A ring refuses an agent with a herdr name unless it is
  that name's record's session, so a record whose name a lane later took doesn't count.
  Orchestration names its threads `<build>` and its lanes `<build>-<lane>`, the controller
  never talks to them, and attaching one would rename it out of its build's reach. Plain sessions
  and MAIN have no herdr name until they attach.
- **One controller** reads `owner/in` at a time. Two would each file what the other has not seen.

## Session subcommands

Run by the attached session in its own herdr pane. `report` and `typed` are run by its hooks.
A call with the wrong arguments prints usage on stderr and exits 1.

### `ctl.py attach <name> [--hold <minutes>]`

Attaches the session in this pane under `<name>`: names its herdr agent `<name>`, writes the record
(`attached` true), and marks any other record attached from this pane not attached. Repeatable: a
record that exists keeps its authority, hold, `typed` and `started`, and takes the agent's current
`session`; the mail waiting at `<name>/in` stays unread. A `/clear` and a resume drop the session's
hooks (a compaction keeps them), so attaching again is how a session comes back after either. A new
record gets the defaults. `--hold` sets the hold window, a plain whole number of minutes in ASCII
digits; anything else is a usage error.

| Line | Exit | When |
| --- | --- | --- |
| `WAIT <command>` | 0 | Attached. The session doesn't start the wait here: its Stop hook names `<command>` when it isn't among the running background tasks, since a wait started before a `/clear` is still running and must not be doubled |
| `REFUSED not a name: <name>` | 1 | `<name>` is outside the name pattern |
| `REFUSED owner is the controller's address` | 1 | `<name>` is `owner` |
| `REFUSED not in a herdr pane` | 1 | `HERDR_PANE_ID` is unset |
| `REFUSED <name> is held by pane <pane>` | 1 | A live herdr agent in another pane is named `<name>` |
| `REFUSED herdr: <reason>` | 1 | herdr finds no agent in this pane, can't say whether another agent holds `<name>`, refuses the rename, or replies with anything but JSON holding a result |

`<command>` is exactly

```text
python3 "<mail.py>" wait <name>/in --home "<home>/control"
```

with `<mail.py>` and `<home>` absolute real paths, not the `$HOME` form above. The session runs the
`WAIT` line's command exactly as printed, because the Stop hook matches it verbatim. The session's
read is `python3 "<mail.py>" read <name>/in --home "<home>/control"`, the same paths: on `MAIL`,
read, start the wait again, then act. `ctl.py` has no subcommand for either.

### `ctl.py detach`

Marks this pane's record not attached. Its authority, hold and mail stay. The session then stops its
wait.

| Line | Exit | When |
| --- | --- | --- |
| `DETACHED <name>` | 0 | Done |
| `REFUSED not attached` | 1 | No record is attached from this pane |

### `ctl.py authority observe|relay|delegate`

Sets this pane's session's level, on the owner's own words only.

| Line | Exit | When |
| --- | --- | --- |
| `AUTHORITY <name> <level>` | 0 | Set |
| `REFUSED not attached` | 1 | No record is attached from this pane |

### `ctl.py report`

Sends stdin, unchanged, from `<name>` to `owner/in`: waking when its first line starts
`STATUS: need-decision`, `STATUS: blocked` or `STATUS: done`, quiet otherwise.

| Line | Exit | When |
| --- | --- | --- |
| `SENT owner/in <file>` | 0 | Sent |
| (nothing) | 0 | This pane isn't attached, or stdin is empty or only whitespace |

### `ctl.py typed`

Records now as `typed`, unless stdin, trimmed, isn't the owner typing:

- a ring line, the whole prompt `/control-attach <name>` for any name, so a ring never holds the
  controller (the same text with more after it is typing);
- a prompt starting `<task-notification>` (a background task's wake), `<agent-message ` (a
  subagent's report) or `<cross-session-message ` (another session's message).

This is the one place the owner-activity rule lives. Prints nothing, ever, and exits 0, attached or
not: what a prompt-submit hook prints reaches the model.

## Controller subcommands

Run by the controller. A call with the wrong arguments prints usage on stderr and exits 1. Every
other line is on stdout. `REFUSED herdr: <reason>` (exit 1) is herdr failing or giving a reply that
isn't JSON holding a result.

### `ctl.py sessions`

One row per herdr agent, orchestration's named agents too, then one per gone record: an attached
record that no agent with its name in herdr's list is the session of. Six fields, separated by
single spaces:

```text
<target> <kind> <state> <authority> <held> <unread>
```

A gone row can share its target with a live agent's row, when another agent took the name, so a
parser keys rows on target and state together.

| Field | Value |
| --- | --- |
| `target` | The attached name, else herdr's agent name, else the pane id |
| `kind` | herdr's agent kind (`claude`, `codex`, …), `null` when herdr gives none, or `-` for a gone record |
| `state` | herdr's `agent_status` (`idle`, `working`, `blocked`, `done`, `unknown`), `null` when herdr gives none (as mail.py prints it), or `gone` |
| `authority` | The record's level when attached, else `unattached` |
| `held` | The hold's end, `YYYY-MM-DDTHH:MMZ`, while it lasts, else `-` |
| `unread` | Messages unread at `<name>/in`, or `-` when not attached |

An agent is attached when it is a Claude agent and an attached record has its herdr name and its
session id (`agent_session.value`). A Codex session never is: it has no wait to wake it, so the
controller only observes it and rings it. A cleared session keeps its pane and name under a new
id, so it shows `unattached`, and the controller rings `/control-attach <name>` into it as into any
unattached Claude session. With no rows it prints `NONE`. Exit 0.

### `ctl.py send <name> OWNER|CONTROL|QUESTION <text>` and `ctl.py send <name> DECISION <ref> <answer> [--owner]`

Sends one down message to `<name>/in` from `owner`: `<KIND>: <text>`, or for a decision
`DECISION <ref>: <answer>` and `By: owner` with `--owner`, else `By: controller`. `<text>` is one
argument and may hold several lines.

`send` checks the record alone, not herdr. Mail to a cleared session, whose record is attached under
an old session id, is sent and waits in its box until the session attaches again: the controller
sees it `unattached` in `sessions` and rings it.

| Line | Exit | When |
| --- | --- | --- |
| `SENT <name>/in <file>` | 0 | Sent |
| `HELD <until>` | 1 | Not `QUESTION`, and the owner typed within the hold window; send again after `<until>` |
| `REFUSED <name> is not attached` | 1 | No attached record has that name |
| `REFUSED <name> is at <level>` | 1 | The session's level doesn't permit this message |

### `ctl.py read`

mail.py's `read` of `owner/in`: each new message, oldest first, after a `=== <file>` line, and files
it; or `NO MAIL`. Exit 0.

### `ctl.py wait [--timeout <seconds>]`

mail.py's `wait` on `owner/in`, watching each attached session's herdr agent and its inbox
(`--watch <name>=<name>/in,…`). One line, exit 0:

| Line | Means |
| --- | --- |
| `MAIL <n>` | n waking messages are unread at `owner/in` |
| `BLOCKED <name>` | The session hit a permission or question dialog: tell the owner, never answer it |
| `GONE <name>` | herdr no longer lists the agent: it exited, and herdr cleared its name. A resumed session shows this way, then `unattached` in `sessions`; ring `<name> <name>` once its recorded pane holds an idle agent |
| `UNREAD <name> <n>` | The session sits idle with n messages unread for 5 minutes: its wait stopped, or a `/clear` dropped its hooks (`sessions` then shows it `unattached`). Either way, ring `<name> <name>` |
| `TIMEOUT` | Nothing happened within the timeout (default 3600) |

Run it as a background task, and start it again after each wake: a session attached since is
watched from the next wait.

### `ctl.py ring <name|pane> <attach-name>` and `ctl.py ring <name|pane> --brief <file>`

Types one ring line into the target and Enter. The target is a live herdr agent's name or pane, or,
when herdr has no agent by that name, an attached or started record's name, which rings the agent in
the record's pane. herdr gives a moved pane a new id, so the line goes to the agent by its herdr
name whenever it has one, and by pane only when it has none. `<attach-name>` types
`/control-attach <attach-name>` into a Claude agent; `--brief` types `Read <file> and follow it.`
into a Codex agent. The target's records are the agent's records (A record's session, above),
whichever way the target reached it.

| Line | Exit | When |
| --- | --- | --- |
| `RUNG <target>` | 0 | Typed |
| `REFUSED no agent at <target>` | 1 | Neither herdr nor an attached or started record knows the target, or the record's pane holds no agent |
| `REFUSED <target> is <state>` | 1 | herdr's state is neither `idle` nor `done` |
| `REFUSED <target>'s input line is not empty` | 1 | Its visible input line holds text: the owner may be typing |
| `REFUSED <target> is at observe` | 1 | Any of the target's records is at `observe` |
| `REFUSED <target> is attached as <name>` | 1 | `<attach-name>` isn't the name of one of the target's records, the first of which is `<name>` (A ring never changes a level, above) |
| `REFUSED <target> is <kind>` | 1 | `<attach-name>` into an agent that isn't Claude, or `--brief` into one that isn't Codex |
| `REFUSED <target> is named <herdr name>` | 1 | The agent has a herdr name and isn't that name's record's session: an orchestration thread or lane (Never into orchestration's agents, above) |
| `REFUSED not a name: <attach-name>` | 1 | Outside the name pattern |
| `REFUSED owner is the controller's address` | 1 | `<attach-name>` is `owner` |

### `ctl.py start <name> <folder> <objective-file>`

Opens a new herdr workspace in `<folder>` without focus, starts a Claude agent named `<name>` in it,
writes `<name>`'s record (`started` true, not yet attached; a record that exists keeps its authority
and hold, as on `attach`, and a new one gets the defaults), sends the objective file's text
unchanged to `<name>/in` from `owner` (its first line is an `OWNER:` or `CONTROL:` line), and types
`/control-attach <name>` as the agent's first prompt. The session attaches and its first wait finds
the objective. The objective is a down message, so before anything is made the record's level
must permit its first line's kind, as `send` checks; a first line of no kind counts as `CONTROL:`.
The folder is checked against the list before it is checked to exist, so a refusal never says
whether a path outside the list exists.

| Line | Exit | When |
| --- | --- | --- |
| `STARTED <name> <pane>` | 0 | Started |
| `BLOCKED <name> waiting on a startup prompt` | 0 | Started, but a startup dialog (folder trust) waits for the owner, or herdr refused the first prompt; once it is idle, ring `<name> <name>` |
| `REFUSED no folders file at <path>` | 1 | `<home>/control/folders` doesn't exist |
| `REFUSED <folder> is not a listed folder` | 1 | Neither a listed folder nor inside one |
| `REFUSED <folder> is not a folder` | 1 | A listed path, or one inside it, that isn't an existing directory |
| `REFUSED 3 started sessions are running` | 1 | Three records with `started` are running: herdr lists the record's name or its pane |
| `REFUSED cannot read <objective-file>` | 1 | Missing, not UTF-8 text, or empty |
| `REFUSED <name> is at <level>` | 1 | `<name>`'s level (kept, or the default for a new name) doesn't permit the objective (Authority) |
| `REFUSED not a name: <name>` | 1 | Outside the name pattern |
| `REFUSED owner is the controller's address` | 1 | `<name>` is `owner` |
| `REFUSED <name> is held by pane <pane>` | 1 | A live herdr agent is named `<name>` |

## What the hooks call

The control-attach skill's hooks run in the attached session and call only this:

- **`ctl.wait_command()`**, imported from `scripts/ctl.py` (`sys.path.insert` of the skill's
  `scripts/`): the `<command>` of this pane's `WAIT` line, or `None` when no record is attached from
  `HERDR_PANE_ID`. It reads the record only, never herdr.
- **The Stop hook.** When `wait_command()` is `None`, it does nothing. The wait is up when the
  command of any of the Stop input's `background_tasks` contains `wait_command()` verbatim (an
  entry with no command, such as a subagent, never matches).
  On every stop it runs `ctl.py report` with `last_assistant_message` on stdin, so a turn that
  forgot the wait still sends its report. Then, unless the wait is up or `stop_hook_active` is
  true, it blocks the stop with a reason naming the command; the turn that follows ends with a line
  that isn't a waking `STATUS:`, so its report is quiet. The hook prints nothing but that block and
  exits 0, whatever fails.
- **The prompt-submit hook** runs `ctl.py typed` with every prompt on stdin. It filters nothing:
  `typed` decides what is the owner typing.
