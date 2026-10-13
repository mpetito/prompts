"""Live smoke test of the Python orchestration scripts with real herdr, Claude and Codex agents (plan.md step 9).

    python3 smoke.py [--claude-model <id>] [--codex-model <id>] [--runs <n, default 20>] [--minutes <n, default 20>]
                     [--skip-codex]

Run it from a pane inside herdr, with the branch under test checked out in the checkout that ~/.claude links to,
so the agents run its skills and hooks. It builds a throwaway repository and a separate ORCHESTRATION_HOME under a
temporary folder, never touching the owner's builds, registry or mail, and prints one line per item:

    SMOKE <item> pass|fail <facts>

Items: preflight, launch (a thread starts and mails MAIN), thread-guard (the thread's Write into the checkout is
refused), lanes (a Claude lane and a Codex lane each commit in their worktree and mail the thread; the Codex one
through mail.py --home from its sandbox), lane-guard (the Claude lane's Write into the checkout is refused),
finish-running (finish_lane.py refuses while the lane runs, given its path native, with forward slashes and
relative), finish-closed (it retires both lanes once their panes close), rotate, hook-cost:<hook> (median ms of
<runs> runs as Claude Code starts the agents' exec-form hooks: python3 -c, no shell, under 700 ms), close, cleanup
(no agent, worktree, branch or registry row of the build is left). Then it exits 1 if any item failed.

--skip-codex runs the Claude lane alone, for a machine where Codex's sandbox can't run commands.

Agents can stall on a startup or permission prompt: the script says which pane to answer and keeps waiting, up to
--minutes per wait. Whatever happens, it closes the build's panes and removes the temporary folder at the end.
"""
import argparse
import json
import os
import secrets
import shutil
import stat
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SKILLS = Path.home() / ".claude" / "skills"
SCRIPTS = SKILLS / "agent-orchestration" / "scripts"
HOOKS = SKILLS / "agent-orchestration" / "hooks"
THREAD = SKILLS / "orchestration-main" / "scripts" / "thread.py"
# How a skill tells an agent to run a script: the interpreter named and a path every shell expands.
INVOKE = 'python3 "$HOME/.claude/skills/agent-orchestration/scripts/{}.py"'

failed = False


def report(item, ok, facts=""):
    global failed
    failed |= not ok
    say(f"SMOKE {item} {'pass' if ok else 'fail'} {facts}".rstrip())
    return ok


def say(line):
    """Print a line; a closed stdout (a pipe whose reader was interrupted) never stops the run or its cleanup."""
    try:
        print(line, flush=True)
    except OSError:
        pass


