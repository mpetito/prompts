# Implementation Plan: VS Code Custom Agents Extension

## Summary

Implement a VS Code extension that exposes custom agent files (`.agent.md`), prompt files (`.prompt.md`), instruction files (`.instructions.md`), and skill files (`SKILL.md`) from this repository to VS Code's Copilot Chat using the **programmatic `chatPromptFiles` API**. This approach enables hot-reload capability when files change, essential for iterative development.

## Research Findings

| Finding | Source | Implication |
|---------|--------|-------------|
| Programmatic API requires `checkProposedApiEnabled(extension, 'chatPromptFiles')` | VS Code source `extHost.api.impl.ts` | Extension must declare proposed API and use `--enable-proposed-api` flag |
| `registerCustomAgentProvider()` returns `Disposable` | VS Code proposed API types | Provider can be disposed on deactivation |
| `registerInstructionsProvider()` available for instructions | VS Code proposed API types | Instructions and skills use this provider |
| `onDidChangeCustomAgents` event enables hot-reload | Proposed API types | File watcher can trigger refresh without restart |
| `CustomAgentChatResource` requires URI to agent file | Proposed API types | Use `vscode.Uri.file()` to create resource URIs |
| `OrganizationAndEnterpriseAgentProvider` pattern | `microsoft/vscode-copilot-chat` | Reference for implementing dynamic agent providers |

## Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| API approach | **Programmatic** (`register*Provider()`) | Enables hot-reload; essential for iterative development |
| File discovery | TypeScript with `vscode.workspace.findFiles()` | Native VS Code API, respects `.gitignore` |
| Hot-reload | `FileSystemWatcher` + `onDidChange*` events | Automatic refresh when files change |
| TypeScript | **Required** | Programmatic API requires extension code |
| Proposed API | `chatPromptFiles` | Must use `--enable-proposed-api` flag |
| Reference | `microsoft/vscode-copilot-chat` | Production-grade pattern from Microsoft |
| Directory structure | Fixed `.github/` paths | No configuration needed, consistent with conventions |

## Implementation Steps

### Phase 1: Extension Scaffolding

1. [ ] Create `package.json` with extension manifest
   - Set `engines.vscode: "^1.106.0"`
   - Set `main: "./out/extension.js"`
   - Set `activationEvents: ["onStartupFinished"]`
   - Add `enabledApiProposals: ["chatPromptFiles"]`
   - Set `categories: ["Chat"]`

2. [ ] Create `tsconfig.json` for TypeScript compilation
   - Target ES2020, module commonjs
   - Output to `./out` directory
   - Strict mode enabled

3. [ ] Create `.vscode/launch.json` with debug configuration
   - Include `--enable-proposed-api=local.local-custom-agents`
   - Configure pre-launch compile task

4. [ ] Create `.vscode/tasks.json` with build tasks
   - `npm: compile` task for building
   - `npm: watch` task for development

5. [ ] Copy `vscode.proposed.chatPromptFiles.d.ts` from VS Code source
   - Place in project root or `src/types/`
   - Reference in `tsconfig.json`

6. [ ] Create `.vscodeignore` for extension packaging
   - Exclude `src/`, `specs/`, `docs/`, `node_modules/`

7. [ ] **Verification**: `npm run compile` succeeds, F5 launches debug host

### Phase 2: Core Implementation

1. [ ] Create `src/extension.ts` - Extension entry point
   - `activate()`: Register providers, set up file watchers
   - `deactivate()`: Dispose providers and watchers
   - Log activation status to console

2. [ ] Create `src/utils/fileDiscovery.ts` - File discovery utilities
   - `discoverAgentFiles()`: Find `.agent.md` in `.github/agents/`
   - `discoverPromptFiles()`: Find `.prompt.md` in `.github/prompts/` and `fragments/`
   - `discoverInstructionFiles()`: Find `.instructions.md` in `.github/instructions/`
   - `discoverSkillFiles()`: Find `SKILL.md` in `.github/skills/{skill_name}/SKILL.md`
   - Use `vscode.workspace.findFiles()` with glob patterns

