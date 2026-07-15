#!/usr/bin/env python3
"""L2 compiler-correctness test: compile a game's ZIL source with zorkie (and ZILF
if available), then replay a *source-matched* walkthrough through the zwalker
interpreter and check that it reaches a verified win.

This is the top rung of the strength ladder in docs/ZORKIE_TESTING.md:

    L0  structural  -- hexdiff the compiled .z against a ZILF/official golden
                       (zorkie's own tests/test-games/compare-zcode.sh); not here.
    L1  boots       -- the compiled .z loads and runs GO in zwalker without crashing.
    L2  plays+wins  -- replay a source-matched walkthrough to a verified win.   <== this script

Why a *source-matched* walkthrough and not one of the 50 verified solves in
walkthroughs/: those target the RELEASED Infocom binaries, which are a different
build than compile(historicalsource ZIL) -- different release/serial, object
numbers, scoring globals, RNG stream, and ending text. See docs/ZORKIE_TESTING.md.
So each entry here pairs a ZIL source with a walkthrough recorded against a build
OF THAT SOURCE (its win is asserted by a `#% WIN_TEXT` header directive).

The reference build (a ZILF or official golden .z, when we have one) is tested too,
so a red result tells you *which* half failed: if the reference wins but zorkie
does not, zorkie miscompiled the source; if neither wins, the source itself isn't
winnable as preserved (a provenance problem, not a compiler bug).

Usage:
    python3 scripts/test_zorkie_game.py            # all registered games
    python3 scripts/test_zorkie_game.py cloak      # one game
    python3 scripts/test_zorkie_game.py --keep      # keep compiled artifacts
"""
import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path
from shutil import which
from tempfile import mkdtemp

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
ZORKIE = Path.home() / "src" / "zorkie"

from zwalker.walker import GameWalker  # noqa: E402

# Reuse replay_solve's verifier (solve/run_once) without a package import.
_spec = importlib.util.spec_from_file_location("replay_solve", REPO / "scripts" / "replay_solve.py")
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)


# Registry of source-build test targets. `zil` is the ZIL source; `walkthrough` is
# recorded against a build of that source; `reference` (optional) is a known-good
# ZILF/official golden .z used as the behavioral oracle.
GAMES = {
    "cloak": {
        "zil": ZORKIE / "tests" / "test-pairs" / "cloak.zil",
        "walkthrough": REPO / "walkthroughs" / "cloak_zilf_win.txt",
        "version": 3,
        "reference": ZORKIE / "tests" / "test-pairs" / "cloak.z3",  # ZILF 0.8 golden
        "seeds": 1,
    },
    # Next targets (see docs/ZORKIE_TESTING.md): advent (zorkie games/advent_source/
    # advent.zil; re-fetch the 404-stub golden first), then comp-scale games, then
    # the full Infocom titles as zorkie's routine codegen coverage closes.
}


def compile_zorkie(zil: Path, out: Path, version: int):
    """Compile ZIL -> .z with zorkie. Returns (ok, detail)."""
    if not zil.exists():
        return False, f"ZIL source not found: {zil}"
    if not (ZORKIE / "zorkie").exists():
        return False, f"zorkie not found at {ZORKIE}"
    try:
        r = subprocess.run(
            [sys.executable, "zorkie", str(zil), "-o", str(out), "-v", str(version)],
            capture_output=True, text=True, timeout=180, cwd=str(ZORKIE),
            env={**os.environ, "PYTHONPATH": str(ZORKIE)},
        )
    except Exception as e:  # noqa: BLE001
        return False, f"zorkie crashed: {e}"
    if r.returncode == 0 and out.exists() and out.stat().st_size > 64:
        return True, f"{out.stat().st_size} bytes"
    msg = (r.stderr or r.stdout or "no diagnostics").strip()
    return False, msg.splitlines()[-1] if msg else "compile produced no file"


def compile_zilf(zil: Path, out: Path, version: int):
    """Compile ZIL -> .zap -> .z with a locally installed ZILF+ZAPF, if present.
    Returns (ok, detail) or (None, reason) when ZILF is unavailable."""
    zilf, zapf = which("zilf"), which("zapf")
    if not zilf:
        return None, "zilf not on PATH (using committed reference golden instead)"
    zap = out.with_suffix(".zap")
    try:
        c = subprocess.run([zilf, str(zil), str(zap)], capture_output=True, text=True, timeout=180)
        if c.returncode != 0:
            return False, (c.stderr or c.stdout or "zilf failed").strip().splitlines()[-1]
        if zapf:
            a = subprocess.run([zapf, str(zap)], capture_output=True, text=True, timeout=180)
            if a.returncode != 0:
                return False, (a.stderr or a.stdout or "zapf failed").strip().splitlines()[-1]
    except Exception as e:  # noqa: BLE001
        return False, f"zilf/zapf crashed: {e}"
    return (True, f"{out.stat().st_size} bytes") if out.exists() else (False, "no .z produced")


