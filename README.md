# Agentic Coding Toolkit

A collection of agent skills for reliable agentic coding workflows, shared across GitHub Copilot (VS Code + Copilot CLI), Claude Code, Codex, and OpenCode.

Skills are the single unit of reusable workflow guidance in this repository: they auto-load when relevant, and both VS Code and Claude Code expose each skill as an explicit `/name` entry point. There is no separate `prompts/` concept; former prompt slugs are preserved as skill names.

## Skills

| Skill                     | `/slash` invocation        | Purpose                                                                                         |
| ------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------- |
| `commit`                  | `/commit`                  | Validate changes, create conventional commits, push branches, and open or update pull requests  |
| `implement`               | `/implement`               | Execute a spec or clear request end-to-end, from planning through implementation and validation |
| `pr-feedback`             | `/pr-feedback`             | Address PR feedback from reviews, CI, and code analysis tools                                   |
| `model-council`           | `/model-council`           | Resolve uncertain technical decisions with independent Claude/Codex perspectives and cited evidence |
| `pr-resolve`              | `/pr-resolve`              | Reply to and resolve PR review threads                                                          |
| `pr-consolidate`          | `/pr-consolidate`          | Consolidate multiple PRs or branches into a unified integration branch                          |
| `review`                  | `/review`                  | Run a structured code review of staged or recently implemented changes                          |
| `spec`                    | `/spec`                    | Produce `spec.md` (what + why) and `plan.md` (how) under `specs/{NNN-slug}/`                    |
| `tt`                      | `/tt`                      | Log or update a Harvest time entry for current work, linked to an ADO item                      |
| `story`                   | `/story`                   | Create a user story, issue, or bug in Azure DevOps                                              |
| `research`                | `/research`                | Conduct deep technical research using documentation, search, and GitHub resources               |
| `pr-review`               | `/pr-review`               | Review someone else's PR by number and draft/post feedback with approval                        |
| `pr-authoring`            | `/pr-authoring`            | Write concise, motivation-led pull request descriptions                                         |
| `upgrade`                 | `/upgrade`                 | Safely upgrade dependencies with research, risk assessment, and validation                      |
| `code-authoring`          | `/code-authoring`          | Implementation methodology: prepare, implement, test, self-review, and validate                 |
| `agents-md-authoring`     | `/agents-md-authoring`     | Author AGENTS.md / CLAUDE.md project-wide context files                                         |
| `skill-authoring`         | `/skill-authoring`         | Author, split, and tune SKILL.md files and skill folders                                        |
| `autonomous-loops`        | `/autonomous-loops`        | Run iterative loops against asynchronous external evaluators such as CI or deploys              |
| `code-quality-standards`  | `/code-quality-standards`  | Detailed Next.js, React, and TypeScript code quality review standards                           |
| `design-review-standards` | `/design-review-standards` | UI/UX and accessibility review standards for brand, responsive design, and conversion           |
| `ecommerce-patterns`      | `/ecommerce-patterns`      | Cart, checkout, payments, orders, and conversion patterns for React/Next.js apps                |
| `playwright-e2e`          | `/playwright-e2e`          | Playwright end-to-end testing: Page Object Models, locators, and monorepo setup                 |
| `seo-aeo-structured-data` | `/seo-aeo-structured-data` | SEO, AEO, structured data, metadata, sitemap, and Core Web Vitals guidance                      |
| `agentmail`               | `/agentmail`               | Use the AgentMail MCP server as a test mailbox when verifying email send/receive flows          |
| `word-doc-editing`        | `/word-doc-editing`        | Edit Word .docx files via Word COM automation: tracked changes, structural ops, verification    |
| `firecrawl`               | `/firecrawl`               | Search, scrape, crawl, map, and extract from the live web; developer and research indexes       |
| `herdr-delegation`        | `/herdr-delegation`        | Coordinate agents across Herdr panes: cross-harness delegation, worktrees, blocked peers        |

