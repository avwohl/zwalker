#!/usr/bin/env python3
"""Deephome: A Telleen Adventure (Joshua Wise, 1999; Release 1 / serial 991210,
Z-machine V5) adaptive route harness.

Replays the verified route against GameWalker under a pinned interpreter RNG
seed, records EVERY command actually sent, adapts the single piece of
state-relevant randomness (the Eranti combat at the pond), and asserts the win
so a winning recording replays deterministically through replay_solve.py.

Determinism model (see logs/deephome_notes.md for the mechanics writeup):
  * Boot draws no randomness -- two boots are byte-identical -- so the seed is
    pinned right after start() and no `restart` prelude is needed.
  * Every clock is turn-based: the Main-Hall dark spirit's ~4-turn paralysis
    (we wait it out with five `z`s) and the metal scraps melting in the
    blacksmith's furnace (one `z`). Identical command lists line these up
    identically under any seed.
  * The ONLY state-relevant randomness is the Eranti fight south of Ember.
    With the sword wielded and shield worn the dwarf reliably wins; the recorder
    loops `kill eranti` until the score jumps +20 (the Eranti dies) and records
    exactly the kill count that worked at the chosen seed (10 at seed 1). The
    dwarf auto-heals between blows, so at seed 1 he never drops into danger; a
    death guard aborts the seed if a bad streak ever kills him.

zwalker / interpreter notes (V5 quirks -- none require touching shared code):
  * get_current_room() is stuck at object 10 ("west wall") for the whole game,
    so room tracking here is done from the parsed status line and room headers.
  * vm.get_score() reads V3 status-var 17, which is a fixed low value on this
    build (5 at boot, never the real score). The TRUE score is status global
    var 21 == the "Score: N" the game paints on the status line, which we read.
  * Because get_score() is wrong, the walkthrough is verified purely via
    `#% WIN_TEXT` (the "*** You have won ***" banner). A `#% MAX_SCORE`
    directive would make replay_solve compare the broken get_score() against it
    and report won=False, so it is deliberately omitted -- see the walkthrough
    header and logs/deephome_notes.md.

Score plan (max 300; visiting all 46 Deephome rooms would give 301, an
off-by-one that prints the absurd "301 out of a possible 300" and a LOWER rank,
so the route intentionally skips one optional room -- Dwarven Village -- to land
on the game's canonical 300 and its top rank "remembered forever by your
people"):
  enter city (push mountain) +5; 45 Deephome rooms +45; coal +10; power +30;
  terrock/moss +10; water +30; gate +40; Eranti +20; squirrel +10; benign-spirit
  host +20; temple spirit (Indanaz) +30; treasury spirit (Kebarn) +40 = 300.

Usage:
  python3 scripts/solve_deephome_adaptive.py --seed 1 --out walkthroughs/deephome_verified_300.txt
  python3 scripts/solve_deephome_adaptive.py --seeds 1-6
  python3 scripts/solve_deephome_adaptive.py --seed 1 --trace
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'deephome.z5')

WIN_PAT = re.compile(r'You have won', re.I)
DEATH_PAT = re.compile(r'You have died', re.I)
SCORE_RE = re.compile(r'Score:\s*(-?\d+)')

# The verified route. `KILL` is the adaptive Eranti-combat token (expanded to
# however many `kill eranti` the pinned seed needs). Section comments document
# the room each block runs in; they are stripped before play.
ROUTE_TEXT = """
# SECRET ENTRANCE -> push the mountain button, enter the city (+5, +1)
push mountain
sw
# NORTHERN GUARD POST -> sword + shield, ready for the Eranti later
open cabinet
take sword
wield sword
take shield
wear shield
sw
# MAIN HALL: wait out the dark spirit's paralysis (5 z), then leave.
# We go straight south, SKIPPING the optional Dwarven Village (its +1 would
# push the total to the off-by-one 301); this lands the win on 300.
z
z
z
z
z
s
# N. MAIN STREET
ne
# CLOTHIER
sw
e
# BAKERY
w
w
# SCRIVENER'S -> open desks now so the blank paper is takeable later
open desks
e
s
# S. MAIN STREET
e
# DWARVEN LIBRARY (visit for the point; the encyclopedia lookups are player
# hints only -- the rituals are physical, so no lookups are needed)
w
w
# GREAT TEMPLE OF KRAXIS
e
s
# INTERSECTION -> dump the king's order here
drop order
w
# EAST ROYAL ROAD
s
# LESSER NOBLE'S PALACE
n
w
# WEST ROYAL ROAD -> the glowing green moss (repels the terrock)
take moss
n
# GREATER NOBLE'S PALACE
s
w
# OUTER COURT
w
# THRONE ROOM (the benign luminous spirit Cholok is here)
e
e
e
e
e
# EASTERN GUARD POST
se
# CITY GATES -> pop the panel hatch open (gear goes here later)
open hatch
nw
w
s
# EXTREME SOUTH MAIN STREET
sw
# WATER WORKS (wheel does nothing until the intake pipe is cleared)
ne
s
# MINING CENTER
s
# ORE MINES -> the pickaxe
take axe
n
e
# COAL MINES -> dig a lump of coal out of the rock wall (+10)
dig rock with axe
take coal
w
n
e
# CITY GENERATOR -> fuel + fire the generator: POWER ON (+30)
open furnace
put coal in furnace
close furnace
pull lever
w
n
n
e
w
n
n
w
# RAILWAY (Main Hall) -> yellow to Smithy Court
enter car
push yellow button
out
nw
# SMITHY COURT
sw
# BLACKSMITH -> the gear for the gate panel
open forge
take gear
ne
w
# SILVERSMITH
e
nw
# CARPENTER'S SHOP
se
n
# COMMON FORGE
s
ne
# SLAG PIT
sw
e
# GOLDSMITH
w
se
# RAILWAY (Smithy) -> green to Barracks
enter car
push green button
out
w
# SOLDIERS' BARRACKS
w
# ARMORY
e
s
# MESS HALL
n
sw
# TRAINING GROUNDS
sw
# WATERFALL (scout; the terrock nests in the intake pipe)
ne
ne
e
# RAILWAY (Barracks) -> red to Treasury
enter car
push red button
out
sw
# TREASURY ANTECHAMBER
n
# THE COMMON BANK
w
# COMMON VAULT
e
s
ne
# RAILWAY (Treasury) -> yellow back to Main Hall
enter car
push yellow button
out
# ... -> green to Barracks to place the moss
enter car
push green button
out
w
sw
sw
# WATERFALL -> moss into the nest drives off the terrock (+10); clear the pipe
put moss in nest
push rod
ne
ne
e
# RAILWAY (Barracks) -> yellow to Main Hall
enter car
push yellow button
out
e
s
s
s
s
sw
# WATER WORKS -> now the wheel works: WATER ON (+30)
turn wheel
ne
n
e
se
# CITY GATES -> seat the gear, throw the lever, open the GATE (+40)
put gear on post
close hatch
push lever
push button
s
# DEEPHOME ENTRANCE
w
w
# GREAT WOODS LIMITS -> the enchanted-woods path to the clearing
w
sw
w
s
e
n
w
e
# FOREST CLEARING -> reveal and take the four leaf clover
x clover
take four leaf clover
s
e
# GREAT WOODS LIMITS
e
e
s
s
# WOODED PATH (the squirrel + acorns; trapped on the second trip)
s
# TOWN OF EMBER
w
# SHOPS
e
s
# EMBER'S TOWN SQUARE
w
# EMBER TOOL SHOP -> the young man will give his hammer once the Eranti is gone
ask man about hammer
ask man about eranti
e
s
# POND -> the Eranti fight (adaptive; +20 when it dies)
KILL
n
w
# EMBER TOOL SHOP -> collect the promised hammer
ask man about hammer
take hammer
e
n
n
n
n
n
nw
w
n
n
n
# MAIN HALL -> a magical torch (fire source)
take torch
w
# RAILWAY (Main Hall) -> yellow to Smithy
enter car
push yellow button
out
nw
sw
# BLACKSMITH -> forge the metal (sharp) pick from scraps
take scrap
put scrap in furnace
burn coal with torch
z
take scraps
put scraps on anvil
hammer scraps
take metal pick
ne
se
# RAILWAY (Smithy) -> red to Treasury
enter car
push red button
out
sw
n
# THE COMMON BANK -> pick the deposit box, reveal and take the large key
unlock box with metal pick
open box
look in box
take large key
s
# TREASURY ANTECHAMBER -> unlock the vault door
unlock door with large key
drop large key
open door
w
# THE TREASURY -> the gold coin (Kebarn the shadow spirit is here) (+10)
search wealth
take gold coin
e
ne
# RAILWAY (Treasury) -> yellow to Main Hall
enter car
push yellow button
out
e
s
s
# S. MAIN STREET -> the long path to the Small Shack (trip 2)
s
e
se
s
s
s
s
s
e
# SMALL SHACK -> pick the chest, take the net
unlock chest with metal pick
open chest
take net
w
n
n
# WOODED PATH -> trap the squirrel: hole + net + acorns, climb tree (+10)
dig ground with axe
put net on hole
take acorns
put acorns in net
climb tree
down
take net
n
n
n
nw
w
w
w
w
w
# THRONE ROOM -> release the squirrel; Cholok inhabits it and leaves (+20)
open net
e
e
e
e
# INTERSECTION -> drop the now-unneeded digging tools
drop axe
drop metal pick
n
n
w
# SCRIVENER'S -> a blank paper (burned to ashes for the temple rite)
take paper
e
e
# BAKERY -> the bottle, fill with running water, burn the paper to ashes
take bottle
fill bottle
burn blank paper with torch
w
s
w
# GREAT TEMPLE OF KRAXIS -> banish the dark spirit Indanaz (+30)
drop coin
pour water on coin
put ashes on coin
put clover on coin
pray to Kraxis
manaz
take coin
take all from coin
e
n
e
# BAKERY -> refill the bottle for the second rite
fill bottle
w
n
w
# RAILWAY (Main Hall) -> red to Treasury for the final rite
enter car
push red button
out
sw
w
# THE TREASURY -> banish the shadow spirit Kebarn -> *** You have won *** (+40)
open net
drop net
put coin in net
pour water on net
take coin
pray to Kraxis
manaz
"""

ROUTE = [ln.strip() for ln in ROUTE_TEXT.splitlines()
         if ln.strip() and not ln.strip().startswith('#')]


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, trace=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.boot = self.w.start()
        self.w.vm.rng.seed(seed)          # pin RNG after start(); boot is fixed
        self.seed = seed
        self.trace = trace
        self.commands = []
        self.last = self.boot
        self.won = False

    def score(self):
        m = SCORE_RE.search(self.last)
        return int(m.group(1)) if m else None

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        if WIN_PAT.search(out):
            self.won = True
        if DEATH_PAT.search(out):
            raise Desync(f'DIED at "{cmd}": ...{out.strip()[-120:]!r}')
        if self.trace:
            first = out.strip().split('\n')[0][:62]
            print(f'[{self.score()}] > {cmd:<26} | {first}')
        return out

    def fight_eranti(self):
        """Adaptive: kill the Eranti until the score jumps +20; record each
        blow. The dwarf auto-heals between rounds, so under a good seed he wins
        without ever retreating; send() raises Desync on death."""
        base = self.score() or 0
        for _ in range(40):
            self.send('kill eranti')
            if (self.score() or 0) >= base + 20:
                return
        raise Desync('Eranti not defeated within 40 blows')


def run_route(seed, trace=False):
    r = Runner(seed, trace)
    for cmd in ROUTE:
        if cmd == 'KILL':
            r.fight_eranti()
        else:
            r.send(cmd)
    if r.score() != 300:
        raise Desync(f'final score {r.score()} != 300')
    if not r.won:
        raise Desync('no winning banner seen')
    return r


HEADER = """\
# Deephome: A Telleen Adventure (Joshua Wise, 1999; Release 1 / serial 991210,
# Inform 6 / Z-machine V5)
# VERIFIED COMPLETE SOLVE: 300/300 (the game's canonical maximum), won=True,
# died=False.
#
# Reproduce with the RNG-pinned replay harness (free, no API):
#   cd ~/src/zwalker
#   python3 scripts/replay_solve.py games/zcode/deephome.z5 \\
#       walkthroughs/deephome_verified_300.txt --seeds 24 \\
#       --out solutions/deephome_verified.json
#   => deephome_verified_300.txt: VERIFIED .../None at seed 1 | 315 cmds |
#      died=False | won=True
#
# Ending: with the power on, the water running, the city gate open, and all
# three spirits dealt with -- the dark spirit Indanaz exorcised in the temple,
# the shadow spirit Kebarn exorcised in the treasury, and the benign luminous
# spirit Cholok given a squirrel to inhabit -- the dwarven Reclaimer cleanses
# the last spirit and the game ends:
#   "*** You have won ***
#    In that game you scored 300 out of a possible 300, in 315 turns,
#    You have gone beyond the call of duty and vanquished the spirits.  You
#    will be remembered forever by your people."
#
# Why WIN_TEXT and NOT MAX_SCORE (important): this is a V5 build, so vm.get_score()
# reads the V3 status-var 17, which is a fixed low value here and never the real
# score (the true score is the status-line "Score:" == global var 21). Declaring
# `#% MAX_SCORE: 300` would make replay_solve compare that broken get_score()
# against 300 and report won=False; verification is therefore done purely by the
# winning banner below. The interpreter is shared code and must not be modified,
# so no _SCORE_VAR_OVERRIDES entry was added. (The game's real max is 300; the
# SCORE verb says "out of a possible 300". Visiting every one of the 46 Deephome
# rooms would actually yield 301 -- an off-by-one that prints the absurd "301 out
# of a possible 300" and a LOWER rank -- so the route deliberately skips one
# optional room, Dwarven Village, to hit the intended 300 and its top rank.)
#
# Why a pinned seed (no restart prelude -- boot draws no randomness; two boots
# are byte-identical and the seed is pinned right after start()): the only
# state-relevant randomness is the Eranti fight at the pond south of Ember. With
# the Sword wielded and the shield worn the dwarf auto-heals between blows and
# reliably wins; under seed 1 exactly ten `kill eranti` blows kill it (+20) and
# he is never in danger. Everything else is turn-based clockwork -- the Main-Hall
# spirit's ~4-turn paralysis (waited out with five z's) and the metal scraps
# melting in the furnace (one z) -- and replays identically under any seed with
# the same command list. Route synthesis: logs/deephome_notes.md and
# logs/deephome_route.txt.
#
# Route summary: push the mountain symbol to open the barred door and enter the
# city; grab sword+shield; wait out the paralysing dark spirit; sweep the streets,
# temple, royal roads (take the glowing moss), throne room and gates (open the
# panel hatch); mine a pickaxe and dig coal, fuel+fire the City Generator ->
# POWER; ride the coloured rail cars (yellow/green/red) round the four station
# wings; grab the gate gear at the blacksmith; drop moss in the waterfall nest to
# oust the terrock, clear the intake pipe, turn the Water Works wheel -> WATER;
# seat the gear and open the GATE; through the enchanted woods to Ember for the
# four-leaf clover; kill the Eranti to earn the tool-shop hammer; forge a sharp
# pick from scraps (torch-lit forge + anvil + hammer); pick the bank deposit box
# for the large key, open the vault, take the gold coin; pick the shack chest for
# the net, trap the squirrel (hole+net+acorns+climb), release it in the throne
# room so the benign spirit has a host; ashes from a burned blank paper + water +
# clover + coin + "pray to Kraxis"/"manaz" banish Indanaz in the temple; net +
# coin + water + "pray to Kraxis"/"manaz" banish Kebarn in the treasury -> win.
#
# Generated by scripts/solve_deephome_adaptive.py (adaptive recorder, RNG seed 1);
# replay-verified by scripts/replay_solve.py.
#% WIN_TEXT: \\*\\*\\* You have won \\*\\*\\*
"""


def write_walkthrough(path, commands):
    with open(path, 'w') as f:
        f.write(HEADER)
        for c in commands:
            f.write(c + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default=None, help='range, e.g. 1-6')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--trace', action='store_true')
    a = ap.parse_args()

    if a.seeds:
        lo, hi = (int(x) for x in a.seeds.split('-'))
        seeds = range(lo, hi + 1)
    else:
        seeds = [a.seed if a.seed is not None else 1]

    wins = total = 0
    for seed in seeds:
        total += 1
        try:
            r = run_route(seed, a.trace)
        except Desync as e:
            print(f'seed {seed}: DESYNC: {e}')
            continue
        wins += 1
        print(f'seed {seed}: WIN 300/300 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves), {r.commands.count("kill eranti")} '
              f'eranti blows')
        if a.out:
            write_walkthrough(a.out, r.commands)
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached 300/300 and the winning banner')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
