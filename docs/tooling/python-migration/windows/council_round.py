"""One real blind round of the model council, run from this checkout (plan.md step 11's last check).

    python3 council_round.py [--codex-model <id>] [--claude-model <id>] [--minutes <n, default 20>]

Run it from PowerShell on Windows, with every other Codex session closed; on Linux it checks the script itself. It builds
a throwaway repository holding one small decision, fills the blind-round template in references/member-prompt.md
for each member, runs the Codex member through codex_member.py and the Claude member through `claude -p` with no
edit tools, tallies the round with tally.py, and prints one line per check:

    ROUND <check> pass|fail <facts>

Checks:
- preflight: codex and claude are on PATH; their versions. On Windows it refuses to start while any other Codex
  process runs (the CLI, the desktop app, an IDE's): they all write the same sandbox log, so another session's lines
  could stand in for this run's.
- codex-member: a MEMBER done line.
- sandbox-mode: the argv codex_member.py's run() received carries -c windows.sandbox="unelevated" on Windows and no
  windows.sandbox elsewhere, and Codex ran shell commands. On Windows, Codex's own sandbox log
  ($CODEX_HOME/.sandbox/sandbox*.log) must also show the mode: this run added START lines, which Codex writes for
  each command it runs in its Windows sandbox, and no "setup refresh: spawning" line, which only the elevated path
  writes, once per command, as it starts codex-windows-sandbox-setup.exe; and no other Codex process may be running
  once the member is done. That is codex-rs/windows-sandbox-rs at rust-v0.162.1 (identity.rs
  require_logon_sandbox_creds, setup.rs run_setup_refresh_payload, unified_exec/backends/legacy.rs); the docs say
  nothing about the log, so the facts name the installed version and say when the rule is unverified for it. Only
  the counts are kept: the log is shared, and its lines are never saved.
- claude-member: an answer block.
- read-only: the repository is unchanged.
- tally: a COUNCIL line that is not incomplete.
- scrubbed: no home path, user name or command output is left in the saved evidence (below).
Then it exits 1 if any check failed.

Evidence goes to results/council-round-<windows|linux>/ beside this script, replaced on each run: both prompts, both
answers, Codex's event stream and log, the argv run() received, and the printed lines (round.txt). The folder is committed to a public repository, so every saved file is scrubbed: the home folder
becomes ~ (%USERPROFILE% on Windows), the user name <user> and the Codex session id <session>, and the event
stream keeps each command but not its output.
"""
import argparse
import contextlib
import csv
import getpass
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
COUNCIL = HERE.parents[3] / "skills" / "model-council"
sys.path.insert(0, str(COUNCIL / "scripts"))

import codex_member  # noqa: E402
import run as spawn  # noqa: E402  (codex_member's spawn helper)

WINDOWS = os.name == "nt"
# Codex's sandbox service (the [[bin]] of codex-rs/windows-sandbox-service): a Windows service that runs with every
# session closed, so it is no other session.
SANDBOX_SERVICE = "codex-windows-sandbox-service.exe"
# The Codex release whose source the sandbox-log rule was read from.
LOG_RULE_VERSION = "0.162.1"

FILES = {
    "cache.py": '''"""The per-request cache, one process-wide dict shared by every tenant."""
_cache = {}


def cache_key(tenant_id, user_id, resource):
    return f"{user_id}:{resource}"


def get(tenant_id, user_id, resource, load):
    key = cache_key(tenant_id, user_id, resource)
    if key not in _cache:
        _cache[key] = load()
    return _cache[key]
''',
    "users.py": '''"""User ids are allocated per tenant: every tenant's first user is 1."""


def next_user_id(tenant):
    tenant.last_user_id += 1
    return tenant.last_user_id
''',
}
DECISION = ("A reviewer says cache_key in cache.py lets one tenant read another tenant's cached entries. Candidate "
            "actions: add tenant_id to the key built by cache_key; or no change.")
FOCUS = {"codex": "simplicity and maintenance: compare the smallest valid change with current conventions, and name "
                  "the real harm of leaving the code as is",
         "claude": "correctness and contract: trace the claimed failure through real callers, invariants and tests, "
                   "and look for an existing guard that refutes it"}
lines = []
failed = False


def report(check, ok, facts=""):
    global failed
    failed |= not ok
    line = f"ROUND {check} {'pass' if ok else 'fail'} {facts}".rstrip()
    lines.append(line)
    print(line, flush=True)
    return ok


def run(args, cwd=None, timeout=None, stdin=None):
    """Run args without a shell; return (code, stdout, stderr), with code 124 on timeout."""
    try:
        with open(stdin or os.devnull, "rb") as i:
            r = subprocess.run([str(a) for a in args], cwd=cwd, timeout=timeout, stdin=i, capture_output=True)
        return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def git(cwd, *args):
    return run(["git", "-C", cwd, *args])[1].strip()