When you already have a spec in `specs/{NNN-slug}/`, use `/implement spec NNN` to execute it end-to-end. For ad-hoc implementation requests without a spec, describe the work directly or invoke `/implement`.

## Agents

Subagent definitions for delegated work. Each runs in its own context with an explicitly
selected model and returns a compact result instead of bringing all intermediate output into
the calling session. Ad hoc subagents default to Opus; named agents retain the role-specific
model settings below, and new weaker-model choices require a task-specific reason.

| Agent         | Model / effort      | Use for                                                                                 |
| ------------- | ------------------- | --------------------------------------------------------------------------------------- |
| `test-runner` | `sonnet` / `low`    | Run tests, build, lint, or typecheck; report pass/fail with the failing output verbatim |
| `pr-watch`    | `sonnet` / `low`    | Watch a PR settle — CI runs and check suites, plus Copilot review comments              |
| `analyst`     | `sonnet` / `medium` | Explain how a subsystem, flow, or symbol actually works, with `file:line` citations     |
| `researcher`  | `sonnet` / `high`   | Investigate libraries, APIs, and external docs; return a sourced synthesis, not pages   |
| `debugger`    | `sonnet` / `xhigh`  | Reproduce a failure, isolate its root cause, propose a minimal fix with evidence        |
| `verifier`    | `opus` / `high`   | Adversarially check one claim, diff, or fix; return CONFIRMED, REFUTED, or UNPROVEN     |
| `migrator`    | `sonnet` / `medium` | Apply one mechanical transformation across many files, in an isolated git worktree      |

Only `migrator` can edit files, and it works in a temporary git worktree so its changes cannot disturb the caller's working tree. The other six are granted neither `Edit` nor `Write`. Note that a `Bash` grant is not a read-only guarantee — `analyst`, `verifier`, and `debugger` are restricted to inspection by their instructions, not by their tool list.

**When to delegate.** Send deterministic, log-heavy work to `test-runner` and `pr-watch` by default. Send reading that spans many files to `analyst`, and anything answered by external documentation to `researcher`. Send a failure to `debugger`, a conclusion that is expensive to get wrong to `verifier`, and a repetitive change across many files to `migrator`. Keep work in the main session when it needs the conversation's full context or is a trivial single-file change.

**Why the model tiers.** Named agents retain their explicit role-specific models; `verifier`
pins Opus instead of inheriting. Ad hoc subagents and dynamic workflow agents start on explicit
Opus; a new weaker-model choice needs a concrete reason
based on bounded work and verifiable output. This does not change skill-level model settings
or the main session's model. The canonical policy, including runtime checks and escalation, is
[agent model selection](skills/skill-authoring/references/agent-model-selection.md).

Each agent defines a strict output contract so the caller can assess its evidence. Beyond `model` and `effort`, they set `permissionMode: auto` so background work does not stall on a prompt, `maxTurns` as a runaway guard, and `memory: project` where a project-specific fact is worth carrying between sessions — the test command, a repository's CI shape, a recurring failure mode. `analyst` and `verifier` deliberately keep no memory: both must answer from the code as it is now, and a remembered claim invites a stale one.

## Instructions

`instructions/CLAUDE.md` is the user-level global instruction file, symlinked to `~/.claude/CLAUDE.md`. Unlike skills and agents, it is **always loaded**, in every session and every project — so it holds only what must apply everywhere: attribution rules, the delegation routing table, and model-tier guidance. Anything narrower belongs in a skill, which loads on demand.

Keeping it here rather than in `~/.claude` puts it under version control alongside the agents it routes to, so the routing table and the agent definitions cannot drift apart.

The coding path is `code-authoring` → applicable `code-quality-standards` → `review`, including
bug fixes and refactors without a spec. Project conventions take precedence over personal
style; concise comments and reuse are checked during implementation and review. `pr-feedback`
collects full review bodies as well as threads and verifies visible and suppressed Copilot
claims before accepting changes. These routes are explicit in skill bodies for other hosts,
which do not load this Claude-only global file.