3. [ ] Create `src/utils/frontmatter.ts` - YAML frontmatter parsing
   - `parseFrontmatter(content: string)`: Extract name, description, tools, model
   - Handle missing fields gracefully with filename fallback

4. [ ] Create `src/agentProvider.ts` - CustomAgentProvider implementation
   - Implement `provideCustomAgents()` returning `CustomAgentChatResource[]`
   - Implement `onDidChangeCustomAgents` event emitter
   - Create `FileSystemWatcher` for `.github/agents/**/*.agent.md`

5. [ ] Create `src/promptProvider.ts` - PromptFileProvider implementation
   - Implement `providePromptFiles()` returning `PromptFileChatResource[]`
   - Implement `onDidChangePromptFiles` event emitter
   - Create `FileSystemWatcher` for prompt directories

6. [ ] Create `src/instructionsProvider.ts` - InstructionsProvider implementation
   - Implement `provideInstructions()` returning `InstructionsChatResource[]`
   - Include both `.instructions.md` files and `SKILL.md` files
   - Implement `onDidChangeInstructions` event emitter
   - Create `FileSystemWatcher` for `.github/instructions/` and `.github/skills/`

7. [ ] **Verification**: Extension compiles, all providers registered on activation

### Phase 3: Hot-Reload & File Watching

1. [ ] Implement file watcher in `agentProvider.ts`
   - Watch `.github/agents/**/*.agent.md` for create/change/delete
   - Fire `onDidChangeCustomAgents` event on any change
   - Debounce rapid file changes (100ms)

2. [ ] Implement file watcher in `promptProvider.ts`
   - Watch `.github/prompts/**/*.prompt.md` and `fragments/**/*.prompt.md`
   - Fire `onDidChangePromptFiles` event on any change

3. [ ] Implement file watcher in `instructionsProvider.ts`
   - Watch `.github/instructions/**/*.instructions.md`
   - Watch `.github/skills/*/SKILL.md` (one level deep per Agent Skills standard)
   - Fire `onDidChangeInstructions` event on any change

4. [ ] Test hot-reload scenarios
   - Add new `.agent.md` file → appears in Copilot Chat immediately
   - Add new `.instructions.md` or `SKILL.md` file → appears immediately
   - Modify existing file → changes reflected without restart
   - Delete file → removed from Copilot Chat

5. [ ] **Verification**: All hot-reload scenarios work without F5 restart

### Phase 4: Testing & Documentation

1. [ ] Test extension in debug mode
   - Verify agents appear in `@` agent dropdown
   - Verify prompts appear in `/` prompt dropdown
   - Verify instructions and skills appear in instructions panel
   - Test selecting and using an agent
   - Test hot-reload scenarios for all resource types

2. [ ] Update `README.md` with extension documentation
   - Prerequisites (VS Code 1.106+, proposed API flag)
   - Setup instructions (`npm install`, `npm run compile`, F5)
   - Hot-reload behavior explanation
   - Adding new agents, prompts, instructions, and skills guide
   - Troubleshooting

3. [ ] Create resource directories
   - `.github/prompts/` for prompt files
   - `.github/instructions/` for instruction files
   - `.github/skills/` for skill files

4. [ ] **Verification**: Full workflow documented and tested

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `package.json` | Create | Extension manifest with proposed API declaration |
| `tsconfig.json` | Create | TypeScript compilation configuration |
| `.vscode/launch.json` | Create | Debug configuration with `--enable-proposed-api` |
| `.vscode/tasks.json` | Create | Build and watch tasks |
| `src/extension.ts` | Create | Extension entry point (activate/deactivate) |
| `src/agentProvider.ts` | Create | CustomAgentProvider implementation |
| `src/promptProvider.ts` | Create | PromptFileProvider implementation |
| `src/utils/fileDiscovery.ts` | Create | File discovery utilities |
| `src/utils/frontmatter.ts` | Create | YAML frontmatter parsing |
| `vscode.proposed.chatPromptFiles.d.ts` | Copy | Type definitions from VS Code source |
| `.vscodeignore` | Create | Exclude src, specs from packaged extension |
| `.github/prompts/` | Create | Directory for prompt files |
| `README.md` | Modify | Add extension documentation |

