# MCP profiles

This directory is the source-controlled registry for the MCP tools used by Claude Code and Codex.

- `core-dev` contains general development and research tools.
- `envative` contains company-specific tools.
- Both profiles are intentionally disjoint because both clients connect to both profiles.
- Dynamic MCP is disabled so profile contents remain explicit and reproducible.
- Tool-name prefixes are enabled so each exposed tool retains its source server identity (for example, Azure DevOps rather than only `core_list_projects`).

Run `bootstrap/install.ps1` on each machine. It builds the pinned local wrappers, enables source-server tool prefixes, imports both profiles, migrates the existing AgentMail and Firecrawl keys into Docker Desktop's secret store, and connects Claude Code and Codex. The installer gives both Codex gateways a 30-second startup timeout. Harvest, Estimator, and GitHub use gateway-managed OAuth.

After installation, authorize hosted servers as needed:

```powershell
docker mcp oauth authorize harvest-time --open-browser
docker mcp oauth authorize estimator --open-browser
docker mcp oauth authorize github --open-browser
```

AgentMail currently uses its existing API key through Docker's secret store because its hosted server is not yet available in Docker's public catalog for the standalone OAuth command.

The Envative KB uses a dedicated IAM access key stored as `envative-kb.aws_access_key_id` and `envative-kb.aws_secret_access_key` in Docker Desktop's secret store. Its policy permits only `bedrock-agentcore:InvokeGateway` against the estimator gateway. The access key is machine-local and is never committed.

The managed AWS MCP Server uses SigV4 through `mcp-proxy-for-aws`. The installer requires an explicit list of AWS CLI profiles, mounts the host AWS configuration directory read-only into the proxy container, and allows the agent to select only those profiles. Run `aws sso login --profile <name>` on the host before using an SSO-backed profile. The first profile is the default for calls that do not specify one, and each profile supplies its own default AWS Region.

Azure DevOps uses the local server's headless `envvar` authentication mode. The installer copies `AZURE_DEVOPS_PAT` into Docker's secret store as `azure-devops.pat` and injects it into the container as `ADO_MCP_AUTH_TOKEN`; the PAT itself is never committed.

The Azure DevOps remote server is preferred, but Microsoft Entra currently rejects Docker Gateway's dynamic client-registration discovery. The pinned local server remains in use until the remote endpoint supports DCR or CIMD for third-party clients.

Machine-specific values can be supplied to the installer:

```powershell
.\bootstrap\install.ps1 `
    -AwsProfiles envative-dev,envative-prod-readonly `
    -AwsRegion us-east-1
```

Playwright runs inside Docker. Use `host.docker.internal` instead of `localhost` when it needs to reach a development server running on the host.

Run `bootstrap/verify.ps1` to enumerate tools through each gateway and show both client registrations.
