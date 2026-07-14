#!/usr/bin/env python3
"""Replay a walkthrough at a fixed RNG seed and print the full transcript.

Companion to replay_solve.py: that tool verifies, this one shows you WHERE a
walkthrough goes wrong (parser rejections, deaths, timing misses) so you can
fix the command list.

Usage:
    python3 scripts/debug_replay.py games/zcode/zork_iii.z3 wt.txt --seed 3
    python3 scripts/debug_replay.py game.z3 wt.txt --seed 3 --from 100 --to 160
    python3 scripts/debug_replay.py game.z3 wt.txt --seed 3 --quiet   # score/death events only
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402
from replay_solve import load_commands, normalize, DEATH_MARKERS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("walkthrough")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--from", dest="start", type=int, default=0,
                    help="first command index to print (all are still executed)")
    ap.add_argument("--to", dest="end", type=int, default=None,
                    help="stop executing after this command index")
    ap.add_argument("--quiet", action="store_true",
                    help="print only score changes, deaths and parser rejections")
    a = ap.parse_args()

    data = open(a.game, "rb").read()
    cmds = load_commands(a.walkthrough)
    w = GameWalker(data)
    out = w.start()
    if a.start == 0 and not a.quiet:
        print(f"=== START ===\n{out}\n")
    w.vm.rng.seed(a.seed)
    prev = w.vm.get_score()

    for i, raw in enumerate(cmds):
        if a.end is not None and i > a.end:
            break
        r = w.try_command(normalize(raw))
        text = (r.output if r is not None and hasattr(r, "output") else "") or ""
        score = w.vm.get_score()
        turns = w.vm.get_turns()
        show = not a.quiet and i >= a.start
        flag = ""
        if score != prev:
            flag += f"  [SCORE {prev}->{score}]"
            prev = score
        low = text.lower()
        if any(m in low for m in DEATH_MARKERS):
            flag += "  [DEATH]"
        if "i don't know the word" in low or "you can't see any" in low \
                or "you used the word" in low or "there was no verb" in low:
            flag += "  [PARSER]"
        if show or flag:
            print(f"--- [{i}] t={turns} s={score}{flag} > {raw}")
            if show or "[DEATH]" in flag or "[PARSER]" in flag:
                print(text.rstrip())
        if "[DEATH]" in flag:
            print(f"*** died at command {i}: {raw!r} (seed {a.seed})")
            break

    print(f"\n=== END: score {w.vm.get_score()}/{w.max_score} "
          f"turns {w.vm.get_turns()} seed {a.seed} ===")


if __name__ == "__main__":
    main()