def run(args, cwd=None, timeout=None, input=None):
    """Run args without a shell; return (code, stdout, stderr), with code 124 on timeout."""
    try:
        r = subprocess.run([str(a) for a in args], cwd=cwd, timeout=timeout, input=input, capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"


def script(name, *args, **kw):
    return run(["python3", SCRIPTS / f"{name}.py", *args], **kw)


def git(cwd, *args):
    return run(["git", "-C", cwd, *args])


def agents():
    code, out, _ = run(["herdr", "agent", "list"])
    return json.loads(out)["result"]["agents"] if code == 0 else []


def wait_mail(box, watch, minutes, want=1):
    """Wait on box until want messages arrived, saying which pane to answer when a watched agent blocks. Returns
    the bodies read, possibly fewer than want after the time runs out."""
    bodies, deadline = [], time.time() + minutes * 60
    while len(bodies) < want and time.time() < deadline:
        left = max(10, int(deadline - time.time()))
        _, line, _ = script("mail", "wait", box, "--watch", ",".join(watch), "--timeout", str(min(left, 300)))
        if line.startswith("MAIL"):
            _, text, _ = script("mail", "read", box)
            bodies += [m for m in text.split("=== ")[1:]]
        elif line.startswith("BLOCKED"):
            say(f"  {line}: answer the prompt in that agent's pane; still waiting")
        elif line.startswith("GONE"):
            say(f"  {line}")
    return bodies


def await_idle(name, minutes):
    """Wait until agent name is idle, saying once that its prompt needs answering; False if it never gets there."""
    deadline, told = time.time() + minutes * 60, False
    while time.time() < deadline:
        status = next((g.get("agent_status") for g in agents() if (g.get("name") or "") == name), "gone")
        if status in ("idle", "done"):
            return True
        if status == "gone":
            return False
        if status == "blocked" and not told:
            say(f"  BLOCKED {name}: answer its startup prompt in its pane; the lane gets its brief after")
            told = True
        time.sleep(3)
    return False


def guard_payload(path, cwd):
    return json.dumps({"tool_name": "Write", "cwd": str(cwd), "tool_input": {"file_path": str(path), "content": "x"}})


def remove(root):
    """Delete root. Git makes its object files read-only, which rmtree can't delete on Windows: clear the bit and
    retry, and say what still couldn't be removed."""
    def writable(func, path, _exc):
        for each in (os.path.dirname(path), path):
            os.chmod(each, os.stat(each).st_mode | stat.S_IWRITE | stat.S_IEXEC * os.path.isdir(each))
        func(path)
    try:
        shutil.rmtree(root, onexc=writable)
    except OSError as e:
        say(f"  could not remove {Path(root).as_posix()}: {e}")


def preflight():
    missing = [t for t in ("python3", "git", "herdr", "claude", "codex") if not shutil.which(t)]
    linked = (HOOKS / "guard_bash.py").is_file() and THREAD.is_file()
    inside = os.environ.get("HERDR_ENV") == "1"
    return report("preflight", not missing and linked and inside,
                  f"missing={','.join(missing) or 'none'} hooks_linked={linked} inside_herdr={inside}")


def thread_brief(build, checkout):
    send = INVOKE.format("mail") + f" send {build}/main --from {build}/thread"
    return f"""This is a smoke test of the orchestration scripts, not a build. Do only the steps below, in order, then
stop and wait: no mail wait, no lanes, no state file.

1. Use the Write tool to create {Path(checkout, 'smoke-thread-guard.txt').as_posix()} with the text x. A hook is
   expected to refuse it; do not retry or work around a refusal.
2. Run: {send} "STATUS: working - smoke thread up; guard <refused|wrote>"
   writing refused if step 1 was refused and wrote if the file was written.
"""


def lane_brief(build, lane, kind, checkout, home):
    home_opt = f" --home {Path(home).as_posix()}" if kind == "codex" else ""
    send = INVOKE.format("mail") + f" send {build}/thread{home_opt} --from {build}/{lane}"
    guard = (f"2. Use your file-writing tool to create {Path(checkout, 'smoke-lane-guard.txt').as_posix()} with the "
             "text x. A hook is expected to refuse it; do not retry or work around a refusal.\n" if kind == "claude"
             else "2. (Nothing to do in this step.)\n")
    return f"""This is a smoke test of the orchestration scripts. Do only the steps below, in order, then stop.

1. In your current folder, create lane.txt containing "{kind} ok", then git add lane.txt and git commit -m smoke.
{guard}3. Run: {send} "STATUS: done - lane.txt committed; guard <refused|wrote|n/a>"
   writing refused or wrote for step 2's outcome, or n/a if step 2 had nothing to do.
"""


def hook_costs(coord, checkout, runs):
    payloads = {
        "guard_bash": json.dumps({"tool_name": "Bash", "cwd": str(coord), "tool_input": {"command": "git status"}}),
        "guard_writes": guard_payload(Path(coord, "notes.md"), coord),
        "guard_timestamps": json.dumps({"tool_name": "Edit", "cwd": str(coord), "tool_input": {
            "file_path": str(Path(coord, ".orchestration", "notes.md")), "new_string": "done 14:30Z"}}),
    }
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(coord)}
    for hook, payload in payloads.items():
        times, code = [], 0
        start_hook = (f"import os,runpy,sys; p=os.path.expanduser('~/.claude/skills/agent-orchestration/hooks/{hook}.py'); "
                      "sys.argv=[p]; runpy.run_path(p, run_name='__main__')")
        for _ in range(runs):
            start = time.perf_counter()
            r = subprocess.run(["python3", "-c", start_hook], input=payload, capture_output=True, text=True, cwd=coord,
                               env=env)
            times.append((time.perf_counter() - start) * 1000)
            code = r.returncode or code
        median = statistics.median(times)
        report(f"hook-cost:{hook}", code == 0 and median < 700, f"median_ms={median:.0f} runs={runs} exit={code}")


