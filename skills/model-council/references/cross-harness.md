# Claude and Codex participation

A council coordinates real model calls. Role-playing multiple models in one response is not
an independent council. Either Claude or Codex may coordinate; both receive the same evidence
and return the same [member report](member-prompt.md).

## Choose a transport

1. Use native delegation when the exposed tools can select the required models/providers.
   Follow the actual tool schema, explicitly setting the model and supported effort. A
   same-provider subagent tool does not gain another provider by accepting an invented alias.
2. Inside an active Herdr environment, load
   [herdr-delegation](../../herdr-delegation/SKILL.md) and use one Claude peer and one Codex peer.
   Confirm the model on each peer before sending work. Use task-owned peers and file-based
   results; the `--kind` harness choice alone does not select a model.
3. Without a suitable native tool or Herdr, use the installed, already-authenticated Claude
   and Codex CLIs in separate processes. Read their installed help before assembling commands:

   ```powershell
   claude --help
   codex exec --help
   ```

   | Concern | Claude CLI | Codex CLI |
   | --- | --- | --- |
   | Noninteractive task | `--print`, packet via stdin | `exec`, packet via stdin using `-` |
   | Explicit worker model | `--model opus` | `--model` with the selected available Codex model ID |
   | Reasoning effort | `--effort high` where supported | Supported reasoning setting from installed help/config docs |
   | Code access | Start in the reviewed repository; restrict tools to the needed read capabilities | `--cd` for the reviewed repository and `--sandbox read-only` |
   | Result capture | `--output-format json`; coordinator captures stdout and checks the result/error status | `--output-last-message` for the report; `--json` when event/model metadata is needed |

   Pass the prepared packet through stdin or a safely quoted file-based mechanism. Do not
   interpolate PR text into shell command source. Set a host process deadline, inspect the
   exit status and completion/error result, and keep each output separate. A file existing
   does not prove the review completed. Preserve model metadata when available; otherwise
   distinguish the requested model from an unverified effective model.

   Claude tool restrictions and Codex sandbox settings are different controls. Restrict
   available tools as supported and explicitly prohibit external mutations in the packet;
   a filesystem sandbox alone does not restrict connected apps. Do not use permission-bypass
   flags or grant broader access to get a council response. Let the coordinator capture output
   files without giving reviewers source-write access.

4. If one provider is unavailable, report the limitation. Use two fresh independent contexts
   on the available high-capability model if that still helps, identifying it as a single-family
   council. Do not label a simulated persona as a Codex/Claude participant. If only one review
   can run, return a single-review assessment and the missing coverage rather than claiming
   a completed council. Essential cross-provider requirements remain unfulfilled until available.

## Runtime sources and verification

The CLI options above were checked against local `claude --help` and `codex exec --help`.
They are command-building guidance, not a live cross-provider execution test. Model availability,
authentication, and tool access still need checking in the environment where the council runs.
Do not alter persistent user model settings to select a one-off council worker.

[Codex noninteractive mode](https://developers.openai.com/codex/noninteractive) documents stdin,
result capture, and structured output; the
[Codex CLI reference](https://developers.openai.com/codex/cli/reference) covers model and sandbox
options. Claude's installed CLI help and
[subagent documentation](https://code.claude.com/docs/en/sub-agents#choose-a-model) cover explicit
model selection. For model policy use
[agent model selection](../../skill-authoring/references/agent-model-selection.md).
