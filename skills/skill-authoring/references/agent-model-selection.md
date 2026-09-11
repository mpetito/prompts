# Agent model selection

Apply before spawning a subagent, team member, background worker, or dynamic workflow.
This policy selects models for authorized delegation; it does not require delegation.

## Select per task

1. Define a bounded task, needed tools, relevant context, and a concise output contract.
   Keep small tasks local when startup and handoff would cost more than the work.
2. **Start with explicit `opus` in Claude Code.** Start with a high-capability coding/reasoning
   model from the exposed catalog in other hosts; do not pass Anthropic aliases to Codex.
   This preference applies to named subagents, ad hoc workers, and every dynamic workflow
   agent. It does not change the main session or skill-level model settings. It avoids
   accidentally inheriting Fable while starting high.

   Preserve existing named-agent model pins as deliberate role-specific choices. The Opus
   default fills an unspecified worker choice; it does not require rewriting or overriding
   those definitions. A new lower-tier choice still needs the justification below.

   | Task | Model choice and justification |
   | --- | --- |
   | Implementation, research synthesis, debugging, review, ambiguous feedback | `opus`; medium/high effort for the task |
   | Architecture, security reasoning, council adjudication | `opus`, high; stronger only for a specific unmet capability need |
   | Exact test/build command, status collection, predefined mechanical edit | Default `opus`; `sonnet` is justified only when the actual task is bounded and mechanically verifiable |
   | Narrow lookup or extraction with an exact output contract | Default `opus`; `haiku` is justified only when no substantive judgment is delegated and the result is easy to verify |

3. Use a named agent with a suitable explicit model or pass the model in the launch API.
   Do not omit it or use `inherit` as a convenience. **Any weaker model requires a brief,
   task-specific justification before launch**, naming the bounded work and verification.
   "Routine", "read-only", or "save tokens" alone is insufficient. Put the rationale beside
   the model in the delegation plan; grouped identical tasks can share one rationale.
   Opus needs no special justification. No routine permission question is needed within
   the user's existing scope and budget.
4. For generated workflows, select a model for **every** agent-producing stage, including
   planners, evaluators, retry paths, and nested workers. Use the host's installed workflow
   authoring instructions and actual schema; a prose request for a model is not a
   model setting. Check the generated configuration before execution. Start with a small
   bounded batch and expand only when independent work warrants it.
5. Check the effective model when the host exposes it. If a requested model is unavailable
   or substituted, select a supported alternative deliberately before expanding the run.
   Preserve the choice on resume/retry. If model selection cannot be controlled, keep the
   task local or use a controllable worker instead of silently multiplying premium calls.
6. Return a downgraded worker's unresolved judgment to Opus rather than repeatedly retrying
   the weaker tier. Escalate beyond Opus only when evidence shows it is insufficient;
   include the failed hypothesis or capability gap. Missing tools, access, or context call
   for fixing the setup, not a larger model. Reuse completed results and stop duplicate work.

For independent perspectives on an uncertain decision, use
[model-council](../../model-council/SKILL.md). A council complements evidence gathering;
it does not justify reducing reviewer capability or launching many copies of the same review.

## Claude Code runtime checks

Omitted model settings can fall back to the main session. Built-in agents and full-context
forks can inherit too; don't infer a tier from an agent name. Model precedence and environment
overrides have changed across releases, so check the installed version and relevant settings
when the actual model differs. Inspect only model-related configuration, not unrelated secrets.
Use `/tasks` when available to inspect ordinary workers.
[Claude Code subagent documentation](https://code.claude.com/docs/en/sub-agents#choose-a-model)
describes precedence, substitutions, and fork behavior.

A workflow stage's model is a per-invocation choice. Without an effective selection it can
use the session model, and the workflow UI can report substitutions. Consult the installed
workflow authoring capability for configuration syntax and `/workflows` for the running stages.
[Claude Code workflow documentation](https://code.claude.com/docs/en/workflows#cost).

Skill frontmatter is not a portable worker-model control. Reference skills may leave `model`
unset because they are read inside another task; the worker running that task still needs an
explicit choice. Carry relevant standards and this selection policy into delegated prompts;
do not assume the parent's loaded skills or conversation are present.
