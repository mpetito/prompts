"""Run the Codex council member once, read-only, on a prompt file, and print one line:
  MEMBER done|failed|timeout|malformed member=codex model=<id> session=<id> ...
  codex_member.py <repo> <prompt file> <answer file> --model <id> [--effort <level>] [--resume <session id>]
                  [--timeout <duration, default 20m>]
Run it with the host's background option so its exit wakes the coordinator. The event stream goes to
<answer file without .md>.jsonl and Codex's stderr to <answer file without .md>.log; pass the printed session to
--resume for the member's next round. A usage error or a refused path exits 1; every MEMBER line exits 0.
On native Windows, Codex runs in its unelevated sandbox, whatever the user's config says.
"""
import os
import re
import shutil
import sys

import run

USAGE = ("usage: codex_member.py <repo> <prompt file> <answer file> --model <id> [--effort <level>] "
         "[--resume <session id>] [--timeout <duration>]")
WINDOWS = os.name == "nt"
# On Windows, --ignore-user-config also drops the user's [windows] sandbox setting, so the mode is set here. The
# elevated sandbox's setup fails on some machines (openai/codex#52488, open); unelevated is Codex's documented
# fallback (https://learn.chatgpt.com/docs/windows/windows-sandbox) and enough for a read-only member.
WINDOWS_SANDBOX = 'windows.sandbox="unelevated"'


def seconds(duration):
    """A timeout(1) duration, a number with an optional s, m, h or d suffix, in seconds; None when it isn't one.
    0 means no limit, as it does for timeout(1)."""
    m = re.fullmatch(r"(\d+(?:\.\d+)?)([smhd]?)", duration)
    return float(m[1]) * {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400}[m[2]] if m else None


def field(key, path):
    """The last value of key in the answer file, trimmed: the answer may quote the template before its own block."""
    if not os.path.isfile(path):
        return ""
    # Lines end at \n alone, as grep's do: splitlines() would also split at \f, \x85, \u2028 and others.
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        lines = f.read().split("\n")
    values = [line.split(":", 1)[1].strip() for line in lines if re.match(rf"\s*{key}:", line, re.IGNORECASE)]
    return values[-1] if values else ""


def codex_args(repo, out, model, effort, resume):
    """codex's arguments for a fresh run in repo, or a resumed one. Read-only on both paths: `codex exec resume` takes
    no --sandbox or --cd, so the sandbox is also a config override and the command runs from inside the repository;
    without both, a resumed member runs under the user's own Codex default. --ignore-user-config skips
    $CODEX_HOME/config.toml (auth still loads), so a member does not depend on the user's servers, plugins or
    defaults. Never --ephemeral: nothing to resume."""
    opts = ["--ignore-user-config", "-c", 'sandbox_mode="read-only"', "--model", model, "--json",
            "--output-last-message", out]
    if WINDOWS:
        opts += ["-c", WINDOWS_SANDBOX]
    if effort:
        opts += ["-c", f'model_reasoning_effort="{effort}"']
    if resume:
        return ["exec", "resume", resume, *opts, "-"]
    return ["exec", "--cd", repo, "--sandbox", "read-only", *opts, "-"]


def refuse(message):
    print(message, file=sys.stderr)
    return 1


def main(argv):
    if len(argv) < 3:
        return refuse(USAGE)
    repo, prompt, out = argv[:3]
    opts = {"--model": "", "--effort": "", "--resume": "", "--timeout": "20m"}
    rest = argv[3:]
    while rest:
        if len(rest) < 2:
            return refuse(f"{rest[0]} needs a value; {USAGE}")
        if rest[0] not in opts:
            return refuse(f"unknown option {rest[0]}; {USAGE}")
        opts[rest[0]] = rest[1]
        rest = rest[2:]
    model, timeout_for = opts["--model"], opts["--timeout"]
    if not model:
        return refuse("--model is required: pick a high-capability model from 'codex debug models'")
    if re.search("opus|sonnet|haiku|fable|claude", model, re.IGNORECASE):
        return refuse(f"{model} is an Anthropic model; the Codex member needs a Codex model ID")
    if seconds(timeout_for) is None:
        return refuse(f"--timeout takes a duration such as 90s, 20m or 1h; {USAGE}")
    if not os.path.isdir(repo):
        return refuse(f"no repository at {repo}")
    if not os.path.isfile(prompt):
        return refuse(f"no prompt at {prompt}")
    if not shutil.which("codex"):
        return refuse("codex is not on PATH")
    # abspath, not realpath, keeps a symlinked answer path as the link itself; it is refused below.
    repo, prompt, out = os.path.realpath(repo), os.path.realpath(prompt), os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    stem = out.removesuffix(".md")
    events, log = stem + ".jsonl", stem + ".log"
    # Only the member's own regular files are removed or written, never a symlink's target or anything else.
    for f in (out, events, log):
        if os.path.islink(f) or (os.path.exists(f) and not os.path.isfile(f)):
            return refuse(f"{f} is a symlink or not a regular file; refusing")
    if os.path.exists(out):
        os.remove(out)  # a stale answer from an earlier run must not survive this one

    code = run.run(["codex", *codex_args(repo, out, model, opts["--effort"], opts["--resume"])], cwd=repo,
                   stdin=prompt, stdout=events, stderr=log, timeout=seconds(timeout_for) or None)

    session = opts["--resume"]
    if not session and os.path.isfile(events):
        with open(events, encoding="utf-8", errors="replace") as f:
            m = re.search(r'"thread_id": *"([^"]*)"', f.read())
        session = m[1] if m else ""
    line = f"member=codex model={model} session={session or 'none'}"
    # A failed or timed-out member leaves no answer file, so tally.py can never count it.
    if code != 0:
        if os.path.exists(out):
            os.remove(out)
        if code == 124:
            print(f"MEMBER timeout {line} after {timeout_for}; log {log}")
        else:
            # A signal's death is -N here; bash reported 128+N.
            print(f"MEMBER failed {line} exit={128 - code if code < 0 else code}; log {log}")
        return 0
    stance, disposition = field("stance", out), field("disposition", out)
    if not stance or not disposition:
        print(f"MEMBER malformed {line} out={out} (no answer block)")
        return 0
    print(f"MEMBER done {line} stance={stance} disposition={disposition} out={out}")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
