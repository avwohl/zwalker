#!/usr/bin/env python3
"""Enchanter adaptive solver/recorder.

Plays Enchanter (r29) under a pinned interpreter RNG seed following the
3-day, 400/400 route in logs/enchanter_notes.md (mechanics verified against
the original ZIL source, github.com/historicalsource/enchanter). Adaptive
rules cover the game's random gates:

  - the bedraggled adventurer's appearance in the mirror halls (15%/turn)
    and his pilfering of the map/pencil (25%/item/turn),
  - hunger/thirst warnings (reactive eat/drink on the warning text),
  - the sleep gates (bed auto-sleep on day 1, 76-turn sleep permission on
    day 2), and the turtle errand.

Every command issued is recorded; replaying the recording with
scripts/replay_solve.py at the same seed reproduces the run move-for-move.

Usage:
    python3 scripts/solve_enchanter_adaptive.py --seeds 1-20
    python3 scripts/solve_enchanter_adaptive.py --seed 1 --verbose
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solve_zork3_adaptive import Player, SeedFailed  # noqa: E402  (generic driver)

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "games", "zcode", "enchanter.z3")

THIRST_RX = re.compile(r"very thirsty|lips are parched|faint from lack of water", re.I)
HUNGER_RX = re.compile(r"quite hungry|very hungry|faint from lack of (food|nourishment)", re.I)


class EPlayer(Player):
    """Player with reactive eat/drink on warning text (legal only when the
    warning has fired, which is exactly when the <=60-turns gate is open)."""

    meals_enabled = True

    def send(self, cmd):
        out = super().send(cmd)
        if self.meals_enabled:
            if THIRST_RX.search(out):
                out2 = super().send("drink water")
                if "swallow" not in out2.lower() and "refresh" not in out2.lower() \
                        and "thirsty" in out2.lower():
                    pass  # refused (already sated) - harmless
            if HUNGER_RX.search(out):
                super().send("eat bread")
        return out


def expect_score(p, at_least, where):
    if p.score < at_least:
        raise SeedFailed(f"score {p.score} < {at_least} after {where}")


def phase_day1(p):
    p.run(["se", "se", "ne"])                  # crone hands over the rezrov scroll
    p.run(["s", "gnusto rezrov"])
    p.run(["ne", "ne", "nw", "nw", "sw", "n", "open oven", "take bread and jug",
           "s", "ne", "se", "ne", "fill jug", "drink water", "frotz book",
           "learn rezrov", "learn rezrov"])
    expect_score(p, 35, "brook (drink+frotz)")
    p.run(["sw", "se", "e", "e"])
    p.send("rezrov gate")
    expect_score(p, 55, "west gate")
    p.run(["e", "n", "n", "u", "rezrov egg", "take egg", "d",
           "s", "s", "s", "s", "e", "drop book", "e"])
    p.send("move lighted portrait")             # dark-entry gallery
    expect_score(p, 85, "gallery portrait")
    p.run(["take black scroll", "w", "take book", "gnusto ozmoo", "learn ozmoo",
           "n", "n", "e", "e"])                 # Temple: captured at turn end
    # (the jewelled box stays in the Closet - carrying it would overload us;
    #  we return with the dagger after the sacrifice)
    p.send("ozmoo me")
    for _ in range(4):                          # sacrifice fires 4 turns post-capture
        out = p.send("wait")
        if "dagger" in out.lower() or "altar" in out.lower():
            break
    expect_score(p, 120, "sacrifice survived")
    p.run(["d", "open south cell door", "s", "take all",
           "n", "w", "w", "s"])                 # back to the Closet
    p.send("cut rope with dagger")
    expect_score(p, 145, "box rope")
    p.run(["open box", "take vellum scroll", "gnusto melbor", "learn melbor",
           "melbor me", "drop dagger",
           "s", "d", "open door", "n", "move block", "e",
           "take stained scroll", "gnusto exex", "w", "s", "u",
           "eat bread", "drink water",
           "e", "e", "n", "n", "n", "n", "examine tracks"])
    p.send("reach in hole")
    expect_score(p, 180, "gondar scroll")
    p.run(["gnusto gondar", "s", "s", "s", "s", "w", "w", "w", "u"])
    # Bed auto-sleeps once the 86-turn day has elapsed; wait out any remainder.
    for _ in range(12):
        out = p.send("get in bed")
        if re.search(r"dream|awaken|toss and turn|you wake", out, re.I):
            return
        out = p.send("wait")
        if re.search(r"dream|you wake", out, re.I):
            return
        p.send("get up")
    raise SeedFailed("day-1 bed sleep never happened")


def phase_day2_scrolls(p):
    p.run(["get up", "press button"])
    expect_score(p, 200, "bedpost button")
    p.run(["take gold leaf scroll", "gnusto vaxum", "learn rezrov",
           "d", "e", "e", "e", "n", "n", "n", "n", "n", "rezrov gate", "n",
           "take crumpled scroll", "e", "look under lily pad"])
    out = p.send("take damp scroll")            # in case look-under didn't take it
    p.run(["w", "s", "krebf shredded scroll"])
    expect_score(p, 210, "krebf repair")
    p.run(["gnusto zifmia", "gnusto cleesh", "learn zifmia", "learn vaxum",
           "drink water", "eat bread", "w"])    # Mirror Hall 4


def phase_day2_adventurer(p):
    # SYNC 1: 15%/turn appearance; zifmia on the very next input.
    out = p.wait_until(r"adventurer", max_iters=45)
    p.send("zifmia adventurer")
    expect_score(p, 220, "zifmia adventurer")
    p.send("vaxum adventurer")                  # 20-turn charm window from here
    p.run(["e", "e", "drop egg"])
    p.send("point at door")
    expect_score(p, 255, "guarded door")
    p.send("n")                                 # Map Room
    p.send("take map and pencil")
    inv = p.send("inventory")
    if "map" not in inv.lower():
        p.send("ask adventurer for map")
    if "pencil" not in inv.lower():
        p.send("ask adventurer for pencil")
    inv = p.send("inventory")
    if "map" not in inv.lower() or "pencil" not in inv.lower():
        raise SeedFailed("could not recover map and pencil from the adventurer")


def phase_day2_terror(p):
    p.run(["s", "w", "s", "s", "s", "s", "s", "w", "w", "d", "d",
           "s", "e",
           "draw line from p to f", "erase line from p to f",
           "erase line from m to v", "draw line from m to p",
           "se", "take powerful scroll", "nw", "w", "n"])
    expect_score(p, 305, "guncho scroll (terror trapped)")
    p.run(["u", "u", "drop map and pencil", "drink water"])
    # Sleep permission needs >= 76 turns since waking; pad with waits.
    for _ in range(15):
        out = p.send("sleep")
        if re.search(r"wake|awaken|dream|slept", out, re.I):
            return
        p.send("wait")
    raise SeedFailed("day-2 sleep never accepted")


def phase_day3(p):
    p.run(["learn gondar", "learn cleesh", "learn nitfol", "learn exex",
           "eat bread", "e", "e", "s", "se",
           "nitfol turtle", "turtle, follow me",
           "nw", "n", "e", "u", "exex turtle",
           "turtle, se. take scroll. nw"])
    out = ""
    for _ in range(4):                          # errand: out, grab, back, drop
        out = p.send("wait")
        if "brittle" in out.lower() or "drops" in out.lower():
            break
    p.send("take brittle scroll")
    expect_score(p, 330, "turtle delivers kulcad")
    p.run(["d", "w", "n", "n", "n", "e", "e"])
    # Endgame: strictly one command per turn - disable meal insertions.
    p.meals_enabled = False
    p.send("kulcad stairs")
    expect_score(p, 340, "kulcad stairs")
    p.send("izyuk me")
    p.send("e")
    expect_score(p, 350, "fly east")
    p.send("gondar dragon")
    p.send("cleesh monster")
    out = p.send("guncho krill")
    if p.score != 400:
        raise SeedFailed(f"endgame finished at {p.score}/400")
    return out


PHASES = [phase_day1, phase_day2_scrolls, phase_day2_adventurer,
          phase_day2_terror, phase_day3]


def attempt(data, seed, verbose=False):
    p = EPlayer(data, seed, verbose=verbose)
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
                f.write(f"# Enchanter recorded adaptive solve, seed {seed}\n")
                for c in p.commands:
                    f.write(c + "\n")
            print("wrote", a.out)
        if won:
            break


if __name__ == "__main__":
    main()
