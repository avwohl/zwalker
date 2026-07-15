#!/usr/bin/env python3
"""Wearing the Claw (Release 3, serial 970327) adaptive route harness.

Replays the verified route milestone-by-milestone against GameWalker under a
pinned interpreter RNG seed, asserts a distinctive line of text after each
milestone (cheap desync tripwires), and RECORDS every command actually sent,
so a winning recording replays deterministically through
scripts/replay_solve.py.

Determinism model (see logs/wearing_the_claw_notes.md):
  * Wearing the Claw is a scoreless, deterministic puzzle game: no SCORE verb,
    no timers, no combat, no wandering NPCs.  The only randomness is flavor
    text (a fearful child on the beach, crying gulls, breeze lulls, the "black
    fly" stings by the river).  None of it gates a puzzle, so with an identical
    command list every seed reaches the same ending -- but the flavor RNG means
    exact TEXT only reproduces under a pinned seed, hence the pin (seed 1).
  * Boot draws no randomness (two boots are byte-identical), so the seed is
    pinned right after start().  The very first recorded command, `enter`,
    satisfies the title screen's press-SPACE read_char AND flushes the whole
    prologue, landing at Dirt Road.  There is only ONE intro keypress.

Because nothing here is genuinely adaptive, this harness is a faithful,
tripwire-checked recorder rather than a search: it plays the fixed route,
verifies each milestone's landmark text, and emits the command list.  The win
is declared by the WIN_TEXT phrase (the game is scoreless).

Usage:
  python3 scripts/solve_wearing_the_claw_adaptive.py --seed 1 \
      --out walkthroughs/cmds.txt
  python3 scripts/solve_wearing_the_claw_adaptive.py --seeds 1-4
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'wearing_the_claw.z5')

WIN_PAT = re.compile(r'save another foolish wizard', re.I)
DEATH_PAT = re.compile(r'\*\*\*\s+You have (died|failed)\s+\*\*\*', re.I)


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)          # pin RNG AFTER start()
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.last = ''
        self.won = False

    def send(self, cmd, allow_death=False):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN_PAT.search(out):
            self.won = True
        if DEATH_PAT.search(out) and not allow_death:
            raise Desync(f'died/failed at "{cmd}": ...{out[-160:]!r}')
        return out


# The verified route, split into milestones: (name, [commands], must_see_regex
# or None).  Commands are exactly the seed-1 recording, INCLUDING flavor
# examines, because they mirror David Welbourn's Release-3 walkthrough and keep
# the transcript faithful.  The must_see regex is a landmark that has to appear
# somewhere in that milestone's combined output.
SEGMENTS = [
    ('boot-prologue', ['enter'], r'dirt road|assailing your face'),
    ('dirt-road', ['x me', 'i', 'remove pack', 'x it', 'open it',
                   'x parchment', 'x handkerchief', 'x gold', 'x topaz',
                   'x town', 'x mountains', 'w'], r'Outskirts of Village'),
    ('to-town', ['x buildings', 'w', 'x garments', 'x alehouse', 'w', 'n',
                 's', 'w', 'x shop', 's', 'x desk', 'x bell', 'ring bell',
                 'n', 'w'], r'End of the Road'),
    ('shed-meet', ['x sand', 'x waves', 'n', 'x man', 'ask man about ships',
                   'x paw'], r'cringes with fear'),
    ('beach-loop', ['s', 'nw', 'x island', 'x bushes', 's', 'e', 'sw',
                    'x ship', 'x sea', 'w', 'ne', 's', 'x pebbles', 'e',
                    'nw', 'e', 'e', 'e', 'n'],
     r"Goodman's Used Clothing Emporium"),
    ('buy-glove', ['x clothes', 'x box', 'x table', 'x glove', 'buy glove',
                   'wear glove', 'take handkerchief', 'tie glove to paw'],
     r'tie the glove to your paw'),
    ('quiz-clerk', ['x clerk', 'ask clerk about glove', 'ask clerk about town',
                    'ask clerk about alehouse', 'ask clerk about shop',
                    'ask clerk about boarding house',
                    'ask clerk about old bill', 'ask clerk about ship',
                    'ask clerk about goergs'], r'powerful magicians'),
    ('buy-contract', ['s', 'w', 'w', 'w', 'n', 'ask man about ship',
                      'buy contract', 'x contract'], r'Paid in full'),
    ('sail-island', ['s', 'sw', 'w', 'x sea', 'w'], r'Southeast Corner'),
    ('island-plaque-coat', ['x wall', 'read plaque', 'take plaque', 'x sand',
                            'w', 'take coat', 'x it', 'x crag', 'n',
                            'climb wall', 'e'], r'Clearing'),
    ('ring-to-clearing', ['x silver wall', 'e', 'w', 'n', 'x pebbles',
                          'x waves', 's'], r'silver wall'),
    ('open-silver-wall', ['touch silver wall', 'wear coat',
                          'touch silver wall', 's'], r'North of River'),
    ('stow-cross-river', ['read sign', 'remove coat', 'put coat in pack',
                          'close pack', 'x river', 'x shapes', 's', 's'],
     r'South of River'),
    ('past-cerberus', ['x dog', 'pet dog', 'open pack', 'wear coat', 's'],
     r'Before the Barrier'),
    ('through-barrier', ['x water', 'remove coat', 'put coat in pack',
                         'close pack', 's', 's', 's'], r'Hall of the Goergs'),
    ('get-pendant', ['x clea', 'look in crystal', 'again', 'again',
                     'ask clea about midel', 'ask clea about marnian',
                     'ask clea about crystal', 'ask clea about curse',
                     'ask clea about pendant', 'ask clea about goergs',
                     'ask clea about magic', 'ask clea about illusion',
                     'give crystal to clea', 'x pendant', 'look',
                     'x northwest door', 'x northeast door', 'x throne',
                     'x dog', 'x basins'], r'You keep that'),
    ('return-yeyos', ['n', 'x drain', 'n', 'n', 'e', 's', 'x plaque',
                      'yeyos'], r'word of returning'),
    ('endgame', ['remove pendant', 'give pendant to marnian', 'open pack',
                 'wear coat', 'enter cage', 'remove coat'],
     r'stepped into the cage just in time'),
    ('the-win', ['give coat to marnian'], r'save another foolish wizard'),
]


def run_route(seed, verbose=False, upto=None):
    r = Runner(seed, verbose)
    for name, cmds, must in SEGMENTS:
        seen = []
        for c in cmds:
            r.send(c, allow_death=(name == 'the-win'))
            seen.append(r.last)
        blob = '\n'.join(seen)
        if must is not None and not re.search(must, blob, re.I):
            raise Desync(f'{name}: expected /{must}/ missing')
        if verbose or upto:
            print(f'*** {name}: cmds={len(r.commands)}')
        if upto == name:
            raise SystemExit(0)
    if not r.won:
        raise Desync('no winning phrase seen')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-8')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--upto', help='stop after this milestone')
    a = ap.parse_args()
    seeds = ([a.seed] if a.seed is not None else
             range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[1]) + 1))
    wins = total = 0
    for seed in seeds:
        total += 1
        try:
            r = run_route(seed, a.verbose, a.upto)
        except Desync as e:
            print(f'seed {seed}: DESYNC: {e}')
            continue
        print(f'seed {seed}: WIN (scoreless) in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Wearing the Claw recorded adaptive solve, '
                        f'seed {seed}\n')
                f.write('#% WIN_TEXT: save another foolish wizard\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached the winning ending')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
