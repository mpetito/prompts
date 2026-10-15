"""scan_sessions.py over synthetic Claude transcripts and Codex rollouts, one test per format trap.

Every fixture is written to a temporary folder; times are in a fixed UTC-4 zone so the local-day cases do not
depend on the machine running them. Repositories that git must resolve are real `git init` folders.
"""
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
import unittest.mock
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scan_sessions.py"
spec = importlib.util.spec_from_file_location("scan_sessions", SCRIPT)
scan_sessions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan_sessions)

TZ = timezone(timedelta(hours=-4))
DAY = date(2026, 10, 13)
SHOP = "github.com/acme/shop"


def utc(local):
    """ISO UTC timestamp, as both tools write them, for a local 'YYYY-MM-DD HH:MM' in TZ."""
    t = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
    return t.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def minutes(start, count, step=5, day="2026-10-13"):
    """Local 'HH:MM' strings every step minutes from start, count of them."""
    t = datetime.strptime(f"{day} {start}", "%Y-%m-%d %H:%M")
    return [(t + timedelta(minutes=step * n)).strftime("%Y-%m-%d %H:%M") for n in range(count)]


class ScanTest(unittest.TestCase):
    def setUp(self):
        scan_sessions.git_remote.cache_clear()
        scan_sessions.canon.cache_clear()
        folder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)  # git leaves read-only objects on Windows
        self.addCleanup(folder.cleanup)
        self.tmp = Path(folder.name)
        self.claude = self.tmp / "claude" / "projects"
        self.codex = self.tmp / "codex" / "sessions"
        self.temp_root = self.tmp / "scratch"
        self.shop = self.repo("shop", "https://github.com/acme/shop.git")

    def repo(self, name, remote):
        path = self.tmp / name
        path.mkdir()
        subprocess.run(["git", "init", "-q", str(path)], check=True)
        subprocess.run(["git", "-C", str(path), "remote", "add", "origin", remote], check=True)
        return path

    def claude_session(self, sid, cwd, stamps, extra=(), project="proj", subagent=None):
        """A transcript whose records are timestamped at the local times in stamps."""
        lines = [json.dumps({"type": "user", "sessionId": sid, "cwd": str(cwd), "timestamp": utc(s)})
                 for s in stamps]
        lines += [json.dumps(r) if isinstance(r, dict) else r for r in extra]
        folder = self.claude / project
        path = folder / sid / "subagents" / f"agent-{subagent}.jsonl" if subagent else folder / f"{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def codex_session(self, sid, cwd, stamps, folder_day, remote=None, payload=None):
        meta = {"id": sid, "cwd": str(cwd), "git": {"repository_url": remote} if remote else {"branch": "main"}}
        # Codex writes the timestamp first in each record.
        lines = [json.dumps({"timestamp": utc(stamps[0]), "type": "session_meta", "payload": meta})]
        lines += [json.dumps({"timestamp": utc(s), "type": "response_item", "payload": payload or {}})
                  for s in stamps[1:]]
        path = self.codex / folder_day.replace("-", "/") / f"rollout-{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def backdate(self, path, local):
        """Set a file's modification time to a local 'YYYY-MM-DD HH:MM' in TZ."""
        when = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=TZ).timestamp()
        os.utime(path, (when, when))

    def scan(self, first=DAY, last=DAY):
        return [scan_sessions.format_row(r) for r in
                scan_sessions.scan(self.claude, self.codex, first, last, TZ, (self.temp_root,))]

    def test_one_session_hours_rounded_up_to_a_quarter(self):
        self.claude_session("s1", self.shop, minutes("09:00", 8))  # 35 minutes: up to 0.75, not to the nearest 0.5
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.75 1 claude 09:00-09:35"])

    def test_two_overlapping_sessions_are_a_union_not_a_sum(self):
        self.claude_session("s1", self.shop, minutes("09:00", 13))  # 09:00-10:00
        self.claude_session("s2", self.shop, minutes("09:30", 13))  # 09:30-10:30
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.50 2 claude 09:00-10:30"])

    def test_idle_gap_over_fifteen_minutes_is_not_counted(self):
        self.claude_session("s1", self.shop, minutes("09:00", 7) + minutes("10:00", 7))  # 30 + 30 minutes
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.00 1 claude 09:00-09:30,10:00-10:30"])

    def test_gap_of_exactly_fifteen_minutes_is_counted(self):
        self.claude_session("s1", self.shop, ["2026-10-13 09:00", "2026-10-13 09:15"])
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.25 1 claude 09:00-09:15"])

    def test_session_crossing_local_midnight_splits_between_days(self):
        stamps = minutes("23:00", 13, day="2026-10-12")  # 23:00 .. 00:00
        stamps += minutes("00:05", 12, day="2026-10-13")  # 00:05 .. 01:00
        self.claude_session("s1", self.shop, stamps)
        self.assertEqual(self.scan(date(2026, 10, 12), DAY), [
            f"2026-10-12 {SHOP} 1.00 1 claude 23:00-24:00",
            f"2026-10-13 {SHOP} 1.00 1 claude 00:00-01:00",
        ])

    def test_codex_folder_is_local_date_and_records_are_utc(self):
        # Started 22:00 local on the 12th, which is 02:00Z on the 13th: the folder says the 12th.
        stamps = minutes("22:00", 13, day="2026-10-12") + minutes("23:05", 12, day="2026-10-12")
        self.codex_session("c1", self.shop, stamps, "2026-10-12", remote="git@github.com:acme/shop.git")
        self.assertEqual(self.scan(date(2026, 10, 12), date(2026, 10, 12)),
                         [f"2026-10-12 {SHOP} 2.00 1 codex 22:00-24:00"])
        self.assertEqual(self.scan(), [])

    def test_codex_session_begun_the_day_before_the_range_is_read(self):
        stamps = minutes("23:30", 7, day="2026-10-12") + minutes("00:05", 6)
        self.codex_session("c1", self.shop, stamps, "2026-10-12", remote="https://github.com/acme/shop")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 codex 00:00-00:30"])

    def test_codex_and_claude_on_one_repository_share_a_line(self):
        self.claude_session("s1", self.shop, minutes("09:00", 13))
        self.codex_session("c1", self.shop, minutes("09:30", 13), "2026-10-13", remote="https://github.com/acme/shop.git")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.50 2 claude,codex 09:00-10:30"])

    def test_codex_without_a_recorded_remote_falls_back_to_git(self):
        self.codex_session("c1", self.shop, minutes("09:00", 7), "2026-10-13")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 codex 09:00-09:30"])

    def test_codex_recorded_remote_beats_git_on_the_folder(self):
        # The folder now holds another clone; the rollout recorded what it worked on at the time.
        self.codex_session("c1", self.shop, minutes("09:00", 7), "2026-10-13", remote="https://github.com/acme/api.git")
        self.assertEqual(self.scan(), ["2026-10-13 github.com/acme/api 0.50 1 codex 09:00-09:30"])

    def test_codex_recorded_remote_maps_a_removed_worktree(self):
        gone = self.tmp / "gone-worktree"
        self.codex_session("c1", gone, minutes("09:00", 7), "2026-10-13", remote="https://github.com/acme/shop.git")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 codex 09:00-09:30"])

    def test_removed_worktree_falls_back_to_the_pr_link_record(self):
        gone = self.tmp / "gone-worktree"
        link = {"type": "pr-link", "sessionId": "s1", "prNumber": 7, "prRepository": "acme/shop",
                "prUrl": "https://github.com/acme/shop/pull/7", "timestamp": utc("2026-10-13 09:35")}
        self.claude_session("s1", gone, minutes("09:00", 7), extra=[link])
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.75 1 claude 09:00-09:35"])

    def test_removed_worktree_without_a_pr_link_is_unmapped(self):
        gone = self.tmp / "gone-worktree"
        self.claude_session("s1", gone, minutes("09:00", 7))
        self.assertEqual(self.scan(), [f"2026-10-13 unmapped:{gone} 0.50 1 claude 09:00-09:30"])

    def test_git_beats_the_pr_link_when_the_folder_exists(self):
        link = {"type": "pr-link", "sessionId": "s1", "prRepository": "acme/other",
                "prUrl": "https://github.com/acme/other/pull/1", "timestamp": utc("2026-10-13 09:10")}
        self.claude_session("s1", self.shop, minutes("09:00", 7), extra=[link])
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 claude 09:00-09:30"])

    def test_resumed_session_repeating_records_counts_them_once(self):
        first = minutes("09:00", 13)
        self.claude_session("s1", self.shop, first)
        self.claude_session("s2", self.shop, first + minutes("10:05", 6))  # resume copies s1's records, then goes on
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.50 2 claude 09:00-10:30"])

    def test_records_without_a_timestamp_and_out_of_order_lines(self):
        stamps = minutes("09:00", 7)
        extra = [{"type": "mode", "sessionId": "s1", "mode": "normal"}, {"type": "last-prompt", "sessionId": "s1"}]
        self.claude_session("s1", self.shop, list(reversed(stamps)), extra=extra)
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 claude 09:00-09:30"])

    def test_malformed_line_is_skipped_and_reported(self):
        self.claude_session("s1", self.shop, minutes("09:00", 7), extra=['{"type": "user", "timest'])
        err = io.StringIO()
        with unittest.mock.patch("sys.stderr", err):
            rows = self.scan()
        self.assertEqual(rows, [f"2026-10-13 {SHOP} 0.50 1 claude 09:00-09:30"])
        self.assertIn("skipped 1 malformed", err.getvalue())

    def test_temp_dir_session_is_excluded(self):
        work = self.temp_root / "claude-ws-1"
        work.mkdir(parents=True)
        self.claude_session("eval", work, minutes("09:00", 13))
        self.codex_session("c-eval", work, minutes("09:00", 13), "2026-10-13")
        self.claude_session("s1", self.shop, minutes("11:00", 7))
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 claude 11:00-11:30"])

    def test_temp_root_spelled_differently_from_the_session_cwd_is_excluded(self):
        # On Windows TEMP names the runner's profile by its 8.3 short name (RUNNER~1) while the cwd resolves to the
        # long one; a symlinked temp root makes the same split on any OS. On Windows the link needs Developer Mode
        # or elevation.
        real = self.tmp / "real-temp"
        (real / "claude-ws-1").mkdir(parents=True)
        self.temp_root.symlink_to(real, target_is_directory=True)
        self.claude_session("eval", real / "claude-ws-1", minutes("09:00", 13))
        self.codex_session("c-eval", self.temp_root / "claude-ws-1", minutes("09:00", 13), "2026-10-13")
        self.claude_session("s1", self.shop, minutes("11:00", 7))
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 claude 11:00-11:30"])

    def test_session_in_the_temp_root_itself_is_excluded(self):
        self.temp_root.mkdir()
        self.claude_session("eval", self.temp_root, minutes("09:00", 13))
        self.claude_session("s1", self.shop, minutes("11:00", 7))
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 claude 11:00-11:30"])

    def test_sibling_whose_name_extends_the_temp_root_is_counted(self):
        sibling = self.repo(self.temp_root.name + "-2", "https://github.com/acme/site.git")
        self.claude_session("s1", sibling, minutes("09:00", 13))
        self.assertEqual(self.scan(), ["2026-10-13 github.com/acme/site 1.00 1 claude 09:00-10:00"])

    def test_subagent_counts_with_its_parent_session(self):
        self.claude_session("s1", self.shop, minutes("09:00", 7))
        self.claude_session("s1", self.shop, minutes("09:20", 9), subagent="a1")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.00 1 claude 09:00-10:00"])

    def test_cwd_carries_forward_to_records_that_lack_one(self):
        other = self.repo("site", "https://dev.azure.com/acme/web/_git/site")
        path = self.claude_session("s1", self.shop, minutes("09:00", 3))
        later = [{"type": "user", "sessionId": "s1", "cwd": str(other), "timestamp": utc("2026-10-13 10:00")},
                 {"type": "assistant", "sessionId": "s1", "timestamp": utc("2026-10-13 10:10")}]
        with open(path, "a", encoding="utf-8") as f:
            f.writelines(json.dumps(r) + "\n" for r in later)
        self.assertEqual(self.scan(), [
            "2026-10-13 dev.azure.com/acme/web/_git/site 0.25 1 claude 10:00-10:10",
            f"2026-10-13 {SHOP} 0.25 1 claude 09:00-09:10",
        ])

    def test_days_outside_the_range_print_nothing(self):
        self.claude_session("s1", self.shop, minutes("09:00", 7, day="2026-10-14"))
        self.assertEqual(self.scan(), [])


    def test_session_inside_another_counts_once(self):
        self.claude_session("s1", self.shop, minutes("09:00", 13))  # 09:00-10:00
        self.claude_session("s2", self.shop, minutes("09:20", 5))  # 09:20-09:40, inside s1
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.00 2 claude 09:00-10:00"])

    def test_session_read_later_that_starts_earlier(self):
        # Files are read in path order, so z's earlier start reaches the union last.
        self.claude_session("a", self.shop, minutes("10:00", 13))  # 10:00-11:00
        self.claude_session("b", self.shop, minutes("10:30", 13))  # 10:30-11:30
        self.claude_session("z", self.shop, minutes("09:00", 4))  # 09:00-09:15
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 1.75 3 claude 09:00-09:15,10:00-11:30"])

    def test_back_to_back_sessions_show_one_interval(self):
        self.claude_session("s1", self.shop, minutes("09:00", 13))  # 09:00-10:00
        self.claude_session("s2", self.shop, minutes("10:00", 13))  # 10:00-11:00
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 2.00 2 claude 09:00-11:00"])

    def test_codex_rollout_resumed_days_after_its_folder_date(self):
        stamps = minutes("16:00", 4, day="2026-10-10") + minutes("09:00", 7)  # resumed three days later
        self.codex_session("c1", self.shop, stamps, "2026-10-10", remote="https://github.com/acme/shop.git")
        # Windows can leave a rollout's modification time at its start while records are appended.
        started = datetime(2026, 10, 10, 16, 0, tzinfo=TZ).timestamp()
        for rollout in self.codex.rglob("*.jsonl"):
            os.utime(rollout, (started, started))
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 codex 09:00-09:30"])

    def test_file_last_written_before_the_range_is_skipped(self):
        self.claude_session("s1", self.shop, minutes("09:00", 7, day="2026-10-10"))
        with unittest.mock.patch.object(scan_sessions, "records", side_effect=AssertionError("read")):
            old = datetime(2026, 10, 10, 9, 30, tzinfo=TZ).timestamp()
            for transcript in self.claude.rglob("*.jsonl"):
                os.utime(transcript, (old, old))
            self.assertEqual(self.scan(), [])

    def test_subagent_of_a_removed_worktree_maps_by_its_session_pr_link(self):
        gone = self.tmp / "gone-worktree"
        link = {"type": "pr-link", "sessionId": "s1", "prNumber": 7, "prRepository": "acme/shop",
                "prUrl": "https://github.com/acme/shop/pull/7", "timestamp": utc("2026-10-13 09:05")}
        self.claude_session("s1", gone, minutes("09:00", 2), extra=[link])
        self.claude_session("s1", gone, minutes("10:00", 7), subagent="a1")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.75 1 claude 09:00-09:05,10:00-10:30"])

    def test_azure_devops_pr_link_maps_a_removed_worktree(self):
        gone = self.tmp / "gone-worktree"
        link = {"type": "pr-link", "sessionId": "s1", "prNumber": 12, "prRepository": "acme/web/site",
                "prUrl": "https://dev.azure.com/Acme/Web/_git/Site/pullrequest/12", "timestamp": utc("2026-10-13 09:05")}
        self.claude_session("s1", gone, minutes("09:00", 7), extra=[link])
        self.assertEqual(self.scan(), ["2026-10-13 dev.azure.com/acme/web/_git/site 0.50 1 claude 09:00-09:30"])

    def test_two_remote_forms_of_one_repository_share_a_line(self):
        other_clone = self.repo("shop-ssh", "git@GitHub.com:Acme/Shop.git")
        self.claude_session("s1", self.shop, minutes("09:00", 7))
        self.claude_session("s2", other_clone, minutes("09:15", 7))
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.75 2 claude 09:00-09:45"])


    def test_last_record_longer_than_the_tail_is_still_read(self):
        big = {"text": "x" * (scan_sessions.TAIL_BYTES + 1000)}
        path = self.codex_session("c1", self.shop, minutes("16:00", 2, day="2026-10-10") + minutes("09:00", 7),
                                  "2026-10-10", remote="https://github.com/acme/shop.git", payload=big)
        self.backdate(path, "2026-10-10 16:00")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 codex 09:00-09:30"])

    def test_non_iso_timestamp_in_the_tail_is_skipped(self):
        path = self.claude_session("s1", self.shop, minutes("09:00", 7),
                                   extra=[{"type": "note", "sessionId": "s1", "timestamp": "yesterday"}])
        self.backdate(path, "2026-10-13 09:30")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.50 1 claude 09:00-09:30"])

    def test_subagent_records_keep_the_parent_session_active(self):
        self.claude_session("s1", self.shop, ["2026-10-13 09:00", "2026-10-13 09:20", "2026-10-13 09:40"])
        self.claude_session("s1", self.shop, ["2026-10-13 09:10", "2026-10-13 09:30"], subagent="a1")
        self.assertEqual(self.scan(), [f"2026-10-13 {SHOP} 0.75 1 claude 09:00-09:40"])

    def test_short_azure_devops_ssh_remote_is_unmapped(self):
        odd = self.repo("odd", "git@ssh.dev.azure.com:v3/acme/web")
        self.claude_session("s1", odd, minutes("09:00", 7))
        self.assertEqual(self.scan(), [f"2026-10-13 unmapped:{odd} 0.50 1 claude 09:00-09:30"])


