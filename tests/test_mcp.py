"""mcp/bootstrap/install.py and mcp_common.py with docker, codex, claude and opencode faked at setup_common.run: no
Docker daemon, network, credentials or live config is used. Paths, previews, prerequisites, native failures, client
selection, config backups, the JSONC merge, timeout updates and credential migration."""
import json
import os
import re
import subprocess
import sys
import unittest.mock
from pathlib import Path

from .support import MCP_BOOTSTRAP, SetupTest, call, load, sc

INSTALL = load(MCP_BOOTSTRAP / "install.py")
import mcp_common as mcp  # noqa: E402  (support put mcp/bootstrap on sys.path)

JSONC = '{ // keep this comment in the backup\n"model":"keep-model","mcp":{"personal":{"type":"remote",' \
        '"url":"https://example.test"},},}'


class ClientCLIs:
    """Fakes for the four CLIs. A call whose text equals fail exits 9. codex and claude change their config files as
    the real CLIs would: codex mcp add replaces its table, keeping the others; claude mcp add and remove edit
    mcpServers."""

    def __init__(self, codex_config, claude_config):
        self.codex_config, self.claude_config = codex_config, claude_config
        self.calls, self.fail, self.secrets = [], "", {}

    def __call__(self, args, input):
        call = " ".join(args)
        self.calls.append(call)
        if call == self.fail:
            return subprocess.CompletedProcess(args, 9, "", "")
        if args[:4] == ["docker", "mcp", "secret", "set"]:
            self.secrets[args[4]] = input
        if args[:3] == ["codex", "mcp", "add"]:
            text = Path(self.codex_config).read_text()
            text = re.sub(rf"(?ms)^\[mcp_servers\.{args[3]}\].*?(?=^\[|\Z)", "", text)
            Path(self.codex_config).write_text(text + f'[mcp_servers.{args[3]}]\ncommand = "docker"\n')
        if args[0] == "claude":
            config = mcp.read_json(self.claude_config)
            if args[2] == "remove":
                del config["mcpServers"][args[5]]
            if args[2] == "add":
                config["mcpServers"][args[5]] = {"command": "docker"}
            Path(self.claude_config).write_text(json.dumps(config))
        return subprocess.CompletedProcess(args, 0, "", "")


class McpTest(SetupTest):
    """Clients' config variables pointing into the test folder, and the four CLIs on PATH, faked."""

    def setUp(self):
        super().setUp()
        os.environ.update(CODEX_HOME=str(self.tmp / "codex"), CLAUDE_CONFIG_DIR=str(self.tmp / "claude"),
                          OPENCODE_CONFIG=str(self.tmp / "opencode.jsonc"))
        self.bin = self.tmp / "bin"
        self.bin.mkdir()
        for name in ("docker", "codex", "claude", "opencode"):
            # Found by shutil.which only; every call goes to the fakes.
            exe = self.bin / (f"{name}.cmd" if os.name == "nt" else name)
            exe.write_text("exit 1\n")
            exe.chmod(0o755)
        os.environ["PATH"] = f"{self.bin}{os.pathsep}{os.environ['PATH']}"
        self.paths = sc.setup_paths()
        self.codex_config = os.path.join(self.paths.codex_root, "config.toml")
        self.cli = ClientCLIs(self.codex_config, self.paths.claude_config)
        self.fake_run(self.cli)

    def backups(self):
        return list(self.tmp.glob("opencode.jsonc.prompts-backup-*"))


class Paths(McpTest):
    def test_paths_honour_the_client_variables(self):
        self.assertTrue(sc.same_path(self.paths.codex_root, os.environ["CODEX_HOME"]))
        self.assertTrue(sc.same_path(self.paths.claude_root, os.environ["CLAUDE_CONFIG_DIR"]))
        self.assertTrue(sc.same_path(self.paths.opencode_config, os.environ["OPENCODE_CONFIG"]))
        isolated = sc.setup_paths(str(self.tmp / "isolated"))
        self.assertFalse(sc.same_path(isolated.codex_root, os.environ["CODEX_HOME"]))
        del os.environ["OPENCODE_CONFIG"]
        os.environ["XDG_CONFIG_HOME"] = str(self.tmp / "xdg")
        self.assertTrue(sc.same_path(sc.setup_paths().opencode_config, self.tmp / "xdg" / "opencode" / "opencode.json"))
        os.environ["OPENCODE_CONFIG_DIR"] = str(self.tmp / "custom-config")
        self.assertTrue(sc.same_path(sc.setup_paths().opencode_config,
                                     self.tmp / "custom-config" / "opencode.json"))
        (self.tmp / "custom-config").mkdir()
        (self.tmp / "custom-config" / "opencode.jsonc").write_text("{}")
        self.assertTrue(sc.same_path(sc.setup_paths().opencode_config,
                                     self.tmp / "custom-config" / "opencode.jsonc"))