def blind_prompt(member, repo, head):
    """The blind-round template from member-prompt.md with this round's decision, focus and evidence filled in."""
    text = (COUNCIL / "references" / "member-prompt.md").read_text(encoding="utf-8")
    template = re.search(r"## Blind round\n+~~~~text\n(.*?)~~~~", text, re.DOTALL)[1]
    evidence = (f"Repository {Path(repo).as_posix()} at commit {head}, a clean working tree: read cache.py and "
                "users.py there. Nothing has been run; no tests exist. Observed: the code as committed. Assumed: "
                "nothing else.")
    for label, value in (("Decision:", DECISION), ("Your focus:", FOCUS[member]), ("Evidence", evidence)):
        template = re.sub(rf"({re.escape(label)}[^\n]*\n)<.*?>\n", lambda m: m[1] + value + "\n", template, count=1,
                          flags=re.DOTALL)
    return template


def commands(events):
    """(ran, failed) counts of the shell commands in a Codex --json event stream."""
    ran = bad = 0
    for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line).get("item") or {}
        except ValueError:
            continue
        if item.get("type") == "command_execution" and item.get("status") in ("completed", "failed"):
            ran += 1
            bad += item.get("exit_code") != 0
    return ran, bad


def member(argv):
    """Run codex_member.main(argv) in-process: (exit code, its one line, the argv its run() handed to the spawn)."""
    spawned, real = [], spawn.run

    def recording(args, **kw):
        spawned.append(list(args))
        return real(args, **kw)

    out, err = io.StringIO(), io.StringIO()
    spawn.run = recording
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = codex_member.main([str(x) for x in argv])
    finally:
        spawn.run = real
    return code, (out.getvalue() or err.getvalue()).strip(), spawned[0] if spawned else []


def sandbox_logs():
    """{path: size} of Codex's Windows sandbox logs, $CODEX_HOME/.sandbox/sandbox*.log (CODEX_HOME: ~/.codex)."""
    d = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / ".sandbox"
    return {f: f.stat().st_size for f in d.glob("sandbox*.log")} if d.is_dir() else {}


def log_lines_since(before):
    """The lines added to the sandbox logs since the sizes in before, including any new log file."""
    added = []
    for f in sorted(sandbox_logs()):
        with open(f, "rb") as h:
            h.seek(before.get(f, 0))
            added += h.read().decode("utf-8", "replace").splitlines()
    return added


def codex_processes():
    """'<image> (<pid>)' for each running Codex process on Windows, any image named codex* but the sandbox service:
    the CLI, the desktop app and their sandbox helpers. Empty elsewhere, where Codex keeps no shared sandbox log."""
    if not WINDOWS:
        return []
    rows = csv.reader(run(["tasklist", "/FO", "CSV", "/NH"])[1].splitlines())
    return [f"{r[0]} ({r[1]})" for r in rows
            if len(r) > 1 and r[0].lower().startswith("codex") and r[0].lower() != SANDBOX_SERVICE]


def council_round(a, repo, out):
    codex, claude = shutil.which("codex"), shutil.which("claude")
    versions = {name: run([exe, "--version"])[1].strip() if exe else "missing"
                for name, exe in (("codex", codex), ("claude", claude))}
    others = codex_processes()
    facts = f"python={sys.version.split()[0]} codex={versions['codex']!r} claude={versions['claude']!r}"
    if others:
        facts += f" other_codex={others}: close every Codex session (CLI, desktop app, IDE) and run again"
    if not report("preflight", bool(codex and claude) and not others, facts):
        return
    repo.mkdir()
    for name, body in FILES.items():
        (repo / name).write_text(body, encoding="utf-8", newline="\n")
    run(["git", "init", "-q", repo])
    git(repo, "add", ".")
    git(repo, "-c", "user.name=council", "-c", "user.email=council@example.invalid", "commit", "-q", "-m", "init")
    head = git(repo, "rev-parse", "HEAD")
    for name in ("codex", "claude"):
        (out / f"round0-{name}.prompt.md").write_text(blind_prompt(name, repo, head), encoding="utf-8")

    before = sandbox_logs()
    code, member_line, argv = member([repo, out / "round0-codex.prompt.md", out / "round0-codex.md",
                                      "--model", a.codex_model, "--effort", "high", "--timeout", f"{a.minutes}m"])
    sandbox_log = log_lines_since(before)
    others = codex_processes()
    (out / "codex-argv.json").write_text(json.dumps(argv, indent=1), encoding="utf-8")
    report("codex-member", code == 0 and member_line.startswith("MEMBER done "), member_line)
    flag = 'windows.sandbox="unelevated"' in argv
    any_flag = any(x.startswith("windows.sandbox=") for x in argv)
    events = out / "round0-codex.jsonl"
    ran, bad = commands(events) if events.is_file() else (0, 0)
    starts = sum("START: " in line for line in sandbox_log)
    helper = sum("setup refresh: spawning" in line for line in sandbox_log)
    installed = re.search(r"\d+\.\d+\.\d+", versions["codex"])
    rule = f"rust-v{LOG_RULE_VERSION}" + ("" if installed and installed[0] == LOG_RULE_VERSION else
                                          ", unverified for this version")
    if WINDOWS:
        mode_ok = flag and starts > 0 and helper == 0 and not others
    else:
        mode_ok = not any_flag
    report("sandbox-mode", mode_ok and ran > bad,
           f"os={os.name} argv_unelevated={flag} commands_ran={ran} commands_failed={bad} "
           f"sandbox_log_start={starts} sandbox_log_setup_helper={helper} other_codex={others or 'none'} "
           f"codex={installed[0] if installed else 'unknown'} log_rule={rule}")

    code, stdout, stderr = run([claude, "-p", "--model", a.claude_model, "--disallowedTools", "Edit,Write,NotebookEdit"],
                               cwd=repo, timeout=a.minutes * 60, stdin=out / "round0-claude.prompt.md")
    (out / "round0-claude.md").write_text(stdout, encoding="utf-8")
    block = re.search(r"(?im)^\s*disposition:\s*(\S+)", stdout)
    report("claude-member", code == 0 and bool(block), f"exit={code} disposition={block[1] if block else 'none'}"
           + (f" stderr={stderr.strip()[:200]!r}" if code else ""))

    status = git(repo, "status", "--porcelain")
    report("read-only", git(repo, "rev-parse", "HEAD") == head and not status, f"head={head[:12]} status={status!r}")

    code, stdout, stderr = run([sys.executable, COUNCIL / "scripts" / "tally.py", out / "round0-claude.md",
                                out / "round0-codex.md", "--exchange", "0"])
    tally_line = stdout.strip() or stderr.strip()
    report("tally", code == 0 and tally_line.startswith("COUNCIL ") and "incomplete" not in tally_line.split()[1],
           tally_line)


