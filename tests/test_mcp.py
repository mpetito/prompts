"""mcp/bootstrap/install.py, verify.py, gateways.py and mcp_common.py with docker, codex, claude, opencode and
powershell faked at setup_common.run: no Docker daemon, network, credentials, scheduled task or live config is used.
Paths, previews, prerequisites, native failures, client selection, config backups, the JSONC merge, timeout updates,
credential migration, and the shared gateways' tasks, token and runner."""
import http.server
import json
import os
import re
import shlex
import subprocess
import threading
import sys
import tempfile
import time
import unittest.mock
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

from .support import MCP_BOOTSTRAP, SetupTest, call, load, sc

INSTALL = load(MCP_BOOTSTRAP / "install.py")
import mcp_common as mcp  # noqa: E402  (support put mcp/bootstrap on sys.path)

OPEN = urllib.request.OpenerDirector.open
JSONC = '{ // keep this comment in the backup\n"model":"keep-model","mcp":{"personal":{"type":"remote",' \
        '"url":"https://example.test"},},}'


class ClientCLIs:
    """Fakes for the CLIs. A call whose text equals fail exits 9; inputs holds each call's stdin. codex and claude
    change their config files as the real CLIs would: codex mcp add replaces its table, keeping the others; claude mcp
    add (--transport http, its name at index 7) and remove (its name at index 5) edit mcpServers."""

    def __init__(self, codex_config, claude_config):
        self.codex_config, self.claude_config = codex_config, claude_config
        self.calls, self.fail, self.secrets, self.inputs = [], "", {}, []

    def __call__(self, args, input):
        call = " ".join(args)
        self.calls.append(call)
        self.inputs.append(input)
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
                config["mcpServers"][args[7]] = {"type": args[6], "url": args[8]}
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
        reference = f"{{env:{mcp.TOKEN_VARIABLE}}}"
        for name, _, port in mcp.GATEWAYS:
            # Each client names the token variable; none holds a token.
            self.assertIn(f"codex mcp add {name} --url {mcp.gateway_url(port)} --bearer-token-env-var "
                          f"{mcp.TOKEN_VARIABLE}", self.cli.calls)
            self.assertIn(f"claude mcp add --scope user --transport http {name} {mcp.gateway_url(port)} --header "
                          f"Authorization: Bearer ${{{mcp.TOKEN_VARIABLE}}}", self.cli.calls)
            self.assertEqual(claude["mcpServers"][name]["url"], mcp.gateway_url(port))
            entry = opencode["mcp"][name]
            self.assertEqual((entry["type"], entry["url"], entry["oauth"]), ("remote", mcp.gateway_url(port), False))
            self.assertTrue(entry["headers"]["Authorization"].endswith(reference))
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
    def test_backups_are_readable_only_by_their_owner_from_the_start(self):
        self.addCleanup(os.umask, os.umask(0o022))
        # A backup made readable and narrowed afterwards would be left readable here.
        with unittest.mock.patch.object(os, "chmod"):
            self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")
        self.assertEqual([p.stat().st_mode & 0o777 for p in self.backups()], [0o600])
        self.assertEqual([p.read_text() for p in self.backups()], [JSONC])

    def test_a_missing_opencode_config_is_created(self):
        os.remove(self.paths.opencode_config)
        self.assertEqual(self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")[0],
                         0)
        self.assertEqual(set(mcp.read_json(self.paths.opencode_config)["mcp"]), {name for name, _, _ in mcp.GATEWAYS})
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

    def test_a_json_error_names_its_line_in_the_file(self):
        Path(self.paths.opencode_config).write_text('{\n/* a\nlong\ncomment */ // and one more\n"a": 1,\n"b" 2\n}\n')
        code, _, err = self.install("--tools", "opencode", "--skip-credential-migration")
        self.assertEqual(code, 1)
        self.assertIn("line 6", err)

    def test_non_ascii_text_is_written_as_it_was(self):
        Path(self.paths.opencode_config).write_text('{"model": "café"}', encoding="utf-8")
        self.install("--tools", "opencode", "--skip-gateway-setup", "--skip-credential-migration")
        self.assertIn('"café"', Path(self.paths.opencode_config).read_text(encoding="utf-8"))

    def test_credentials_reach_docker_on_stdin(self):
        Path(self.paths.claude_config).write_text(
            '{"mcpServers":{"agent-mail":{"url":"https://mail.test/mcp?x=1&apiKey=mail+key%2B"},'
            '"firecrawl":{"headers":{"Authorization":"Bearer fc-key"}}}}')
        os.environ.update(AZURE_DEVOPS_PAT="pat-value", SONAR_TOKEN="sonar-value")
        for name in ("AGENTMAIL_API_KEY", "FIRECRAWL_API_KEY"):
            os.environ.pop(name, None)
        self.assertEqual(self.install("--tools", "codex", "--skip-gateway-setup")[0], 0)
        self.assertEqual(self.cli.secrets, {"azure-devops.pat": "pat-value", "sonarqube.token": "sonar-value",
                                            "agentmail.api_key": "mail+key+", "firecrawl.api_key": "fc-key"})
        for value in self.cli.secrets.values():
            self.assertFalse([c for c in self.cli.calls if value in c])

        self.cli.secrets.clear()
        Path(self.paths.claude_config).write_text('{"mcpServers":{"agent-mail":{"headers":{"x-api-key":"hdr-key"}}}}')
        self.assertEqual(self.install("--tools", "codex", "--skip-gateway-setup")[0], 0)
        self.assertEqual(self.cli.secrets["agentmail.api_key"], "hdr-key")

    def test_a_missing_gateway_token_is_reported(self):
        for token, reported in ((None, True), ("token-value", False)):
            with unittest.mock.patch.object(mcp, "gateway_token", return_value=token):
                code, _, err = self.install("--tools", "codex", "--skip-gateway-setup", "--skip-credential-migration")
            self.assertEqual(code, 0)
            self.assertEqual(mcp.TOKEN_VARIABLE in err, reported, token)


