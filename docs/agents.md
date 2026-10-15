# Agents

Subagent definitions in [`agents/`](../agents/), linked into Claude Code only. Each runs in its
own context with an explicitly selected model and returns a compact result instead of bringing
all intermediate output into the calling session.

| Agent          | Model / effort      | Use for                                                                                                        |
| -------------- | ------------------- | -------------------------------------------------------------------------------------------------------------- |
| `test-runner`  | `sonnet` / `low`    | Run tests, build, lint, or typecheck; report pass/fail with the failing output verbatim                        |
| `pr-watch`     | `sonnet` / `low`    | Watch a PR settle — CI runs and check suites, plus Copilot, Codex or Claude code reviews                       |
| `analyst`      | `sonnet` / `medium` | Explain how a subsystem, flow, or symbol actually works, with `file:line` citations                            |
| `researcher`   | `sonnet` / `high`   | Investigate libraries, APIs, and external docs; return a sourced synthesis, not pages                          |
| `debugger`     | `sonnet` / `xhigh`  | Reproduce a failure, isolate its root cause, propose a minimal fix with evidence                               |
| `verifier`     | `opus` / `high`     | Adversarially check one claim, diff, or fix; return CONFIRMED, REFUTED, or UNPROVEN                            |
| `migrator`     | `sonnet` / `medium` | Apply one mechanical transformation across many files, in an isolated git worktree                             |
| `orchestrator` | `opus` / `high`     | Not a subagent: the session agent for one orchestration thread, a herdr agent launched by `orchestration-main` |
| `lane`         | set at launch       | Not a subagent: the session agent for one Claude lane of a build, a herdr agent started by the thread          |

## When to delegate

Send deterministic, log-heavy work to `test-runner` and `pr-watch` by default. Send reading that
spans many files to `analyst`, and anything answered by external documentation to `researcher`.
Send a failure to `debugger`, a conclusion that is expensive to get wrong to `verifier`, and a
repetitive change across many files to `migrator`. Keep work in the main session when it needs
the conversation's full context or is a trivial single-file change. The same routing table is in
[`instructions/CLAUDE.md`](../instructions/CLAUDE.md), which every Claude session loads.

## Model tiers

Named agents retain their explicit role-specific models; `verifier` pins Opus instead of
inheriting. Ad hoc subagents and dynamic workflow agents start on explicit Opus; a new
weaker-model choice needs a concrete reason based on bounded work and verifiable output. This
does not change skill-level model settings or the main session's model. The canonical policy,
including runtime checks and escalation, is [agent model selection](agent-model-selection.md).

## Write access

`migrator` edits files only in a temporary git worktree, so its changes cannot disturb the
caller's working tree; `orchestrator` and `lane` edit in their own worktrees. Of the rest, six
are granted neither `Edit` nor `Write`; a hook refuses an `orchestrator` or `lane` write into
your own checkout and reminds the orchestrator when it writes outside its coordination
worktree, `../<repo>-orch-<build>`. A `Bash` grant is not a read-only guarantee — `analyst`,
`verifier`, and `debugger` are restricted to inspection by their instructions, not by their
tool list.

The two-thread design behind `orchestrator` and `lane`, a main session that talks to you and
orchestration threads that run builds, is in
[orchestration/2026-10-10-two-thread-spike.md](orchestration/2026-10-10-two-thread-spike.md);
its move onto herdr agents and a file mailbox is in
[orchestration/herdr-rework/](orchestration/herdr-rework/spec.md).

## Output contracts and settings

Each agent defines a strict output contract so the caller can assess its evidence. Beyond
`model` and `effort`, they set `permissionMode: auto` so background work does not stall on a
prompt, `maxTurns` as a runaway guard, and `memory: project` where a project-specific fact is
worth carrying between sessions — the test command, a repository's CI shape, a recurring failure
mode. `analyst` and `verifier` deliberately keep no memory: both must answer from the code as it
is now, and a remembered claim invites a stale one.

To evaluate an agent definition, see the Agents section of
[evaluating-skills.md](evaluating-skills.md).