When actionability remains unclear, `pr-feedback` invokes
[model-council](skills/model-council/SKILL.md): two independent reviews focused on correctness
and maintenance cost, preferably Claude plus Codex, followed by evidence-based synthesis.
A third reviewer is reserved for a specific unresolved question. The council can use native
delegation, Herdr peers, or authenticated CLIs; it reports recommendations without posting or
editing code itself. Skill-level model settings remain independent of council worker models.

## Status Line

`statusline/statusline.js` is Claude Code's custom status line — the line under the input box
showing the working directory, repository, branch with a coloured git-state badge, model and
reasoning effort, and context-window usage. Claude Code runs it on every render, so it must be
fast and it must exit; both constraints are documented in
[`statusline/README.md`](statusline/README.md), along with the three-step initial setup — the
symlink, the `settings.json` entry that activates it, and the Nerd Font plus terminal font-face
setting the icons depend on.

It lives here for the same reason `instructions/CLAUDE.md` does: it is user-level Claude Code
configuration, and version control is the only thing that makes a hand-tuned script recoverable.
`settings.json` itself is **not** tracked — it holds machine paths and secrets.

## Fragments

Reusable prompt fragments for specialized workflows.

| Fragment              | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `snyk-upgrade-review` | Review and complete Snyk dependency upgrade PRs |

## Workflows

### Standard Feature Development

```
/spec → /implement spec NNN → /review → /commit
```

1. **Spec** (`/spec`): produce `spec.md` + `plan.md` under `specs/{NNN-slug}/`
2. **Implement** (`/implement spec NNN`): apply any clarifications, create or review the plan, build all phases
3. **Review** (`/review`): independent quality pass
4. **Commit** (`/commit`): branch, commit, push, open/update PR

### Direct Implementation (Clear Requirements, No Spec)

```
(describe the work) → /review → /commit
```

### Research Spike

```
/research → /spec → ...
```

### PR Feedback Loop

```
/pr-feedback → /pr-resolve → /commit
```

Repeat until approved.

### Dependency Upgrade

```
/upgrade → /commit
```

### Branch Consolidation

```
/pr-consolidate → /commit
```

## Setup

