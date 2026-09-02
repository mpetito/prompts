---
name: code-authoring
description: "Methodology for implementing features end-to-end: decomposing work, writing code that follows project conventions, validating with tests and linters, and producing a coherent change set. Use when implementing a feature, executing a plan, building something new, completing a non-trivial change, or following a spec from `specs/`."
---

# Code Authoring Skill

Procedural knowledge for executing implementation tasks: from spec/plan to validated, conventionally-styled code.

## When to Use

- A user asks to implement, build, or add a feature
- A `specs/{NNN-slug}/plan.md` exists and needs to be executed
- A spec from `/spec` is ready to be built
- Any multi-step code change beyond a trivial tweak

For very small surgical changes (rename, typo, single-line fix), just make the minimal edit directly rather than running the full protocol below.

## Context Sources (priority order)

1. **Spec + Plan**: If `specs/{NNN-slug}/spec.md` and `plan.md` exist, follow the plan step-by-step
2. **Direct user input**: The current request

## Execution Protocol

Run the loop below once for a single-phase change, or once per phase for a multi-phase plan.

### 1. Prepare

- Re-read the spec objective and the current phase's goals
- List affected files; read them before modifying
- Identify existing patterns to follow (similar features, utilities, types)
- Note dependencies and integration points

If the scope is large or the codebase unfamiliar, delegate analysis to a read-only subagent (e.g. the `Explore` agent) rather than burning primary context on file reads.

### 2. Implement

- Define types/interfaces first, then implement core logic
- Follow patterns surfaced in Prepare; do not invent new ones when an established one exists
- Add error handling at boundaries (user input, external APIs); trust internal code
- Use CLI for package operations (`npm install`, `pnpm add`, `dotnet add package`) — never hand-edit lockfiles or manifests
- Make atomic, focused changes; one logical concern at a time
- Follow the Coding Standards below

### 3. Test

- Write unit tests for new logic, covering happy paths and meaningful edge cases
- Run the existing test suite; fix any regressions before proceeding
- For UI changes, validate behavior visually or via e2e when applicable

### 4. Self-Review

- Re-read every file you changed
- For React/Next.js/TypeScript changes, also apply the `code-quality-standards` skill checklist (security, DRY, correctness, performance, accessibility)
- Confirm DRY: no duplicated logic that an existing utility would have served
- Remove deprecated or dead code outright — do not just mark it
- Verify no `any`, non-null assertions, or unsafe casts were introduced
- Confirm every checklist item for the phase is complete

### 5. Validate

- Run linters and type-checks: `npm run lint`, `npx tsc --noEmit`, `dotnet format --verify-no-changes`, etc.
- Check IDE diagnostics if available (`#problems` in VS Code, the `LSP` tool in Claude Code) and resolve all errors/warnings introduced by the change
- Remove any debug code, console logs, or temporary scaffolding

Repeat for the next phase, or proceed to Output.

## Subagent Delegation (Optional)

When useful, fan out independent, read-only work to subagents:

| Use For                         | Pattern                                                          |
| ------------------------------- | ---------------------------------------------------------------- |
| Codebase pattern discovery      | `Explore` agent, "find all usages of X with thoroughness medium" |
| Multi-file reads in parallel    | Multiple `Explore` agents in the same turn                       |
| Deep library/API research       | Reference the `research` skill                                   |
| Standalone documentation lookup | Subagent with `docs-context7` / web tools                        |
| Parallel implementation         | Write subagents over **disjoint file sets** (see below)          |

Writes may be delegated when partitioned to disjoint files. Subagents are stateless and do not auto-load skills, so each write subagent's prompt must embed complete context: the relevant spec/plan excerpt, established patterns to follow, and the Coding Standards below. Never assign two subagents overlapping files. The primary agent still performs Self-Review and Validate across all delegated changes.

## Coding Standards

This section is the canonical copy of the personal coding standards. Other skills (e.g. `review`) carry condensed excerpts; when standards change, update here first.

