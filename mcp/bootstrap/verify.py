"""Check Docker MCP, both gateways, and the selected clients' registrations.
  python3 mcp/bootstrap/verify.py [--tools codex,claude,opencode]
Prints each command's own output. This can start gateway containers and contact configured services; the offline
tests mock those calls instead. A failed command, or a shared gateway that does not answer its health check, stops
verification (exit 1); a selected client that is not installed is skipped with a warning.
"""
import shutil
import urllib.request

import mcp_common as mcp
from mcp_common import sc


def main(argv):
    parser = sc.Parser(prog="verify.py", description="Check Docker MCP and the clients' gateway registrations.")
    parser.add_argument("--tools", help="comma-separated: codex, claude, opencode")
    args = parser.parse_args(argv)
    selected = sc.select_tools(args.tools, mcp.CLIENTS)
    mcp.assert_prerequisites()
    sc.run_checked(["docker", "mcp", "feature", "list"])
    for _, profile, port in mcp.GATEWAYS:
        sc.run_checked(["docker", "mcp", "profile", "show", profile, "--format", "yaml"])
        # Over stdio: a dry run with --port binds it, which the shared gateway already holds.
        sc.run_checked(["docker", "mcp", "gateway", "run", "--profile", profile, "--dry-run"])
        # /health needs no token; the gateway answers it once it is serving. No proxy: HTTP_PROXY, or Windows' proxy
        # settings, would otherwise take even a loopback request.
        health = mcp.gateway_url(port, "health")
        try:
            urllib.request.build_opener(urllib.request.ProxyHandler({})).open(health, timeout=5).close()
        except OSError as e:
            raise sc.Fail(f"The shared {profile} gateway is not serving at {health} ({e}). Start it with"
                          " 'python3 mcp/bootstrap/gateways.py install'.") from None
        print(f"[OK] {profile} gateway: {health}")
    for tool in selected:
        if shutil.which(tool):
            sc.run_checked([tool, "mcp", "list"])
        else:
            sc.warn(f"Skipping {tool} MCP verification: CLI is not installed.")
    return 0


if __name__ == "__main__":
    sc.entry(main)
