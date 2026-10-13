"""Sleep until a UTC time, then print one line. Run it with the Bash tool's run_in_background so its exit
wakes the thread; a foreground wait leaves messages and hand-backs unread until it ends.
  wake_at.py <UTC time YYYY-MM-DDTHH:MMZ | +<N>m | +<N>h> [<label>]
Prints: WAKE <label> <UTC now> (armed for <UTC target>)
"""
import time

import lib


def main(argv):
    if not 1 <= len(argv) <= 2:
        raise lib.Fail("usage: wake_at.py <UTC time | +<N>m | +<N>h> [label]")
    target = lib.to_epoch(argv[0])
    time.sleep(max(0, target - time.time()))
    label = argv[1] if len(argv) == 2 and argv[1] else "timer"
    print(f"WAKE {label} {lib.utc_now()} (armed for {lib.fmt_utc(target)})")
    return 0


if __name__ == "__main__":
    lib.entry(main)