### Naming & Readability

- Descriptive names for meaningful code; short names (`i`, `j`, `x`) only for iterators and trivial temporaries
- Group related lines together; blank lines separate distinct logical steps
- Template literals for string interpolation

### Comments & Documentation

- Comment the **why**, not the **what** — explain reasoning, not mechanics
- Doc comments on public APIs (param/return)
- Let good names and types document internal code; do not add narration
- **Reach for clearer code before a longer comment.** A rationale that needs a paragraph is
  usually naming an extraction, a better name, or a type that has not been written yet.
  Rewrite the code first; keep the comment only for what the code genuinely cannot say
- **Keep a comment proportionate to what it explains.** More comment than code is a smell, and
  a multi-paragraph block above a short statement almost always belongs somewhere else
- **One home per rationale.** If the reasoning already lives in AGENTS.md, a spec, or a runbook,
  link to it rather than restating it — two copies drift, and the copy in the source goes stale
  first because it is the one nobody re-reads
- Incident history, review discussion, and changelog narrative belong in commits, PRs, and
  AGENTS.md — not in the source

### Functions & Structure

- Small, single-purpose functions for clear high-level workflow
- Avoid over-fragmenting into single-use helpers that just shuffle parameters
- A callback longer than a screen is a function that has not been named yet — extract it, even
  when it has one caller. Error handling you cannot see without scrolling is error handling
  nobody reviews
- Guard clauses + early returns for edge cases; ternaries for simple remaining logic
- Omit braces only for early-return guards; use braces for logic blocks

### Error Handling & Validation

- Fail fast with exceptions for unrecoverable errors
- Use result objects when callers have meaningful recovery paths
- Make invalid states unrepresentable via types; validate explicitly at boundaries only

### Data & Types

- Annotate function signatures; let inference handle internals
- Protect inputs and shared state (immutability); local mutation is fine
- Optional chaining + nullish coalescing for null handling
- Name constants for non-obvious values; `0`, `1`, `2` are fine in self-evident contexts
- TypeScript: `interface` for object shapes; `type` for unions, intersections, and utilities

### Parameters & APIs

- Positional params for 2–3 clear arguments
- Options objects when >3 params, when params are easily confused, or for API consistency
- Avoid boolean flag parameters; prefer enums, options objects, or separate methods

### Control Flow & Iteration

- Functional methods (`map`, `filter`, `reduce`) for transformations
- Traditional loops for side effects, complex logic, or early exits
- `async/await` for linear flow; `Promise.all` to parallelize when performance requires it

### Architecture

- Constructor injection for explicit, testable dependencies
- Group by feature for APIs; group by type (layer) for UIs
- Tolerate duplication at 2 occurrences; extract when a 3rd appears or when more occurrences are clearly expected near-term

### Modules & Files

- Export style (named vs default) and file naming follow established project or framework conventions; consistency within the project is what matters

### Classes vs Functions

- Classes for stateful things; plain functions for stateless logic

### Testing

- `describe` blocks group by unit; keep test names concise
- Test names describe behavior in plain language within their group context

### Logging

- Prefer structured logging via the framework's idiom: message templates in .NET (`logger.LogInformation("Order {OrderId} created", orderId)`), field objects in JS (`logger.info('order created', { orderId })`)
- Never concatenate raw values into log message strings; keep field names consistent across the codebase

### Version Control

- Feature-complete commits — one logical change per commit

## Boundaries

- ✅ Implement directly, run tests, run linters, modify files in scope
- ✅ Use CLI for dependency operations
- ⚠️ Ask first: delete files outside the change scope, modify CI/CD config, change project structure
- 🚫 Never commit directly to protected branches
- 🚫 Never skip the Test or Validate steps

## Output

After completion, report:

1. Brief summary of what was implemented
2. Files created / modified
3. Test results (new tests + suite status)
4. Any follow-ups or deferred items

Suggest next steps:

- `/review` for an independent quality pass
- `/commit` to commit and open a PR
