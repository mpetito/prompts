# Documentation

## Guides

Current reference for using and changing the repository.

| Document | Covers |
| --- | --- |
| [setup.md](setup.md) | Linking skills, agents, instructions and the status line into each client; overrides, conflicts, migration, optional dependencies |
| [authoring.md](authoring.md) | Cross-tool portability rules, progressive disclosure, Claude-only frontmatter, agent format |
| [agents.md](agents.md) | The subagents: what each is for, model tiers, write access, output contracts |
| [plugins.md](plugins.md) | The Claude Code plugins every machine should have, and the commands to install them |
| [agent-model-selection.md](agent-model-selection.md) | The canonical policy for choosing a worker's model before any delegation |
| [evaluating-skills.md](evaluating-skills.md) | Running, reading and writing a skill's or agent's eval suite |
| [skill-audit/readmission.md](skill-audit/readmission.md) | The bar an archived or new skill must clear to enter `skills/` |
| [skill-audit/candidates.md](skill-audit/candidates.md) | The ledger of observed gaps that start a readmission |

Component guides live beside their code: [`mcp/README.md`](../mcp/README.md) for the MCP
profiles and [`statusline/README.md`](../statusline/README.md) for the Claude status line.
How to commit and what to run first is in [CONTRIBUTING.md](../CONTRIBUTING.md).

## Records

Dated evidence, specs and retrospectives. They describe the repository as it was when written
and are not updated afterwards.

| Folder | Contents |
| --- | --- |
| [skill-audit/](skill-audit/) | The 2026-10-09 archive of every skill (best-practice reviews, usage data, synthesis) and the retrospective and digest for each readmission |
| [orchestration/](orchestration/) | The two-thread orchestration spike, the herdr mailbox spike, and the herdr rework spec and plan |
| [tooling/python-migration/](tooling/python-migration/) | The spec, plan, performance notes and Windows results for porting the tooling to Python |

Superseded research (the prompts-to-skills consolidation, VS Code virtual tools, an orientation
written for another coordinator) is in [`archive/docs/`](../archive/docs/).
