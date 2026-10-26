# MCP profiles

This directory is the source-controlled registry for the MCP tools used by Claude Code, Codex, and OpenCode.

- `core-dev` contains general development and research tools.
- `envative` contains company-specific tools.
- Both profiles are intentionally disjoint because each selected client connects to both profiles.
- Dynamic MCP is disabled so profile contents remain explicit and reproducible.
- Tool-name prefixes are enabled so each exposed tool retains its source server identity (for example, Azure DevOps rather than only `core_list_projects`).
- Every client session shares one gateway per profile over streamable HTTP on loopback: `core-dev` at
  `http://127.0.0.1:8811/mcp` and `envative` at `http://127.0.0.1:8812/mcp`. See [Shared gateways](#shared-gateways).

Run these commands from the repository root with **Python 3.12+** (`python3`) on Windows or Ubuntu:

```sh
python3 mcp/bootstrap/install.py --what-if
python3 mcp/bootstrap/install.py
python3 mcp/bootstrap/gateways.py install
python3 mcp/bootstrap/verify.py
```

Restart Claude Code, Codex and OpenCode after the first `gateways.py install`, so they read the token it stores
(on Linux, from a new login).

MCP setup is optional and independent of skill linking. Prerequisites are Docker with a running
daemon, a compatible **Docker MCP Toolkit** (`docker mcp version`), and the secret backend used
by the profiles (`docker-desktop-store`). Docker Engine alone, including a normal Ubuntu Docker
installation, does not supply these. The installer checks the plugin, daemon, and secret listing
before builds or client changes. Installing or configuring the Docker MCP backend is a separate
machine setup step; these scripts do not install system packages or silently choose another
secret provider. See [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/).

By default the installer detects `codex`, `claude`, and `opencode` on PATH. Missing clients are
skipped; `--tools codex,claude` narrows the selection. A preview can describe registrations for
clients not yet installed, but applying MCP setup requires the selected CLIs. Copilot MCP
registration is not managed by this bootstrap.

The installer builds the pinned local wrappers, enables source-server tool prefixes, imports
both profiles, refreshes the two managed catalogs, optionally migrates credentials into Docker's
secret store, and registers the gateways with selected clients. Codex uses a 30-second startup
timeout; OpenCode uses a 30,000 ms tool-fetch timeout. Harvest, Estimator, and GitHub use
gateway-managed OAuth.

When installing another client after the gateways are ready, reuse them without rebuilding:

```sh
python3 mcp/bootstrap/install.py --tools opencode --skip-gateway-setup --skip-credential-migration
```

`--skip-gateway-setup` checks that the existing profiles are accessible. `--skip-credential-migration`
leaves Docker secrets untouched. `--what-if` makes no changes and invokes no external commands,
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

```sh
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

```sh
python3 mcp/bootstrap/install.py --aws-region us-east-1
```

Playwright runs inside Docker. On Docker Desktop, use `host.docker.internal` to reach a host
development server. On standalone Linux Docker, host access depends on the gateway/container
network configuration; do not assume that hostname is available automatically.

Run `python3 mcp/bootstrap/verify.py` from the repository root to validate both
profiles, check that both shared gateways answer `/health`, and list detected clients'
registrations. Use `--tools` to narrow the client checks.
This verification can start gateway containers and contact configured services; the offline
regression tests in `tests/` mock those calls instead.

## Shared gateways

A stdio registration starts a gateway per client session, so ten restored sessions start ten
gateways, each with its own server containers. Instead, each client registers a streamable HTTP
entry, and `gateways.py` runs one gateway per profile with `--transport streaming --host 127.0.0.1
--port <port>`. The gateway requires a Bearer token from `MCP_GATEWAY_AUTH_TOKEN` on
every request except `/health`. The client entries name that variable and never hold its value:

| Client | Token reference |
| --- | --- |
| Claude Code | header `Authorization: Bearer ${MCP_GATEWAY_AUTH_TOKEN}`, expanded at each connection ([MCP docs](https://code.claude.com/docs/en/mcp)) |
| Codex | `bearer_token_env_var = "MCP_GATEWAY_AUTH_TOKEN"` ([MCP docs](https://learn.chatgpt.com/docs/extend/mcp)) |
| OpenCode | header `Authorization: Bearer {env:MCP_GATEWAY_AUTH_TOKEN}`, with `oauth: false` ([MCP format](https://opencode.ai/docs/mcp-servers/)) |

The token stops other local processes, and web pages, from using the gateways. It cannot stop a
local user who binds a gateway's port before the gateway starts from receiving the token, since
no client can check who is listening; on a machine shared with untrusted users, do not use the
shared gateways.

The URLs use `127.0.0.1` rather than `localhost`: the gateway listens on IPv4 only, and on Windows
a refused `::1` costs each new connection about two seconds before the IPv4 fallback.

`python3 mcp/bootstrap/gateways.py install` creates a random token when there is none, then has the
user's service manager start `gateways.py run <profile>` for each profile at logon. The runner waits
for the Docker engine, runs the gateway, and starts it again whenever it exits; stopping the
service stops its gateway. Gateway output goes to `mcp-gateway-<profile>.log`, readable only by
you: in the user's temporary folder on Windows, beside the token on Linux. Install records the paths of this checkout and of the Python that ran it, so
rerun it after moving either or upgrading that Python. `--what-if` previews install and uninstall.

| | Windows | Linux |
| --- | --- | --- |
| Token | user environment variable | `~/.config/mcp-gateway/token.env` (owner-only), exported to login shells by a line added to `~/.profile` |
| Service | hidden per-user logon task per profile, `Docker MCP gateway <profile>`, run under the `pythonw.exe` beside the Python that ran install | systemd user unit instance per profile, `docker-mcp-gateway@<profile>.service` |
| Status | Task Scheduler | `systemctl --user status 'docker-mcp-gateway@*'` |

On Linux, `~/.config` follows `XDG_CONFIG_HOME`. The `~/.profile` line reaches login shells and
the desktop sessions started from them; a shell that does not read `~/.profile` (zsh, or bash
with a `~/.bash_profile`) needs the same line in its own startup file. The units need a systemd
user manager, so on WSL enable systemd first. They run while you are logged in; for a gateway that
outlives your sessions, `loginctl enable-linger`.

`python3 mcp/bootstrap/gateways.py uninstall` stops and removes the services, the `~/.profile`
line and the token. To return to per-session stdio gateways, run it, then restore the client
configs from their `.prompts-backup-*` copies or rerun the previous revision's `install.py`.

The gateway lists every server's tools once, at startup; a session that connects and lists tools
starts no containers. Sessions do not share server containers: each gets its own instance of each
containerized server it calls, such as its own Playwright browser. The gateway runs without
`--long-lived`, which keeps those containers until the gateway stops, so a session that exits
without an HTTP `DELETE` would leave them running.
