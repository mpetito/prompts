# Claude Code plugins

The plugins every machine should have, and how to bring a new one in line. Plugins are not
linked by setup: they install into `~/.claude/plugins/` and are enabled in `~/.claude/settings.json`,
which is machine-local and untracked. This file is the record to install from.

None of them are visible to skill evals, which load project settings only (see
[evaluating-skills.md](evaluating-skills.md#what-each-arm-can-see)). Readmission still compares
a skill against any of them it overlaps ([readmission bar](skill-audit/readmission.md)).

## Installed

User scope. Versions as of 2026-10-14. `claude-plugins-official` auto-updates in interactive
sessions, so its versions (12-character commits) can differ between machines at any moment.

| Plugin | Marketplace | Version | State |
| --- | --- | --- | --- |
| `code-review` | `claude-plugins-official` | `641d925db5a6` | enabled |
| `commit-commands` | `claude-plugins-official` | `641d925db5a6` | enabled |
| `pr-review-toolkit` | `claude-plugins-official` | `641d925db5a6` | enabled |
| `frontend-design` | `claude-plugins-official` | `641d925db5a6` | enabled |
| `playwright` | `claude-plugins-official` | `641d925db5a6` | enabled |
| `security-guidance` | `claude-plugins-official` | `2.0.13` | enabled |
| `typescript-lsp` | `claude-plugins-official` | `1.0.0` | enabled |
| `typesafe` | `typesafe-ai` (`typesafe-ai/skills`) | `0.5.7` | enabled |
| `code-simplifier` | `claude-plugins-official` | `1.0.0` | installed, disabled |

On a new machine, from Bash or PowerShell:

```sh
# A machine that has never opened an interactive session has no official marketplace yet.
claude plugin marketplace add anthropics/claude-plugins-official
claude plugin marketplace add typesafe-ai/skills

claude plugin install code-review@claude-plugins-official
claude plugin install commit-commands@claude-plugins-official
claude plugin install pr-review-toolkit@claude-plugins-official
claude plugin install frontend-design@claude-plugins-official
claude plugin install playwright@claude-plugins-official
claude plugin install security-guidance@claude-plugins-official
claude plugin install typescript-lsp@claude-plugins-official
claude plugin install typesafe@typesafe-ai
claude plugin install code-simplifier@claude-plugins-official
claude plugin disable code-simplifier@claude-plugins-official
```

`install` defaults to user scope. `typescript-lsp` also needs the language server itself:
`npm install -g typescript-language-server typescript`.

## Synced from claude.ai

`design`, `engineering`, `marketing` and `product-management` (`1.2.0`) are turned on for the
claude.ai account, not installed. They download to `~/.claude/plugins/synced/` on any machine
signed in to that account, with their skills, agents and MCP servers, so there is nothing to
run per machine. They appear as `<name>@synced`. To drop one on a machine, set
`"<name>@synced": false` under `enabledPlugins`; `syncClaudeAiPlugins: false` stops all of
them and moves copies already synced to `~/.claude/plugins/.trash/`
([synced plugins](https://code.claude.com/docs/en/plugins/loading.md#synced-plugins)).

## Check a machine

`claude plugin list` shows each plugin's version, scope and state, synced ones included;
`claude plugin list --json` gives the same for a diff between machines. After adding,
removing or disabling a plugin anywhere, update the table and the commands above.
