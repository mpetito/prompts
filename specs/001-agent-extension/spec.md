# Feature Specification: VS Code Custom Agents Extension

**Branch**: `feature/001-agent-extension` | **Date**: 2026-01-16 | **Status**: Draft  
**Context**: The repository contains custom agent files (`.agent.md`) in `.github/agents/` that are shared across workstations. Currently, these agents are only discoverable when the repository is opened as a workspace. This extension will expose them globally to VS Code Copilot Chat via the proposed `chatPromptFiles` API.

## Objective

- Implement a VS Code extension that exposes custom agent files (`.agent.md`) from this repository to VS Code's Copilot Chat, enabling the agents to be available across all workspaces

## Scope

**In scope**:
- VS Code extension scaffolding with TypeScript
- Programmatic registration via `vscode.chat.registerCustomAgentProvider()`
- Programmatic registration via `vscode.chat.registerPromptFileProvider()`
- Programmatic registration via `vscode.chat.registerInstructionsProvider()`
- Hot-reload capability via `FileSystemWatcher` and `onDidChange*` events
- Auto-discovery of `.agent.md` files in `.github/agents/`
- Auto-discovery of `.prompt.md` files in `.github/prompts/` and `fragments/`
- Auto-discovery of `.instructions.md` files in `.github/instructions/`
- Auto-discovery of `SKILL.md` files in `.github/skills/{skill_name}/SKILL.md`
- Debug/launch configuration with proposed API enabled
- Documentation for setup and usage

**Out of scope**:
- Publishing to VS Code Marketplace (proposed API restriction)
- Declarative approach (lacks hot-reload capability)
- Custom UI or webview components
- Settings/configuration UI
- Configurable search directories (fixed to `.github/` structure)

## Clarifications

- Q: Should the extension use declarative (package.json) or programmatic API?  
  → A: **Programmatic approach** via `vscode.chat.registerCustomAgentProvider()`. This enables hot-reload capability when agent files change, which is essential for iterative development. Requires TypeScript and the `chatPromptFiles` proposed API.

- Q: What directories contain agent and prompt files?  
  → A: Fixed directory structure:
    - `.github/agents/` for `.agent.md` files
    - `.github/prompts/` and `fragments/` for `.prompt.md` files
    - `.github/instructions/` for `.instructions.md` files
    - `.github/skills/` for `SKILL.md` files

- Q: What VS Code version is required?  
  → A: `^1.106.0` minimum (`chatPromptFiles` API requires VS Code 1.105+)

- Q: Is the `--enable-proposed-api` flag required?  
  → A: **Yes**. The programmatic API (`registerCustomAgentProvider`, `registerPromptFileProvider`) calls `checkProposedApiEnabled(extension, 'chatPromptFiles')` internally. Extension must declare `enabledApiProposals: ["chatPromptFiles"]` in package.json and VS Code must be launched with `--enable-proposed-api=<extension-id>`.

## User Stories & Acceptance

### Story 1: Extension Activation
As a developer, I want the extension to activate automatically when VS Code starts, so that my custom agents are available without manual intervention.

**Acceptance Criteria**:
- Extension activates on `onStartupFinished` event
- Console logs confirm successful activation
- Warning displayed if proposed API is unavailable

### Story 2: Agent Discovery
As a developer, I want the extension to discover all `.agent.md` files in the repository, so that all my custom agents are exposed to Copilot Chat.

**Acceptance Criteria**:
- All `.agent.md` files in `.github/agents/` are discovered
- Files in `node_modules/`, `out/`, and hidden directories (except `.github`) are excluded
- Agent files appear in Copilot Chat's agent selector

### Story 3: Hot Reload
As a developer, I want agent file changes to be detected automatically, so that I can iterate on agents without restarting VS Code.

**Acceptance Criteria**:
- Adding a new `.agent.md` file triggers agent list refresh
- Modifying an existing agent file triggers refresh
- Deleting an agent file triggers refresh
- No manual refresh or restart required

### Story 4: Development Experience
As a developer, I want to debug and test the extension easily, so that I can iterate on the implementation.

**Acceptance Criteria**:
- F5 launches extension in debug mode with proposed API enabled
- TypeScript watch mode available for development
- Comprehensive console logging for troubleshooting

## Requirements

### Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| FR1 | Extension registers agents via `vscode.chat.registerCustomAgentProvider()` | Must |
| FR2 | Extension registers prompts via `vscode.chat.registerPromptFileProvider()` | Must |
| FR3 | Extension registers instructions via `vscode.chat.registerInstructionsProvider()` | Must |
| FR4 | Extension auto-discovers `.agent.md` files in `.github/agents/` at startup | Must |
| FR5 | Extension auto-discovers `.prompt.md` files in `.github/prompts/` and `fragments/` | Should |
| FR6 | Extension auto-discovers `.instructions.md` files in `.github/instructions/` | Should |
| FR7 | Extension auto-discovers `SKILL.md` files in `.github/skills/{skill_name}/SKILL.md` | Should |
| FR8 | Extension extracts `name` and `description` from YAML frontmatter | Must |
| FR9 | Extension watches for file changes and fires `onDidChange*` events | Must |
| FR10 | Extension can be loaded in debug mode via F5 with proposed API | Must |

