"""Shared by the MCP installer and its verification: prerequisites, client config backups and edits, credentials.

Builds on scripts/setup_common.py for paths, tool selection and commands. Only the two gateway names in GATEWAYS are
managed in a client's configuration; every other entry is kept. Secret values reach Docker on stdin, never on a
command line or in an error.
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
GATEWAYS = (("MCP_DOCKER_CORE", "core-dev"), ("MCP_DOCKER_ENVATIVE", "envative"))
OPENCODE_TIMEOUT_MS = 30000

# A JSON string, kept whole so nothing inside one is taken for a comment or a trailing comma.
_STRING = r'("(?:\\.|[^"\\])*")'
_COMMENT = re.compile(_STRING + r"|//[^\n]*|/\*.*?\*/", re.DOTALL)
_TRAILING_COMMA = re.compile(_STRING + r"|,(?=\s*[\]}])")


def gateway_command(profile):
    return ["docker", "mcp", "gateway", "run", "--profile", profile]


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
        shutil.copyfile(path, backup)
        if os.name != "nt":
            os.chmod(backup, 0o600)
        print(f"[BACKUP] {backup}")


def read_json(path):
    """The JSON object in path, {} when the file is missing. Comments and trailing commas (JSONC) are accepted. Fail
    when the file is not JSON or not an object, without showing its contents."""
    if not os.path.exists(path):
        return {}
    text = Path(path).read_text(encoding="utf-8-sig")
    text = _TRAILING_COMMA.sub(lambda m: m[1] or "", _COMMENT.sub(lambda m: m[1] or "", text))
    try:
        config = json.loads(text)
    except ValueError as e:
        raise sc.Fail(f"Invalid JSON in {path} (line {getattr(e, 'lineno', '?')})") from None
    if not isinstance(config, dict):
        raise sc.Fail(f"Expected a JSON object in {path}")
    return config


def set_opencode_config(path, *, validate_only=False, what_if=False):
    """Merge both gateways into OpenCode's mcp object at path. A changed file is backed up first and rewritten as
    JSON, so its comments survive only in the backup; an unchanged one is not touched. validate_only reads and checks
    the file and writes nothing. Fail when the file or its mcp entry is not an object."""
    config = read_json(path)
    if not isinstance(config.setdefault("mcp", {}), dict):
        raise sc.Fail(f"Expected an mcp object in {path}")
    changed = False
    for name, profile in GATEWAYS:
        expected = {"type": "local", "command": gateway_command(profile), "enabled": True,
                    "timeout": OPENCODE_TIMEOUT_MS}
        current = config["mcp"].get(name)
        if isinstance(current, dict) and current.get("type") == "local" and current.get("enabled") is True and \
                current.get("timeout") == OPENCODE_TIMEOUT_MS and current.get("command") == expected["command"]:
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
        Path(path).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


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
        key = next(iter(urllib.parse.parse_qs(urllib.parse.urlsplit(agent_mail["url"]).query).get("apiKey", [])),
                   None)
    key = key or (agent_mail.get("headers") or {}).get("x-api-key")
    if key:
        set_docker_secret("agentmail.api_key", key)
    firecrawl = os.environ.get("FIRECRAWL_API_KEY") or \
        re.sub(r"^Bearer\s+", "", ((servers.get("firecrawl") or {}).get("headers") or {}).get("Authorization", ""))
    if firecrawl:
        set_docker_secret("firecrawl.api_key", firecrawl)
