#!/usr/bin/env python3
"""Zork III adaptive solver/recorder.

Plays Zork III (r25) with an RNG-pinned interpreter using a scripted route plus
adaptive rules for the game's random gates (amulet grab, viking ship, hooded-
figure fight, old man, 776 guards). Every command issued is recorded; because
the interpreter RNG is seeded, replaying the recorded list with
scripts/replay_solve.py at the same seed reproduces the run move-for-move.

Route follows the classic lake-first walkthrough (eristic.net / InvisiClues),
cross-checked against the original ZIL source (historicalsource/zork3):
aqueduct before the quake (turn 71-140), repellent can as the beam block,
pole-down mirror-box ride past the Guardians (no potion needed).

Usage:
    python3 scripts/solve_zork3_adaptive.py --seeds 1-30
    python3 scripts/solve_zork3_adaptive.py --seed 7 --verbose
    python3 scripts/solve_zork3_adaptive.py --seeds 1-30 --out walkthroughs/zork3_recorded.txt
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "games", "zcode", "zork_iii.z3")

DEATH = re.compile(r"you have died|slavering fangs|you are dead|fills your lungs"
                   r"|\*\*\* {0,2}you have died", re.I)


class SeedFailed(Exception):
    pass


class Player:
    def __init__(self, data, seed, verbose=False):
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)
        self.seed = seed
        self.verbose = verbose
        self.log = []          # (command, output)
        self.commands = []

    @property
    def turns(self):
        return self.w.vm.get_turns()

    @property
    def score(self):
        return self.w.vm.get_score()

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None and hasattr(r, "output") else "") or ""
        self.commands.append(cmd)
        self.log.append((cmd, out))
        if self.verbose:
            print(f"[{len(self.commands)-1}] t={self.turns} s={self.score} > {cmd}")
            print(out.rstrip()[:600])
        if DEATH.search(out):
            raise SeedFailed(f"died at t={self.turns} on {cmd!r}: {out.strip()[:120]}")
        return out

    def run(self, cmds):
        out = ""
        for c in cmds:
            out = self.send(c)
        return out

    def wait_until(self, pattern, max_iters=40, cmd="wait", forbid=None):
        """Issue `cmd` until output matches pattern. Returns the matching output."""
        rx = re.compile(pattern, re.I)
        for _ in range(max_iters):
            out = self.send(cmd)
            if forbid and re.search(forbid, out, re.I):
                raise SeedFailed(f"forbidden {forbid!r} while waiting for {pattern!r}")
            if rx.search(out):
                return out
        raise SeedFailed(f"never saw {pattern!r} in {max_iters} x {cmd!r}")

    def retry(self, cmd, pattern, max_iters=8):
        rx = re.compile(pattern, re.I)
        for _ in range(max_iters):
            out = self.send(cmd)
            if rx.search(out):
                return out
        raise SeedFailed(f"{cmd!r} never produced {pattern!r}")


def phase_lake_and_vista(p):
    p.run(["take lamp", "turn on lamp", "south", "south", "south", "south",
           "turn off lamp", "drop lamp"])
    # -- amulet: 50%/try, 3-turn air limit, ~7-turn cold limit --
    out = p.send("enter lake")
    got = False
    for dip in range(4):
        out = p.send("dive")
        for _ in range(3):
            out = p.send("take object")
            if "golden amulet" in out or "already wearing" in out:
                got = True
                break
            if "return to the surface" in out:
                break
        if got:
            break
        # on the surface without it: leave the water before hypothermia
        if "return to the surface" not in out and "On the Lake" not in out:
            out = p.send("up")
        p.send("north")            # Lake Shore
        out = p.send("enter lake")
        if "roc" in out.lower():
            continue               # next loop iteration dives immediately
    if not got:
        raise SeedFailed("could not grab the amulet in 4 dips")
    # we may still be underwater (air remaining) - surface, then swim west
    if "return to the surface" not in out and "On the Lake" not in out:
        p.send("up")
    p.send("west")
    p.send("south")                # Scenic Vista
    p.send("get torch")
    # -- vista trips: II = grue repellent (Room 8), III = torch drop (Damp Passage)
    p.wait_until(r'changes to "II"', max_iters=8)
    out = p.send("touch table")
    if "Room 8" not in out:
        raise SeedFailed("vista II trip missed Room 8")
    p.send("get can")
    p.wait_until(r"back in the viewing room", max_iters=3)
    p.wait_until(r'changes to "III"', max_iters=8)
    out = p.send("touch table")
    if "Damp Passage" not in out:
        raise SeedFailed("vista III trip missed Damp Passage")
    p.send("drop torch")
    p.wait_until(r"back in the viewing room", max_iters=3)
    p.send("north")                # Western Shore (one dark-ish move is safe)
    # -- recover the can from the lake bottom (dropped on entry) --
    p.send("enter lake")
    got = False
    for dip in range(4):
        p.send("dive")
        for _ in range(3):
            out = p.send("get can")
            if "Taken" in out or "already have" in out:
                got = True
                break
            if "return to the surface" in out:
                break
        if got:
            break
        out = p.send("south")      # try to leave via southern shore to rest
        if "Southern Shore" in out:
            p.send("enter lake")
        else:
            p.send("up")
    if not got:
        raise SeedFailed("could not recover the repellent can in 4 dips")
    out = p.send("south")          # Southern Shore
    if "Southern Shore" not in out:
        p.send("up")
        p.send("south")


def phase_key_and_aqueduct(p):
    p.send("spray repellent on me")
    p.run(["south", "south", "east"])   # 3 dark moves inside the 5-turn window
    out = p.send("get key")
    if "Taken" not in out:
        raise SeedFailed("no key in Key Room")
    p.run(["raise manhole cover", "down", "north", "north", "north"])
    out = p.send("get torch")           # waiting in Damp Passage since the vista
    if "Taken" not in out:
        raise SeedFailed("torch missing from Damp Passage")


def phase_cliff_and_staff(p):
    p.run(["west", "west", "west", "get bread"])
    p.send("down")                      # Cliff Ledge (scores point 3)
    p.send("get chest")
    p.wait_until(r"tied that chest|tie that rope|Maybe I can help", max_iters=15)
    p.send("tie chest to rope")
    p.wait_until(r"grab onto the rope", max_iters=8)
    out = p.send("grab rope")
    if "staff" not in out:
        raise SeedFailed("cliff man did not hand over the staff")


def phase_ocean_vial(p):
    p.run(["down", "down", "south"])    # Flathead Ocean
    p.wait_until(r"Viking ship|crusty sailor", max_iters=40)
    out = p.send("hello sailor")
    if "waited three ages" not in out:
        raise SeedFailed("missed the ship window")
    out = p.send("get vial")
    if "Taken" not in out:
        p.send("look")
        out = p.send("get vial")
        if "Taken" not in out:
            raise SeedFailed("vial not on the beach")


def phase_shadow_fight(p):
    out = p.send("east")                # Land of Shadow
    if "hooded figure" not in out:
        out = p.wait_until(r"cloaked and hooded figure", max_iters=25)
    my_wounds = 0
    for round_ in range(60):
        low = out.lower()
        if "badly hurt and defenseless" in low or "badly wounded and defenseless" in low:
            break
        # our own damage accounting (1 normal hit, 2 for the heavy blow)
        if re.search(r"slips its sword between your ribs|hurt very badly", low):
            my_wounds += 2
        elif re.search(r"you are hit|wounds you|you are wounded|black smoke", low):
            my_wounds += 1
        if my_wounds >= 3:
            # retreat west out of the Land of Shadow and heal up
            out = p.send("west")
            if "hooded figure" in out.lower() and "way" in out.lower():
                out = p.send("south")   # west blocked; sidestep then west
                out = p.send("west")
            for _ in range(12):         # ~36 turns: heal 3-4 points
                p.send("wait")
            my_wounds = 0
            out = p.send("east")        # back into the Land of Shadow
            if "hooded figure" not in out.lower():
                out = p.wait_until(r"cloaked and hooded figure", max_iters=25)
            continue
        out = p.send("attack figure")
    else:
        raise SeedFailed("figure never reached 'badly hurt and defenseless'")
    out = p.send("take hood")
    if "remove the hood" not in out.lower():
        raise SeedFailed(f"take hood failed: {out.strip()[:100]}")
    out = p.send("take cloak")
    if not re.search(r"wearing the cloak|taken", out, re.I):
        p.send("look")
        out = p.send("take cloak")
        if not re.search(r"wearing the cloak|taken", out, re.I):
            raise SeedFailed("cloak not takeable after mercy")


def phase_to_great_door(p):
    # Exit the Land of Shadow northeastward to a landmark, then take the
    # mapped corridor: Junction -> Creepy Crawl -> Tight Squeeze ->
    # Crystal Grotto -> Royal Hall -> Great Door.
    at_junction = False
    blocked = ("can't go that way", "stone wall blocks", "standing in your way",
               "quicksand prevents")
    for _ in range(10):
        out = None
        for d in ("ne", "north", "east"):
            out = p.send(d)
            if not any(b in out.lower() for b in blocked):
                break
        if any(b in out.lower() for b in blocked):
            continue
        if "Junction" in out:
            at_junction = True
            break
        if "Barren Area" in out:
            p.send("east")
            at_junction = True
            break
        if "Cliff" in out and "Ledge" not in out and "Base" not in out:
            p.run(["east", "east"])
            at_junction = True
            break
        if "Land of Shadow" not in out:
            raise SeedFailed(f"shadow exit surprise: {out.strip()[:80]}")
    if not at_junction:
        raise SeedFailed("could not find the way out of the Land of Shadow")
    out = p.run(["south", "east", "east", "south"])
    if "Royal Hall" not in out:
        raise SeedFailed(f"lost en route to Royal Hall: {out.strip()[:80]}")
    out = p.send("south")              # Great Door
    if "Great Door" not in out:
        raise SeedFailed("did not reach Great Door")
    # quake gate: wait here until the cleft opens (turn 71-140)
    if not any("great tremor" in o.lower() for _, o in p.log):
        p.wait_until(r"great tremor|dungeon shakes", max_iters=40)


def phase_museum_ring(p):
    p.send("east")                     # through the cleft: Museum Entrance
    p.send("north")                    # Technology Museum
    p.run(["push gold machine south", "open stone door", "push gold machine east"])
    p.run(["turn dial to 776", "sit on seat"])
    out = p.send("push button")
    if "disorientation" not in out.lower():
        raise SeedFailed(f"time travel failed: {out.strip()[:100]}")
    p.send("take ring")
    p.wait_until(r"marching away", max_iters=10)
    p.run(["open door", "west", "open wooden door", "north"])
    p.send("put ring under seat")
    p.run(["sit on seat", "turn dial to 948", "push button"])
    out = p.send("look under seat")
    if "ring" not in out.lower():
        raise SeedFailed("ring did not survive 172 years under the seat")
    p.run(["stand", "open wooden door", "south", "open stone door", "east"])
    p.send("get all")                  # belongings left behind by the time trip


ROYAL_PUZZLE = [
    "push east wall", "s", "s", "se", "push south wall", "n", "ne",
    "push south wall", "take book", "push south wall", "e", "ne",
    "push west wall", "sw", "nw", "ne", "push south wall", "sw",
    "push east wall", "ne", "push south wall", "nw", "n", "n", "n",
    "push east wall", "sw", "s", "se", "ne", "n", "push west wall", "nw",
    "push south wall", "again", "w", "nw", "nw", "push south wall",
    "se", "se", "se", "ne", "push west wall", "again", "sw",
    "push north wall", "again", "again", "nw", "up",
]


def phase_royal_puzzle(p):
    p.run(["west", "south"])           # Royal Puzzle Entrance
    p.send("down")
    for cmd in ROYAL_PUZZLE:
        out = p.send(cmd)
        if "won't budge" in out.lower() or "can't" in out.lower() and "push" in cmd:
            raise SeedFailed(f"royal puzzle desync at {cmd!r}: {out.strip()[:80]}")
    if "book" not in " ".join(c for c in p.commands[-60:]):
        pass
    out = p.send("inventory")
    if "book" not in out.lower():
        raise SeedFailed("left the Royal Puzzle without the lore book")


def phase_old_man_and_beam(p):
    # Royal Puzzle Entrance -> Engravings Room
    p.run(["north", "west", "north", "north", "west", "west", "north", "east"])
    out = p.send("ne")
    for _ in range(12):                # old man present 30%/entry
        if "old" in out.lower() and "man" in out.lower():
            break
        p.send("sw")
        out = p.send("ne")
    else:
        raise SeedFailed("old man never appeared in the Engravings Room")
    p.send("wake man")
    out = p.send("give bread to man")
    if "secret door" not in out.lower() and "outline" not in out.lower():
        raise SeedFailed(f"old man did not reveal the door: {out.strip()[:100]}")
    p.run(["open secret door", "north", "north"])   # Button Room -> Beam Room
    p.send("drop can")                 # blocks the beam
    p.send("south")
    out = p.send("press button")
    if "click" not in out.lower():
        raise SeedFailed("mirror panel button did not click")
    p.run(["north", "north", "north"])  # into the mirror box within 7 turns


def phase_mirror_box(p):
    p.send("raise short pole")
    p.run(["push yellow wall", "push yellow wall"])   # 270 -> 0 (north)
    p.send("lower short pole")
    p.run(["push mahogany wall", "push mahogany wall", "push mahogany wall"])
    p.send("raise short pole")
    p.run(["push white wall", "push white wall", "push white wall", "push white wall"])
    p.send("push pine wall")
    out = p.send("north")
    if "Dungeon Entrance" not in out:
        raise SeedFailed(f"mirror box exit missed: {out.strip()[:80]}")


def phase_endgame(p):
    out = p.send("knock on door")
    if "come back" in out.lower():
        raise SeedFailed("Dungeon Master turned us away (missing an item)")
    p.run(["north", "east", "north", "north"])        # Parapet
    p.run(["turn dial to 4", "press button"])
    p.run(["south", "open cell door", "south"])       # into cell 4
    p.send("master, go to the parapet")
    p.send("master, turn the dial to 1")
    out = p.send("master, push the button")
    out = p.send("unlock bronze door with key")
    if "mold" not in out.lower() and "unlock" not in out.lower():
        raise SeedFailed(f"bronze door unlock failed: {out.strip()[:100]}")
    p.send("open bronze door")
    out = p.send("south")
    return out


PHASES = [phase_lake_and_vista, phase_key_and_aqueduct, phase_cliff_and_staff,
          phase_ocean_vial, phase_shadow_fight, phase_to_great_door,
          phase_museum_ring, phase_royal_puzzle, phase_old_man_and_beam,
          phase_mirror_box, phase_endgame]


def attempt(data, seed, verbose=False):
    p = Player(data, seed, verbose=verbose)
    final = ""
    for phase in PHASES:
        final = phase(p) or final
    return p, final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--seeds", default="1-30", help="range like 1-30")
    ap.add_argument("--out", default=None, help="write recorded commands here on success")
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    data = open(GAME, "rb").read()
    if a.seed is not None:
        seeds = [a.seed]
    else:
        lo, hi = a.seeds.split("-")
        seeds = range(int(lo), int(hi) + 1)

    for seed in seeds:
        try:
            p, final = attempt(data, seed, verbose=a.verbose)
        except SeedFailed as e:
            print(f"seed {seed}: FAILED - {e}")
            continue
        won = p.score == 7
        print(f"seed {seed}: score {p.score}/7 turns {p.turns} "
              f"commands {len(p.commands)} won={won}")
        print("ending:", final.strip().replace("\n", " | ")[:300])
        if won and a.out:
            with open(a.out, "w") as f:
                f.write(f"# Zork III recorded adaptive solve, seed {seed}\n")
                for c in p.commands:
                    f.write(c + "\n")
            print("wrote", a.out)
        if won:
            break


if __name__ == "__main__":
    main()
