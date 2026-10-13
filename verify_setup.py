"""Check this checkout's links for the selected clients, and the python3 its scripts run on.
  python3 verify_setup.py [--tools codex,claude,opencode,copilot] [--home-directory <path>]
Prints [OK] for each link in place and [AVAILABLE] for each optional command found; a missing optional command only
warns. Exits 1 naming how many checks failed: a missing or conflicting link, a skills folder that is not a real
folder, or a python3 that is missing, is the Microsoft Store placeholder, or is older than 3.12.
"""
import os
import re
import shutil
import sys
from pathlib import Path

REPO = str(Path(__file__).absolute().parent)
sys.path.insert(0, str(Path(REPO) / "scripts"))

import setup_common as sc  # noqa: E402

MINIMUM = (3, 12)
STORE_PLACEHOLDER = 9009    # the exit code of Windows' python3 App Execution Alias when no Python is installed


def check_python():
    """None when python3, run as its own process the way skills and hooks run it, is MINIMUM or later; else why
    not. A process, not this interpreter: this one may be a different install."""
    version = sc.run(["python3", "--version"], timeout=60)
    if version.returncode == 127:
        return "python3 is not on PATH. Install Python 3.12 or later."
    if version.returncode == STORE_PLACEHOLDER:
        return "python3 is the Microsoft Store placeholder, not an installed Python. Install Python 3.12 or later."
    if version.returncode:
        return f"python3 --version failed (exit {version.returncode})."
    info = sc.run(["python3", "-c", "import sys; print(sys.version_info[:2])"], timeout=60)
    found = tuple(int(n) for n in re.findall(r"\d+", info.stdout))
    if info.returncode or found < MINIMUM:
        return f"python3 is {version.stdout.strip() or info.stdout.strip()}; scripts need 3.12 or later."
    print(f"[OK] python3: {version.stdout.strip()}")
    return None


def main(argv):
    parser = sc.Parser(prog="verify_setup.py", description="Check this checkout's links and python3.")
    parser.add_argument("--tools", help="comma-separated: codex, claude, opencode, copilot")
    parser.add_argument("--home-directory", help="the isolated home setup used")
    args = parser.parse_args(argv)
    paths = sc.setup_paths(args.home_directory)
    selected = sc.select_tools(args.tools)
    if not selected:
        raise sc.Fail("No clients detected. Use --tools to verify prepared client files.")
    failed = 0
    for target in sc.skill_targets(REPO, paths, selected):
        links = [target]
        if target.children:
            if sc.is_link(target.path) or not os.path.isdir(target.path):
                sc.warn(f"Skills root must be a real directory: {target.path}")
                failed += 1
            links = [sc.Target(child, os.path.join(target.path, name), False)
                     for name, child in sc.skill_dirs(target.source)]
        for link in links:
            if os.path.exists(link.source) and sc.is_repo_link(link.path, link.source):
                print(f"[OK] {link.path}")
            else:
                sc.warn(f"Missing or conflicting link: {link.path}")
                failed += 1
    for command in [*selected, "gh", "node"]:
        if shutil.which(command):
            print(f"[AVAILABLE] {command}")
        else:
            sc.warn(f"Optional dependency not on PATH: {command}")
    problem = check_python()
    if problem:
        sc.warn(problem)
        failed += 1
    if failed:
        raise sc.Fail(f"{failed} setup check(s) failed.")
    print("Skill links verified. MCP registration is checked separately by mcp/bootstrap/verify.py.")
    return 0


if __name__ == "__main__":
    sc.entry(main)