class RepoKeyTest(unittest.TestCase):
    def test_github_forms_share_one_key(self):
        for url in ("https://github.com/acme/shop.git", "git@github.com:acme/shop.git",
                    "https://user@GitHub.com/acme/shop/", "ssh://git@github.com/acme/shop.git",
                    "git@GitHub.com:Acme/Shop.git", "ssh://git@ssh.github.com:443/acme/shop.git",
                    "https://github.com/acme/shop/pull/7"):
            self.assertEqual(scan_sessions.repo_key(url), SHOP, url)

    def test_azure_devops_forms_share_one_key(self):
        site = "dev.azure.com/acme/web/_git/site"
        for url in ("https://dev.azure.com/acme/web/_git/site", "https://dana@dev.azure.com/Acme/Web/_git/Site",
                    "git@ssh.dev.azure.com:v3/acme/web/site", "ssh://git@ssh.dev.azure.com:v3/acme/web/site",
                    "https://acme.visualstudio.com/web/_git/site",
                    "https://acme.visualstudio.com/DefaultCollection/web/_git/site",
                    "acme@vs-ssh.visualstudio.com:v3/acme/web/site",
                    "https://dev.azure.com/acme/web/_git/site/pullrequest/12"):
            self.assertEqual(scan_sessions.repo_key(url), site, url)


if __name__ == "__main__":
    unittest.main()
