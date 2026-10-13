"""One real blind round of the model council, run from this checkout (plan.md step 11's last check).

    python3 council_round.py [--codex-model <id>] [--claude-model <id>] [--minutes <n, default 20>]

Run it from PowerShell on Windows; on Linux it checks the script itself. It builds a throwaway repository holding
one small decision, fills the blind-round template in references/member-prompt.md for each member, runs the Codex
member through codex_member.py and the Claude member through `claude -p` with no edit tools, tallies the round with
tally.py, and prints one line per check:

    ROUND <check> pass|fail <facts>

Checks: preflight (codex and claude on PATH, their versions), codex-member (a MEMBER done line), sandbox-mode (the
codex argv carries -c windows.sandbox="unelevated" on Windows and no windows.sandbox elsewhere, and Codex ran shell
commands inside its sandbox: on a machine where the elevated sandbox is broken, openai/codex#52488, none would run
in any other mode), claude-member (an answer block), read-only (the repository is unchanged), tally (a COUNCIL line
that is not incomplete). Then it exits 1 if any check failed.

Evidence goes to results/council-round-<windows|linux>/ beside this script, replaced on each run: the packet and
both prompts, both answers, Codex's event stream and log, the codex argv, and the printed lines (round.txt). The
Codex session id is replaced by <session> in every saved file, since they are committed to a public repository.
"""
import argparse
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


def council_round(a, repo, out):
    codex, claude = shutil.which("codex"), shutil.which("claude")
    versions = {name: run([exe, "--version"])[1].strip() if exe else "missing"
                for name, exe in (("codex", codex), ("claude", claude))}
    if not report("preflight", bool(codex and claude), f"python={sys.version.split()[0]} "
                  f"codex={versions['codex']!r} claude={versions['claude']!r}"):
        return
    repo.mkdir()
    for name, body in FILES.items():
        (repo / name).write_text(body, encoding="utf-8", newline="\n")
    run(["git", "init", "-q", repo])
    git(repo, "add", ".")
    git(repo, "-c", "user.name=council", "-c", "user.email=council@example.invalid", "commit", "-q", "-m", "init")
    head = git(repo, "rev-parse", "HEAD")
    for member in ("codex", "claude"):
        (out / f"round0-{member}.prompt.md").write_text(blind_prompt(member, repo, head), encoding="utf-8")

    argv = codex_member.codex_args(str(repo), str(out / "round0-codex.md"), a.codex_model, "high", "")
    (out / "codex-argv.json").write_text(json.dumps(argv, indent=1), encoding="utf-8")
    code, stdout, stderr = run([sys.executable, COUNCIL / "scripts" / "codex_member.py", repo,
                                out / "round0-codex.prompt.md", out / "round0-codex.md", "--model", a.codex_model,
                                "--effort", "high", "--timeout", f"{a.minutes}m"])
    member_line = stdout.strip() or stderr.strip()
    report("codex-member", code == 0 and member_line.startswith("MEMBER done "), member_line)
    windows_flag = any(x.startswith("windows.sandbox=") for x in argv)
    want_flag = 'windows.sandbox="unelevated"' in argv if os.name == "nt" else not windows_flag
    events = out / "round0-codex.jsonl"
    ran, bad = commands(events) if events.is_file() else (0, 0)
    setup_failed = events.is_file() and "setup refresh had errors" in events.read_text(encoding="utf-8", errors="replace")
    report("sandbox-mode", want_flag and ran > bad and not setup_failed,
           f"os={os.name} windows_flag={windows_flag} commands_ran={ran} commands_failed={bad} "
           f"setup_refresh_errors={setup_failed}")

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


def redact(out):
    """Replace the Codex session id with <session> in every evidence file."""
    events = out / "round0-codex.jsonl"
    m = events.is_file() and re.search(r'"thread_id": *"([^"]+)"', events.read_text(encoding="utf-8", errors="replace"))
    if not m:
        return
    for f in out.iterdir():
        text = f.read_text(encoding="utf-8", errors="replace")
        f.write_text(text.replace(m[1], "<session>"), encoding="utf-8")


def main(argv):
    p = argparse.ArgumentParser(prog="council_round.py")
    p.add_argument("--codex-model", default="gpt-6.1-sol")
    p.add_argument("--claude-model", default="opus")
    p.add_argument("--minutes", type=int, default=20)
    a = p.parse_args(argv)
    out = HERE / "results" / f"council-round-{'windows' if os.name == 'nt' else 'linux'}"
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
        redact(out)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