Use **PowerShell 7.4+ (`pwsh`)** on Windows, Ubuntu, and macOS. Windows PowerShell 5.1
(`powershell.exe`) is not supported. Install PowerShell using the
[Microsoft instructions](https://learn.microsoft.com/powershell/scripting/install/installing-powershell).
Keep a local clone on each machine and sync the source through Git; the installer derives the
checkout location from its own script, so the clone can live anywhere.

From the repository root, these commands work from Bash or PowerShell:

```sh
# Preview setup for clients detected on PATH, then apply and verify it.
pwsh -NoProfile -File ./setup-skills-link.ps1 -WhatIf
pwsh -NoProfile -File ./setup-skills-link.ps1
pwsh -NoProfile -File ./verify-setup.ps1

# Select clients explicitly, including clients not installed yet.
pwsh -NoProfile -File ./setup-skills-link.ps1 -Tools codex,claude,opencode
pwsh -NoProfile -File ./verify-setup.ps1 -Tools codex,claude,opencode
```

Automatic detection checks the `codex`, `claude`, `opencode`, and `copilot` commands on PATH.
For desktop/IDE-only clients, or to prepare files before installing a CLI, use `-Tools`.
When adding a client, install it and rerun setup. No client authentication or Docker is needed
for skill linking. Windows symlinks require Developer Mode or an elevated PowerShell session;
Linux and macOS need no elevation when writing your own home directory. Run as your normal user.

| Repository source | Client | Default destination |
| --- | --- | --- |
| `skills/*` | Codex and OpenCode | `~/.agents/skills/*` |
| `skills/*` | Claude Code | `~/.claude/skills/*` |
| `skills/*` | GitHub Copilot | `~/.copilot/skills/*` |
| `agents/` | Claude Code | `~/.claude/agents` |
| `instructions/CLAUDE.md` | Claude Code | `~/.claude/CLAUDE.md` |
| `statusline/statusline.js` | Claude Code | `~/.claude/statusline.js` |

[Codex](https://learn.chatgpt.com/docs/build-skills) and
[OpenCode](https://opencode.ai/docs/skills/) both discover `~/.agents/skills`.
Skills are linked individually, including the shared `pr-scripts` helper directory, so the
destination remains a real directory and client-managed entries stay local. Global Claude
instructions and agents keep their Claude-specific formats.

The installer honors `CLAUDE_CONFIG_DIR` for Claude destinations and `CODEX_HOME` when migrating
old Codex links. Shared skills remain under the user's `~/.agents/skills`, independent of
`CODEX_HOME`. `-HomeDirectory <path>` redirects **all skill destinations** to an isolated home
and ignores these environment overrides; use it for testing, not to configure a client that
still reads your normal home.

Setup is idempotent. Conflicting files, directories, and foreign links are preserved and reported
as incomplete setup (nonzero exit). To replace them deliberately, preview with
`-ReplaceConflicts -WhatIf`, then rerun with `-ReplaceConflicts`. Originals move to a unique
folder under `~/.prompts-backups`, outside skill discovery. Nothing is silently overwritten.
Missing source files and link failures are errors, with a Windows privilege hint when applicable.

Existing whole-folder skill links to this checkout are converted to real directories containing
per-skill links. With Codex selected, old repo-owned links under `~/.codex/skills` are removed
only after their replacements exist under `~/.agents/skills`; unrelated entries and `.system`
remain. Broken links are pruned only when their target exactly matches this checkout's expected
skill path. Tool-managed content previously written through a whole-folder link must still be
moved out of the repository manually; setup warns when converting it.

After adding or renaming a top-level skill, rerun setup. Edits inside already-linked skills are
visible immediately after `git pull`; restart clients if they cache their skill lists.
Claude's status line also needs its machine-local settings entry and a terminal font; see
[`statusline/README.md`](statusline/README.md).

### Optional dependencies and MCP

- PR helpers use PowerShell 7 and an authenticated `gh` CLI on Windows, Linux, or macOS. From Bash, invoke
  them with `pwsh -NoProfile -File <script.ps1>`.
- The Claude status line needs Node.js and Git.
- Word editing helpers require **Windows and desktop Microsoft Word**. They report that
  requirement explicitly on Linux and macOS.
- MCP configuration is a separate opt-in step; see [`mcp/README.md`](mcp/README.md). Docker
  Engine alone is insufficient: the profiles also require the Docker MCP Toolkit and their
  configured secret backend. Credentials and generated configuration stay machine-local.

### Validation

```sh
pwsh -NoProfile -File ./tests/Setup.Tests.ps1
pwsh -NoProfile -File ./tests/Mcp.Tests.ps1
```

These offline tests create temporary homes, exercise migration and conflicts, and mock MCP CLI
commands. The GitHub Actions workflow runs them on Windows and Ubuntu. The same scripts are
written for macOS, but macOS is not currently in the CI matrix.

### Cross-Tool Authoring Notes

Skills here target the lowest common denominator so they work everywhere:

- `name` and `description` are the only required and universally-honored frontmatter keys
- Directory names match the frontmatter `name`
- Tool references are described as capabilities (e.g. "Context7 docs", "IDE diagnostics") rather than literal tool IDs, which differ per host
- Cross-references are **skill-relative** (`../other-skill/SKILL.md`), never repo-root-relative — the tree is symlinked into user-level folders where no repo root exists
- `skills/pr-scripts/` holds shared PowerShell helpers rather than a skill. It is linked alongside the skills because sibling-relative references from PR skills depend on it; having no `SKILL.md`, it never enters a tool's skill catalog. `README.md` there is the script inventory; `REFERENCE.md` is the shared agent-facing usage, decision matrix, and reply templates that `pr-feedback`, `pr-resolve`, and `pr-review` all link to
- `instructions/CLAUDE.md` is the user-level global instruction file, linked only into Claude Code for the same reason. It loads into every session in every project, so keep it short and keep every line load-bearing
- `agents/` is Claude Code's subagent format and is deliberately **not** cross-tool — other hosts use incompatible agent formats, so the setup script links it into Claude Code only. Keep agent bodies host-generic and project-agnostic (no employer, stack, or repository specifics) so they behave the same in every project. Agents may depend on `skills/` two ways — a relative path such as `../skills/pr-scripts/…`, which resolves in both the repository and `~/.claude/`, and a `skills:` frontmatter entry naming a skill to preload. `researcher` also names specific documentation MCP servers in its `tools` list; adjust that line on a machine where those servers are not configured

Codex custom agents use standalone TOML files under `~/.codex/agents/` (or `.codex/agents/` for one repository), so the Claude Markdown files in `agents/` cannot be linked there directly. If Codex equivalents are added later, keep them in a separate source folder and link those TOML files into `~/.codex/agents/`; share behavioral instructions deliberately, but translate model, reasoning, sandbox, MCP, and skill settings to Codex's schema.

### Progressive Disclosure

Large skills keep `SKILL.md` lean and push detail into a `references/` subfolder, which loads
only when `SKILL.md` points at it. `SKILL.md` carries the workflow, decisions, and pitfalls;
`references/` carries code libraries, command tables, and long worked examples. Currently used
by `ecommerce-patterns`, `firecrawl`, `seo-aeo-structured-data`, `story`, and `upgrade`.

### Host-Specific Frontmatter

Claude Code accepts extra frontmatter keys; other hosts ignore unknown keys, so using them does
not break portability. Several skills set them:

| Key                        | Used for                                                                                            |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| `model`                    | Pinning a cheaper tier on mechanical skills (`commit`, `tt`, `story`, `pr-resolve`, `pr-authoring`) |
| `effort`                   | Tuning reasoning depth without changing model tier (`firecrawl` runs `sonnet` at `high`)            |
| `disable-model-invocation` | User-typed `/name` only (`pr-consolidate`, whose merges are destructive)                            |

Skills that are _consumed inside another task_ rather than invoked directly — the standards and
pattern skills — deliberately set no `model`, so they inherit whatever the calling workflow uses.
`firecrawl` is the exception: it is tool-driving work, so it pins `sonnet` to stay cheap under an
Opus session while keeping `effort: high`, because choosing the right rung of the search/scrape/crawl
ladder and writing a good query is where its judgment actually goes.
See the `skill-authoring` skill for the full key list and selection guidance.

Codex ignores Claude-only skill keys such as `model: sonnet`, `effort`, and `disable-model-invocation`; they do not select an Anthropic model or prevent the skill from loading. When a Claude-only key carries behavior that must also hold in Codex, add the Codex equivalent in the skill's optional `agents/openai.yaml`. In particular, Codex's equivalent of `disable-model-invocation: true` is `policy.allow_implicit_invocation: false`.

## Customization

### Tools

MCP tools (Context7, Perplexity, GitHub) are referenced from skills that benefit from research or PR capabilities. Skills still work with reduced functionality if those tools are not configured.

### Skill Descriptions

Skills auto-load based on their `description` frontmatter. To make a skill trigger on different phrasing, edit its description to include the trigger phrases you use.

## Requirements

- VS Code 1.106+ with GitHub Copilot, Claude Code, and/or Codex
- `gh` CLI (authenticated) and PowerShell for the PR workflows
- Optional: MCP servers (Context7, Perplexity, GitHub) for richer research and PR workflows
