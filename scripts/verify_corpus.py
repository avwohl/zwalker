#!/usr/bin/env python3
"""Phase 0: two-track corpus scoreboard over corpus_manifest.json.

Reports, per Z-machine version, how many games are:
  - SRC-win     : ZIL/ZILF source compiles and wins in zwalker (the L2 track;
                  authoritative runner is scripts/test_zorkie_game.py).
  - PUB-solved  : a released .z binary replays a walkthrough to won=True here.
  - source-only / binary-only / neither.

With --run-pub it actually replays each PUB binary that has a walkthrough (via
replay_solve) and records the result back into the manifest; otherwise it reports
the manifest's recorded state. This is the measurement tool the roadmap phases
track against; it does not itself compile source (that's test_zorkie_game.py).
"""
import argparse
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "corpus_manifest.json"


def _load_replay_solve():
    spec = importlib.util.spec_from_file_location("rs", REPO / "scripts" / "replay_solve.py")
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    return rs


def run_pub(row, rs):
    """Replay the first PUB walkthrough on the PUB binary; return won bool or None."""
    if not row.get("pub_path") or not row.get("pub_walkthroughs"):
        return None
    z = REPO / row["pub_path"]
    wt = REPO / "walkthroughs" / row["pub_walkthroughs"][0]
    if not z.exists() or not wt.exists():
        return None
    try:
        best = rs.solve(str(z), str(wt), 4)
        return bool(best["won"])
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-pub", action="store_true",
                    help="actually replay PUB binaries that have a walkthrough")
    a = ap.parse_args()

    man = json.loads(MANIFEST.read_text())
    games = man["games"]
    rs = _load_replay_solve() if a.run_pub else None

    if a.run_pub:
        for row in games:
            r = run_pub(row, rs)
            if r is not None:
                row["pub_solved"] = r
        MANIFEST.write_text(json.dumps(man, indent=2) + "\n")

    # scoreboard by version
    board = defaultdict(lambda: dict(src_total=0, src_win=0, pub_total=0, pub_solved=0))
    for row in games:
        sv, pv = row.get("src_version"), row.get("pub_version")
        if row.get("src_dir") or row.get("src_kind"):
            board[sv]["src_total"] += 1
            if row.get("src_win"):
                board[sv]["src_win"] += 1
        if row.get("pub_path"):
            board[pv]["pub_total"] += 1
            if row.get("pub_solved"):
                board[pv]["pub_solved"] += 1

    print(f"corpus: {len(games)} games\n")
    print(f"{'ver':>4} | {'SRC win/total':>14} | {'PUB solved/total':>16}")
    print("-" * 42)
    tot = dict(sw=0, st=0, ps=0, pt=0)
    for v in sorted(k for k in board if isinstance(k, int) and 1 <= k <= 8):
        b = board[v]
        print(f"v{v:>3} | {b['src_win']:>6}/{b['src_total']:<7} | "
              f"{b['pub_solved']:>7}/{b['pub_total']:<8}")
        tot["sw"] += b["src_win"]; tot["st"] += b["src_total"]
        tot["ps"] += b["pub_solved"]; tot["pt"] += b["pub_total"]
    print("-" * 42)
    print(f"{'all':>4} | {tot['sw']:>6}/{tot['st']:<7} | {tot['ps']:>7}/{tot['pt']:<8}")
    if not a.run_pub:
        print("\n(PUB solved counts are from the manifest; run --run-pub to re-measure)")


if __name__ == "__main__":
    main()
