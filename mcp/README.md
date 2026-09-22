# MCP profiles

This directory is the source-controlled registry for the MCP tools used by Claude Code, Codex, and OpenCode.

- `core-dev` contains general development and research tools.
- `envative` contains company-specific tools.
- Both profiles are intentionally disjoint because each selected client connects to both profiles.
- Dynamic MCP is disabled so profile contents remain explicit and reproducible.
- Tool-name prefixes are enabled so each exposed tool retains its source server identity (for example, Azure DevOps rather than only `core_list_projects`).

Run these commands from the repository root with **PowerShell 7.4+** on Windows or Ubuntu:

```sh
pwsh -NoProfile -File ./mcp/bootstrap/install.ps1 -WhatIf
pwsh -NoProfile -File ./mcp/bootstrap/install.ps1
pwsh -NoProfile -File ./mcp/bootstrap/verify.ps1
```

MCP setup is optional and independent of skill linking. Prerequisites are Docker with a running
daemon, a compatible **Docker MCP Toolkit** (`docker mcp version`), and the secret backend used
by the profiles (`docker-desktop-store`). Docker Engine alone, including a normal Ubuntu Docker
installation, does not supply these. The installer checks the plugin, daemon, and secret listing
before builds or client changes. Installing or configuring the Docker MCP backend is a separate
machine setup step; these scripts do not install system packages or silently choose another
secret provider. See [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/).

By default the installer detects `codex`, `claude`, and `opencode` on PATH. Missing clients are
skipped; `-Tools codex,claude` narrows the selection. A preview can describe registrations for
clients not yet installed, but applying MCP setup requires the selected CLIs. Copilot MCP
registration is not managed by this bootstrap.

The installer builds the pinned local wrappers, enables source-server tool prefixes, imports
both profiles, refreshes the two managed catalogs, optionally migrates credentials into Docker's
secret store, and registers the gateways with selected clients. Codex uses a 30-second startup
timeout; OpenCode uses a 30,000 ms tool-fetch timeout. Harvest, Estimator, and GitHub use
gateway-managed OAuth.

When installing another client after the gateways are ready, reuse them without rebuilding:

```sh
pwsh -NoProfile -File ./mcp/bootstrap/install.ps1 -Tools opencode -SkipGatewaySetup -SkipCredentialMigration
```

`-SkipGatewaySetup` checks that the existing profiles are accessible. `-SkipCredentialMigration`
leaves Docker secrets untouched. `-WhatIf` makes no changes and invokes no external commands,
so it can be used before installing Docker MCP. Actual command failures stop the installer
instead of allowing a misleading success message.

Codex and Claude registrations use their CLIs. Existing configuration files receive uniquely
named `.prompts-backup-*` copies before changes. Only the two `MCP_DOCKER_*` names are managed;
other registrations remain. Keep backups private, since client configuration may hold secrets.

OpenCode registration merges these names into the existing `mcp` object and retains other
settings. It uses `OPENCODE_CONFIG` when set; otherwise `OPENCODE_CONFIG_DIR`, or
`$XDG_CONFIG_HOME/opencode` (default `~/.config/opencode`). An existing `opencode.jsonc` is
preferred over `opencode.json`. JSONC is accepted, including comments and trailing commas;
**a changed file is formatted as JSON, with its original comments retained in the backup**.
A configuration already containing the expected entries is left untouched. Project and runtime
OpenCode overrides can still supersede these entries; inspect `opencode mcp list` in the project
where you use it. See [OpenCode config](https://opencode.ai/docs/config/) and
[MCP format](https://opencode.ai/docs/mcp-servers/).

`CODEX_HOME` and `CLAUDE_CONFIG_DIR` are honored. Skills and MCP share portable path resolution;
no Windows user-profile paths are embedded in the scripts. Credentials can come from
`AZURE_DEVOPS_PAT`, `SONAR_TOKEN`, `AGENTMAIL_API_KEY`, and `FIRECRAWL_API_KEY` in the process
environment. Credential migration also checks existing Claude AgentMail/Firecrawl settings and,
on Windows only, the persisted user-level `AZURE_DEVOPS_PAT` and `SONAR_TOKEN`. Secret values
are sent through stdin, never command-line arguments. AWS credentials and OAuth remain
machine-local setup steps.

After installation, authorize hosted servers as needed:

```powershell
docker mcp oauth authorize harvest-time --open-browser
docker mcp oauth authorize estimator --open-browser
docker mcp oauth authorize github --open-browser
```

AgentMail currently uses its existing API key through Docker's secret store because its hosted server is not yet available in Docker's public catalog for the standalone OAuth command.

The Envative KB uses a dedicated IAM access key stored as `envative-kb.aws_access_key_id` and `envative-kb.aws_secret_access_key` in Docker Desktop's secret store. Its policy permits only `bedrock-agentcore:InvokeGateway` against the estimator gateway. The access key is machine-local and is never committed.

No general-purpose AWS tooling server runs in either profile. Docker Gateway refuses to bind-mount any host path containing an `.aws` segment, so a containerized AWS server cannot reach the host's SSO profiles. The `deploy-on-aws` plugin for Claude Code covers this instead: it supplies AWS documentation through the hosted `knowledge-mcp.global.api.aws` endpoint, plus IaC and pricing servers that run on the host and read the AWS CLI profiles directly. Codex has no plugin equivalent and therefore no AWS tooling through this registry.

Azure DevOps uses the local server's headless `envvar` authentication mode. The installer copies `AZURE_DEVOPS_PAT` into Docker's secret store as `azure-devops.pat` and injects it into the container as `ADO_MCP_AUTH_TOKEN`; the PAT itself is never committed.

The Azure DevOps remote server is preferred, but Microsoft Entra currently rejects Docker Gateway's dynamic client-registration discovery. The pinned local server remains in use until the remote endpoint supports DCR or CIMD for third-party clients.

SonarQube runs the upstream `sonarsource/sonarqube-mcp` image pinned by digest rather than the
Docker catalog's `mcp/sonarqube`, whose only tag was last pushed months behind the pinned build
and therefore misses both feature and security releases. It is scoped to
`SONARQUBE_TOOLSETS=issues`, which exposes five tools instead of eighteen; the `projects`
toolset is always on because other tools need project keys. The hosted `api.sonarcloud.io/mcp`
endpoint is a supported alternative but currently serves an older build whose
`change_sonar_issue_status` takes no `comment` parameter. Issue triage is limited to `accept`,
`falsepositive`, and `reopen` on one issue per call; assignment, severity changes, and bulk
edits are not available through MCP and need the SonarQube web API.

Machine-specific values can be supplied to the installer:

```powershell
pwsh -NoProfile -File ./mcp/bootstrap/install.ps1 -AwsRegion us-east-1
```

Playwright runs inside Docker. On Docker Desktop, use `host.docker.internal` to reach a host
development server. On standalone Linux Docker, host access depends on the gateway/container
network configuration; do not assume that hostname is available automatically.

Run `pwsh -NoProfile -File ./mcp/bootstrap/verify.ps1` from the repository root to validate both
gateways and list detected clients' registrations. Use `-Tools` to narrow the client checks.
This verification can start gateway containers and contact configured services; the offline
regression tests in `tests/` mock those calls instead.
