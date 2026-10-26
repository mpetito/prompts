"""Build the local MCP images, import the core-dev and envative profiles into Docker MCP, and register both shared
gateways with the selected clients, which reach them over HTTP; gateways.py runs the gateways.
  python3 mcp/bootstrap/install.py [--tools codex,claude,opencode] [--aws-region <region>]
                                   [--skip-credential-migration] [--skip-gateway-setup] [--what-if]
Without --tools, registers the clients found on PATH; a selected client that is not installed is skipped. Every
client config is checked before Docker changes anything, and Docker's prerequisites before any build. --what-if runs
no command and changes no file. --skip-gateway-setup reuses the profiles already imported, after checking they
exist; --skip-credential-migration leaves Docker's secrets alone. A failed command stops the installer (exit 1).
"""
import os
import shutil
from pathlib import Path

import mcp_common as mcp
from mcp_common import sc

MCP_ROOT = Path(__file__).absolute().parents[1]
IMAGES = (("azure-devops", "2.9.0"), ("material-ui", "0.1.4"), ("envative-kb", "1.6.0"))


def register_opencode(paths, what_if):
    mcp.set_opencode_config(paths.opencode_config, what_if=what_if)


def register_codex(paths, what_if):
    if not sc.should(what_if, "codex", "Back up configuration and register both Docker MCP gateways"):
        return
    config = os.path.join(paths.codex_root, "config.toml")
    mcp.backup_config(config)
    for name, _, port in mcp.GATEWAYS:
        sc.run_checked(["codex", "mcp", "add", name, "--url", mcp.gateway_url(port), "--bearer-token-env-var",
                        mcp.TOKEN_VARIABLE])
        mcp.set_codex_startup_timeout(config, name)


def register_claude(paths, what_if):
    if not sc.should(what_if, "claude", "Back up configuration and register both Docker MCP gateways"):
        return
    mcp.backup_config(paths.claude_config)
    servers = mcp.read_json(paths.claude_config).get("mcpServers") or {}
    for name, _, port in mcp.GATEWAYS:
        if name in servers:
            sc.run_checked(["claude", "mcp", "remove", "--scope", "user", name])
        # Kept as ${...} in the config: Claude Code expands it from the environment at each connection.
        sc.run_checked(["claude", "mcp", "add", "--scope", "user", "--transport", "http", name, mcp.gateway_url(port),
                        "--header", f"Authorization: Bearer ${{{mcp.TOKEN_VARIABLE}}}"])


REGISTER = {"codex": register_codex, "claude": register_claude, "opencode": register_opencode}


def set_up_gateways(aws_region):
    for image, version in IMAGES:
        sc.run_checked(["docker", "build", "--tag", f"local/mcp-{image}:{version}", str(MCP_ROOT / "images" / image)])
    sc.run_checked(["docker", "mcp", "feature", "disable", "dynamic-tools"])
    sc.run_checked(["docker", "mcp", "feature", "enable", "tool-name-prefix"])
    for profile in mcp.PROFILES:
        sc.run_checked(["docker", "mcp", "profile", "import", str(MCP_ROOT / "profiles" / f"{profile}.yaml")])
    sc.run_checked(["docker", "mcp", "profile", "config", "envative", "--set", f"envative-kb.aws_region={aws_region}"])
    # 'catalog create' upserts an existing ref in place (Docker MCP Toolkit v0.43.3), so no remove step is needed.
    # The CLI documents no schema for 'catalog ls'; do not gate on it.
    for profile in mcp.PROFILES:
        sc.run_checked(["docker", "mcp", "catalog", "create", f"local/{profile}:latest", "--from-profile", profile,
                        "--title", profile])


def main(argv):
    parser = sc.Parser(prog="install.py", description="Register the Docker MCP gateways with the selected clients.")
    parser.add_argument("--tools", help="comma-separated: codex, claude, opencode")
    parser.add_argument("--aws-region", default="us-east-1")
    parser.add_argument("--skip-credential-migration", action="store_true")
    parser.add_argument("--skip-gateway-setup", action="store_true")
    parser.add_argument("--what-if", action="store_true")
    args = parser.parse_args(argv)
    paths = sc.setup_paths()
    selected = []
    for tool in sc.select_tools(args.tools, mcp.CLIENTS):
        if shutil.which(tool) or args.what_if:
            selected.append(tool)
        else:
            sc.warn(f"Skipping {tool} MCP registration: CLI is not installed.")
    if not selected:
        print("No installed MCP clients selected. Install a client and rerun setup.")
        return 0

    # Check the selected JSON configs before Docker changes, without showing their contents.
    if "claude" in selected or not args.skip_credential_migration:
        mcp.read_json(paths.claude_config)
    if "opencode" in selected:
        mcp.set_opencode_config(paths.opencode_config, validate_only=True)
    if not args.what_if:
        mcp.assert_prerequisites()
        if args.skip_gateway_setup:
            for profile in mcp.PROFILES:
                sc.run_checked(["docker", "mcp", "profile", "show", profile, "--format", "yaml"], show=False)

    if not args.skip_gateway_setup and \
            sc.should(args.what_if, "Docker MCP", "Build images and import core-dev and envative profiles"):
        set_up_gateways(args.aws_region)
    if not args.skip_credential_migration and sc.should(
            args.what_if, "Docker MCP secret store", "Migrate available PAT, SonarQube, AgentMail, and Firecrawl"
                                                      " credentials"):
        mcp.copy_credentials(paths.claude_config)
    for tool in selected:
        REGISTER[tool](paths, args.what_if)
    if args.what_if:
        print("MCP preview complete. No commands were run and no files were changed.")
    else:
        print(f"Registered Docker MCP gateways for: {', '.join(selected)}.")
        if not mcp.gateway_token():
            sc.warn(f"{mcp.TOKEN_VARIABLE} is unset, so clients cannot reach the gateways. Run"
                    " 'python3 mcp/bootstrap/gateways.py install'.")
        print("Authorize hosted services with 'docker mcp oauth authorize <server> --open-browser'.")
    return 0


if __name__ == "__main__":
    sc.entry(main)
