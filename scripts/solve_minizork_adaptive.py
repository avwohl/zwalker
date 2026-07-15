#!/usr/bin/env python3
"""MINI-ZORK I (Rel 34 / Serial 871124) adaptive route harness.

Plays the verified route against GameWalker under a pinned interpreter RNG
seed, adapting the four RNG-sensitive spots (troll melee, thief melee, the
"heal to full carrying-capacity" waits, and the Frigid River buoy grab), and
RECORDS every command actually sent, so a winning recording replays
deterministically through scripts/replay_solve.py.

Why this shape (see logs/minizork_notes.md for ZIL citations, source
github.com/the-infocom-files/zork1-mini):
  * Boot draws no randomness (two boots are byte-identical), so the seed is
    pinned right after start() and no `restart` prelude is needed.
  * Scoring model: 15 treasures (215 pts on first TAKE, VALUE zeroed after),
    3 room-entry bonuses (Kitchen 10 / Cellar 25 / Thief's Lair 20), and
    4 events (troll death 10, drain reservoir 20, pray at altar 15,
    Drafty Room reached lit 10) = exactly 325.  Depositing the 15th treasure
    in the trophy case while SCORE == 325 fires <SETG SCORE 350>, reveals the
    parchment map, and opens the West-of-House SW exit to the Stone Barrow
    (FINISH).  Both tests are EXACT equality, and any death is -10, so the run
    must be perfectly death-free and hit every scored action exactly once.
  * Route order is chosen so the thief is killed BEFORE the coal-mine trip:
    the flaming torch is a TREASUREBIT light source the thief can steal, and
    the mine's basket puzzle depends on lowering that torch into the Drafty
    Room.  Killing the thief first (his DEPOSIT-BOOTY drops all stolen loot,
    incl. the painting/egg he grabbed, in his lair) removes the theft risk and
    hands back anything he took.  Fighting him late is also far safer: the
    player's to-hit is 15 + SCORE/4, ~72% at score 227.

Adaptivity (everything else is fixed geography):
  @killtroll  attack with the sword until the troll dies
  @killthief  attack with the knife until the thief dies
  @heal       wait (checking `diagnose`) until "perfect health" restores the
              full 100-unit carrying capacity (troll/thief wounds cut it 10/pt)
  @buoy       spam "take buoy" until it succeeds (the river current drifts the
              boat downstream by a seed-dependent number of turns)
Light safety: if a move reports darkness (e.g. the torch were ever stolen
before the thief is dead), turn the lamp on before the next move.

Usage:
  python3 scripts/solve_minizork_adaptive.py --seeds 1-24 \
          --out walkthroughs/minizork_verified_350.txt
  python3 scripts/solve_minizork_adaptive.py --seed 1 --verbose
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'minizork.z3')

# Enemy (troll/thief) death -- the KILL-VILLAIN text; NOT a player death.
DEAD_ENEMY = ('breathes his last', 'sinister black fog')
# Player death -- the JIGS-UP texts.  Deliberately excludes the enemy-death
# phrases above (e.g. "...square in the heart: He dies" is the villain dying).
DEATH = ('you have died', 'removes your head', 'you have been killed',
         'lurking grue', 'smothering you', 'booooooom', 'fills your lungs',
         'deserve another chance', 'long way to fall', 'your disrespect')
WIN = re.compile(r'completed a great and perilous adventure', re.I)

# The verified route.  '#' lines are segment comments; '@...' lines are the
# adaptive meta-steps handled in Runner.step(); everything else is sent
# verbatim.  See logs/minizork_route.txt for the prose walkthrough.
ROUTE = r"""
# TRIP 1: setup, egg, painting, troll(+10), torch(light), coins, cyclops, deposit
north
north
up
take egg
down
south
east
open window
west
west
take lamp
take sword
turn on lamp
move rug
open trap door
open case
east
up
take rope
take knife
down
west
put egg in case
down
east
take painting
west
north
@killtroll
@heal
drop sword
east
se
tie rope to railing
down
take torch
turn off lamp
south
down
north
north
west
west
nw
down
take coins
sw
east
east
se
ulysses
east
put painting in case
put coins in case
# TRIP 2: drain(+20) + trunk(+15); fetch matches+screwdriver, stash in Living Room
open trap door
down
north
east
north
east
take matches
northeast
press yellow button
take wrench
take screwdriver
southwest
turn bolt with wrench
drop wrench
west
north
take trunk
south
south
west
west
nw
down
sw
east
east
se
east
put trunk in case
drop matches
drop screwdriver
# TRIP 3: skull(+22) via exorcism at Entrance to Hades
take matches
open trap door
down
north
east
se
down
take bell
south
take candles
take book
down
down
ring bell
take candles
light match
light candles with match
read book
drop bell
drop book
south
take skull
drop candles
drop matches
north
up
north
north
west
west
nw
down
sw
east
east
se
east
put skull in case
# TRIP 4a: sceptre + pray(+15) + rainbow + pot(+19)
open trap door
down
north
east
se
down
down
open coffin
take sceptre
up
south
pray
east
east
ne
wave sceptre
take pot
sw
up
west
nw
west
south
east
west
west
put sceptre in case
put pot in case
# TRIP 4b: coffin(+13) home via pray
open trap door
down
north
east
se
down
down
take coffin
up
south
pray
nw
west
south
east
west
west
put coffin in case
# TRIP 5: RIVER -> emerald(+18), scarab(+15); exit via solid rainbow
open trap door
down
north
east
north
north
north
take pump
south
south
east
down
inflate plastic with pump
drop pump
enter boat
launch
@buoy
east
open buoy
take emerald
get out of boat
take shovel
northeast
dig sand with shovel
dig sand with shovel
dig sand with shovel
dig sand with shovel
take scarab
drop shovel
southwest
south
west
southwest
up
west
nw
west
south
east
west
west
put emerald in case
put scarab in case
# TRIP 6: kill thief -> Lair(+20), chalice(+20); recover loot; keep torch for mine
drop buoy
open trap door
down
north
west
nw
down
sw
east
east
se
up
@killthief
@heal
take all
drop stiletto
down
east
put chalice in case
put painting in case
put egg in case
put coins in case
put trunk in case
put skull in case
put sceptre in case
put pot in case
put coffin in case
put emerald in case
put scarab in case
# TRIP 7: coal mine (thief dead) -> jade(+13), bracelet(+10), drafty(+10), diamond(+25)
take screwdriver
east
open sack
take garlic
west
open trap door
down
north
east
north
north
north
north
north
north
west
north
take jade
east
turn on lamp
put torch in basket
put screwdriver in basket
north
take bracelet
east
north
south
down
take coal
up
east
nw
west
south
put coal in basket
lower basket
north
east
north
south
down
drop knife
drop garlic
drop jade
drop bracelet
drop lamp
west
take torch
take coal
take screwdriver
south
open lid
put coal in machine
close lid
turn switch with screwdriver
open lid
take diamond
north
put diamond in basket
put torch in basket
put screwdriver in basket
east
take lamp
take knife
take garlic
take jade
take bracelet
turn on lamp
up
east
nw
west
south
raise chain
take diamond
take torch
west
south
east
down
north
west
nw
down
sw
east
east
se
east
put jade in case
put bracelet in case
put diamond in case
put torch in case
# ENDGAME: map -> Stone Barrow
take map
read map
east
east
nw
west
sw
"""


class Died(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)            # pin AFTER start(); boot is RNG-free
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.won = False

    def score(self):
        return self.w.vm.get_score()

    def send(self, cmd):
        out = (self.w.try_command(cmd).output or '')
        self.commands.append(cmd)
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN.search(out):
            self.won = True
        if any(m in out.lower() for m in DEATH):
            raise Died(f'died at {cmd!r}: ...{out.strip()[-120:]!r}')
        # Light safety: a move into darkness means our torch is gone (thief);
        # relight the lamp before the next move so a grue never gets a turn.
        if ('pitch black' in out.lower() or 'dark place' in out.lower()
                or 'torch has vanished' in out.lower()):
            self.send('turn on lamp')
        return out

    def step(self, cmd):
        if cmd == '@killtroll':
            for _ in range(14):
                if any(m in self.send('kill troll with sword').lower()
                       for m in DEAD_ENEMY):
                    return
            raise Died('troll would not die in 14 blows')
        if cmd == '@killthief':
            for _ in range(20):
                if any(m in self.send('kill thief with knife').lower()
                       for m in DEAD_ENEMY):
                    return
            raise Died('thief would not die in 20 blows')
        if cmd == '@heal':
            for _ in range(25):
                if 'perfect health' in self.send('diagnose').lower():
                    return
                self.send('wait')
            raise Died('never reached perfect health')
        if cmd == '@buoy':
            for _ in range(15):
                if 'feel of it' in self.send('take buoy').lower():
                    return
            raise Died('never grabbed the buoy on the river')
        self.send(cmd)


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)
    for line in ROUTE.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        r.step(line)
    return r


HEADER = """\
# MINI-ZORK I (Infocom, 1988) -- VERIFIED complete solve: 350/350 + Stone Barrow.
#
# Reproduce:
#   python3 scripts/replay_solve.py games/zcode/minizork.z3 \\
#           walkthroughs/minizork_verified_350.txt --seeds 24 \\
#           --out solutions/minizork_verified.json
#   -> VERIFIED 350/350 at seed {seed} | {n} cmds | died=False | won=True
# Expected final line: the Stone Barrow victory --
#   "You have completed a great and perilous adventure ... You have mastered
#    the first part of the ZORK trilogy."
#
# Binary: minizork.z3, Release 34 / Serial 871124, Z-machine V3, max score 350.
# Why pin the seed: the troll and thief melees and the Frigid-River buoy drift
#   are RANDOM; the interpreter RNG is seeded AFTER start() (boot draws no
#   randomness -- two boots are byte-identical, so no `restart` prelude).  This
#   list is the exact command stream recorded by scripts/solve_minizork_adaptive.py
#   at seed {seed}; every combat repeat, heal-wait, and buoy retry is baked in,
#   so it replays deterministically.  A single death (-10) makes the exact-325
#   trophy-case win unreachable, so the run is perfectly death-free.
#
# Route (see logs/minizork_route.txt / logs/minizork_notes.md):
#   350 = 215 (fifteen treasures, points on first TAKE) + 55 (room entries:
#   Kitchen 10, Cellar 25, Thief's Lair 20) + 55 (events: troll 10, drain dam
#   20, pray at altar 15, Drafty Room lit 10) -> reach exactly 325, then the
#   15th treasure into the trophy case fires +25 -> 350, reveals the map, opens
#   West-of-House SW to the Barrow.  Trips: 1 house/egg/troll/torch/coins/cyclops;
#   2 dam-drain/trunk; 3 skull exorcism; 4 coffin+sceptre / rainbow pot-of-gold;
#   5 river emerald+scarab; 6 kill thief (recover painting+chalice); 7 coal mine
#   (jade/bracelet/diamond via the basket puzzle); then map -> Stone Barrow.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-24', help='range, e.g. 1-24')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    seeds = ([a.seed] if a.seed is not None else
             range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[1]) + 1))
    wins = 0
    for seed in seeds:
        try:
            r = run_route(seed, a.verbose)
        except Died as e:
            print(f'seed {seed}: DIED/DESYNC: {e}')
            continue
        ok = r.won and r.score() == 350
        print(f'seed {seed}: score={r.score()}/350 won={r.won} '
              f'cmds={len(r.commands)} moves={r.w.vm.get_turns()}')
        if ok:
            wins += 1
            if a.out:
                with open(a.out, 'w') as f:
                    f.write(HEADER.format(seed=seed, n=len(r.commands)))
                    for c in r.commands:
                        f.write(c + '\n')
                print('wrote', a.out)
                a.out = None
    print(f'{wins} winning seed(s)')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