def smoke(a, root, build, home):
    checkout = root / "smoke-repo"
    checkout.mkdir()
    run(["git", "init", "-q", "-b", "main", checkout])
    git(checkout, "-c", "user.name=smoke", "-c", "user.email=smoke@example.invalid", "commit", "-q",
        "--allow-empty", "-m", "init")
    git(checkout, "config", "user.name", "smoke")
    git(checkout, "config", "user.email", "smoke@example.invalid")
    coord = root / f"smoke-repo-orch-{build}"

    brief = root / "thread-brief.md"
    brief.write_text(thread_brief(build, checkout), encoding="utf-8")
    code, line, err = run(["python3", THREAD, "launch", build, checkout, brief], timeout=300)
    if not report("launch:start", line.startswith(("LAUNCHED", "BLOCKED")), line or err):
        return
    if line.startswith("BLOCKED"):
        say(f"  answer the startup prompt in herdr workspace {build}")
    bodies = wait_mail(f"{build}/main", [build], a.minutes)
    if not report("launch", bool(bodies), f"mail={len(bodies)}"):
        return
    report("thread-guard", any("guard refused" in b for b in bodies) and not (checkout / "smoke-thread-guard.txt").exists(),
           f"file_written={(checkout / 'smoke-thread-guard.txt').exists()} said={[b.splitlines()[-1] for b in bodies]!r}")

    lanes = {}
    kinds = (("cl", "claude", a.claude_model),) + (() if a.skip_codex else (("cx", "codex", a.codex_model),))
    for lane, kind, model in kinds:
        wt = root / f"smoke-repo-wt-{lane}"
        git(coord, "worktree", "add", "-q", "-b", f"lane/{lane}", wt, f"orchestration/{build}")
        lb = root / f"brief-{lane}.md"
        lb.write_text(lane_brief(build, lane, kind, checkout, home), encoding="utf-8")
        code, line, err = script("lane", build, lane, wt, lb, "--kind", kind, "--model", model, timeout=300)
        report(f"lane-start:{lane}", line.startswith(("LANE", "BLOCKED")), line or err)
        name = f"{build}-{lane}"
        lanes[lane] = (wt, next((g["pane_id"] for g in agents() if (g.get("name") or "") == name), ""))
        # lane.py leaves a lane that started on a prompt without its pointer prompt: the thread sends it once the
        # lane is idle, and so does this script.
        if line.startswith("BLOCKED"):
            ready = await_idle(name, a.minutes)
            if ready:
                run(["herdr", "agent", "prompt", name, f"Read {lb.as_posix()} and follow it."])
            report(f"lane-ready:{lane}", ready)
    bodies = wait_mail(f"{build}/thread", [f"{build}-{l}" for l in lanes], a.minutes, want=len(lanes))
    committed = {l: (git(wt, "log", "-1", "--format=%s")[1] == "smoke") for l, (wt, _) in lanes.items()}
    report("lanes", len(bodies) == len(lanes) and all(committed.values()), f"mail={len(bodies)} committed={committed}")
    report("lane-guard", any("from: " + f"{build}/cl" in b.lower() and "guard refused" in b for b in bodies)
           and not (checkout / "smoke-lane-guard.txt").exists(),
           f"file_written={(checkout / 'smoke-lane-guard.txt').exists()}")

    wt, _ = lanes["cl"]
    # The relative spelling is taken from the worktree's own parent, so it never crosses drives on Windows.
    spellings = {"native": (str(wt), None), "slashes": (wt.as_posix(), None), "relative": (wt.name, wt.parent)}
    refused = {k: script("finish_lane", path, root / "archive-early", cwd=cwd)[0] == 1
               for k, (path, cwd) in spellings.items()}
    report("finish-running", all(refused.values()), f"refused={refused}")

    for lane, (wt, pane) in lanes.items():
        run(["herdr", "pane", "close", pane])
    deadline = time.time() + 60
    while time.time() < deadline and any((g.get("name") or "").startswith(f"{build}-") for g in agents()):
        time.sleep(2)
    finished = {l: script("finish_lane", wt, root / f"archive-{l}")[0] == 0 and not wt.exists()
                for l, (wt, _) in lanes.items()}
    report("finish-closed", all(finished.values()), f"retired={finished}")

    code, line, err = run(["python3", THREAD, "rotate", build, "--force"], timeout=300)
    report("rotate", line.startswith(("ROTATED", "BLOCKED")) and any((g.get("name") or "") == build for g in agents()),
           line or err)

    hook_costs(coord, checkout, a.runs)

    code, line, err = run(["python3", THREAD, "close", build, "--force"], timeout=300)
    report("close", line.startswith("CLOSED"), line or err)