def home_forms():
    """Every spelling of the home folder a saved file may hold: as stored, resolved, with forward slashes, its
    Windows 8.3 short name (TEMP often uses it), and each of those JSON-escaped."""
    home = str(Path.home())
    forms = {home, os.path.realpath(home), Path(home).as_posix()}
    if os.name == "nt":  # a real Windows API, whatever WINDOWS is set to
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(home, buf, 1024):
            forms |= {buf.value, Path(buf.value).as_posix()}
    forms |= {json.dumps(f)[1:-1] for f in forms}
    return sorted(forms, key=len, reverse=True)


# A home path the masking missed, in any spelling: C:\Users\<name>, C:/Users/<name>, /home/<name>, /Users/<name>.
HOME_PATH = re.compile(r"(?i)\b[a-z]:(?:\\+|/)users(?:\\+|/)(?!public\b)[^\\/\s\"']+|/home/[^/\s\"']+|/Users/[^/\s\"']+")


def scrub(out):
    """Make the evidence safe to commit (see the module header). Returns the files a home path, the user name or a
    command's output still survives in, which should be none."""
    events = out / "round0-codex.jsonl"
    session = None
    if events.is_file():
        kept = []
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                kept.append(line)
                continue
            session = session or event.get("thread_id")
            (event.get("item") or {}).pop("aggregated_output", None)
            kept.append(json.dumps(event, ensure_ascii=False))
        events.write_text("".join(line + "\n" for line in kept), encoding="utf-8")
    mask = "%USERPROFILE%" if WINDOWS else "~"
    user = re.compile(rf"(?i)\b{re.escape(getpass.getuser())}\b")
    left = []
    for f in sorted(out.iterdir()):
        text = f.read_text(encoding="utf-8", errors="replace")
        for form in home_forms():
            text = re.sub(re.escape(form), lambda _: mask, text, flags=re.IGNORECASE if WINDOWS else 0)
        text = user.sub("<user>", text)
        if session:
            text = text.replace(session, "<session>")
        f.write_text(text, encoding="utf-8")
        if HOME_PATH.search(text) or user.search(text) or '"aggregated_output"' in text:
            left.append(f.name)
    return left


def main(argv):
    p = argparse.ArgumentParser(prog="council_round.py")
    p.add_argument("--codex-model", default="gpt-6.1-sol")
    p.add_argument("--claude-model", default="opus")
    p.add_argument("--minutes", type=int, default=20)
    a = p.parse_args(argv)
    out = HERE / "results" / f"council-round-{'windows' if WINDOWS else 'linux'}"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    root = Path(tempfile.mkdtemp(prefix="council-round-")).resolve()
    try:
        council_round(a, root / "repo", out)
    except KeyboardInterrupt:
        report("interrupted", False)
    finally:
        shutil.rmtree(root, ignore_errors=True)
        (out / "round.txt").write_text("".join(line + "\n" for line in lines), encoding="utf-8")
        left = scrub(out)
        report("scrubbed", not left, f"files_with_a_home_path_user_name_or_command_output={left or 'none'}")
        with open(out / "round.txt", "a", encoding="utf-8") as f:
            f.write(lines[-1] + "\n")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
