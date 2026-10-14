# Authoring skills and agents

Portability rules for everything this repository links into clients. The procedure for writing
a skill is [skill-authoring](../skills/skill-authoring/SKILL.md); the bar a skill must clear to
enter `skills/` is [skill-audit/readmission.md](skill-audit/readmission.md).

## Cross-tool rules

Skills here target the lowest common denominator so they work everywhere:

- `name` and `description` are the only required and universally-honored frontmatter keys
- Directory names match the frontmatter `name`
- Skills auto-load from their `description`; to make one trigger on different phrasing, put
  that phrasing in the description
- Tool references are described as capabilities (e.g. "Context7 docs", "IDE diagnostics") rather than literal tool IDs, which differ per host
- Cross-references are **skill-relative** (`../other-skill/SKILL.md`), never repo-root-relative — the tree is symlinked into user-level folders where no repo root exists
- `instructions/CLAUDE.md` is the user-level global instruction file, linked only into Claude Code. It loads into every session in every project, so keep it short and keep every line load-bearing
- A skill's helper scripts live in its own `scripts/` folder, with their tests beside them, so they link with the skill; `pull-request` keeps its two Python helpers there
- Scripts are Python 3.12+, standard library only. Skills and agents quote a script path and
  spell it with `$HOME`, never `~`, so bash and both PowerShells can run the same command

## Progressive disclosure

Large skills keep `SKILL.md` lean and push detail into a `references/` subfolder, which loads
only when `SKILL.md` points at it. `SKILL.md` carries the workflow, decisions, and pitfalls;
`references/` carries code libraries, command tables, and long worked examples. `firecrawl`
shows the pattern: a short `SKILL.md`, with its CLI and REST detail in `references/`.

## Host-specific frontmatter

Claude Code accepts extra frontmatter keys; other hosts ignore unknown keys, so using them does
not break portability:

| Key                        | Used for                                                                                |
| -------------------------- | --------------------------------------------------------------------------------------- |
| `model`                    | Pinning a cheaper tier on a mechanical skill                                            |
| `effort`                   | Tuning reasoning depth without changing model tier                                      |
| `disable-model-invocation` | No automatic loading (`agent-orchestration`, which only the `orchestrator` agent loads) |

Skills that are _consumed inside another task_ rather than invoked directly — `code-style`,
`playwright-e2e`, `firecrawl` — deliberately set no `model`, so they inherit whatever the
calling workflow uses. See [skill-authoring](../skills/skill-authoring/SKILL.md) for when to set
each key.

Codex ignores Claude-only skill keys such as `model: sonnet`, `effort`, and `disable-model-invocation`; they do not select an Anthropic model or prevent the skill from loading. When a Claude-only key carries behavior that must also hold in Codex, add the Codex equivalent in the skill's optional `agents/openai.yaml`. In particular, Codex's equivalent of `disable-model-invocation: true` is `policy.allow_implicit_invocation: false`.

## Agents

`agents/` is Claude Code's subagent format and is deliberately **not** cross-tool — other hosts
use incompatible agent formats, so the setup script links it into Claude Code only. Keep agent
bodies host-generic and project-agnostic (no employer, stack, or repository specifics) so they
behave the same in every project.

Agents may depend on a readmitted skill two ways: a relative path such as
`../skills/<name>/…`, which resolves in both the repository and `~/.claude/`, and a `skills:`
frontmatter entry naming a skill to preload. None does yet; agents carry what they need
inline. `researcher` names specific documentation MCP
servers in its `tools` list; adjust that line on a machine where those servers are not
configured.

Codex custom agents use standalone TOML files under `~/.codex/agents/` (or `.codex/agents/` for one repository), so the Claude Markdown files in `agents/` cannot be linked there directly. If Codex equivalents are added later, keep them in a separate source folder and link those TOML files into `~/.codex/agents/`; share behavioral instructions deliberately, but translate model, reasoning, sandbox, MCP, and skill settings to Codex's schema.
