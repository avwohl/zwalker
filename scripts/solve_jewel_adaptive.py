#!/usr/bin/env python3
"""The Jewel of Knowledge (Francesco Bova, 1999, Release 2 / Serial 990710)
adaptive route recorder.

Replays the verified route segment-by-segment against GameWalker under a pinned
interpreter RNG seed, asserts the expected score after each milestone, solves the
gypsum-flower maze adaptively (each disturbed flower's sediment names the correct
exit -- "The breeze picks up ... and blows it to the <direction>!"), and RECORDS
every command actually sent, so the winning recording replays deterministically
through scripts/replay_solve.py.

Determinism model (see logs/jewel_notes.md):
  * Boot draws no randomness (two boots byte-identical), so the seed is pinned
    right after start() and no `restart` prelude is needed.  We open with
    `bypass`/`yes`, the game's own built-in intro-skip, which drops us straight
    onto the Rocky Plateau (Sixth Layer) with only the sword -- exactly the state
    the Jacob-conversation prologue leaves you in.
  * Every hazard is turn-based, not random: the Gaseous Geyser erupts on the 4th
    turn after you enter, the Black Dragon blasts acid on the 14th turn, the two
    dragons on the Divide exhaust themselves on fixed turn counts, and the river
    floats you a fixed number of turns.  With an identical command list every seed
    lines these up identically, so the maze aside there is nothing to adapt.
  * The maze exit sequence is itself fixed (NE, S, W, N, E) but we still read the
    reported direction each room so the recorder is robust to any variation.

Score plan (90 total; Key & Compass / David Welbourn breakdown, Release 2):
  pull quartz (fault line) 2; up into Fifth Layer Dropoff 4; throw book at
  outcrop 7; smell moon-salt smoke 9; Allarah's ebony key 12; enter mist (leave
  temple) 14; clean dirty floor 16; clean skeleton (bladder+crampons) 19; climb
  porous wall (Shaft Base) 21; take lockpick 23; put bladder in geyser (new
  passage) 26; expert marksman 29; break ice wall 32; take coat 34; escape the
  flower maze 36; unlock obsidian door 39; withstand acid (lye in coat) 44; kill
  dragon with sword 46; flee to Top of the Ramp 48; push boulder 51; get ring 53;
  free ride to Red Dragon (ask about red dragon) 58; ride through the gate 60;
  withstand both dragons on the Divide 70; shoot chandelier 73; float the river
  75; survive the river (remove ring) 80; touch the mirror & go home 90 -> WIN.

Usage:
  python3 scripts/solve_jewel_adaptive.py --seed 1 --out walkthroughs/jewel_verified_90.txt
  python3 scripts/solve_jewel_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'jewel.z5')

WIN_PAT = re.compile(r'\*\*\* You have won \*\*\*|'
                     r'scored 90 out of a possible 90')
DEATH_PAT = re.compile(r'\*\*\* You have died \*\*\*|'
                       r'Would you like to RESTART, RESTORE.*QUIT\?')
DIRMAP = {'northeast': 'ne', 'northwest': 'nw', 'southeast': 'se',
          'southwest': 'sw', 'north': 'n', 'south': 's', 'east': 'e',
          'west': 'w', 'up': 'u', 'down': 'd'}
BLOW_RX = re.compile(r'blows it to the (\w+)', re.I)


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)      # pin RNG AFTER start()
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.last = ''
        self.won = False

    def score(self):
        return self.w.vm.get_score()

    def send(self, cmd, allow_win=False):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()[:200]}\n')
        if WIN_PAT.search(out):
            self.won = True
        elif DEATH_PAT.search(out) and not allow_win:
            raise Desync(f'unexpected end at "{cmd}": ...{out[-160:]!r}')
        return out


# The gypsum-flower maze: five rooms, each disturbed with a DIFFERENT verb; the
# sediment names the exit.  We rotate a pool of verbs that reliably report a
# direction and follow it until we step out onto the Obsidian Door.
MAZE_VERBS = ['break', 'push', 'pull', 'squeeze', 'cut', 'touch', 'kick']


def solve_maze(r):
    used = []
    for _ in range(8):
        direction = None
        for v in MAZE_VERBS:
            if v in used:
                continue
            out = r.send(f'{v} flower')
            used.append(v)
            m = BLOW_RX.search(out)
            if m:
                direction = DIRMAP[m.group(1)]
                break
        if direction is None:
            raise Desync('maze: no flower reported a direction')
        out = r.send(direction)
        if 'Obsidian Door' in out:
            return
    raise Desync('maze: never reached the Obsidian Door')


# The verified route as ordered segments: (name, [commands], expected_score).
# Commands are exactly the seed-1 recording -- including harmless probe/examine
# turns -- because the turn-based hazards (geyser, dragon acid, river) are timed
# from room entry and every command in a timed room counts.
SEGMENTS = [
    ('intro-skip', ['bypass', 'yes'], 0),
    ('rocky-plateau', ['x body', 'take sack', 'open sack', 'x salt', 'close sack',
                       'x rocks', 'x hole', 'verbose', 'w', 'nw'], 0),
    ('fault-line', ['x minerals', 'x onyx', 'x garnet', 'x quartz', 'pull quartz',
                    'x line', 'x opal', 'u'], 2),
    ('to-dropoff', ['d', 'drop all', 'u', 'u'], 4),
    ('throw-book', ['x gaping hole', 'x outcrops', 'x insect', 'x book',
                    'throw book at outcrop', 'd', 'd'], 7),
    ('moon-salt', ['take all', 'se', 'e', 'take bug', 'take book', 'open sack',
                   'rub bug', 'light salt with bug', 'smell smoke'], 9),
    ('ebony-key', ['x allarah', 'tell allarah about jacob', 'ask allarah about jewel',
                   'ask allarah about helspeth', 'ask allarah about white dragon',
                   'ask allarah about black dragon'], 12),
    ('leave-temple', ['enter mist'], 14),
    ('clean-floor', ['w', 'w', 'w', 'x steps', 'x stalactites', 'n', 'smell',
                     'x dirt', 'x moss', 'take moss', 'clean dirt with moss'], 16),
    ('clean-skeleton', ['open trapdoor', 'd', 'x lye', 'take lye', 'u', 's', 's',
                        'x skeleton', 'search skeleton', 'pour lye on moss',
                        'clean skeleton with moss'], 19),
    ('climb-porous', ['x bladder', 'take bladder', 'read label', 'take crampons',
                      'x crampons', 'n', 'e', 'e', 'nw', 'w', 'w',
                      'x hole', 'x shaft', 'x vapor', 'wear crampons',
                      'climb porous'], 21),
    ('lockpick', ['u', 'u', 'e', 'x ariana', 'x boots', 'x bulge', 'look in boot',
                  'take lockpick'], 23),
    ('geyser-passage', ['x sash', 'x crossbow', 'take bow', 'x arrow', 'w', 'd',
                        'd', 'd', 'x porous', 'search porous', 'break porous',
                        'put bladder in hole'], 26),
    ('marksman', ['look', 'take bladder', 'w', 'x firepits', 'take pickaxe',
                  'x pickaxe', 'e', 'e', 'e', 'se', 'w', 'w', 'n', 'n',
                  'x fungi', 'x mushroom', 'shoot mushroom with bow', 'take arrow',
                  'put arrow in bow', 'shoot mushroom with bow', 'put arrow in bow',
                  'shoot mushroom with bow'], 29),
    ('break-ice', ['put arrow in bow', 's', 's', 'w', 'x glacier',
                   'break ice with pickaxe', 'g', 'g', 'g', 'g'], 32),
    ('take-coat', ['s', 'se', 'x dragon', 'x claws', 'open claws', 'take coat'], 34),
    # 'maze' is handled specially below (adaptive); expected score after == 36.
    ('to-maze', ['wear coat', 'x coat', 'x fangs', 'open mouth', 'x eyes',
                 'open eyes', 'x tail', 's', 'x treasure', 'search treasure',
                 'n', 'nw', 'n', 'e', 'e', 'e', 'e', 'ne', 'x outcroppings',
                 'x breeze', 'e'], 34),
    ('maze', None, 36),
    ('obsidian-door', ['x door', 'unlock door with key',
                       'unlock door with lockpick', 'e'], 39),
    ('withstand-acid', ['ask dragon about black dragon', 'ask dragon about white dragon',
                        'ask dragon about amylya', 'ask dragon about trinket',
                        'ask dragon about raif', 'ask dragon about red dragon',
                        'ask dragon about treasure', 'ask dragon about cousin',
                        'ask dragon about goblin', 'ask dragon for ring',
                        'ask dragon about ramp', 'ask dragon about plague',
                        'ask dragon about door', 'put lye in coat'], 44),
    ('sever-claw', ['kill dragon with sword'], 46),
    ('flee-ramp', ['se'], 48),
    ('push-boulder', ['push boulder'], 51),
    ('get-ring', ['nw', 'ask dragon for ring'], 53),
    ('free-ride', ['ask dragon about door', 'x ring', 'wear ring',
                   'ask dragon about red dragon'], 58),
    ('gate-ride', ['sit on head', 'x paper', 'x cube', 'x statue', 'x mosses',
                   'z', 'x cliff', 'z', 'x gate', 'z', 'z'], 60),
    ('both-dragons', ['w', 'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z'], 70),
    ('shoot-chandelier', ['i', 'w', 'shoot chandelier with bow'], 73),
    ('float-river', ['look', 'take ember', 'put ember in coat', 'n', 'z', 'z', 'z'], 75),
    ('survive-river', ['z', 'z', 'remove ring'], 80),
    ('to-jewel', ['x pebbles', 'x river', 'x light', 'n', 'x murals', 'n',
                  'x murals', 'n', 'x murals', 'n', 'x mirror', 'x pedestal',
                  'x jewel'], 80),
    ('win', ['touch mirror'], 90),
]


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)
    for name, cmds, want in SEGMENTS:
        if name == 'maze':
            solve_maze(r)
        else:
            for c in cmds:
                r.send(c, allow_win=(name == 'win'))
        if r.score() != want:
            raise Desync(f'{name}: score {r.score()} != expected {want}')
        if verbose:
            print(f'*** {name}: score={r.score()} cmds={len(r.commands)}')
    if not r.won:
        raise Desync('reached the end without the winning banner')
    return r


HEADER = """\
# The Jewel of Knowledge by Francesco Bova (Copyright 1999)
# (Release 2 / Serial 990710 / Inform v6.15 Library 6/7, Z-machine V5)
# VERIFIED COMPLETE SOLVE: 90/90, won=True, died=False
#
# Reproduce with the RNG-pinned replay harness (free, no API):
#   cd ~/src/zwalker
#   python3 scripts/replay_solve.py games/zcode/jewel.z5 \\
#           walkthroughs/jewel_verified_90.txt --seeds 24 --out solutions/jewel_verified.json
#   => jewel_verified_90.txt: VERIFIED 90/90 at seed 1 | ... | died=False | won=True
#
# Expected final line: "In that game you scored 90 out of a possible 90, in 247
# turns, earning you the rank of Humbled Land Owner." after "*** You have won ***".
# Winning ending: you touch the mirror in the Jewel Room and return home WITHOUT
# the jewel, lie to the Druids that no Jewel exists, and live out a quiet life --
# the transcript closes on "the lingering scent of foolish dreams."
#
# Why a pinned seed: get_max_score() returns None for this post-Infocom V5 title,
# so MAX_SCORE below carries the game's own ceiling (its SCORE verb reports "out
# of a possible 90"). The interpreter's RNG is pinned after start() so the replay
# is bit-identical; in practice the game is fully deterministic -- boot draws no
# randomness (two boots are byte-identical) and every hazard is turn-based (the
# geyser erupts on the 4th turn after entry, the Black Dragon blasts acid on the
# 14th turn, the two dragons exhaust themselves and the river floats you on fixed
# turn counts), so any seed wins; seed 1 is the recorded one.
#
# Route: skip the intro with the game's own `bypass`/`yes`; grab Jacob's sack of
# moon salt; drop the fault-line quartz; climb to refind the firebug+book by
# throwing the book at the outcrop; burn the moon salt and smell the smoke to
# visit Allarah, who gives the ebony key; leave via the mist; clean the mossy
# floor to a trapdoor, fetch lye below, clean the skeleton for the air bladder +
# crampons; time the geyser to climb the porous wall to Ariana's body (lockpick,
# crossbow); wedge the bladder in the geyser to blow the porous wall and reach the
# quarry pickaxe; master the crossbow on the mushroom; chop the ice wall; take the
# coat of many colours from the dead White Dragon; thread the gypsum-flower maze
# (NE,S,W,N,E, each flower disturbed a different way); unlock the obsidian door
# (ebony key then lockpick); put lye in the coat to survive the Black Dragon's
# acid, sever a claw, push a boulder onto him, take his ring of heat resistance
# and a free ride to the Red Dragon; on the Divide let both dragons burn
# themselves out; shoot the chandelier onto the Red Dragon; pocket embers in the
# coat; float the river, remove the ring so the coat's warmth reaches you; walk
# the Hall of the Ancients murals to the Jewel Room and TOUCH THE MIRROR (never
# take the jewel -- that is a slow poison death). 90/90.
#
#% MAX_SCORE: 90
#% WIN_TEXT: the lingering scent of foolish dreams
#
# Generated by scripts/solve_jewel_adaptive.py (RNG seed 1); replay-verified by
# scripts/replay_solve.py.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-8')
    ap.add_argument('--out', help='write the recorded walkthrough on a win')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()
    seeds = ([a.seed] if a.seed is not None else
             range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[1]) + 1))
    wins = total = 0
    for seed in seeds:
        total += 1
        try:
            r = run_route(seed, a.verbose)
        except Desync as e:
            print(f'seed {seed}: DESYNC: {e}')
            continue
        print(f'seed {seed}: WIN 90/90 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(HEADER)
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached 90/90')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
