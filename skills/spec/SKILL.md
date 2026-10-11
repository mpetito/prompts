---
name: spec
description: "Write a spec and plan for a feature, then carry the plan out: spec.md says what and why, plan.md says how, in steps that each name their files, end with a check, and are ticked as they land. Use when asked to write a spec, plan or design before coding, to scope a feature (what is in, what is out, how to build it), to carry on with, pick up or finish spec NNN or a half-done plan or checklist, or to work through plan.md until every step is checked off. Not for reviewing or poking holes in an existing plan or spec (plan-review), setting up a specs/ folder, its numbering or AGENTS.md (project-setup), a fix or change with no spec (code-style), or running a build with several parallel lanes (agent-orchestration)."
---

# Spec

Role: worker. Loaded by a session or a lane worker that writes a spec and plan, or carries one
out; this file stays under 80 lines.

The path: write spec.md and plan.md, "grounded in the codebase and the docs"; review them; then
carry the plan out step by step. The `specs/` layout is
[project-setup](../project-setup/SKILL.md)'s.

## Write the spec and plan

1. **spec.md says what and why** ("spec.md (what and why) and plan.md (how)"): behaviour,
   scope, decisions and open questions. No file paths, function or type names, or code, even
   when the request names them; those go in plan.md.
2. **Open questions:** a heading `## Open questions` with items numbered `1.`, `2.`, … Each item
   is the question, one line of context (the options and what each one changes), and
   `Default:` with your pick, so the owner can answer "agreed" by number ("I agree with all
   your defaults and recommendations."). A question without its context comes back as "I need
   more info / context on 1-3."
3. **A claim the request asserts without proof is an open question** for the owner to confirm,
   never a fact or a requirement in spec.md. Such claims are a product fact, a safety, legal or
   money claim, or a guarantee about another system.
4. **Write the plan on the defaults rather than stopping** ("try not to block yourself on
   questions"). Stop only for what the owner reserved: money, access, destructive or production
   changes, and legal or product facts.
5. **plan.md says how:** ordered steps, each a `- [ ] N.` checkbox (or the checkbox form the
   project's existing plans use) that starts with the file paths it touches and ends
   `Check: <command or test>`, a check that can fail. For example: ``- [ ] 3. `src/report.ts`,
   `test/report.test.ts`: group totals by currency. Check: `npm test` passes the new test.``
6. Review spec.md and plan.md with [plan-review](../plan-review/SKILL.md) before any code is
   written. A plan with several lanes seeds an
   [agent-orchestration](../agent-orchestration/SKILL.md) build instead of the section below.

## Carry out the plan

Write the code under [code-style](../code-style/SKILL.md), "ticking off steps in plan.md as
they land":

1. **Resume at the first unticked step.** If its work is already there, run its check; once the
   check passes, tick the step and move on. Don't redo or re-plan it.
2. **Tick each step in the same change that lands it,** before starting the next step; never
   tick in a batch at the end.
3. When a step proves wrong, update plan.md in place and say so. Spec edits go back to the
   owner, never silently.
