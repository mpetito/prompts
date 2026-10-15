"""Active time per local day and repository, read from Claude Code transcripts and Codex rollouts.

  scan_sessions.py --from YYYY-MM-DD [--to YYYY-MM-DD]

Prints one line per (local day, repository) with active time in the range, sorted by day then repository:

  <local date> <repo key> <hours> <sessions> <sources> <intervals>
  2026-10-13 github.com/acme/shop 3.25 2 claude,codex 09:02-10:40,13:15-14:50

- local date and intervals are in this machine's time zone; an interval that crosses midnight is split
  between the two days, and the second day's part starts at 00:00.
- repo key is the origin remote as lowercase host/path (no scheme, user, port or .git; an Azure DevOps
  remote of any form as dev.azure.com/<org>/<project>/_git/<repo>), taken from, in order: the Codex
  rollout's own record of it, git on the session's working directory, a pull-request link anywhere in the
  session (its subagents included), else `unmapped:<working directory>` (a removed worktree with no PR
  link ends here).
- hours is the union of every session's active intervals for that day and repository, rounded up to the
  next ROUND_TO_HOURS. Parallel sessions and a resumed session's repeated records count once.
- sessions counts the distinct session ids (a subagent counts with its parent); sources is claude, codex
  or claude,codex.

A session is active between two of its records at most IDLE_GAP apart, counting its subagents' and resumed
files' records as its own; a longer gap is not counted. Every timestamped record counts, typed by a person or
not. Sessions whose working directory is under a temporary directory (eval and harness runs) are left out.
Claude's transcript retention (`cleanupPeriodDays`, 30 days by default) bounds the range: days whose
transcripts are gone print nothing. These are skipped and counted on stderr: lines that are not a JSON object;
records whose session id, working directory, pull-request link or recorded remote is not a string without NUL,
or whose link or remote is not a parseable URL; a Codex session_meta whose payload or payload.git is not an
object; timestamps that are not ISO 8601 with a time zone, or fall in year 1 or 9999. Reads only; sends
nothing. --to defaults to --from; exit 1 on a usage error.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import MAXYEAR, MINYEAR, date, datetime, time, timedelta, timezone
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

IDLE_GAP = timedelta(minutes=15)
ROUND_TO_HOURS = 0.25
TEMP_ROOTS = tuple(p for p in (
    tempfile.gettempdir(), *(os.environ.get(v) for v in ("TEMP", "TMP", "TMPDIR", "CLAUDE_CODE_TMPDIR")),
    Path.home() / "AppData" / "Local" / "Temp", "/tmp") if p)


CLAUDE_FILES = ("*/*.jsonl", "*/*/subagents/*.jsonl")  # under a Claude projects folder
CODEX_FILES = ("*/*/*/*.jsonl",)  # under Codex's sessions folder: YYYY/MM/DD of the start date


TAIL_BYTES = 65536


def last_written(path):
    """When the file was last written, as a POSIX time: the later of its modification time and the newest
    record timestamp in its last TAIL_BYTES. A Codex rollout resumed days later keeps appending to the file
    in its start date's folder, and on Windows its modification time can stay at the start (seen on 40 of
    233 rollouts), so neither the folder date nor the modification time alone will do. A tail with no
    readable timestamp (a last record longer than TAIL_BYTES) reads as written now, so the file is read."""
    with open(path, "rb") as f:
        f.seek(max(0, f.seek(0, os.SEEK_END) - TAIL_BYTES))
        tail = f.read()
    stamps = []
    for t in re.findall(rb'"timestamp":\s*"([^"]+)"', tail):
        try:
            stamps.append(datetime.fromisoformat(t.decode()).timestamp())
        except ValueError:
            pass
    return max([path.stat().st_mtime, *stamps]) if stamps else math.inf


def recent_files(root, patterns, first):
    """Files under root matching patterns, written to on or after the day before first, in path order (a
    day of slack for records written out of order)."""
    cutoff = datetime.combine(first - timedelta(days=1), time()).timestamp()
    files = (f for pattern in patterns for f in root.glob(pattern))
    return sorted(f for f in files if last_written(f) >= cutoff)


def records(path, bad):
    """The file's JSON objects in file order; a line that is not one adds one to bad[path]."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    r = None
                if isinstance(r, dict):
                    yield r
                else:
                    bad[path] += 1


