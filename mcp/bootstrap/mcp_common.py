"""Shared by the MCP installer and its verification: prerequisites, client config backups and edits, credentials.

Builds on scripts/setup_common.py for paths, tool selection and commands. Only the two gateway names in GATEWAYS are
managed in a client's configuration; every other entry is kept. Each client connects over streamable HTTP to one
shared gateway per profile on loopback (gateways.py runs them), sending the Bearer token held in TOKEN_VARIABLE: client
configs name the variable, never its value. Secret values reach Docker on stdin, never on a command line or in an
error.
"""
import json
import os
import re
import shutil
import sys
import urllib.parse
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).absolute().parents[2] / "scripts"))

import setup_common as sc  # noqa: E402

CLIENTS = ("codex", "claude", "opencode")
PROFILES = ("core-dev", "envative")
# (client name, profile, loopback port of the profile's shared gateway)
GATEWAYS = (("MCP_DOCKER_CORE", "core-dev", 8811), ("MCP_DOCKER_ENVATIVE", "envative", 8812))
TOKEN_VARIABLE = "MCP_GATEWAY_AUTH_TOKEN"
OPENCODE_TIMEOUT_MS = 30000

# A JSON string, kept whole so nothing inside one is taken for a comment or a trailing comma.
_STRING = r'("(?:\\.|[^"\\])*")'
_COMMENT = re.compile(_STRING + r"|//[^\n]*|/\*.*?\*/", re.DOTALL)
_TRAILING_COMMA = re.compile(_STRING + r"|,(?=\s*[\]}])")


def gateway_command(profile, port):
    """The shared gateway for profile: streamable HTTP on 127.0.0.1:port only, requiring the Bearer token in
    TOKEN_VARIABLE. Not --long-lived: that keeps every session's server containers until the gateway stops, and a
    service gateway never stops."""
    return ["docker", "mcp", "gateway", "run", "--profile", profile, "--transport", "streaming", "--host", "127.0.0.1",
            "--port", str(port)]


def gateway_url(port, path="mcp"):
    # 127.0.0.1, not localhost: the gateway listens on IPv4 only, and on Windows a refused ::1 costs each new
    # connection about 2 s before the fallback to IPv4.
    return f"http://127.0.0.1:{port}/{path}"


def assert_prerequisites():
    """Fail unless Docker, its MCP Toolkit plugin, a running daemon and the profiles' secret store all answer: checked
    before any build or client change."""
    if not shutil.which("docker"):
        raise sc.Fail("Docker is not on PATH. Install Docker and its MCP Toolkit before running MCP setup.")
    try:
        sc.run_checked(["docker", "mcp", "version"], show=False)
    except sc.Fail:
        raise sc.Fail("Docker MCP Toolkit is unavailable. Install a compatible docker mcp plugin; Docker Engine alone"
                      " is insufficient. Skill setup does not require Docker.") from None
    sc.run_checked(["docker", "info", "--format", "{{.ServerVersion}}"], show=False)
    # The checked-in profiles use docker-desktop-store; check it answers before builds.
    sc.run_checked(["docker", "mcp", "secret", "ls"], show=False)


def backup_config(path):
    """Copy an existing config to a uniquely named <path>.prompts-backup-<hex> beside it, readable only by its owner
    where the OS has modes: client configs can hold secrets."""
    if os.path.exists(path):
        backup = f"{path}.prompts-backup-{uuid.uuid4().hex}"
        # Made owner-only before the copy, which keeps the mode, so the secrets are never readable by others.
        os.close(os.open(backup, os.O_WRONLY | os.O_CREAT, 0o600))
        shutil.copyfile(path, backup)
        print(f"[BACKUP] {backup}")


def read_json(path):
    """The JSON object in path, {} when the file is missing. Comments and trailing commas (JSONC) are accepted. Fail
    when the file is not JSON or not an object, without showing its contents."""
    if not os.path.exists(path):
        return {}
    text = Path(path).read_text(encoding="utf-8-sig")
    # A comment gives way to its own line breaks, so a parse error names the line it is on in the file.
    text = _COMMENT.sub(lambda m: m[1] or "\n" * m[0].count("\n"), text)
    text = _TRAILING_COMMA.sub(lambda m: m[1] or "", text)
    try:
        config = json.loads(text)
    except ValueError as e:
        raise sc.Fail(f"Invalid JSON in {path} (line {getattr(e, 'lineno', '?')})") from None
    if not isinstance(config, dict):
        raise sc.Fail(f"Expected a JSON object in {path}")
    return config


