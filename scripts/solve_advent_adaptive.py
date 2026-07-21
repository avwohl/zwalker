#!/usr/bin/env python3
"""Adventure (ZILF port, advent.z3 r1/s151001) adaptive route recorder.

Plays the classic 350-point Colossal Cave route through the exact GameWalker
pathway used by scripts/replay_solve.py (seed pinned AFTER start()), adapting
to the two RNG actors, and RECORDS every command it sends so the recording
replays deterministically at the same seed:

  * Dwarves (5): spawn at DWARVES-REMAINING% per turn in lit non-sacred rooms;
    first one ever throws the axe and flees, later ones throw knives (9.5%
    death per throw).  Adaptive response: throw axe at dwarf (2/3 kill),
    re-take the axe, repeat.
  * Pirate: 2% per turn; either robs your carried treasures or is merely
    spotted -- both events park the treasure chest at his maze dead end.
    The recorder tracks what was stolen and recovers it with the chest.

Port-specific mechanics verified against the game's ZIL source (advent.zil,
Jesse McGrew 2015):
  * Cave closing starts once all 15 treasures have TOUCHBIT (i.e. when the
    chest is taken at the dead end), +25 pts; the endgame teleport fires 25
    turns later (+10).  All deposits plus the Witt's End magazine point must
    fit in that window -- the route needs ~16-24 turns depending on how much
    the pirate stole.
  * Score 350 = 36 start + 15x2 finding + 188 deposit (9x14+12+5x10) +
    25 Hall of Mists + 25 closing + 10 past closing + 1 magazine + 35 blast
    (player at SW End, mark rod at NE End).
  * Lantern has 330 turns of power; the recorder switches it off during
    building deposit stops.

Usage:
  python3 scripts/solve_advent_adaptive.py --seed 1 --record /tmp/adv_s1.txt
  python3 scripts/solve_advent_adaptive.py --sweep 12 --record logs/advent_win.txt
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'advent.z3')

# treasure key -> noun used for take/drop
TREASURES = {
    'pyramid': 'pyramid', 'silver': 'silver', 'emerald': 'emerald',
    'trident': 'trident', 'vase': 'vase', 'pearl': 'pearl', 'rug': 'rug',
    'coins': 'coins', 'jewelry': 'jewelry', 'diamonds': 'diamonds',
    'nugget': 'nugget', 'eggs': 'eggs', 'spices': 'spices',
    'chain': 'chain', 'chest': 'chest',
}

WIN_RX = re.compile(r'conquering adventurer off into the sunset', re.I)


class SeedFailed(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        # ADVENT_GAME overrides the default PUB binary -- used to derive a
        # SRC route against a zorkie-compiled build of the same port.
        self.w = GameWalker(open(os.environ.get('ADVENT_GAME', GAME), 'rb').read())
        self.w.start()
        self.w.vm.rng.seed(seed)
        self.seed = seed
        self.verbose = verbose
        self.rec = []                  # every command sent, in order
        self.carried = set()           # treasure keys in hand
        self.stolen = set()            # treasure keys at the pirate dead end
        self.have_axe = False
        self.axe_here = False
        self.dwarf_here = False
        self.pirate_event = False
        self.closing = False
        self.closed = False
        self.won = False

    # ------------------------------------------------------------------ io
    def send(self, cmd, expect=None):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.rec.append(cmd)
        if self.verbose:
            print(f'--- [{len(self.rec)-1}] ({self.score()}) > {cmd}')
            print(out.rstrip())
        # treasure bookkeeping FIRST (the action happens before the pirate
        # daemon on the same turn), then event scanning (robbery etc.)
        low = out.lower()
        m = re.match(r'(take|drop) (\w+)$', cmd)
        if m and m.group(2) in TREASURES:
            key = m.group(2)
            if m.group(1) == 'take':
                if 'pick up' in low or 'taken' in low or 'you catch' in low:
                    self.carried.add(key)
                    self.stolen.discard(key)
            else:
                if 'put down' in low or 'dropped' in low or 'you drop' in low \
                        or 'delicately' in low or 'score has gone' in low:
                    self.carried.discard(key)
        self.scan(cmd, out)
        if expect and not re.search(expect, out, re.I | re.S):
            raise SeedFailed(f'expected {expect!r} after {cmd!r}, got: '
                             f'{out.strip()[-400:]!r}')
        return out

    def score(self):
        return self.w.vm.get_score()

    def turns(self):
        return self.w.vm.get_turns()

    # ------------------------------------------------------------- tracking
    def scan(self, cmd, out):
        low = out.lower()
        if ('gotten yourself killed' in low or 'reincarnate' in low
                or 'out of orange smoke' in low
                or 'call it a day' in low):
            raise SeedFailed('DIED: ' + out.strip()[-250:])
        if 'pounces a bearded pirate' in low:
            self.stolen |= self.carried
            self.carried.clear()
            self.pirate_event = True
        if "been spotted" in low:
            self.pirate_event = True
        if 'comes out of the shadows' in low or 'stalks after you' in low:
            self.dwarf_here = True
        if 'throws a nasty little axe' in low:
            # first-ever dwarf: throws axe, misses, runs away
            self.axe_here = True
            self.dwarf_here = False
        if 'dwarf slips away' in low:
            self.dwarf_here = False
        if 'vaporizes him' in low:
            self.dwarf_here = False
        if 'cave closing soon' in low:
            self.closing = True
        if 'cave is now closed' in low:
            self.closed = True
        if WIN_RX.search(out):
            self.won = True

    # ------------------------------------------------------------- dwarves
    def take_axe(self):
        out = self.send('take axe')
        low = out.lower()
        if 'pick up' in low or 'taken' in low:
            self.have_axe = True
            self.axe_here = False
        elif 'too many things' in low:
            raise SeedFailed('could not take axe: hands full')
        else:
            raise SeedFailed('take axe failed: ' + out.strip()[-200:])

    def fight(self):
        guard = 0
        while self.dwarf_here:
            guard += 1
            if guard > 20:
                raise SeedFailed('dwarf fight did not resolve')
            if self.have_axe:
                out = self.send('throw axe at dwarf')
                low = out.lower()
                self.have_axe = False
                self.axe_here = True
                if 'killed a little dwarf' in low:
                    self.dwarf_here = False
                if not self.dwarf_here or 'missed' in low:
                    self.take_axe()
            elif self.axe_here:
                self.take_axe()
            else:
                # first dwarf ever: no axe exists yet; wait for his axe throw
                self.send('z')
        if self.axe_here and not self.have_axe:
            self.take_axe()

    # ------------------------------------------------------------ commands
    def do(self, cmd, expect=None, atomic=False):
        if not atomic:
            self.fight()
        return self.send(cmd, expect)

    def deposit(self, pillow_first=False):
        """Drop all carried treasures in the building (pillow before vase)."""
        self.fight()
        if pillow_first:
            self.send('drop pillow')
        # nugget last just for stable ordering; vase after pillow always
        order = sorted(self.carried, key=lambda k: (k == 'vase' and -1) or 1,
                       reverse=True)
        for key in list(order):
            before = self.score()
            out = self.send('drop ' + TREASURES[key])
            if self.score() <= before:
                raise SeedFailed(f'deposit of {key} did not score: '
                                 + out.strip()[-200:])
            self.carried.discard(key)

    def dead_end(self):
        """Take the chest and everything the pirate stole."""
        self.fight()
        out = self.send('take chest')
        if "can't see" in out.lower():
            raise SeedFailed('no chest at dead end: pirate never showed')
        if 'pick up' not in out.lower() and 'taken' not in out.lower():
            raise SeedFailed('take chest failed: ' + out.strip()[-200:])
        self.carried.add('chest')
        for key in sorted(self.stolen):
            self.do('take ' + TREASURES[key], atomic=True)
        if self.stolen:
            raise SeedFailed('failed to recover stolen: %s' % self.stolen)

    def wait_for_close(self):
        for _ in range(30):
            if self.closed:
                return
            self.send('z')
        raise SeedFailed('cave never closed while waiting')

    def do_retry(self, cmd, expect, tries=10):
        """Probabilistic exits (Swiss Cheese nw): retry until it lands."""
        for _ in range(tries):
            self.fight()
            out = self.send(cmd)
            if re.search(expect, out, re.I | re.S):
                return out
            if 'crawled around' not in out.lower():
                raise SeedFailed(f'retry {cmd!r}: unexpected '
                                 + out.strip()[-200:])
        raise SeedFailed(f'retry {cmd!r} never reached {expect!r}')


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)
    do = r.do

    # -- prelude ------------------------------------------------------
    do('no', 'At End Of Road')
    do('in', 'Inside Building')
    do('take lamp')
    do('on', 'switch on')

    # -- trip 1: pyramid (via plover) + silver -------------------------
    do('plugh', 'Y2')
    do('plover', 'Plover Room')
    do('ne', 'Dark Room')
    do('take pyramid')
    do('s', 'Plover Room')
    do('plover', 'Y2')
    do('s', 'Low N/S Passage')
    do('take silver')
    do('n', 'Y2')
    do('plugh', 'Inside Building')
    do('off', 'switch off')
    r.deposit()
    do('take bottle')
    do('on', 'switch on')

    # -- trip 2: plant/oil, emerald, vase, pillow, then trident straight
    #    to the clam (short critical window), pearl ---------------------
    do('plugh', 'Y2')
    do('s', 'Low N/S Passage')
    do('d', 'Dirty Passage')
    do('w', 'Dusty Rock Room')
    do('d', 'Complex Junction')
    do('w', 'Bedquilt')
    do('w', 'Swiss Cheese')
    do('w', 'East End of Twopit')
    do('w', 'West End of Twopit')
    do('d', 'West Pit')
    do('water plant', 'spurts into furious growth')
    do('u', 'West End of Twopit')
    do('w', 'Slab Room')
    do('u', 'Secret N/S Canyon')
    do('n', 'Mirror Canyon')
    do('n', 'Reservoir')
    do('fill bottle', 'water')
    do('s', 'Mirror Canyon')
    do('s', 'Secret N/S Canyon')
    do('d', 'Slab Room')
    do('s', 'West End of Twopit')
    do('d', 'West Pit')
    do('water plant', 'grows explosively')
    do('u', 'West End of Twopit')
    do('e', 'East End of Twopit')
    do('d', 'East Pit')
    do('fill bottle', 'oil')
    do('u', 'East End of Twopit')
    do('e', 'Swiss Cheese')
    r.do_retry('nw', 'Oriental Room')
    do('n', 'Misty Cavern')
    do('w', 'Alcove')
    # tight tunnel: only the emerald fits through with you
    r.fight()
    do('drop bottle', atomic=True)
    if r.have_axe:
        do('drop axe', atomic=True)
        r.have_axe = False
        r.axe_here = True
    do('drop lamp', atomic=True)      # lamp stays lit: alcove stays visible
    do('e', 'Plover Room', atomic=True)
    do('take emerald', atomic=True)
    do('w', 'Alcove', atomic=True)
    do('take lamp', atomic=True)
    do('take bottle', atomic=True)
    if r.axe_here:
        r.take_axe()
    do('nw', 'Misty Cavern')
    do('s', 'Oriental Room')
    do('take vase')
    do('se', 'Swiss Cheese')
    do('e', 'Soft Room')
    do('take pillow')
    do('w', 'Swiss Cheese')
    do('w', 'East End of Twopit')
    do('w', 'West End of Twopit')
    do('d', 'West Pit')
    do('climb plant', 'Narrow Corridor')
    do('w', 'Giant Room')
    do('n', 'Immense N/S Passage')
    do('oil door', 'freed up the hinges')
    do('drop bottle')
    do('open door', 'heaves open')
    do('n', 'Cavern With Waterfall')
    do('take trident')
    do('w', 'Steep Incline')
    do('d', 'Large Low Room')
    do('se', 'Oriental Room')
    do('se', 'Swiss Cheese')
    do('ne', 'Bedquilt')
    do('e', 'Complex Junction')
    do('n', 'Shell Room')
    do('unlock clam with trident', 'pearl falls out')
    do('d', 'Ragged Corridor')
    do('d', 'Cul-de-Sac')
    do('take pearl')
    do('u', 'Ragged Corridor')
    do('u', 'Shell Room')
    do('s', 'Complex Junction')
    do('u', 'Dusty Rock Room')
    do('e', 'Dirty Passage')
    do('u', 'Low N/S Passage')
    do('n', 'Y2')
    do('plugh', 'Inside Building')
    do('off', 'switch off')
    r.deposit(pillow_first=True)
    do('on', 'switch on')

    # -- trip 3: rod/cage/bird, snake, dragon rug, coins, jewelry,
    #            diamonds (crystal bridge), gold nugget ----------------
    do('xyzzy', 'Debris Room')
    do('take rod')
    do('e', 'Cobble Crawl')
    do('take cage')
    do('w', 'Debris Room')
    do('w', 'Sloping E/W Canyon')
    do('w', 'Orange River Chamber')
    do('drop rod')
    do('take bird', 'catch')
    do('take rod')
    do('w', 'Top of Small Pit')
    do('d', 'Hall of Mists')
    do('d', 'Hall of the Mountain King')
    do('free bird', 'drives the snake away')
    do('drop cage')
    do('sw', 'Secret E/W Canyon')
    do('w', 'Secret Canyon')
    r.fight()
    do('kill dragon', 'bare hands', atomic=True)
    do('yes', 'You have just vanquished a dragon', atomic=True)
    do('take rug')
    do('e', 'Secret E/W Canyon')
    do('e', 'Hall of the Mountain King')
    do('w', 'West Side Chamber')
    do('take coins')
    do('e', 'Hall of the Mountain King')
    do('s', 'South Side Chamber')
    do('take jewelry')
    do('n', 'Hall of the Mountain King')
    do('u', 'Hall of Mists')
    do('w', 'East Bank of Fissure')
    do('wave rod', 'crystal bridge')
    do('drop rod')
    do('w', 'West Side of Fissure')
    do('take diamonds')
    do('e', 'East Bank of Fissure')
    do('e', 'Hall of Mists')
    do('s', 'Low Room')
    do('take nugget')
    do('n', 'Hall of Mists')
    do('n', 'Hall of the Mountain King')
    do('n', 'Low N/S Passage')
    do('n', 'Y2')
    do('plugh', 'Inside Building')
    do('off', 'switch off')
    r.deposit()
    do('take food')
    do('take keys')
    do('on', 'switch on')

    # -- trip 4: eggs, troll toll, bear, chain, spices, eggs again ------
    do('plugh', 'Y2')
    do('s', 'Low N/S Passage')
    do('d', 'Dirty Passage')
    do('w', 'Dusty Rock Room')
    do('d', 'Complex Junction')
    do('w', 'Bedquilt')
    do('w', 'Swiss Cheese')
    do('w', 'East End of Twopit')
    do('w', 'West End of Twopit')
    do('d', 'West Pit')
    do('climb plant', 'Narrow Corridor')
    do('w', 'Giant Room')
    do('take eggs')
    do('n', 'Immense N/S Passage')
    do('n', 'Cavern With Waterfall')
    do('w', 'Steep Incline')
    do('d', 'Large Low Room')
    do('sw', 'Sloping Corridor')
    do('u', 'SW Side of Chasm')
    do('ne', 'blocks your way')          # troll steps out from under bridge
    do('throw eggs at troll', 'catches your treasure')
    r.carried.discard('eggs')
    do('ne', 'NE Side of Chasm')
    do('ne', 'Corridor')
    do('e', 'Fork in Path')
    do('se', 'Limestone Passage')
    do('s', 'Front of Barren Room')
    do('e', 'Barren Room')
    do('give food to bear', 'calm down')
    do('unlock chain with keys')
    do('take chain')
    do('drop keys')
    do('take bear', 'following you')
    do('w', 'Front of Barren Room')
    do('w', 'Limestone Passage')
    do('n', 'Fork in Path')
    do('ne', 'Warm Walls')
    do('e', 'Chamber of Boulders')
    do('take spices')
    do('w', 'Warm Walls')
    do('s', 'Fork in Path')
    do('w', 'Corridor')
    do('w', 'NE Side of Chasm')
    do('sw', 'blocks your way')          # troll reappears; move is rolled back
    do('release bear', 'scurries away')
    do('sw', 'SW Side of Chasm')
    do('sw', 'Sloping Corridor')
    do('d', 'Large Low Room')
    do('se', 'Oriental Room')
    do('se', 'Swiss Cheese')
    do('w', 'East End of Twopit')
    do('w', 'West End of Twopit')
    do('d', 'West Pit')
    do('climb plant', 'Narrow Corridor')
    do('w', 'Giant Room')
    r.fight()
    do('fee', atomic=True)
    do('fie', atomic=True)
    do('foe', atomic=True)
    do('foo', 'golden eggs', atomic=True)
    do('take eggs')
    do('s', 'Narrow Corridor')
    do('d', 'West Pit')
    do('u', 'West End of Twopit')
    do('w', 'Slab Room')
    do('u', 'Secret N/S Canyon')
    do('s', 'Secret Canyon')
    do('e', 'Secret E/W Canyon')
    do('e', 'Hall of the Mountain King')
    do('n', 'Low N/S Passage')
    do('n', 'Y2')
    do('plugh', 'Inside Building')
    do('off', 'switch off')
    r.deposit()
    do('on', 'switch on')

    # -- trip 5: maze, pirate chest -> closing window -------------------
    do('plugh', 'Y2')
    do('s', 'Low N/S Passage')
    do('s', 'Hall of the Mountain King')
    do('u', 'Hall of Mists')
    do('w', 'East Bank of Fissure')
    do('w', 'West Side of Fissure')
    do('w', 'West End of Hall of Mists')
    do('s', 'Maze')     # alike maze 1
    do('e', 'Maze')     # 2
    do('s', 'Maze')     # 3
    do('s', 'Maze')     # 6
    do('s', 'Maze')     # 8
    do('n', 'Maze')     # 10
    do('e', 'Brink of Pit')
    do('e', 'Maze')     # 13
    do('nw', 'Dead End')
    r.dead_end()        # take chest + stolen loot; closing starts here
    if not r.closing:
        raise SeedFailed('closing did not start at chest take')
    # 25-turn window: get out (6), deposit (1+k), magazine point (8+)
    do('se', 'Maze', atomic=True)       # 13
    do('n', 'Brink of Pit', atomic=True)
    do('d', 'Orange River Chamber', atomic=True)
    do('e', 'Sloping E/W Canyon', atomic=True)
    do('e', 'Debris Room', atomic=True)
    do('xyzzy', 'Inside Building', atomic=True)
    r.deposit()
    do('plugh', 'Y2', atomic=True)
    do('s', 'Low N/S Passage', atomic=True)
    do('d', 'Dirty Passage', atomic=True)
    do('w', 'Dusty Rock Room', atomic=True)
    do('d', 'Complex Junction', atomic=True)
    do('e', 'Anteroom', atomic=True)
    do('take magazine', atomic=True)
    do('e', "Witt's End", atomic=True)
    do('drop magazine', "wit's end", atomic=True)
    r.wait_for_close()

    # -- endgame: rod to NE end, blast from SW end ----------------------
    do('sw', 'SW End', atomic=True)
    do('take rod', atomic=True)
    do('ne', 'NE End', atomic=True)
    do('drop rod', atomic=True)
    do('sw', 'SW End', atomic=True)
    do('blast', 'conquering adventurer off into the sunset', atomic=True)

    final = r.score()
    if final != 350 or not r.won:
        raise SeedFailed(f'finished but score={final} won={r.won}')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--sweep', type=int, default=None,
                    help='try seeds 1..N until one records a clean 350 win')
    ap.add_argument('--record', default=None, help='write command list here')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    seeds = [a.seed] if a.seed else list(range(1, (a.sweep or 12) + 1))
    for seed in seeds:
        try:
            r = run_route(seed, a.verbose)
        except SeedFailed as e:
            print(f'seed {seed}: FAILED [{len(e.args[0]) and e.args[0][:180]}]')
            continue
        print(f'seed {seed}: WON 350/350 in {r.turns()} turns, '
              f'{len(r.rec)} commands')
        if a.record:
            with open(a.record, 'w') as f:
                f.write('\n'.join(r.rec) + '\n')
            print('recorded ->', a.record)
        return 0
    print('no seed produced a clean win')
    return 1


if __name__ == '__main__':
    sys.exit(main())