class Verify(McpTest):
    VERIFY = load(MCP_BOOTSTRAP / "verify.py")

    def setUp(self):
        super().setUp()
        self.health = []
        patcher = unittest.mock.patch.object(urllib.request.OpenerDirector, "open",
                                             lambda _, url, **__: self.health.append(url) or unittest.mock.MagicMock())
        patcher.start()
        self.addCleanup(patcher.stop)

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
        self.assertEqual(self.health, [mcp.gateway_url(port, "health") for _, _, port in mcp.GATEWAYS])
        self.assertIn("claude", err)

    def test_a_gateway_that_is_not_serving_stops_verification(self):
        with unittest.mock.patch.object(urllib.request.OpenerDirector, "open", side_effect=ConnectionRefusedError()):
            self.assertEqual(call(self.VERIFY, "--tools", "codex")[0], 1)
        self.assertNotIn("codex mcp list", self.cli.calls)

    def test_the_health_check_bypasses_any_proxy(self):
        class Healthy(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()

            def log_message(self, *_):
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Healthy)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_port}/health"
        # Port 9 refuses: a request sent through the proxy fails.
        with unittest.mock.patch.object(urllib.request.OpenerDirector, "open", OPEN),                 unittest.mock.patch.object(mcp, "gateway_url", return_value=url),                 unittest.mock.patch.dict(os.environ, HTTP_PROXY="http://127.0.0.1:9", http_proxy="http://127.0.0.1:9"):
            self.assertEqual(call(self.VERIFY, "--tools", "codex")[0], 0)

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


