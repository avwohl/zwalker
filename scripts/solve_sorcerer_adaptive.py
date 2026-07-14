#!/usr/bin/env python3
"""Sorcerer adaptive solver/recorder.

Plays Sorcerer (r18) under a pinned interpreter RNG seed following the route
in logs/sorcerer_notes.md (mechanics verified against the original ZIL source,
github.com/historicalsource/sorcerer). Two values must be parsed from game
text at runtime — the journal's monster code (RANDOM 12 at wake, mapped to
five trunk-button presses via the infotater table) and the coal-mine
combination (RANDOM 873, echoed on the dial and back to your younger self to
close the time loop). Sleep gates and spell wear-offs are text-synced.

Every command issued is recorded; replaying the recording with
scripts/replay_solve.py at the same seed reproduces the run move-for-move.

Usage:
    python3 scripts/solve_sorcerer_adaptive.py --seeds 1-20
    python3 scripts/solve_sorcerer_adaptive.py --seed 1 --verbose
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solve_zork3_adaptive import Player, SeedFailed  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "games", "zcode", "sorcerer.z3")

# Infotater wheel: monster -> the five trunk buttons (NEXT-CODE-TABLE,
# guild.zil:1054-1070; 1=black 2=gray 3=red 4=purple 5=white).
INFOTATER = {
    "bloodworm": ["white", "gray", "black", "red", "black"],
    "brogmoid":  ["red", "purple", "red", "black", "purple"],
    "dorn":      ["gray", "purple", "black", "gray", "white"],
    "dryad":     ["black", "gray", "white", "red", "red"],
    "grue":      ["black", "black", "red", "black", "purple"],
    "hellhound": ["purple", "white", "gray", "red", "gray"],
    "kobold":    ["red", "purple", "black", "purple", "red"],
    "nabiz":     ["purple", "black", "black", "black", "red"],
    "orc":       ["red", "gray", "purple", "gray", "red"],
    "rotgrub":   ["gray", "red", "gray", "purple", "red"],
    "surmin":    ["black", "black", "purple", "red", "black"],
    "yipple":    ["gray", "purple", "white", "purple", "black"],
}


def sleep_when_tired(p, max_iters=40):
    """SLEEP is refused until the first I-TIRED firing (~80 turns into a day)."""
    for _ in range(max_iters):
        out = p.send("sleep")
        if re.search(r"wake up|you awaken|awakened|slept", out, re.I):
            return out
        p.send("z")
    raise SeedFailed("sleep never accepted")


def phase_guild(p):
    p.send("z")                          # the dream: exactly ONE command
    p.run(["frotz me", "get up", "w", "s", "s", "w",
           "take vial and matchbook", "e",
           "open receptacle", "put matchbook in receptacle",
           "open vial", "drink potion", "drop vial",
           "e", "take dusty scroll", "gnusto meef",
           "w", "n", "n", "w", "move hanging", "take key",
           "open desk", "take journal", "open journal"])
    out = p.send("read journal")
    m = re.search(r"current code:\s*([a-z]+)", out, re.I)
    if not m or m.group(1).lower() not in INFOTATER:
        raise SeedFailed(f"could not parse journal code from: {out.strip()[:120]}")
    buttons = INFOTATER[m.group(1).lower()]
    p.run(["drop journal", "drop key", "e", "s", "s",
           "open receptacle", "take orange vial", "d"])
    for color in buttons:                # ONE wrong press = unwinnable
        out = p.send(f"press {color} button")
    if "scroll" not in out.lower() and "trunk" not in out.lower():
        raise SeedFailed(f"trunk did not open: {out.strip()[:120]}")
    p.send("take moldy scroll")
    out = p.send("aimfiz belboz")
    if p.score < 95:
        raise SeedFailed(f"score {p.score} < 95 after aimfiz")
    p.send("ne")                         # flee the hellhound immediately


def phase_river_fort_toll(p):
    p.run(["learn pulver", "learn izyuk", "learn izyuk",
           "e", "ne", "pulver river", "d", "ne",
           "take soiled scroll", "take guano", "gnusto fweep",
           "d", "sw", "u", "w", "w", "ne", "se", "e",
           "lower flag", "examine flag", "take aqua vial",
           "e", "put guano in cannon", "take ordinary scroll",
           "w", "w", "izyuk me", "nw", "sw", "w",
           "learn izyuk", "d", "d", "s", "w",
           "izyuk me", "w", "w", "n", "take coin", "s", "e",
           "izyuk me", "e", "e", "ne", "ne", "e", "e",
           "wake gnome", "give coin to gnome",
           "e", "e", "n", "n"])
    if p.score < 160:
        raise SeedFailed(f"score {p.score} < 160 before day-1 sleep")
    sleep_when_tired(p)


MAZE_IN = ["n", "e", "s", "s", "w", "d", "e", "e", "n", "n", "u", "u", "s", "e"]
DORN_RUN = ["w", "w", "s", "e", "d", "d", "w", "w", "u", "u", "n", "n", "d", "e"]
MAZE_OUT = ["s", "e", "n", "d", "w", "s", "w", "u", "w"]


def phase_glass_maze(p):
    p.run(["learn fweep", "learn fweep", "learn fweep", "fweep me", "e"])
    for c in MAZE_IN:
        p.send(c)
    if p.score < 180:
        raise SeedFailed(f"score {p.score} < 180 at the Hollow")
    p.run(["take parchment scroll", "put scroll in hole", "fweep me"])
    for c in DORN_RUN:                   # exact chase choreography
        out = p.send(c)
    if "worn off" not in out.lower():
        out = p.send("z")                # 2nd fweep expires in room 11
        if "worn off" not in out.lower():
            raise SeedFailed("fweep #2 did not expire on schedule")
    p.send("fweep me")
    for c in MAZE_OUT:
        out = p.send(c)
    for _ in range(8):                   # wait out the 3rd fweep as needed
        if "worn off" in out.lower():
            break
        out = p.send("z")
    else:
        raise SeedFailed("fweep #3 never wore off outside the maze")
    p.run(["take all", "s", "s", "e", "take parchment scroll", "gnusto swanzo",
           "w", "w", "w", "search gnome", "w", "w", "sw", "d", "s", "sw"])
    if p.score < 205:
        raise SeedFailed(f"score {p.score} < 205 after the Stone Hut")


def phase_park_dragon(p):
    p.run(["w", "give coin to gnome", "w", "w", "s",
           "take ball", "open aqua vial", "drink aqua potion",
           "throw ball at bunny"])
    if p.score < 215:
        raise SeedFailed(f"arcade throw failed at {p.score}")
    p.run(["gnusto malyon", "drop aqua vial", "n", "e", "e", "ne", "s",
           "learn malyon", "yonk malyon", "malyon dragon", "s"])
    if p.score < 235:
        raise SeedFailed(f"score {p.score} < 235 in the Sooty Room")
    sleep_when_tired(p)


def phase_coal_mine(p):
    # CRITICAL: exact sequence, no insertions, through to the Cove.
    p.run(["open orange vial", "e", "drink orange potion"])
    out = p.send("give book to twin")
    m = re.search(r"combination is\s*(\d+)", out, re.I)
    if not m:
        raise SeedFailed(f"no combination in twin's speech: {out.strip()[:120]}")
    combo = m.group(1)
    p.run(["drop vial", "e", f"turn dial to {combo}"])
    out = p.send("open door")
    if p.score < 255:
        raise SeedFailed(f"dial door did not open (score {p.score})")
    p.run(["e", "take rope", "u", "nw", "take beam", "nw", "w",
           "tie rope to beam", "put beam across chute", "put rope in chute"])
    out = p.send("d")
    if p.score < 275:
        raise SeedFailed(f"rope descent failed: {out.strip()[:120]}")
    p.run(["take shimmering scroll", "golmac me", "open lamp",
           "take smelly scroll", "e",
           f"younger self, the combination is {combo}"])
    out = p.send("d")                    # lower chute -> Cove
    if p.score < 320:
        raise SeedFailed(f"cove landing failed at {p.score}: {out.strip()[:120]}")
    for _ in range(12):                  # vilstu stage-3 exhaustion, then sleep
        if "vanish" in out.lower() or "exhaust" in out.lower():
            break
        out = p.send("z")
    else:
        raise SeedFailed("vilstu never fully wore off at the Cove")
    out = p.send("sleep")
    if not re.search(r"wake up|awaken", out, re.I):
        out = sleep_when_tired(p, max_iters=10)


def phase_lagoon_finale(p):
    p.run(["learn meef", "learn meef", "learn swanzo", "drop all",
           "e", "d", "meef weeds", "take crate", "w", "open crate"])
    if p.score < 335:
        raise SeedFailed(f"crate score check failed at {p.score}")
    p.run(["wear suit", "take smelly scroll", "ne", "n", "meef vines",
           "w", "w"])
    if p.score < 355:
        raise SeedFailed(f"score {p.score} < 355 in Mammoth Cavern")
    p.run(["vardik me", "open white door"])
    out = p.send("swanzo belboz")
    if p.score != 400:
        raise SeedFailed(f"finale ended at {p.score}/400: {out.strip()[:120]}")
    return out


PHASES = [phase_guild, phase_river_fort_toll, phase_glass_maze,
          phase_park_dragon, phase_coal_mine, phase_lagoon_finale]


def attempt(data, seed, verbose=False):
    p = Player(data, seed, verbose=verbose)
    final = ""
    for phase in PHASES:
        final = phase(p) or final
    return p, final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    data = open(GAME, "rb").read()
    seeds = [a.seed] if a.seed is not None else \
        range(int(a.seeds.split("-")[0]), int(a.seeds.split("-")[1]) + 1)

    for seed in seeds:
        try:
            p, final = attempt(data, seed, verbose=a.verbose)
        except SeedFailed as e:
            print(f"seed {seed}: FAILED - {e}")
            continue
        won = p.score == 400
        print(f"seed {seed}: score {p.score}/400 turns {p.turns} "
              f"commands {len(p.commands)} won={won}")
        print("ending:", (final or "").strip().replace("\n", " | ")[:300])
        if won and a.out:
            with open(a.out, "w") as f:
                f.write(f"# Sorcerer recorded adaptive solve, seed {seed}\n")
                for c in p.commands:
                    f.write(c + "\n")
            print("wrote", a.out)
        if won:
            break


if __name__ == "__main__":
    main()