def text(*values):
    """True when every value is absent (None) or a string without NUL, so a reader can pass it on as a
    session id, path or remote: os.path and subprocess raise on a NUL, the rest on another type."""
    return all(v is None or isinstance(v, str) and "\0" not in v for v in values)


def repo_key(url):
    """One key per repository for every form of its remote (https, ssh URL or scp-style ssh) and for a
    pull-request link to it: lowercase host/path, as the module docstring describes. None for an Azure
    DevOps ssh path without org, project and repository, so the session falls through to the next source."""
    url = re.sub(r"/(?:pull|pullrequest)/\d+/?$", "", url.strip())
    if m := re.fullmatch(r"[^@/:]+@([^:/]+):(.+)", url):
        host, path = m.groups()
    else:
        parts = urlsplit(url)
        host, path = parts.hostname or "", parts.path
    host, path = host.lower(), path.strip("/").removesuffix(".git").lower()
    # Azure DevOps ssh paths are v3/<org>/<project>/<repo>; visualstudio.com names the org in the host.
    if host in ("ssh.dev.azure.com", "vs-ssh.visualstudio.com"):
        parts = path.removeprefix("v3/").split("/", 2)
        return f"dev.azure.com/{parts[0]}/{parts[1]}/_git/{parts[2]}" if len(parts) == 3 else None
    if host.endswith(".visualstudio.com"):
        return f"dev.azure.com/{host.split('.')[0]}/{path.removeprefix('defaultcollection/')}"
    return f"{'github.com' if host == 'ssh.github.com' else host}/{path}"