class Gateways(McpTest):
    GATEWAYS = load(MCP_BOOTSTRAP / "gateways.py")
    NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

    def tasks(self):
        """{task name: parsed task XML} from each registration's stdin."""
        tasks = {}
        for text, xml in zip(self.cli.calls, self.cli.inputs):
            name = re.search(r"Register-ScheduledTask -TaskName '([^']+)'", text)
            if name:
                tasks[name[1]] = ET.fromstring(xml.split("?>", 1)[1])
        return tasks

    @unittest.skipUnless(os.name == "nt", "Task Scheduler is Windows only")
    def test_install_stores_a_token_once_and_registers_a_hidden_logon_task_per_profile(self):
        with unittest.mock.patch.object(mcp, "gateway_token", return_value=None):
            self.assertEqual(call(self.GATEWAYS, "install")[0], 0)
        token = self.cli.inputs[0]
        self.assertIn(f"SetEnvironmentVariable('{mcp.TOKEN_VARIABLE}'", self.cli.calls[0])
        self.assertGreaterEqual(len(token), 32)
        self.assertFalse([c for c in self.cli.calls if token in c])
        tasks = self.tasks()
        self.assertEqual(set(tasks), {self.GATEWAYS.TASK.format(profile=p) for p in mcp.PROFILES})
        for profile in mcp.PROFILES:
            task = tasks[self.GATEWAYS.TASK.format(profile=profile)]
            self.assertEqual(task.findtext("t:Settings/t:Hidden", namespaces=self.NS), "true")
            self.assertTrue(task.findtext("t:Settings/t:RestartOnFailure/t:Count", namespaces=self.NS))
            self.assertTrue(task.findtext("t:Triggers/t:LogonTrigger/t:UserId", namespaces=self.NS))
            command = task.findtext("t:Actions/t:Exec/t:Command", namespaces=self.NS)
            self.assertEqual(Path(command).name.lower(), "pythonw.exe")
            arguments = task.findtext("t:Actions/t:Exec/t:Arguments", namespaces=self.NS)
            self.assertTrue(arguments.endswith(f" run {profile}"), arguments)

        self.cli.calls.clear()
        self.cli.inputs.clear()
        with unittest.mock.patch.object(mcp, "gateway_token", return_value="kept"):
            self.assertEqual(call(self.GATEWAYS, "install")[0], 0)
        self.assertFalse([c for c in self.cli.calls if "SetEnvironmentVariable" in c])
        self.assertEqual(len(self.tasks()), len(mcp.PROFILES))

    @unittest.skipUnless(os.name == "nt", "Task Scheduler is Windows only")
    def test_uninstall_removes_each_task_then_the_token_and_what_if_runs_nothing(self):
        for command in ("install", "uninstall"):
            self.assertEqual(call(self.GATEWAYS, command, "--what-if")[0], 0)
        self.assertEqual(self.cli.calls, [])
        self.assertEqual(call(self.GATEWAYS, "uninstall")[0], 0)
        for profile, text in zip(mcp.PROFILES, self.cli.calls):
            self.assertIn(f"'{self.GATEWAYS.TASK.format(profile=profile)}'", text)
            self.assertIn("Unregister-ScheduledTask", text)
        self.assertIn(f"SetEnvironmentVariable('{mcp.TOKEN_VARIABLE}', $null", self.cli.calls[-1])

    @unittest.skipUnless(os.name == "nt", "Task Scheduler is Windows only")
    def test_a_failed_registration_stops_install(self):
        calls = []
        self.fake_run(lambda args, input: calls.append(args) or subprocess.CompletedProcess(args, 1, "", ""))
        with unittest.mock.patch.object(mcp, "gateway_token", return_value="kept"):
            self.assertEqual(call(self.GATEWAYS, "install")[0], 1)
        self.assertEqual(len(calls), 1)

    @unittest.skipUnless(os.name == "posix", "systemd user units are Linux only")
    def test_install_stores_a_private_token_exports_it_to_login_shells_and_starts_a_unit_per_profile(self):
        os.environ.pop(mcp.TOKEN_VARIABLE, None)
        self.home.mkdir()
        profile = self.home / ".profile"
        profile.write_text("export KEEP=1")
        python = "/opt/a python/bin/python3"
        for _ in range(2):
            with unittest.mock.patch.object(sys, "executable", python):
                self.assertEqual(call(self.GATEWAYS, "install")[0], 0)
        token = mcp.gateway_token()
        self.assertGreaterEqual(len(token), 32)
        self.assertEqual(Path(mcp.token_file()).stat().st_mode & 0o777, 0o600)
        self.assertFalse([c for c in self.cli.calls if token in c])
        self.assertEqual(profile.read_text().count(self.GATEWAYS.profile_line()), 1)
        shell = subprocess.run(["sh", "-c", f". {shlex.quote(str(profile))}; printenv {mcp.TOKEN_VARIABLE} KEEP"],
                               capture_output=True, text=True, env={"PATH": os.environ["PATH"]})
        self.assertEqual(shell.stdout.split(), [token, "1"])
        exec_start = re.search(r"(?m)^ExecStart=(.*)$", Path(self.GATEWAYS.unit_path()).read_text())[1]
        self.assertEqual(shlex.split(exec_start), [python, str(MCP_BOOTSTRAP / "gateways.py"), "run", "%i"])
        enabled = [c for c in self.cli.calls if " enable " in c]
        self.assertEqual(enabled, [f"systemctl --user enable --now {self.GATEWAYS.UNIT.format(profile=p)}"
                                   for p in mcp.PROFILES] * 2)

    @unittest.skipUnless(os.name == "posix", "systemd user units are Linux only")
    def test_uninstall_stops_each_unit_then_removes_the_unit_the_profile_line_and_the_token(self):
        os.environ.pop(mcp.TOKEN_VARIABLE, None)
        self.home.mkdir()
        profile = self.home / ".profile"
        profile.write_text("export KEEP=1\n")
        self.assertEqual(call(self.GATEWAYS, "install")[0], 0)
        self.cli.calls.clear()
        for command in ("install", "uninstall"):
            self.assertEqual(call(self.GATEWAYS, command, "--what-if")[0], 0)
        self.assertEqual(self.cli.calls, [])
        self.assertTrue(mcp.gateway_token())
        for _ in range(2):
            self.assertEqual(call(self.GATEWAYS, "uninstall")[0], 0)
        self.assertEqual(self.cli.calls, [f"systemctl --user disable --now {self.GATEWAYS.UNIT.format(profile=p)}"
                                          for p in mcp.PROFILES] + ["systemctl --user daemon-reload"])
        self.assertEqual(profile.read_text(), "export KEEP=1\n")
        self.assertFalse(Path(self.GATEWAYS.unit_path()).exists())
        self.assertIsNone(mcp.gateway_token())

    def test_run_waits_for_docker_then_restarts_the_gateway_whenever_it_exits(self):
        engine = iter([1, 0, 0])
        tokens = []

        def docker(args, input):
            self.cli.calls.append(" ".join(args))
            tokens.append(os.environ.get(mcp.TOKEN_VARIABLE))
            return subprocess.CompletedProcess(args, next(engine) if args[1] == "info" else 3, "", "")

        def sleep(_):
            if len(self.cli.calls) >= 5:
                raise InterruptedError

        self.fake_run(docker)
        with unittest.mock.patch.object(self.GATEWAYS, "die_with_this_process"), \
                unittest.mock.patch.object(time, "sleep", sleep), \
                unittest.mock.patch.object(tempfile, "gettempdir", return_value=str(self.tmp)), \
                unittest.mock.patch.object(mcp, "gateway_token", return_value="token-value"), \
                self.assertRaises(InterruptedError):
            self.GATEWAYS.main(["run", "envative"])
        info, gateway = "docker info --format {{.ServerVersion}}", " ".join(mcp.gateway_command("envative", 8812))
        self.assertEqual(self.cli.calls, [info, info, gateway, info, gateway])
        # Loopback only: without --host the gateway listens on every interface.
        self.assertIn("--host 127.0.0.1 --port 8812", gateway)
        self.assertEqual(set(tokens), {"token-value"})
        self.assertTrue((self.tmp / "mcp-gateway-envative.log").exists())

    def test_run_without_a_token_starts_nothing(self):
        with unittest.mock.patch.object(mcp, "gateway_token", return_value=None), \
                unittest.mock.patch.object(tempfile, "gettempdir", return_value=str(self.tmp)):
            self.assertEqual(call(self.GATEWAYS, "run", "core-dev")[0], 1)
        self.assertEqual(self.cli.calls, [])

    @unittest.skipUnless(os.name == "nt", "the job object is Windows only")
    def test_stopping_the_runner_stops_what_it_started(self):
        # A stand-in runner joins the job, starts a long sleep and prints its pid. Killing the runner, as Task
        # Scheduler's End does, must take the sleep with it.
        script = f"import sys; sys.path.insert(0, {str(MCP_BOOTSTRAP)!r}); import gateways, subprocess, time; " \
                 "gateways.die_with_this_process(); " \
                 "print(subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']).pid, flush=True); " \
                 "time.sleep(60)"
        runner = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True)
        with runner:
            child = int(runner.stdout.readline())
            import ctypes
            kernel32 = ctypes.WinDLL("kernel32")
            kernel32.OpenProcess.restype = ctypes.c_void_p
            handle = ctypes.c_void_p(kernel32.OpenProcess(0x00100000, False, child))  # SYNCHRONIZE
            self.assertTrue(handle.value)
            self.addCleanup(kernel32.CloseHandle, handle)
            runner.kill()
        self.assertEqual(kernel32.WaitForSingleObject(handle, 10000), 0)  # WAIT_OBJECT_0: the sleep has exited


class Usage(SetupTest):
    """Each MCP script run as a program: a usage error exits 1."""

    def test_an_unknown_option_exits_1(self):
        for script in ("install.py", "verify.py", "gateways.py"):
            r = subprocess.run([sys.executable, str(MCP_BOOTSTRAP / script), "--nope"], capture_output=True,
                               text=True, cwd=self.tmp)
            self.assertEqual(r.returncode, 1, script)
            self.assertIn("usage:", r.stderr, script)