def set_opencode_config(path, *, validate_only=False, what_if=False):
    """Merge both gateways into OpenCode's mcp object at path, as remote servers reading the token from
    TOKEN_VARIABLE. A changed file is backed up first and rewritten as JSON, so its comments survive only in the
    backup; an unchanged one is not touched. validate_only reads and checks the file and writes nothing. Fail when the
    file or its mcp entry is not an object."""
    config = read_json(path)
    if not isinstance(config.setdefault("mcp", {}), dict):
        raise sc.Fail(f"Expected an mcp object in {path}")
    changed = False
    for name, _, port in GATEWAYS:
        # oauth false: a 401 from the gateway means a missing token, not a server to sign in to.
        expected = {"type": "remote", "url": gateway_url(port), "enabled": True, "oauth": False,
                    "headers": {"Authorization": f"Bearer {{env:{TOKEN_VARIABLE}}}"}, "timeout": OPENCODE_TIMEOUT_MS}
        if config["mcp"].get(name) == expected:
            continue
        config["mcp"][name] = expected
        changed = True
    if validate_only:
        return
    if not changed:
        print(f"[UNCHANGED] OpenCode MCP configuration: {path}")
        return
    if sc.should(what_if, path, "Back up and merge Docker MCP registrations (JSONC comments are retained in the"
                                " backup)"):
        backup_config(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Path(path).write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def set_codex_startup_timeout(config_path, server_name, seconds=30):
    """Set startup_timeout_sec in Codex's [mcp_servers.<server_name>] table, which `codex mcp add` cannot set.
    Idempotent; adjacent tables and the file's line endings are kept. Fail when the table is missing."""
    with open(config_path, encoding="utf-8", newline="") as f:
        config = f.read()
    name = re.escape(server_name)
    section = re.search(rf'(?ms)(^\[mcp_servers\.(?:{name}|"{name}")\][ \t]*\r?\n)(.*?)(?=^\[|\Z)', config)
    if not section:
        raise sc.Fail(f"Codex MCP server '{server_name}' was not written to '{config_path}'.")
    body = section[2]
    newline = "\r\n" if "\r\n" in config else "\n"
    setting = f"startup_timeout_sec = {seconds}"
    if re.search(r"(?m)^startup_timeout_sec\s*=", body):
        body = re.sub(r"(?m)^startup_timeout_sec[^\r\n]*", lambda _: setting, body)
    else:
        body = setting + newline + body
    with open(config_path, "w", encoding="utf-8", newline="") as f:
        f.write(config[:section.start(2)] + body + config[section.end(2):])


def set_docker_secret(name, value):
    if sc.run(["docker", "mcp", "secret", "set", name], input=value).returncode:
        raise sc.Fail(f"Failed to store Docker MCP secret '{name}'.")


def user_env(name):
    """name from this process's environment, else on Windows from the user's persisted environment, which a shell
    started before the variable was set does not have."""
    if os.environ.get(name):
        return os.environ[name]
    if os.name == "nt":
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
                return winreg.QueryValueEx(key, name)[0]
        except OSError:
            return None
    return None


def token_file():
    """Where gateways.py install keeps the token outside Windows: one TOKEN_VARIABLE=<value> line, which a shell can
    source, readable only by its owner."""
    return os.path.join(sc.setup_paths().config_root, "mcp-gateway", "token.env")


def gateway_token():
    """The gateway token: TOKEN_VARIABLE from this process's environment, else where gateways.py install keeps it (the
    user's persisted environment on Windows, token_file() elsewhere); None when there is none."""
    if os.name == "nt" or os.environ.get(TOKEN_VARIABLE):
        return user_env(TOKEN_VARIABLE)
    try:
        return Path(token_file()).read_text(encoding="utf-8").strip().partition("=")[2] or None
    except FileNotFoundError:
        return None


def copy_credentials(claude_config_path):
    """Store the credentials the profiles need in Docker's secret store: the Azure DevOps PAT and SonarQube token
    from the environment, and the AgentMail and Firecrawl keys from the environment or Claude's existing MCP
    entries. A missing PAT or token only warns."""
    for variable, secret in (("AZURE_DEVOPS_PAT", "azure-devops.pat"), ("SONAR_TOKEN", "sonarqube.token")):
        value = user_env(variable)
        if value:
            set_docker_secret(secret, value)
        else:
            sc.warn(f"{variable} is unavailable. Use 'docker mcp secret set {secret}'.")
    servers = read_json(claude_config_path).get("mcpServers") or {}
    agent_mail = servers.get("agent-mail") or {}
    key = os.environ.get("AGENTMAIL_API_KEY")
    if not key and agent_mail.get("url"):
        # unquote, not unquote_plus: a + in the key is kept, as .NET's UnescapeDataString keeps it.
        pairs = urllib.parse.urlsplit(agent_mail["url"]).query.split("&")
        key = next((urllib.parse.unquote(p.split("=", 1)[1]) for p in pairs if p.startswith("apiKey=")), None)
    key = key or (agent_mail.get("headers") or {}).get("x-api-key")
    if key:
        set_docker_secret("agentmail.api_key", key)
    firecrawl = os.environ.get("FIRECRAWL_API_KEY") or \
        re.sub(r"^Bearer\s+", "", ((servers.get("firecrawl") or {}).get("headers") or {}).get("Authorization", ""))
    if firecrawl:
        set_docker_secret("firecrawl.api_key", firecrawl)