@cache
def git_remote(cwd):
    """The origin remote's key for a working directory, or None when it is gone or has no origin."""
    r = subprocess.run(["git", "-C", cwd, "config", "--get", "remote.origin.url"], capture_output=True, text=True)
    return repo_key(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


@cache
def canon(path):
    """path as the temp check compares it: os.path.realpath (symlinks, and 8.3 short names such as RUNNER~1 on
    Windows) then os.path.normcase, so two spellings of one directory compare equal."""
    return os.path.normcase(os.path.realpath(path))


def is_temp(cwd, temp_roots):
    """True when cwd is a temp root or below one, both sides in canon form."""
    path = canon(cwd)
    return any(path == root or path.startswith(root.rstrip(os.sep) + os.sep) for root in map(canon, temp_roots))


def claude_events(path, bad, pr_links):
    """(session id, cwd, timestamp, None) per timestamped record; the cwd carries forward to records that
    lack one. A pr-link record's repo key goes into pr_links under its session id."""
    events, cwd = [], None
    for r in records(path, bad):
        if not text(r.get("sessionId"), r.get("cwd"), r.get("prUrl")):
            bad[path] += 1
            continue
        sid = r.get("sessionId", path.stem)
        if r.get("type") == "pr-link" and r.get("prUrl"):
            try:
                pr_links[sid] = repo_key(r["prUrl"])
            except ValueError:  # urlsplit rejects it, e.g. an unclosed IPv6 host
                bad[path] += 1
                continue
        cwd = r.get("cwd") or cwd
        if "timestamp" in r and cwd:
            events.append((sid, cwd, r["timestamp"], None))
    return events


def codex_events(path, bad, pr_links):
    """(session id, cwd, timestamp, remote key) per timestamped record of a rollout; pr_links is unused."""
    events, sid, cwd, remote = [], path.stem, None, None
    for r in records(path, bad):
        if r.get("type") == "session_meta":
            # A session_meta with any bad field is dropped whole: its id, cwd and remote describe one session.
            meta = r.get("payload") or {}
            git = (meta.get("git") or {}) if isinstance(meta, dict) else None
            if not (isinstance(git, dict) and text(meta.get("id"), meta.get("cwd"), git.get("repository_url"))):
                bad[path] += 1
                continue
            try:
                key = repo_key(url) if (url := git.get("repository_url")) else remote
            except ValueError:  # urlsplit rejects it, e.g. an unclosed IPv6 host
                bad[path] += 1
                continue
            sid, cwd, remote = meta.get("id", sid), meta.get("cwd", cwd), key
        if "timestamp" in r and cwd:
            events.append((sid, cwd, r["timestamp"], remote))
    return events


def active_intervals(stamps):
    """Merge timestamps into [start, end] runs whose neighbours are at most IDLE_GAP apart; a lone record
    makes a zero-length run, which split_by_day drops."""
    runs = []
    for t in sorted(stamps):
        if runs and t - runs[-1][1] <= IDLE_GAP:
            runs[-1][1] = t
        else:
            runs.append([t, t])
    return runs


def local_midnight(day, tz):
    """Start of a local day as an aware datetime; tz None is this machine's zone, with its DST rules."""
    return datetime.combine(day, time()).astimezone() if tz is None else datetime.combine(day, time(), tz)


def split_by_day(start, end, tz):
    """(local date, start, end) pieces of an interval, cut at each local midnight."""
    start, end = start.astimezone(tz), end.astimezone(tz)
    while start < end:
        cut = min(end, local_midnight(start.date() + timedelta(days=1), tz))
        yield start.date(), start, cut
        start = cut.astimezone(tz)


def merged(pieces):
    """(start, end) pieces with overlapping or touching ones joined, in order."""
    out = []
    for s, e in sorted(pieces):
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        else:
            out.append([s, e])
    return out


def scan(claude_root, codex_root, first, last, tz=None, temp_roots=TEMP_ROOTS):
    """Rows (date, repo key, hours, sessions, sources, intervals) for first..last inclusive, as the module
    docstring defines them. Missing roots read as empty."""
    bad, pr_links = defaultdict(int), {}
    # Every file is read before any repository is resolved: a session's PR link may sit in another file.
    events = [(source, path, *event)
              for source, read, root, patterns in (("claude", claude_events, claude_root, CLAUDE_FILES),
                                                   ("codex", codex_events, codex_root, CODEX_FILES))
              for path in (recent_files(root, patterns, first) if root.is_dir() else [])
              for event in read(path, bad, pr_links)]
    # A session's subagent and resumed files share one stream: a subagent's records keep its parent active.
    streams = defaultdict(list)  # (source, session, repo) -> timestamps
    for source, path, sid, cwd, ts, recorded in events:
        if is_temp(cwd, temp_roots):
            continue
        # A zoneless time cannot be ordered against the others. A local day lies within a day of UTC, so a
        # year strictly inside MINYEAR..MAXYEAR keeps the local conversion and the next midnight in range.
        try:
            stamp = datetime.fromisoformat(ts)
            ok = stamp.tzinfo is not None and MINYEAR < stamp.astimezone(timezone.utc).year < MAXYEAR
        except (TypeError, ValueError, OverflowError):
            ok = False
        if not ok:
            bad[path] += 1
            continue
        # The remote a Codex rollout recorded comes first; a session's PR link is the last resort after git.
        repo = recorded or git_remote(cwd) or pr_links.get(sid) or f"unmapped:{cwd}"
        streams[source, sid, repo].append(stamp)
    days = defaultdict(lambda: ([], set(), set()))
    for (source, sid, repo), stamps in streams.items():
        for start, end in active_intervals(stamps):
            for day, s, e in split_by_day(start, end, tz):
                if first <= day <= last:
                    pieces, sids, srcs = days[day, repo]
                    pieces.append((s, e))
                    sids.add(sid)
                    srcs.add(source)
    for path, n in bad.items():
        print(f"skipped {n} malformed line(s) or timestamp(s) in {path}", file=sys.stderr)
    rows = []
    for (day, repo), (pieces, sids, srcs) in sorted(days.items()):
        spans = merged(pieces)
        active = sum((e - s for s, e in spans), timedelta()).total_seconds() / 3600
        hours = math.ceil(active / ROUND_TO_HOURS) * ROUND_TO_HOURS
        rows.append((day, repo, hours, len(sids), sorted(srcs), spans))
    return rows


def clock(t, day):
    return "24:00" if t.date() > day else f"{t:%H:%M}"


def format_row(row):
    day, repo, hours, sessions, srcs, spans = row
    intervals = ",".join(f"{clock(s, day)}-{clock(e, day)}" for s, e in spans)
    return f"{day} {repo} {hours:.2f} {sessions} {','.join(srcs)} {intervals}"


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from", dest="first", type=date.fromisoformat, required=True)
    parser.add_argument("--to", dest="last", type=date.fromisoformat)
    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 1
    claude = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "projects"
    codex = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"
    for row in scan(claude, codex, args.first, args.last or args.first):
        print(format_row(row))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