def cleanup(root, build, checkout):
    for g in agents():
        if (g.get("name") or "") == build or (g.get("name") or "").startswith(f"{build}-"):
            run(["herdr", "pane", "close", g["pane_id"]])
    if any((g.get("name") or "").startswith(build) for g in agents()) or Path(root, f"smoke-repo-orch-{build}").exists():
        run(["python3", THREAD, "close", build, "--force"], timeout=300)
    left_agents = [(g.get("name") or "") for g in agents() if (g.get("name") or "").startswith(build)]
    _, worktrees, _ = git(checkout, "worktree", "list", "--porcelain") if checkout.exists() else (0, "", "")
    _, branches, _ = git(checkout, "branch", "--list", f"orchestration/{build}", "lane/*") if checkout.exists() \
        else (0, "", "")
    registry = Path(os.environ["ORCHESTRATION_HOME"], "threads.tsv")
    rows = [r for r in registry.read_text(encoding="utf-8").splitlines()[1:] if r.startswith(build + "\t")] \
        if registry.is_file() else []
    clean = not left_agents and worktrees.count("worktree ") <= 1 and not branches.strip() and not rows
    report("cleanup", clean, f"agents={left_agents} worktrees={worktrees.count('worktree ')} "
                             f"branches={branches.split()} rows={len(rows)}")


def main(argv):
    p = argparse.ArgumentParser(prog="smoke.py")
    p.add_argument("--claude-model", default="opus")
    p.add_argument("--codex-model", default="gpt-6.1-sol")
    p.add_argument("--runs", type=int, default=20)
    p.add_argument("--minutes", type=int, default=20)
    p.add_argument("--skip-codex", action="store_true")
    a = p.parse_args(argv)
    if not preflight():
        return 1
    root = Path(tempfile.mkdtemp(prefix="orch-smoke-")).resolve()
    build = "smk" + secrets.token_hex(2)
    home = root / "orch"
    os.environ["ORCHESTRATION_HOME"] = str(home)
    print(f"SMOKE setup build={build} root={root.as_posix()}", flush=True)
    try:
        smoke(a, root, build, home)
    except KeyboardInterrupt:
        report("interrupted", False)
    finally:
        try:
            cleanup(root, build, root / "smoke-repo")
        finally:
            remove(root)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
