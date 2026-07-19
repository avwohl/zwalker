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
    # === The integration suite: self-contained ZIL games (source in this repo)
    # that zorkie compiles today and zwalker drives to a real win. These are the
    # green regression that proves zorkie output runs and wins inside zwalker.
    # The suite's pass/fail is the harness exit code. ===
    "microquest": {
        "zil": REPO / "games" / "zil" / "microquest.zil",
        "walkthrough": REPO / "walkthroughs" / "microquest_zorkie_win.txt",
        "version": 3,
        "reference": None,  # no ZILF/official golden; zorkie is the only build
        "seeds": 1,
    },
    "mazekey": {
        "zil": REPO / "games" / "zil" / "mazekey.zil",
        "walkthrough": REPO / "walkthroughs" / "mazekey_zorkie_win.txt",
        "version": 3,
        "reference": None,
        "seeds": 1,
    },
    "reactor": {
        "zil": REPO / "games" / "zil" / "reactor.zil",
        "walkthrough": REPO / "walkthroughs" / "reactor_zorkie_win.txt",
        "version": 3,
        "reference": None,
        "seeds": 1,
    },
    "minizork": {
        # THE MILESTONE: the first real Infocom game zorkie compiles to a full
        # verified win (350/350, Stone Barrow) in zwalker. Once zorkie honored
        # PROPDEF defaults (the <PROPDEF SIZE 5> the official ZILCH build also
        # applies), the source build became LOCKSTEP-IDENTICAL to the published
        # minizork.z3 -- so it now wins the OFFICIAL released-binary route
        # directly. (The old minizork_zorkie_350.txt was tuned to the pre-fix
        # SIZE=0 build and only reaches 305 on the correct build / official.)
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "minizork-1987" / "mini.zil",
        "walkthrough": REPO / "walkthroughs" / "minizork_verified_350.txt",
        "version": 3,
        "reference": REPO / "games" / "zcode" / "minizork.z3",
        "seeds": 1,
    },
    "zork1": {
        # THE FULL ZORK I (renovated Release-0 source), 350/350 to Master
        # Adventurer. The published Release-119 route was re-derived for this
        # build's RNG stream by scripts/solve_zork1_zorkie_adaptive.py (seed 3;
        # combat repeats, heal-waits, and the river-buoy drift baked in).
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "zork1" / "zork1.zil",
        "walkthrough": REPO / "walkthroughs" / "zork1_zorkie_350.txt",
        "version": 3,
        "reference": None,  # official Release 119 is a different build
        "seeds": 3,
    },
    "zork3": {
        # The OFFICIAL verified route replays clean on the zorkie build --
        # lockstep-identical (rooms AND scores) to the Release-25 binary over
        # all 216 commands to the Treasury of Zork.
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "zork3" / "zork3.zil",
        "walkthrough": REPO / "walkthroughs" / "zork3_verified_7.txt",
        "version": 3,
        "reference": REPO / "games" / "zcode" / "zork_iii.z3",
        "seeds": 1,
    },
    "starcross": {
        # The OFFICIAL verified route replays clean on the zorkie build --
        # lockstep-identical to the Release-18 binary over all 240 commands,
        # 400/400 in the Control Bubble.
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "starcross" / "starcross.zil",
        "walkthrough": REPO / "walkthroughs" / "starcross_verified_400.txt",
        "version": 3,
        "reference": REPO / "games" / "zcode" / "starcross.z3",
        "seeds": 1,
    },
    "zork2": {
        # ZORK II from source: route re-derived for this build's RNG stream.
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "zork2" / "zork2.zil",
        "walkthrough": REPO / "walkthroughs" / "zork2_zorkie_400.txt",
        "version": 3, "reference": None, "seeds": 2,
    },
    "deadline": {
        # The official verified route replays as-is on the zorkie build.
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "deadline" / "deadline.zil",
        "walkthrough": REPO / "walkthroughs" / "deadline_verified_win.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "deadline.z3", "seeds": 1,
    },
    "suspended": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "suspended" / "suspended.zil",
        "walkthrough": REPO / "walkthroughs" / "suspended_verified_win.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "suspended.z3", "seeds": 1,
    },
    "infidel": {
        # Lockstep-identical to the official Release-22 binary over all 306 cmds.
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "infidel" / "infidel.zil",
        "walkthrough": REPO / "walkthroughs" / "infidel_verified_400.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "infidel.z3", "seeds": 1,
    },
    "witness": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "witness" / "witness.zil",
        "walkthrough": REPO / "walkthroughs" / "witness_verified_win.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "witness.z3", "seeds": 1,
    },
    "cutthroats": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "cutthroats" / "cutthroats.zil",
        "walkthrough": REPO / "walkthroughs" / "cutthroats_zorkie_250.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "cutthroats.z3", "seeds": 1,
    },
    "sorcerer": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "sorcerer" / "sorcerer.zil",
        "walkthrough": REPO / "walkthroughs" / "sorcerer_verified_400.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "sorcerer.z3", "seeds": 2,
    },
    "enchanter": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "enchanter" / "enchanter.zil",
        "walkthrough": REPO / "walkthroughs" / "enchanter_verified_400.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "enchanter.z3", "seeds": 1,
    },
    "hitchhikersguide": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "hitchhikersguide" / "s4.zil",
        "walkthrough": REPO / "walkthroughs" / "hhgg_verified_400.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "hhgg.z3", "seeds": 1,
    },
    "suspect": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "suspect" / "suspect.zil",
        "walkthrough": REPO / "walkthroughs" / "suspect_zorkie_win.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "suspect.z3", "seeds": 1,
    },
    # Unblocked once zorkie's size peephole (Z/K folds) + abbreviation-corpus fix
    # brought the source build under the V3 cap; the OFFICIAL verified route then
    # replays clean to the 200/200 win (no RNG re-derivation needed).
    "ballyhoo": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "ballyhoo" / "m4.zil",
        "walkthrough": REPO / "walkthroughs" / "ballyhoo_verified_200.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "ballyhoo.z3", "seeds": 1,
    },
    # Won after a round-6 lockstep pass fixed the tipped-room state machine
    # (THINGS pseudo tables, FSET/FCLEAR void ops, reversed syntax lines) and an
    # 8-bit vocab-placeholder overflow (index 256 -> 0 aliased 'hole' to 'all',
    # blocking 'put peg in hole'). Lockstep-clean vs the official binary over all
    # 394 commands; the OFFICIAL route replays to the 150/150 win.
    "hollywoodhijinx": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "hollywoodhijinx" / "hijinx.zil",
        "walkthrough": REPO / "walkthroughs" / "hollywood_zorkie_150.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "hollywood.z3", "seeds": 1,
    },
    # Fits since round-5; the round-5 build already PLAYS the official route to the
    # true "finished the story of Wishbringer! Your score is 100 points out of 100"
    # ending. Wishbringer is a V3 time-game (status line = clock, not score) and a
    # zorkie build's score global sits at a different variable than the official
    # binary's, so get_score() reads the clock; the win is verified by the endgame
    # WIN_TEXT via the WIN_TEXT_SUFFICIENT directive (see scripts/replay_solve.py).
    "wishbringer": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "wishbringer" / "wishbringer.zil",
        "walkthrough": REPO / "walkthroughs" / "wishbringer_zorkie_100.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "wishbringer.z3", "seeds": 1,
    },
    # Won in round-7 on the reduced base: the wip 8-fix set (PREP-SYNONYM, reversed
    # SYNTAX lines, TELL 'atom, CEXIT-gate globals, %,CONST props, DO variable-limit
    # loops, direction-synonym adjectives, funny-global SETG) plus three more general
    # fixes (VOC part-of-speech accumulation, pseudo-noun dict value byte, DO-loop
    # LONG exit-branch off-by-2). OFFICIAL route, lockstep-clean over all 422 cmds.
    "spellbreaker": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "spellbreaker" / "z6.zil",
        "walkthrough": REPO / "walkthroughs" / "spellbreaker_verified_600.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "spellbreaker.z3", "seeds": 1,
    },
    # Won in round-7: PROPDEF defaults populated (Thermos CAPACITY) + JE
    # nested-comparand evaluation. OFFICIAL route, lockstep-clean end-to-end.
    "stationfall": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "stationfall" / "s6.zil",
        "walkthrough": REPO / "walkthroughs" / "stationfall_verified_80.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "stationfall.z3", "seeds": 1,
    },
    # Won in round-7: branch-context multi-operand EQUAL? evaluation (+2 more
    # general codegen fixes). OFFICIAL route, lockstep-clean end-to-end.
    "plunderedhearts": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "plunderedhearts" / "plundered.zil",
        "walkthrough": REPO / "walkthroughs" / "plundered_verified_25.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "plundered.z3", "seeds": 1,
    },
    # Won in round-8: ZIL backslash-escape normalization at the Dictionary
    # boundary (mars.zil's escaped THINGS words created a phantom dict entry
    # whose late insertion shifted 43 objects' SYNONYM word addresses by one
    # slot -- 'take stool' resolved to 'stone'). OFFICIAL route, lockstep-clean;
    # LGOP self-randomizes its score, so the WIN_TEXT ending is the signal.
    "leathergoddesses": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "leathergoddesses" / "x1.zil",
        "walkthrough": REPO / "walkthroughs" / "lgop_verified_win.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "lgop.z3", "seeds": 1,
    },
    # Won in round-8: fit under the cap via the CELF abbreviation selector +
    # peephole/AUX-local/VTBL levers, then the MDL macro machinery fixes
    # (P?/PE/MULTIFROB expansion -- 135 routines had compiled to garbage),
    # ZILCH-builtin exit constants, MAP-DIRECTIONS branch widening, and
    # variadic-arithmetic operand evaluation. OFFICIAL route.
    "lurkinghorror": {
        "zil": ZORKIE / "tests" / "test-games" / "infocom-zil" / "lurkinghorror" / "h1.zil",
        "walkthrough": REPO / "walkthroughs" / "lurking_verified_100.txt",
        "version": 3, "reference": REPO / "games" / "zcode" / "lurking.z3", "seeds": 1,
    },
    # === Frontier target (informational; NOT counted in the suite pass/fail). ===
    # A real Infocom-library game via the ZILF stdlib. Parses fully and is now
    # past the old LIBRARY-MESSAGE macro blocker; current compile error is the
    # stdlib's ISAVE (a V5+ opcode) reached in this V3 build.
    # Tracks progress toward compiling ZILF-library games. See docs/ZORKIE_TESTING.md.
    "cloak": {
        "zil": ZORKIE / "tests" / "test-pairs" / "cloak.zil",
        "walkthrough": REPO / "walkthroughs" / "cloak_zilf_win.txt",
        "version": 3,
        "reference": ZORKIE / "tests" / "test-pairs" / "cloak.z3",  # ZILF 0.8 golden
        "seeds": 1,
        "frontier": True,
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

    suite_zorkie = []    # (name, zorkie_row) for suite games (counted)
    frontier_zorkie = []  # (name, zorkie_row) for frontier games (informational)
    for name in names:
        rows = test_game(name, GAMES[name], workdir)
        zrow = next((r for r in rows if r["label"] == "zorkie"), None)
        if GAMES[name].get("frontier"):
            frontier_zorkie.append((name, zrow))
        else:
            suite_zorkie.append((name, zrow))

    won = sum(1 for _, r in suite_zorkie if r and r["pass"])
    print(f"\nzorkie L2 suite: {won}/{len(suite_zorkie)} games play-and-win"
          + (f"  ({', '.join(n for n, _ in suite_zorkie)})" if suite_zorkie else ""))
    if frontier_zorkie:
        for n, r in frontier_zorkie:
            state = "PASS" if (r and r["pass"]) else "not yet"
            print(f"frontier (not counted): {n} -> {state}")

    if not a.keep:
        for p in workdir.glob("*"):
            p.unlink()
        workdir.rmdir()
    else:
        print(f"artifacts kept in {workdir}")
    # exit 0 iff every suite game's zorkie build reached L2 (frontier excluded)
    return 0 if won == len(suite_zorkie) and suite_zorkie else 1


if __name__ == "__main__":
    sys.exit(main())
