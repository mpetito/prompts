"""Test support for the setup and MCP suites: load a script, call its main() in-process, and keep every test inside a
throwaway folder.

Every script spawns through setup_common.run, so a test that fakes a CLI replaces that one function. HOME,
USERPROFILE and the clients' config variables point into the test's own folder, so nothing reaches the real
~/.claude, ~/.codex or ~/.agents.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCP_BOOTSTRAP = ROOT / "mcp" / "bootstrap"
for folder in (ROOT / "scripts", MCP_BOOTSTRAP):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import setup_common as sc  # noqa: E402

# The variables that move a client's files away from the home; a test sets the ones it needs.
CLIENT_VARIABLES = ("CODEX_HOME", "CLAUDE_CONFIG_DIR", "OPENCODE_CONFIG", "OPENCODE_CONFIG_DIR", "XDG_CONFIG_HOME")


def load(path):
    """Import the script at path as a fresh module, without running it."""
    path = Path(path)
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call(module, *argv):
    """Run module.main(argv) as setup_common.entry would: returns (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = module.main([str(a) for a in argv])
        except sc.Fail as e:
            print(e, file=sys.stderr)
            code = 1
    return code, out.getvalue(), err.getvalue()


def symlink(target, link):
    """A directory symlink at link to target, which may be relative or missing."""
    os.symlink(target, link, target_is_directory=True)


class SetupTest(unittest.TestCase):
    """A throwaway folder per test, with HOME and USERPROFILE inside it, not yet created, and no client variable."""

    def setUp(self):
        self.tmp = Path(os.path.realpath(tempfile.mkdtemp(prefix="prompts-tests-")))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.home = self.tmp / "home"
        env = {k: v for k, v in os.environ.items() if k not in CLIENT_VARIABLES}
        env.update(HOME=str(self.home), USERPROFILE=str(self.home))
        patcher = unittest.mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def fake_run(self, handler):
        """Send every setup_common.run call to handler(args, input) instead of a process."""
        patcher = unittest.mock.patch.object(sc, "run", lambda args, *, input=None, **_: handler(list(args), input))
        patcher.start()
        self.addCleanup(patcher.stop)
