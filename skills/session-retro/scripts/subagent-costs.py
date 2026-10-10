"""Per-subagent turns, tokens and an estimated list-price cost for one or more Claude Code sessions.

usage: subagent-costs.py <session jsonl path>...
Reads <session dir>/subagents/*.jsonl and .meta.json beside each session file. Prices are an estimate
(USD per million tokens: input, output, cache read, cache write) and are printed with the result.
"""
import collections
import glob
import json
import os
import statistics
import sys

PRICE = {"opus": (5, 25, 0.5, 6.25), "sonnet": (3, 15, 0.3, 3.75)}


def family(model):
    return "sonnet" if "sonnet" in (model or "") else "opus"


def cost(row):
    p = PRICE[family(row["model"])]
    return (row["inp"] * p[0] + row["out"] * p[1] + row["cache_r"] * p[2] + row["cache_w"] * p[3]) / 1e6


def read_agent(meta_path):
    meta = json.load(open(meta_path))
    jsonl = meta_path.replace(".meta.json", ".jsonl")
    if not os.path.exists(jsonl):
        return None
    row = dict(turns=0, inp=0, out=0, cache_r=0, cache_w=0, first=None, last=None, tools=0, bash=0, model=None)
    for line in open(jsonl):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        if d.get("type") != "assistant":
            continue
        msg = d.get("message", {})
        usage = msg.get("usage") or {}
        row["turns"] += 1
        row["inp"] += usage.get("input_tokens", 0)
        row["out"] += usage.get("output_tokens", 0)
        row["cache_r"] += usage.get("cache_read_input_tokens", 0)
        row["cache_w"] += usage.get("cache_creation_input_tokens", 0)
        row["model"] = msg.get("model") or row["model"]
        row["first"] = row["first"] or d.get("timestamp")
        row["last"] = d.get("timestamp")
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                row["tools"] += 1
                row["bash"] += block["name"] == "Bash"
    row.update(type=meta.get("agentType"), model_req=meta.get("model"), desc=meta.get("description"))
    return row


def main(paths):
    rows = []
    for path in paths:
        session_dir = path[:-len(".jsonl")]
        for meta_path in glob.glob(os.path.join(session_dir, "subagents", "*.meta.json")):
            row = read_agent(meta_path)
            if row:
                row["sess"] = os.path.basename(session_dir)[:8]
                rows.append(row)
    rows.sort(key=lambda r: r["first"] or "")
    totals = collections.defaultdict(lambda: [0, 0.0, 0, 0])
    for r in rows:
        r["cost"] = cost(r)
        t = totals[(r["sess"], family(r["model"]))]
        t[0] += 1; t[1] += r["cost"]; t[2] += r["turns"]; t[3] += r["out"]
    print("prices (USD/M tokens in, out, cache read, cache write):", PRICE)
    print("session,family,n,est_usd,turns,out_tokens")
    for k, v in sorted(totals.items()):
        print(k, v[0], round(v[1], 1), v[2], v[3])
    print("\nTop 25 by estimated cost:")
    for r in sorted(rows, key=lambda r: -r["cost"])[:25]:
        print(f"{r['sess']} {(r['first'] or '')[:16]} {r['model']} {r['type']} turns={r['turns']} bash={r['bash']} "
              f"out={r['out']} cacheR={r['cache_r'] // 1000}k est=${r['cost']:.1f} :: {r['desc']}")
    if rows:
        turns = sorted(r["turns"] for r in rows)
        print("\nturn distribution: median", statistics.median(turns), "p90", turns[int(len(turns) * .9)], "max", turns[-1])
    json.dump(rows, open("subagent-rows.json", "w"))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
