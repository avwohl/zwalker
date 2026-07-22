#!/usr/bin/env python3
"""Re-verify every route in walkthroughs/ifarchive/ against its story file.

The trust gate for the wild-corpus solve track: agent-derived routes are only
counted once THIS script replays them to an Inform "*** ... ***" win. Run it
before committing new routes (a route that no longer wins is a regression) and
in CI-style sweeps.

  python3 scripts/verify_ifarchive_wins.py            # all routes, seeds 1-4
  python3 scripts/verify_ifarchive_wins.py --quiet    # summary only

Exit 0 iff every route wins.
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from zwalker.walker import GameWalker  # noqa: E402

ROUTES = REPO / "walkthroughs" / "ifarchive"
GAMES = [REPO / "games" / "ifarchive", REPO / "games" / "zcode"]
# Explicit victory words (always a win). "escape/freedom/home/fin de" are here
# because several games' ONLY victory banner uses them.
WIN_RX = re.compile(r"\*\*\*[^*\n]*(you have won|you won|victor|congratulat"
                    r"|you did it|finis|fin de l|occupant|rightful"
                    r"|freedom|good time|survived|you have escaped"
                    r"|managed to escape|have a good time)[^*\n]*\*\*\*", re.I)
# Explicit LOSS banners -- a "*** ... ***" ending is NOT a win if it matches.
# Beyond death: capture/arrest/imprisonment, failure, time-out, and generic
# "game over". ("captured"/"caught"/"arrested" are failure endings that the
# bare-non-death rule would otherwise miscount -- Tangle's "*** You have been
# captured ***".)
LOSS_RX = re.compile(r"\*\*\*[^*\n]*(die[ds]?|dead|you have failed|failed"
                     r"|you lose|lost|game over|perish|killed|fatal"
                     r"|captured|caught|arrested|imprisoned|trapped forever"
                     r"|out of time|too late|time.s up|defeat|doomed"
                     r"|the end of your|paranoi)[^*\n]*\*\*\*", re.I)
END_RX = re.compile(r"\*\*\*[^*\n]+\*\*\*")


def find_game(stem: str):
    for d in GAMES:
        for p in d.glob(stem + ".z[1-8]"):
            return p
        # zcode/ uses the un-prefixed short name
        short = stem.split("__")[-1]
        for p in d.glob(short + ".z[1-8]"):
            return p
    return None


def replay(game: Path, cmds, win_phrase=None):
    for seed in (1, 2, 3, 4):
        w = GameWalker(game.read_bytes())
        w.start()
        w.vm.rng.seed(seed)
        for c in cmds:
            try:
                out = (w.try_command(c).output or "")
            except Exception:  # noqa: BLE001
                break
            if win_phrase and win_phrase in out:
                return seed
            if LOSS_RX.search(out):
                break            # a losing ending -- not a win, stop this seed
            if WIN_RX.search(out) or END_RX.search(out):
                # a positive victory banner, or a non-loss "*** ... ***" ending
                return seed
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()
    routes = sorted(ROUTES.glob("*.txt")) if ROUTES.exists() else []
    wins = fails = 0
    for rf in routes:
        lines = rf.read_text().splitlines()
        cmds = [l.strip() for l in lines
                if l.strip() and not l.strip().startswith("#")]
        wp = None
        for l in lines:
            m = re.match(r"#\s*WIN_PHRASE:\s*(.+)", l)
            if m:
                wp = m.group(1).strip()
        game = find_game(rf.stem)
        if game is None:
            print(f"  MISSING-GAME {rf.stem}")
            fails += 1
            continue
        seed = replay(game, cmds, wp)
        if seed is not None:
            wins += 1
            if not a.quiet:
                print(f"  WIN seed={seed}  {rf.stem} ({len(cmds)} cmds)")
        else:
            fails += 1
            print(f"  FAIL          {rf.stem} ({len(cmds)} cmds)")
    print(f"\n{wins}/{wins + fails} routes verified win")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
