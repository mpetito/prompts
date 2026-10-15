# Agentic Coding Toolkit

Agent configuration shared across GitHub Copilot (VS Code + Copilot CLI), Claude Code, Codex,
and OpenCode: skills, subagent definitions, global instructions, and a status line. This
repository is the source of truth; setup symlinks it into each client's user-level folders, so
an edit here takes effect in every session immediately.

## Quick start

Needs Python 3.12+ as `python3`. From the repository root, in Bash or PowerShell:

```sh
python3 setup_skills_link.py --what-if   # preview
python3 setup_skills_link.py
python3 verify_setup.py
```

Setup detects clients on PATH; `--tools codex,claude,opencode,copilot` selects them explicitly.
Windows symlinks need Developer Mode or an elevated shell. Destinations, overrides, conflicts and
migration are in [docs/setup.md](docs/setup.md); MCP is a separate opt-in step in
[mcp/README.md](mcp/README.md).

## What's here

| Path | Contents | Linked into |
| --- | --- | --- |
| [`skills/`](skills/) | Readmitted skills, one folder each (`SKILL.md`, `references/`, `scripts/`, `evals/`) | Every client |
| [`agents/`](agents/) | Claude Code subagent definitions; see [docs/agents.md](docs/agents.md) | Claude Code |
| [`instructions/CLAUDE.md`](instructions/CLAUDE.md) | Global instructions loaded into every Claude session: attribution, delegation routing, model tiers | Claude Code |
| [`statusline/`](statusline/README.md) | Claude Code's custom status line | Claude Code |
| [`mcp/`](mcp/README.md) | MCP profiles and their bootstrap | Opt-in |
| `fragments/` | Prompt fragments for specialized workflows (`snyk-upgrade-review`) | Not linked |
| `archive/` | Archived skills and superseded docs | Not linked |
| `scripts/`, `tests/` | Eval runner, usage report, shared setup code, and the setup tests | Not linked |
| `evals/agents/` | Eval suites for the agent definitions | Not linked |
| [`docs/`](docs/README.md) | Guides and dated records | Not linked |

## Skills

**Skills are archived until readmitted.** On 2026-10-09 every skill moved to `archive/skills/`
so that each one has to earn its place back with real usage; the bar is
[docs/skill-audit/readmission.md](docs/skill-audit/readmission.md). Both VS Code and Claude Code
expose each skill as an explicit `/name` entry point, and every client auto-loads one when its
description matches.

| Skill | `/slash` invocation | Purpose |
| --- | --- | --- |
| [skill-authoring](skills/skill-authoring/SKILL.md) | `/skill-authoring` | Write, review, split or fix a skill folder |
| [review](skills/review/SKILL.md) | `/review` | Review a code change adversarially: size it by defect risk and blast radius, prove its tests can fail, give a verdict, and keep the repository's `REVIEW.md` scope brief current |
| [spec](skills/spec/SKILL.md) | `/spec` | Write a spec (what and why) and plan (how) with numbered open questions and their defaults, then carry the plan out, ticking each step as it lands |
| [plan-review](skills/plan-review/SKILL.md) | `/plan-review` | Review a plan, spec or design before work starts: cuts, blast radius, contracts, overlap, owner questions |
| [model-council](skills/model-council/SKILL.md) | `/model-council` | Settle one bounded technical decision by debate between a Claude and a Codex member: consensus, or `no consensus` with each position for the human |
| [firecrawl](skills/firecrawl/SKILL.md) | `/firecrawl` | Pull many pages with Firecrawl: a bounded crawl or a checked keyless scrape to files, and fields across pages as JSON |
| [orchestration-main](skills/orchestration-main/SKILL.md) | `/orchestration-main` | Run a multi-agent build from your own session: launch, steer and rotate orchestration threads, and keep your decisions in front of you |
| [project-setup](skills/project-setup/SKILL.md) | `/project-setup` | Set a repository up, or bootstrap an existing one, for agents: size and complexity caps as lint config with CI and a commit hook, and the files agents read (AGENTS.md, CLAUDE.md, copilot-instructions.md, REVIEW.md, CONTRIBUTING.md, `specs/`) |
| [code-style](skills/code-style/SKILL.md) | loaded by workers before they write code | Steer code toward the owner's pragmatic style: least mechanism, reuse what exists, trust your own callers, registry dispatch, contract-level comments, delete what a change replaces, tests that never match copy |
| [agent-orchestration](skills/agent-orchestration/SKILL.md) | loaded by the `orchestrator` agent | Run one build as an orchestration thread that reports to the main session; not invoked directly |
| [pull-request](skills/pull-request/SKILL.md) | `/pull-request` | Work a pull request: answer review feedback on your own PR (check each claim, fix what is right, reply to every thread, resolve or leave it open), open a PR or update its description, and post a review of someone else's PR once you approve the text |
| [playwright-e2e](skills/playwright-e2e/SKILL.md) | loaded by workers that write or run browser tests | Structure and run Playwright E2E tests that stay independent: the project's conventions for test data and layout (raised with the owner when unsettled), page objects through fixtures, no serial chains, anchored absence checks, and a port and capped workers per checkout on a shared machine |
| [review-lenses](skills/review-lenses/SKILL.md) | `/review-lenses`, or loaded by plan-review and review | Four review lenses (Reuse, Adopt, Reversibility, Trust boundary), a signals table for picking them, a rule for settling conflicts between them, and the lens finding prefix |

## How the pieces fit

Work with a spec runs `spec` → `plan-review` → `spec` (carrying out the plan under `code-style`)
→ `review`; bug fixes and refactors without a spec run `code-style` → `review`. `code-style`
holds the personal style rules (project conventions win); `review` judges the diff;
`pull-request` takes it through review feedback. When a review claim stays ambiguous after
checking the code and docs, `model-council` gets a blind Claude and Codex answer and reports
consensus or the crux for the human.
`plan-review` and `review` pick lenses from `review-lenses` while sizing a review and name
the picked and skipped lenses in the report.

These routes are stated in the skill bodies themselves, because Codex and other hosts do not
load `instructions/CLAUDE.md`; worker briefs name the skill for the same reason. Claude sessions
also get the delegation routing table from that file, which sends bounded work to the
[agents](docs/agents.md).

## Further reading

- [docs/](docs/README.md) — index of guides and records
- [CONTRIBUTING.md](CONTRIBUTING.md) — commit to `main`, the checks CI runs, changing or readmitting a skill
- [docs/authoring.md](docs/authoring.md) — cross-tool rules every skill and agent follows
- [docs/evaluating-skills.md](docs/evaluating-skills.md) — measuring whether a skill earns its tokens
