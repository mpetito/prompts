"""Read both members' answers for one round and print the council's next step, one line:
  COUNCIL consensus|exchange|no-consensus|incomplete ...
  tally.py <answer file> <answer file> --exchange <k>     (k = 0 for the blind round, then 1, 2, ...)
Consensus is mechanical: the same disposition and the same action text in each member's own (last) block,
whether reached blind or through agree, so the coordinator never judges whether two differently worded
actions match. It still has to verify the decisive citations. A usage error exits 1; every verdict exits 0.
"""
import os
import re
import sys

# Exchange rounds after the blind round. Debate studies find nearly all of the gain in the first exchange and
# flat or falling accuracy after it, with conformity growing; the second round confirms a revised position.
MAX_EXCHANGE_ROUNDS = 2
DISPOSITIONS = {"defect", "improvement", "false-positive", "unnecessary-complexity", "already-addressed", "deferred",
                "needs-human"}
USAGE = "usage: tally.py <answer file> <answer file> --exchange <k>"


def field(key, text):
    """The last value of key in text, whitespace collapsed: an answer may quote the template before its own block.
    Lines end at \n alone, as grep's do: splitlines() would also split at \f, \x85, \u2028 and others."""
    values = [line.split(":", 1)[1] for line in text.split("\n") if re.match(rf"\s*{key}:", line, re.IGNORECASE)]
    return " ".join(values[-1].split()) if values else ""


def incomplete(f, text, k):
    """The reason f's answer can't be tallied in round k, or None when it can."""
    if not text:
        return "no-answer"
    if not field("action", text):
        return "no-action"
    if not field("decisive", text):
        return "no-decisive-citation"
    disposition, stance = field("disposition", text).lower(), field("stance", text).lower()
    if disposition not in DISPOSITIONS:
        return f"disposition '{disposition}'"
    if k == 0 and stance != "initial":
        return f"stance '{stance}' in the blind round"
    if k > 0 and stance not in ("agree", "revise", "hold"):
        return f"stance '{stance}'"
    return None


def verdict(a, b, k):
    """The COUNCIL line for answer files a and b after exchange round k."""
    texts = {}
    for f in (a, b):
        texts[f] = open(f, encoding="utf-8", errors="replace").read() if os.path.isfile(f) else ""
        if reason := incomplete(f, texts[f], k):
            return f"COUNCIL incomplete member={f} reason={reason}"
    ta, tb = texts[a], texts[b]
    da, db = field("disposition", ta).lower(), field("disposition", tb).lower()
    if da == db and field("action", ta) == field("action", tb):
        return f"COUNCIL consensus after-exchange={k} disposition={da}; verify the decisive citations before reporting it"
    if k >= 1 and field("stance", ta).lower() == field("stance", tb).lower() == "hold":
        return f"COUNCIL no-consensus reason=both-hold after-exchange={k}; report each final position and its crux"
    if k >= MAX_EXCHANGE_ROUNDS:
        return (f"COUNCIL no-consensus reason=round-cap after-exchange={k} of {MAX_EXCHANGE_ROUNDS}; "
                "report each final position and its crux")
    return f"COUNCIL exchange next={k + 1} of {MAX_EXCHANGE_ROUNDS}; send each member the other's answer, unattributed"


def main(argv):
    if len(argv) != 4 or argv[2] != "--exchange":
        print(USAGE, file=sys.stderr)
        return 1
    if not re.fullmatch(r"[0-9]+", argv[3]):
        print(f"--exchange takes a round number; {USAGE}", file=sys.stderr)
        return 1
    print(verdict(argv[0], argv[1], int(argv[3])))
    return 0


if __name__ == "__main__":
    for stream in (sys.stdin, sys.stdout):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
