"""Link this checkout into the selected clients on Windows, Linux or macOS.
  python3 setup_skills_link.py [--tools codex,claude,opencode,copilot] [--home-directory <path>]
                               [--replace-conflicts] [--what-if]
Without --tools, sets up the clients found on PATH; --tools also prepares clients not installed yet. A conflicting
entry is kept and setup ends incomplete (exit 1) unless --replace-conflicts backs it up and replaces it. --what-if
changes nothing and prints what setup would do. An explicit --home-directory isolates every destination and ignores
the clients' environment overrides.
"""
import os
import sys
from pathlib import Path

REPO = str(Path(__file__).absolute().parent)
sys.path.insert(0, str(Path(REPO) / "scripts"))

import setup_common as sc  # noqa: E402


def main(argv):
    parser = sc.Parser(prog="setup_skills_link.py", description="Link this checkout into the selected clients.")
    parser.add_argument("--tools", help="comma-separated: codex, claude, opencode, copilot")
    parser.add_argument("--home-directory", help="an isolated home for every destination")
    parser.add_argument("--replace-conflicts", action="store_true")
    parser.add_argument("--what-if", action="store_true")
    args = parser.parse_args(argv)
    paths = sc.setup_paths(args.home_directory)
    selected = sc.select_tools(args.tools)
    if not selected:
        print("No supported clients detected. Use --tools to select clients explicitly.")
        return 0
    linker = sc.Linker(paths.backup_root, args.replace_conflicts, args.what_if)
    complete = True
    for target in sc.skill_targets(REPO, paths, selected):
        if not (linker.link_children if target.children else linker.link)(target.source, target.path):
            complete = False
    if "codex" in selected:
        linker.remove_legacy_codex_links(REPO, paths)
    if "claude" in selected:
        # The Node status line became statusline.py. Its old link goes only while it points into this checkout.
        linker.remove_stale(os.path.join(paths.claude_root, "statusline.js"),
                            os.path.join(REPO, "statusline", "statusline.js"), "Remove retired status line link")
    if args.what_if:
        print("Preview complete. No files were changed.")
    elif not complete:
        raise sc.Fail("Setup is incomplete; conflicting entries were preserved. Review the warnings or run"
                      " verify_setup.py.")
    else:
        print(f"Skills configured for: {', '.join(selected)}. Restart clients to refresh skill discovery.")
    return 0


if __name__ == "__main__":
    sc.entry(main)