class Install(McpTest):
    def setUp(self):
        super().setUp()
        os.makedirs(self.paths.codex_root)
        os.makedirs(self.paths.claude_root)
        Path(self.codex_config).write_text('model = "keep-model"\n[mcp_servers.personal]\ncommand = "keep-command"\n')
        Path(self.paths.claude_config).write_text(
            '{"theme":"keep","mcpServers":{"personal":{"command":"keep"},"MCP_DOCKER_CORE":{"command":"old"}}}\n')
        Path(self.paths.opencode_config).write_text(JSONC)

    def install(self, *argv):
        return call(INSTALL, *argv)

    def test_what_if_runs_nothing_and_changes_nothing(self):
        self.assertEqual(self.install("--tools", "codex,claude,opencode", "--what-if")[0], 0)
        self.assertEqual(self.cli.calls, [])
        self.assertEqual(Path(self.paths.opencode_config).read_text(), JSONC)
        self.assertEqual(list(self.tmp.rglob("*.prompts-backup-*")), [])

    def test_a_missing_mcp_plugin_stops_before_any_build_or_write(self):
        self.cli.fail = "docker mcp version"
        code, _, err = self.install("--tools", "codex", "--skip-credential-migration")
        self.assertEqual(code, 1)
        self.assertIn("MCP Toolkit is unavailable", err)
        self.assertEqual(len(self.cli.calls), 1)

    def test_each_prerequisite_stops_the_install_before_any_build(self):
        checks = ["docker mcp version", "docker info --format {{.ServerVersion}}", "docker mcp secret ls"]
        for check in checks:
            self.cli.calls.clear()
            self.cli.fail = check
            self.assertEqual(self.install("--tools", "codex", "--skip-credential-migration")[0], 1, check)
            self.assertEqual(self.cli.calls, checks[:checks.index(check) + 1])
        for docker in self.bin.glob("docker*"):
            docker.unlink()
        with unittest.mock.patch.dict(os.environ, PATH=str(self.bin)):
            code, _, err = self.install("--tools", "codex", "--skip-credential-migration", "--skip-gateway-setup")
        self.assertEqual(code, 1)
        self.assertIn("Docker is not on PATH", err)

    def test_a_failed_build_stops_before_registration(self):
        image = MCP_BOOTSTRAP.parent / "images" / "azure-devops"
        self.cli.fail = f"docker build --tag local/mcp-azure-devops:2.9.0 {image}"
        code, _, err = self.install("--tools", "codex", "--skip-credential-migration")
        self.assertEqual(code, 1)
        self.assertIn("Command failed", err)
        self.assertFalse([c for c in self.cli.calls if c.startswith("codex ")])

    def test_install_registers_both_gateways_and_keeps_everything_else(self):
        self.assertEqual(self.install("--tools", "codex,claude,opencode", "--skip-credential-migration")[0], 0)
        for profile in mcp.PROFILES:
            self.assertIn(f"docker mcp catalog create local/{profile}:latest --from-profile {profile} "
                          f"--title {profile}", self.cli.calls)
        self.assertFalse([c for c in self.cli.calls if c.startswith("docker mcp catalog remove")])
        self.assertIn("claude mcp remove --scope user MCP_DOCKER_CORE", self.cli.calls)
        self.assertNotIn("claude mcp remove --scope user MCP_DOCKER_ENVATIVE", self.cli.calls)
        codex = Path(self.codex_config).read_text()
        self.assertIn("keep-model", codex)
        self.assertIn("keep-command", codex)
        self.assertEqual(codex.count("startup_timeout_sec = 30"), 2)
        claude = mcp.read_json(self.paths.claude_config)
        self.assertEqual((claude["theme"], claude["mcpServers"]["personal"]["command"]), ("keep", "keep"))
        opencode = mcp.read_json(self.paths.opencode_config)
        self.assertEqual((opencode["model"], opencode["mcp"]["personal"]["url"]),
                         ("keep-model", "https://example.test"))
        self.assertEqual(opencode["mcp"]["MCP_DOCKER_CORE"]["timeout"], 30000)
        self.assertEqual(opencode["mcp"]["MCP_DOCKER_ENVATIVE"]["command"][-1], "envative")
        self.assertEqual([p.read_text() for p in self.backups()], [JSONC])

        self.cli.calls.clear()
        self.assertEqual(self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")[0],
                         0)
        self.assertEqual(len(self.backups()), 1)
        self.assertFalse([c for c in self.cli.calls if re.match("^(codex|claude) |^docker build", c)])

    def test_install_sets_up_the_gateways_and_backs_up_each_client_config(self):
        originals = {path: Path(path).read_text() for path in (self.codex_config, self.paths.claude_config)}
        os.environ["AZURE_DEVOPS_PAT"] = "pat-value"
        self.assertEqual(self.install("--tools", "codex,claude,opencode", "--skip-credential-migration")[0], 0)
        root = MCP_BOOTSTRAP.parent
        expected = [f"docker build --tag local/mcp-{image}:{version} {root / 'images' / image}"
                    for image, version in INSTALL.IMAGES]
        expected += ["docker mcp feature disable dynamic-tools", "docker mcp feature enable tool-name-prefix"]
        expected += [f"docker mcp profile import {root / 'profiles' / f'{p}.yaml'}" for p in mcp.PROFILES]
        expected += ["docker mcp profile config envative --set envative-kb.aws_region=us-east-1"]
        self.assertEqual(self.cli.calls[3:3 + len(expected)], expected)
        self.assertFalse([c for c in self.cli.calls if c.startswith("docker mcp secret set")])
        for path, text in originals.items():
            self.assertEqual([p.read_text() for p in Path(path).parent.glob("*.prompts-backup-*")], [text], path)

    def test_reusing_the_gateways_checks_both_profiles(self):
        self.assertEqual(self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")[0],
                         0)
        for profile in mcp.PROFILES:
            self.assertIn(f"docker mcp profile show {profile} --format yaml", self.cli.calls)

    def test_a_client_not_installed_is_skipped(self):
        for claude in self.bin.glob("claude*"):
            claude.unlink()
        with unittest.mock.patch.dict(os.environ, PATH=str(self.bin)):
            code, _, err = self.install("--tools", "codex,claude", "--skip-gateway-setup",
                                        "--skip-credential-migration")
        self.assertEqual(code, 0)
        self.assertIn("claude", err)
        self.assertFalse([c for c in self.cli.calls if c.startswith("claude ")])
        self.assertTrue([c for c in self.cli.calls if c.startswith("codex ")])

    def test_an_invalid_claude_config_stops_before_docker(self):
        Path(self.paths.claude_config).write_text("{broken")
        self.assertEqual(self.install("--tools", "codex")[0], 1)
        self.assertEqual(self.cli.calls, [])

    @unittest.skipIf(os.name == "nt", "Windows files have no owner-only mode")
    def test_backups_are_readable_only_by_their_owner(self):
        self.addCleanup(os.umask, os.umask(0o022))
        self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")
        self.assertEqual([p.stat().st_mode & 0o777 for p in self.backups()], [0o600])

    def test_a_missing_opencode_config_is_created(self):
        os.remove(self.paths.opencode_config)
        self.assertEqual(self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")[0],
                         0)
        self.assertEqual(set(mcp.read_json(self.paths.opencode_config)["mcp"]), {name for name, _ in mcp.GATEWAYS})
        self.assertEqual(self.backups(), [])

    def test_a_changed_timeout_is_rewritten(self):
        self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")
        config = mcp.read_json(self.paths.opencode_config)
        config["mcp"]["MCP_DOCKER_CORE"]["timeout"] = 60000
        Path(self.paths.opencode_config).write_text(json.dumps(config))
        self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")
        self.assertEqual(mcp.read_json(self.paths.opencode_config)["mcp"]["MCP_DOCKER_CORE"]["timeout"], 30000)

    def test_a_config_that_is_not_an_object_stops_before_docker(self):
        for text in ("[1]", '{"mcp": []}'):
            Path(self.paths.opencode_config).write_text(text)
            self.assertEqual(self.install("--tools", "opencode", "--skip-credential-migration")[0], 1, text)
            self.assertEqual(self.cli.calls, [], text)

    def test_an_invalid_client_config_stops_before_docker(self):
        Path(self.paths.opencode_config).write_text("{broken\n")
        code, _, err = self.install("--tools", "opencode", "--skip-credential-migration")
        self.assertEqual(code, 1)
        self.assertIn("JSON", err)
        self.assertEqual(self.cli.calls, [])

    def test_credentials_reach_docker_on_stdin(self):
        Path(self.paths.claude_config).write_text(
            '{"mcpServers":{"agent-mail":{"url":"https://mail.test/mcp?x=1&apiKey=mail%2Bkey"},'
            '"firecrawl":{"headers":{"Authorization":"Bearer fc-key"}}}}')
        os.environ.update(AZURE_DEVOPS_PAT="pat-value", SONAR_TOKEN="sonar-value")
        for name in ("AGENTMAIL_API_KEY", "FIRECRAWL_API_KEY"):
            os.environ.pop(name, None)
        self.assertEqual(self.install("--tools", "codex", "--skip-gateway-setup")[0], 0)
        self.assertEqual(self.cli.secrets, {"azure-devops.pat": "pat-value", "sonarqube.token": "sonar-value",
                                            "agentmail.api_key": "mail+key", "firecrawl.api_key": "fc-key"})
        for value in self.cli.secrets.values():
            self.assertFalse([c for c in self.cli.calls if value in c])

        self.cli.secrets.clear()
        Path(self.paths.claude_config).write_text('{"mcpServers":{"agent-mail":{"headers":{"x-api-key":"hdr-key"}}}}')
        self.assertEqual(self.install("--tools", "codex", "--skip-gateway-setup")[0], 0)
        self.assertEqual(self.cli.secrets["agentmail.api_key"], "hdr-key")


