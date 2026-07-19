#!/usr/bin/env python3
"""Sweep the full Infocom-ZIL corpus through zorkie: compile -> boot -> replay
the verified walkthrough -> report a status table.

This is the measurement tool for the "every source compiles and wins" goal:
one row per game, worst-first exit code. Unlike scripts/test_zorkie_game.py
(the counted regression suite), this sweeps EVERYTHING, including games that
do not compile yet, and replays each game's OFFICIAL verified walkthrough
(which doubles as the source-matched route whenever the source build's RNG
stream happens to line up, as it did for zork3 and starcross).

Usage:
    python3 scripts/sweep_zorkie_corpus.py            # all 26
    python3 scripts/sweep_zorkie_corpus.py zork2 amfv # subset
    python3 scripts/sweep_zorkie_corpus.py --jobs 2   # parallel compiles
"""
import argparse
import concurrent.futures
import importlib.util
import json
import os
import subprocess
import sys
from glob import glob
from pathlib import Path
from tempfile import mkdtemp

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
ZORKIE = Path.home() / "src" / "zorkie"
SRC = ZORKIE / "tests" / "test-games" / "infocom-zil"

from zwalker.walker import GameWalker  # noqa: E402

_spec = importlib.util.spec_from_file_location("replay_solve", REPO / "scripts" / "replay_solve.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)

# game -> (source subdir, entry file, zversion, walkthrough, solutions-glob)
CORPUS = {
    "minizork":        ("minizork-1987", "mini.zil", 3, "minizork_zorkie_350.txt", "minizork_zorkie*"),
    "zork1":           ("zork1", "zork1.zil", 3, "zork1_zorkie_350.txt", "zork1_zorkie*"),
    "zork3":           ("zork3", "zork3.zil", 3, "zork3_verified_7.txt", "zork3_verified*"),
    "starcross":       ("starcross", "starcross.zil", 3, "starcross_verified_400.txt", "starcross_verified*"),
    "zork2":           ("zork2", "zork2.zil", 3, "zork2_zorkie_400.txt", "zork2_zorkie*"),
    "deadline":        ("deadline", "deadline.zil", 3, "deadline_verified_win.txt", "deadline_verified*"),
    "suspect":         ("suspect", "suspect.zil", 3, "suspect_verified_win.txt", "suspect_verified*"),
    "witness":         ("witness", "witness.zil", 3, "witness_verified_win.txt", "witness_verified*"),
    "sorcerer":        ("sorcerer", "sorcerer.zil", 3, "sorcerer_verified_400.txt", "sorcerer_verified*"),
    "planetfall":      ("planetfall", "planetfall.zil", 3, "planetfall_verified_80.txt", "planetfall_verified*"),
    "suspended":       ("suspended", "suspended.zil", 3, "suspended_verified_win.txt", "suspended_verified*"),
    "hollywoodhijinx": ("hollywoodhijinx", "hijinx.zil", 3, "hollywood_verified_150.txt", "hollywood_verified*"),
    "cutthroats":      ("cutthroats", "cutthroats.zil", 3, "cutthroats_zorkie_250.txt", "cutthroats_verified*"),
    "infidel":         ("infidel", "infidel.zil", 3, "infidel_verified_400.txt", "infidel_verified*"),
    "enchanter":       ("enchanter", "enchanter.zil", 3, "enchanter_verified_400.txt", "enchanter_verified*"),
    "lurkinghorror":   ("lurkinghorror", "h1.zil", 3, "lurking_verified_100.txt", "lurking_verified*"),
    "spellbreaker":    ("spellbreaker", "z6.zil", 3, "spellbreaker_verified_600.txt", "spellbreaker_verified*"),
    "ballyhoo":        ("ballyhoo", "m4.zil", 3, "ballyhoo_verified_200.txt", "ballyhoo_verified*"),
    "moonmist":        ("moonmist", "moonmist.zil", 3, "moonmist_verified_win.txt", "moonmist_verified*"),
    "wishbringer":     ("wishbringer", "wishbringer.zil", 3, "wishbringer_verified_100.txt", "wishbringer_verified*"),
    "leathergoddesses": ("leathergoddesses", "x1.zil", 3, "lgop_verified_win.txt", "lgop_verified*"),
    "plunderedhearts": ("plunderedhearts", "plundered.zil", 3, "plundered_verified_25.txt", "plundered_verified*"),
    "stationfall":     ("stationfall", "s6.zil", 3, "stationfall_verified_80.txt", "stationfall_verified*"),
    "hitchhikersguide": ("hitchhikersguide", "s4.zil", 3, "hhgg_verified_400.txt", "hhgg_verified*"),
    "trinity":         ("trinity", "trinity.zil", 4, "trinity_verified_100.txt", "trinity_verified*"),
    "amfv":            ("amfv", "s5.zil", 4, "amfv_verified_win.txt", "amfv_verified*"),
}


def entry_for(game):
    sub, entry, ver, wt, sol = CORPUS[game]
    path = SRC / sub / entry
    if not path.exists():
        cands = sorted((SRC / sub).glob("*.zil"))
        path = cands[0] if cands else path
    return path, ver


def verified_seed(game):
    sol = CORPUS[game][4]
    for f in sorted(glob(str(REPO / "solutions" / (sol + ".json")))):
        try:
            return json.load(open(f)).get("rng_seed") or 1
        except Exception:  # noqa: BLE001
            pass
    return 1


def compile_game(game, outdir):
    path, ver = entry_for(game)
    out = Path(outdir) / f"{game}.z{ver}"
    try:
        r = subprocess.run(
            [sys.executable, "zorkie", str(path), "-o", str(out), "-v", str(ver)],
            capture_output=True, text=True, timeout=900, cwd=str(ZORKIE),
            env={**os.environ, "PYTHONPATH": str(ZORKIE)},
        )
    except subprocess.TimeoutExpired:
        return None, "compile TIMEOUT"
    if r.returncode == 0 and out.exists() and out.stat().st_size > 64:
        return out, f"{out.stat().st_size} bytes"
    msg = (r.stderr or r.stdout or "no diagnostics").strip().splitlines()
    err = next((l for l in reversed(msg) if 'rror' in l), msg[-1] if msg else "?")
    return None, err[:110]


def run_game(game, zpath):
    wt = REPO / "walkthroughs" / CORPUS[game][3]
    seed = verified_seed(game)
    try:
        w = GameWalker(open(zpath, "rb").read())
        w.start()
    except Exception as e:  # noqa: BLE001
        return f"BOOT-CRASH {type(e).__name__}: {e}"[:110]
    if not wt.exists():
        return "boots (no walkthrough on file)"
    try:
        best = rs.solve(str(zpath), str(wt), seed)
    except Exception as e:  # noqa: BLE001
        return f"REPLAY-CRASH {type(e).__name__}: {e}"[:110]
    tag = "WIN" if best["won"] else "no-win"
    return (f"{tag} score {best['score']}/{best['max_score']} died={best['died']} "
            f"seed={best['seed']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games", nargs="*")
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    names = a.games or list(CORPUS)
    outdir = mkdtemp(prefix="zorkie_sweep_")

    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as ex:
        futs = {ex.submit(compile_game, g, outdir): g for g in names}
        for fut in concurrent.futures.as_completed(futs):
            g = futs[fut]
            z, detail = fut.result()
            results[g] = (z, detail)
            print(f"[compile] {g}: {detail}", flush=True)

    wins = []
    for g in names:
        z, detail = results[g]
        if z is None:
            print(f"{g}\tCOMPILE-FAIL\t{detail}", flush=True)
            continue
        status = run_game(g, z)
        print(f"{g}\tcompiled {detail}\t{status}", flush=True)
        if status.startswith("WIN"):
            wins.append(g)

    print(f"\nSWEEP: {len(wins)}/{len(names)} games WIN: {', '.join(wins)}")
    if not a.keep:
        for p in Path(outdir).glob("*"):
            p.unlink()
        Path(outdir).rmdir()
    return 0 if len(wins) == len(names) else 1


if __name__ == "__main__":
    sys.exit(main())