def boots(zpath: Path):
    """L1: does the compiled story file load and run GO without crashing?"""
    try:
        w = GameWalker(open(zpath, "rb").read())
        w.start()
        return True, None
    except Exception as e:  # noqa: BLE001
        return False, str(e)


def play(zpath: Path, walkthrough: Path, seeds: int):
    """L2: replay the source-matched walkthrough; returns replay_solve's best dict."""
    return rs.solve(str(zpath), str(walkthrough), seeds)


def test_build(label: str, zpath: Path, walkthrough: Path, seeds: int):
    ok, err = boots(zpath)
    if not ok:
        return {"label": label, "level": "L1", "pass": False, "detail": f"boot crash: {err}"}
    best = play(zpath, walkthrough, seeds)
    detail = f"score {best['score']}/{best['max_score']} died={best['died']} seed={best['seed']} ({best['num_commands'] if 'num_commands' in best else len(best['commands'])} cmds)"
    return {"label": label, "level": "L2", "pass": best["won"], "detail": detail}


def test_game(name: str, spec: dict, workdir: Path):
    print(f"\n=== {name} ===")
    print(f"  source:      {spec['zil']}")
    print(f"  walkthrough: {spec['walkthrough'].relative_to(REPO)}")
    rows = []

    # zorkie (the unit under test)
    zk = workdir / f"{name}_zorkie.z{spec['version']}"
    ok, detail = compile_zorkie(spec["zil"], zk, spec["version"])
    if ok:
        rows.append(test_build("zorkie", zk, spec["walkthrough"], spec["seeds"]))
    else:
        rows.append({"label": "zorkie", "level": "compile", "pass": False, "detail": f"COMPILE FAILED: {detail}"})

    # ZILF fresh build if the toolchain is installed, else fall back to the golden
    zf = workdir / f"{name}_zilf.z{spec['version']}"
    ok, detail = compile_zilf(spec["zil"], zf, spec["version"])
    if ok:
        rows.append(test_build("zilf(fresh)", zf, spec["walkthrough"], spec["seeds"]))
    elif ok is False:
        rows.append({"label": "zilf(fresh)", "level": "compile", "pass": False, "detail": f"COMPILE FAILED: {detail}"})
    # ok is None -> zilf absent; the committed reference below covers the oracle.

    ref = spec.get("reference")
    if ref and Path(ref).exists():
        rows.append(test_build("reference (ZILF golden)", Path(ref), spec["walkthrough"], spec["seeds"]))

    for r in rows:
        verdict = "PASS" if r["pass"] else ("COMPILE-FAIL" if r["level"] == "compile" else "FAIL")
        print(f"    {r['label']:24} [{r['level']:7}] {verdict:12} {r['detail']}")

    zwins = next((r for r in rows if r["label"] == "zorkie"), None)
    refwins = next((r for r in rows if r["label"].startswith("reference")), None)
    if zwins and zwins["pass"]:
        print("  => zorkie build PLAYS AND WINS (L2 pass).")
    elif refwins and refwins["pass"]:
        print("  => reference wins but zorkie does not: the source is winnable, so this is a "
              "zorkie compiler bug. Diff the compiled .z against the golden "
              "(zorkie tests/test-games/compare-zcode.sh) and the score_timeline step where it desyncs.")
    else:
        print("  => neither build wins: check the source's own preservation (a provenance "
              "issue) before blaming zorkie.")
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("games", nargs="*", help="game names to test (default: all registered)")
    ap.add_argument("--keep", action="store_true", help="keep compiled artifacts (print their dir)")
    a = ap.parse_args()

    names = a.games or list(GAMES)
    unknown = [n for n in names if n not in GAMES]
    if unknown:
        print(f"unknown game(s): {', '.join(unknown)}; registered: {', '.join(GAMES)}")
        return 2

    workdir = Path(mkdtemp(prefix="zorkie_l2_"))
    print(f"Zorkie L2 test (compile ZIL -> replay source-matched walkthrough -> verify win)")
    print(f"zorkie: {ZORKIE}   artifacts: {workdir}")

    all_rows = []
    for name in names:
        all_rows += test_game(name, GAMES[name], workdir)

    zorkie_l2 = [r for r in all_rows if r["label"] == "zorkie"]
    won = sum(1 for r in zorkie_l2 if r["pass"])
    print(f"\nzorkie L2 summary: {won}/{len(zorkie_l2)} games play-and-win")
    if not a.keep:
        for p in workdir.glob("*"):
            p.unlink()
        workdir.rmdir()
    else:
        print(f"artifacts kept in {workdir}")
    # exit 0 only if every requested game's zorkie build reached L2
    return 0 if won == len(zorkie_l2) else 1


if __name__ == "__main__":
    sys.exit(main())
