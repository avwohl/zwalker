#!/usr/bin/env python3
"""Boot / differential smoke-test for a directory of Z-machine story files.

Two independent verdicts per game:

  boot   -- zwalker loads the file, runs to the first input prompt, and
            survives a fixed probe script (look / inventory / examine me /
            north / undo-ish noise). Any interpreter exception = a zwalker
            (or story) defect worth a look. No walkthrough needed.
  diff   -- the same probe replayed under dfrotz (dumb interface, wide
            screen); normalized outputs are compared. A divergence means one
            of the two interpreters is wrong -- at this corpus scale that is
            the cheapest zwalker-bug detector we have (this technique found
            the EXPAND-PRONOUN/gen_voc class in the from-source track).

Games are sandboxed per-process (a hung story can't stall the sweep) and a
JSON report is written for triage. Verdict counts print at the end.

Usage:
  python3 scripts/smoke_corpus.py                          # games/ifarchive
  python3 scripts/smoke_corpus.py --dir games/zcode        # any corpus dir
  python3 scripts/smoke_corpus.py --limit 40 --no-diff     # quick boot-only
"""
import argparse
import concurrent.futures as cf
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# The probe must be IDENTICAL on both interpreters (including the quit tail
# dfrotz needs to exit) or y/n-gated intros desync the streams and flag
# false divergences.
PROBE = ["look", "inventory", "examine me", "north", "wait", "score",
         "quit", "y"]
TIMEOUT = 45          # seconds per game per interpreter


def _zwalker_probe(game: str):
    """Run the probe in-process (called inside a worker subprocess)."""
    sys.path.insert(0, str(REPO))
    from zwalker.walker import GameWalker  # noqa: PLC0415
    out = []
    w = GameWalker(Path(game).read_bytes())
    out.append(w.start() or "")
    w.vm.rng.seed(1)
    for c in PROBE:
        r = w.try_command(c)
        out.append((r.output if r is not None else "") or "")
    return "\n".join(out)


def _worker(game: str) -> dict:
    """Subprocess entry: boot in zwalker, capture output or the exception."""
    try:
        text = _zwalker_probe(game)
        return {"game": Path(game).name, "boot": "ok", "zwalker_out": text}
    except Exception as e:  # noqa: BLE001 - the whole point is catching these
        return {"game": Path(game).name, "boot": f"EXC {type(e).__name__}: {e}"}


def dfrotz_probe(game: Path, dfrotz: str) -> str:
    inp = "\n".join(PROBE) + "\n"
    try:
        r = subprocess.run([dfrotz, "-w", "500", "-h", "999", "-p", str(game)],
                           input=inp, capture_output=True, text=True,
                           timeout=TIMEOUT)
        return r.stdout
    except subprocess.TimeoutExpired:
        return "[DFROTZ TIMEOUT]"


_WS = re.compile(r"\s+")
_PROMPT = re.compile(r"^\s*>\s*", re.M)


def normalize(text: str) -> str:
    """Collapse whitespace/prompts; drop status-line artifacts for diffing."""
    text = _PROMPT.sub("", text)
    text = re.sub(r"Using normal formatting.*?\n", "", text)
    text = re.sub(r"Loading .*?\n", "", text)
    return _WS.sub(" ", text).strip().lower()


def similarity(a: str, b: str) -> float:
    """Cheap token-level containment score (0..1)."""
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(REPO / "games" / "ifarchive"))
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--no-diff", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--report", default=str(REPO / "logs" / "smoke_corpus.json"))
    a = ap.parse_args()

    games = sorted(p for p in Path(a.dir).glob("*.z[358]"))
    if a.limit:
        games = games[: a.limit]
    dfrotz = shutil.which("dfrotz")
    print(f"{len(games)} games from {a.dir}; diff={'off' if a.no_diff or not dfrotz else dfrotz}",
          flush=True)

    t0 = time.time()
    results = []
    # process pool: each game boots in its own interpreter process
    with cf.ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(_worker, str(g)): g for g in games}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            g = futs[fut]
            try:
                rec = fut.result(timeout=TIMEOUT * 2)
            except Exception as e:  # noqa: BLE001 - hang/crash of the worker
                rec = {"game": g.name, "boot": f"WORKER-FAIL {type(e).__name__}"}
            results.append(rec)
            if i % 50 == 0:
                print(f"  [{i}/{len(games)}] {time.time()-t0:.0f}s", flush=True)

    # differential pass (sequential dfrotz; it is fast)
    if not a.no_diff and dfrotz:
        by_name = {r["game"]: r for r in results}
        for g in games:
            rec = by_name[g.name]
            if rec["boot"] != "ok":
                continue
            df = dfrotz_probe(g, dfrotz)
            sim = similarity(normalize(rec.get("zwalker_out", "")), normalize(df))
            rec["diff_sim"] = round(sim, 3)
            if sim < 0.5:
                rec["dfrotz_head"] = normalize(df)[:300]
                rec["zwalker_head"] = normalize(rec.get("zwalker_out", ""))[:300]

    for r in results:
        r.pop("zwalker_out", None)

    Path(a.report).parent.mkdir(parents=True, exist_ok=True)
    Path(a.report).write_text(json.dumps(
        {"probe": PROBE, "count": len(results), "results":
         sorted(results, key=lambda r: r["game"])}, indent=1) + "\n")

    boots = sum(1 for r in results if r["boot"] == "ok")
    excs = [r for r in results if r["boot"] != "ok"]
    sims = [r.get("diff_sim") for r in results if r.get("diff_sim") is not None]
    low = [r for r in results if r.get("diff_sim", 1) < 0.5]
    print(f"\nBOOT: {boots}/{len(results)} ok, {len(excs)} exceptions")
    for r in excs[:10]:
        print(f"  EXC {r['game']}: {r['boot'][:100]}")
    if sims:
        print(f"DIFF: {len(sims)} compared, {len(low)} low-similarity (<0.5)")
        for r in low[:10]:
            print(f"  LOW {r['game']}: sim={r['diff_sim']}")
    print(f"report -> {a.report}  ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