## Testing Strategy

### Manual Testing
- [ ] Extension compiles without TypeScript errors
- [ ] Extension loads in F5 debug mode with proposed API
- [ ] Agents from `.github/agents/` appear in Copilot Chat `@` dropdown
- [ ] Prompts appear in Copilot Chat `/` dropdown
- [ ] Instructions and skills appear in instructions panel
- [ ] Selecting an agent loads its system prompt
- [ ] Hot-reload: Adding new agent file triggers refresh
- [ ] Hot-reload: Adding new instruction/skill file triggers refresh
- [ ] Hot-reload: Modifying any file triggers refresh
- [ ] Hot-reload: Deleting any file triggers refresh

### Verification Commands
```powershell
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch mode for development
npm run watch

# Launch debug (or press F5)
code --extensionDevelopmentPath="$PWD" --enable-proposed-api=local.local-custom-agents
```

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| VS Code version too old | Clear documentation of 1.106+ requirement |
| Proposed API changes in future versions | Pin to specific API version, copy type definitions |
| `--enable-proposed-api` flag forgotten | Clear launch.json configuration, startup warning |
| File watcher performance | Debounce rapid changes, exclude node_modules |
| YAML parsing failures | Regex-based fallback, graceful filename extraction |

## Dependencies

```
Phase 1 (Scaffolding) → Phase 2 (Implementation) → Phase 3 (Hot-Reload) → Phase 4 (Documentation)
```

All phases are sequential; implementation requires scaffolding, hot-reload requires working providers.

### npm Dependencies

```json
{
  "devDependencies": {
    "@types/vscode": "^1.106.0",
    "@types/node": "^20.x",
    "typescript": "^5.x"
  }
}
```

## Open Questions

1. ~~Should minimum VS Code version be updated to `^1.105.0`?~~ → **Resolved: Use `^1.106.0`**
2. ~~Should we add a root `agents/` directory?~~ → **Resolved: Use existing `.github/agents/`**
3. ~~Should `fragments/*.prompt.md` files be moved to `.github/prompts/`?~~ → **Resolved: Watch both directories**
4. ~~Should instructions (`.instructions.md`) also be supported via `registerInstructionsProvider()`?~~ → **Resolved: Yes, including `SKILL.md` files**
5. ~~Should there be configurable search directories?~~ → **Resolved: No, use fixed `.github/` structure**

## Estimated Effort

| Phase | Estimated Time |
|-------|----------------|
| Phase 1: Extension Scaffolding | 30 minutes |
| Phase 2: Core Implementation | 1.5 hours |
| Phase 3: Hot-Reload & File Watching | 30 minutes |
| Phase 4: Documentation | 30 minutes |
| **Total** | ~3 hours |

## Reference: package.json Structure

```json
{
  "name": "local-custom-agents",
  "displayName": "Local Custom Agents",
  "version": "0.0.1",
  "description": "Exposes custom agents and prompts from this repository to Copilot Chat",
  "publisher": "local",
  "engines": {
    "vscode": "^1.106.0"
  },
  "categories": ["Chat"],
  "main": "./out/extension.js",
  "activationEvents": ["onStartupFinished"],
  "enabledApiProposals": ["chatPromptFiles"],
  "scripts": {
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./"
  },
  "devDependencies": {
    "@types/vscode": "^1.106.0",
    "@types/node": "^20.x",
    "typescript": "^5.x"
  }
}
```

## Reference: launch.json Structure

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Extension",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}",
        "--enable-proposed-api=local.local-custom-agents"
      ],
      "outFiles": ["${workspaceFolder}/out/**/*.js"],
      "preLaunchTask": "npm: compile"
    }
  ]
}
```