### Non-Functional Requirements

| ID | Requirement | Priority |
|----|-------------|----------|
| NFR1 | Extension activates within 500ms of `onStartupFinished` | Must |
| NFR2 | File watcher responds to changes within 1 second | Should |
| NFR3 | TypeScript compiles without errors | Must |
| NFR4 | Works on Windows, macOS, and Linux | Should |

## Data & Interfaces

### Inputs
- **File System**: `.agent.md` files anywhere in the repository
- **VS Code API**: `vscode.chat.registerCustomAgentProvider()` (proposed)
- **Context**: `vscode.ExtensionContext` providing extension path

### Outputs
- **CustomAgentChatResource[]**: Array of agent resources with URIs to agent files
- **Events**: `onDidChangeCustomAgents` fired when agent files change
- **Logging**: Console output for debugging and troubleshooting

### Contracts

**CustomAgentProvider Interface**:
```typescript
interface CustomAgentProvider {
  readonly label: string;
  readonly onDidChangeCustomAgents?: Event<void>;
  provideCustomAgents(
    context: CustomAgentContext,
    token: CancellationToken
  ): ProviderResult<CustomAgentChatResource[]>;
}
```

**Agent File Format** (YAML frontmatter):
```yaml
---
name: Agent Name
description: Agent description
tools: [tool1, tool2]
model: model-id
---
System prompt content...
```

## Technical Design

### Directory Structure

```
prompts/
├── .vscode/
│   ├── launch.json           # Debug configuration with --enable-proposed-api
│   └── tasks.json            # Build tasks
├── .github/
│   ├── agents/               # Agent files (existing)
│   │   ├── exec.agent.md
│   │   ├── plan.agent.md
│   │   ├── review.agent.md
│   │   └── ...
│   ├── prompts/              # Prompt files
│   │   └── *.prompt.md
│   ├── instructions/         # Instruction files
│   │   └── *.instructions.md
│   └── skills/               # Skill files (per GitHub Agent Skills standard)
│       └── {skill_name}/SKILL.md
├── fragments/                # Existing prompt fragments
│   └── snyk-upgrade-review.prompt.md
├── src/
│   ├── extension.ts          # Extension entry point
│   ├── agentProvider.ts      # CustomAgentProvider implementation
│   ├── promptProvider.ts     # PromptFileProvider implementation
│   ├── instructionsProvider.ts # InstructionsProvider implementation
│   └── utils/
│       ├── fileDiscovery.ts  # File discovery and watching
│       └── frontmatter.ts    # YAML frontmatter parsing
├── package.json              # Extension manifest
├── tsconfig.json             # TypeScript configuration
├── .vscodeignore             # Package exclusions
└── [existing files...]
```

### Key Implementation Details

1. **Programmatic Registration**: Agents, prompts, and instructions registered via their respective `vscode.chat.register*Provider()` APIs
2. **Proposed API**: Requires `enabledApiProposals: ["chatPromptFiles"]` in package.json and `--enable-proposed-api` flag
3. **Hot-Reload**: `FileSystemWatcher` monitors all resource directories and fires `onDidChange*` events on file changes
4. **File Format**: YAML frontmatter with `name`, `description`, and optional `tools`/`model` fields
5. **Type Definitions**: Copy `vscode.proposed.chatPromptFiles.d.ts` from VS Code source for type safety
6. **Reference Implementation**: Pattern follows `microsoft/vscode-copilot-chat` `OrganizationAndEnterpriseAgentProvider`
7. **Skills**: `SKILL.md` files per [GitHub Agent Skills standard](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), discovered in `.github/skills/{skill_name}/SKILL.md`

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Proposed API changes in future VS Code versions | High | Medium | Pin to specific API version, monitor VS Code release notes |
| API not available without `--enable-proposed-api` flag | Certain | High | Clear documentation, graceful error handling with user notification |
| File watcher performance with large repositories | Low | Low | Exclude `node_modules` and build directories from scanning |
| Type definitions drift from actual API | Medium | Medium | Copy types from official VS Code source, version-pin definitions |

## Open Questions

1. ~~Should we also support `.prompt.md` and `.instructions.md` files?~~ → **Resolved: Yes, supporting agents, prompts, instructions, and skills**
2. ~~Should there be a configuration option to customize the search directories?~~ → **Resolved: No, using fixed `.github/` directory structure**
3. ~~Should instructions (`.instructions.md`) also be supported via `registerInstructionsProvider()`?~~ → **Resolved: Yes**

## References

- [GitHub Agent Skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) - Official documentation for `SKILL.md` file structure and organization
- [microsoft/vscode-copilot-chat](https://github.com/microsoft/vscode-copilot-chat) - Official Copilot Chat extension with `OrganizationAndEnterpriseAgentProvider` pattern
- [VS Code Proposed API: chatPromptFiles](https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.proposed.chatPromptFiles.d.ts)
- [VS Code extHost.api.impl.ts](https://github.com/microsoft/vscode/blob/main/src/vs/workbench/api/common/extHost.api.impl.ts) - API implementation showing proposed API checks
- [microsoft/hve-core](https://github.com/microsoft/hve-core) - Reference for declarative contributions (alternative approach)
