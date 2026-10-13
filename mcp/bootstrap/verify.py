"""Check Docker MCP, both gateways, and the selected clients' registrations.
  python3 mcp/bootstrap/verify.py [--tools codex,claude,opencode]
Prints each command's own output. This can start gateway containers and contact configured services; the offline
tests mock those calls instead. A failed command stops verification (exit 1); a selected client that is not
installed is skipped with a warning.
"""
import shutil

import mcp_common as mcp
from mcp_common import sc


def main(argv):
    parser = sc.Parser(prog="verify.py", description="Check Docker MCP and the clients' gateway registrations.")
    parser.add_argument("--tools", help="comma-separated: codex, claude, opencode")
    args = parser.parse_args(argv)
    selected = sc.select_tools(args.tools, mcp.CLIENTS)
    mcp.assert_prerequisites()
    sc.run_checked(["docker", "mcp", "feature", "list"])
    for profile in mcp.PROFILES:
        sc.run_checked(["docker", "mcp", "profile", "show", profile, "--format", "yaml"])
        sc.run_checked([*mcp.gateway_command(profile), "--dry-run"])
    for tool in selected:
        if shutil.which(tool):
            sc.run_checked([tool, "mcp", "list"])
        else:
            sc.warn(f"Skipping {tool} MCP verification: CLI is not installed.")
    return 0


if __name__ == "__main__":
    sc.entry(main)
