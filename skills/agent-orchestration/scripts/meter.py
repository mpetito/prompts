"""Read the Codex weekly meter from the newest session log and say what the budget rule requires.
  meter.py [--switch <percent>]
Prints one line: "codex=<used>% resets=<UTC> verdict=<normal|rotate|stop|unknown>", then the rule for
rotate and stop. The Claude meter is not on disk; read it from the harness's usage view and apply the same rule.
"""
import json
import os
import re
from pathlib import Path

import lib

# Rotate from 70%, keeping the last 30% for finishing the lanes already running. In a past week-long build
# (docs/skill-audit/2026-10-09) the coordinators' context re-reads were the largest token cost, so a fresh
# thread lowers the burn rate without lowering any model.
SWITCH = "70"
USAGE = "usage: meter.py [--switch <percent>]"


def newest_log(root):
    """The newest *.jsonl under root, by modification time, that holds a meter reading; None when there is none."""
    try:
        logs = sorted(Path(root).rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    except OSError:
        return None
    for log in logs:
        try:
            if '"used_percent"' in log.read_text(encoding="utf-8", errors="replace"):
                return log
        except OSError:
            continue
    return None


def primary_meter(log):
    """(used percent, reset epoch) as text from the log's last meter line; "" for a field that is missing."""
    line = [ln for ln in log.read_text(encoding="utf-8", errors="replace").split("\n") if '"used_percent"' in ln][-1]
    try:
        primary = json.loads(line)["payload"]["rate_limits"]["primary"]
        # jq's "//" default: only null and false count as missing, so a reading of 0 stays.
        return tuple("" if primary.get(k) is None or primary[k] is False else str(primary[k])
                     for k in ("used_percent", "resets_at"))
    except (ValueError, LookupError, TypeError, AttributeError):
        return "", ""


def main(argv):
    switch = SWITCH
    while argv:
        if argv[0] != "--switch":
            raise lib.Fail(USAGE)
        if len(argv) < 2:
            raise lib.Fail(f"option {argv[0]} needs a value")
        switch, argv = argv[1], argv[2:]
    if not re.fullmatch(r"[0-9]+", switch):
        raise lib.Fail(f"--switch takes a whole percent, got {switch}")
    root = os.environ.get("CODEX_SESSIONS") or str(Path.home() / ".codex" / "sessions")
    log = newest_log(root)
    if not log:
        print(f"codex=unknown resets=unknown verdict=unknown (no session log with a meter under {root})")
        return 0
    used, resets = primary_meter(log)
    if not (re.fullmatch(r"[0-9]+(\.[0-9]+)?", used) and re.fullmatch(r"[0-9]+", resets)):
        print(f"codex=unknown resets=unknown verdict=unknown (no primary meter in {log.name})")
        return 0
    reset_iso = lib.fmt_utc(int(resets))
    pct = int(used.split(".")[0])
    verdict = "stop" if pct >= 100 else "rotate" if pct >= int(switch) else "normal"
    print(f"codex={used}% resets={reset_iso} verdict={verdict} (read {lib.utc_now()} from {log.name})")
    if verdict == "rotate":
        print(f"rule: ask MAIN to rotate this thread (STATUS: working - codex meter at {used}%; ready to rotate); "
              "keep the briefed models and reviewers")
    elif verdict == "stop":
        print(f"rule: write the resume point, log the reset time, arm wake_at.py {reset_iso} in the background, "
              "launch nothing metered")
    return 0


if __name__ == "__main__":
    lib.entry(main)