class Verify(McpTest):
    VERIFY = load(MCP_BOOTSTRAP / "verify.py")

    def test_verify_checks_docker_both_gateways_and_each_installed_client(self):
        for claude in self.bin.glob("claude*"):
            claude.unlink()
        with unittest.mock.patch.dict(os.environ, PATH=str(self.bin)):
            code, _, err = call(self.VERIFY, "--tools", "codex,claude")
        self.assertEqual(code, 0)
        expected = ["docker mcp version", "docker info --format {{.ServerVersion}}", "docker mcp secret ls",
                    "docker mcp feature list"]
        for profile in mcp.PROFILES:
            expected += [f"docker mcp profile show {profile} --format yaml",
                         f"docker mcp gateway run --profile {profile} --dry-run"]
        self.assertEqual(self.cli.calls, expected + ["codex mcp list"])
        self.assertIn("claude", err)

    def test_a_failed_check_stops_verification(self):
        self.cli.fail = "docker mcp gateway run --profile core-dev --dry-run"
        self.assertEqual(call(self.VERIFY, "--tools", "codex")[0], 1)
        self.assertNotIn("codex mcp list", self.cli.calls)


class CodexTimeout(McpTest):
    def test_timeout_updates_are_idempotent_and_keep_tables_and_line_endings(self):
        os.makedirs(self.paths.codex_root)
        for newline in ("\n", "\r\n"):
            with open(self.codex_config, "w", newline="") as f:
                f.write(f'[mcp_servers."MCP_DOCKER_CORE"]{newline}command = "docker"{newline}[other]{newline}'
                        f"value = 42{newline}")
            mcp.set_codex_startup_timeout(self.codex_config, "MCP_DOCKER_CORE")
            mcp.set_codex_startup_timeout(self.codex_config, "MCP_DOCKER_CORE")
            with open(self.codex_config, newline="") as f:
                text = f.read()
            self.assertEqual(text.count("startup_timeout_sec"), 1, repr(newline))
            self.assertEqual(text.count("\n"), text.count(newline), repr(newline))
            self.assertIn(f"[other]{newline}value = 42", text, repr(newline))


class Usage(SetupTest):
    """Each MCP script run as a program: a usage error exits 1."""

    def test_an_unknown_option_exits_1(self):
        for script in ("install.py", "verify.py"):
            r = subprocess.run([sys.executable, str(MCP_BOOTSTRAP / script), "--nope"], capture_output=True,
                               text=True, cwd=self.tmp)
            self.assertEqual(r.returncode, 1, script)
            self.assertIn("usage:", r.stderr, script)
