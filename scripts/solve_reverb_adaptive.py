#!/usr/bin/env python3
"""Reverberations ("Reverb", R1 / serial 990110) adaptive route harness.

Reverberations by Russell Glasser (IF Comp 1996; this is the 1998 revised
release) is a short, plot-driven Inform V5 game with a maximum score of 50.
It is effectively deterministic:

  * Boot draws no randomness -- two boots are byte-identical, so the seed is
    pinned right after start() and no `restart` prelude is needed.
  * Every hazard is a turn-based scripted event (the henchman who kills you if
    you dawdle in the Mayor's office, the thug in the cosmetics department who
    gets back up the turn after you kick him, Jill appearing 2 turns after you
    kick the second-storey window, the earthquake opening a crack in the
    Mayor's-office floor 2 turns after you grab the fire axe). With an identical
    command list every seed lines these up identically -- verified: this exact
    72-command list wins 50/50 on all of seeds 1..24.

SCORE READING QUIRK: the interpreter's get_score() reads Z-machine global 17,
which in this Inform build is NOT the score global -- it holds a constant (3)
the entire game while the real score (shown on the status line as "Score: N",
and by the game's own SCORE verb) climbs 0 -> 50. So there is no usable
get_score()/max_score signal for replay_solve; the win is declared purely by
WIN_TEXT (the "*** You Rule! The game's totally over! ***" banner). This harness
therefore reads the true score by parsing the status-line "Score: N" that the
game bakes into every turn's output, purely as an internal tripwire.

The route (12 scoring actions summing to exactly 50):
  search pizza -> file        [+2 -> 2]   Courthouse
  show file to D.A.           [+5 -> 7]   Courthouse  (Guido jailed)
  get file (mayor's cabinet)  [+3 -> 10]  Mayor's Office
  jump out window             [+5 -> 15]  -> Hangin' Out
  jump (into Jill's arms)     [+5 -> 20]  -> Law Office
  put bomb in sewer           [+5 -> 25]  Street  (triggers the earthquake)
  spray thug                  [+5 -> 30]  Cosmetics Dept
  get rope                    [+2 -> 32]  Hardware Dept
  show box to guard           [+3 -> 35]  Downtown
  jump (rope swing)           [+5 -> 40]  -> Mayor's Office (mob party)
  break glass with hammer     [+3 -> 43]  Mayor's Office (fire-axe case)
  hit floor with axe          [+7 -> 50]  WIN

Usage:
  python3 scripts/solve_reverb_adaptive.py --seed 1 --out walkthroughs/cmds.txt
  python3 scripts/solve_reverb_adaptive.py --seeds 1-24
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'reverb.z5')

WIN_PAT = re.compile(r"You Rule!\s+The game's totally over", re.I | re.S)
DEATH_PAT = re.compile(r'\*\*\*\s*You are toast\s*\*\*\*|'
                       r'RESTART, RESTORE a saved game or QUIT', re.I)
STATUS_SCORE = re.compile(r'Score:\s*(-?\d+)')


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)     # pin RNG AFTER start()
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.last = ''
        self.score = 0
        self.won = False

    def send(self, cmd, allow_win=False):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        m = STATUS_SCORE.findall(out)
        if m:
            self.score = int(m[-1])
        if self.verbose:
            print(f'> {cmd}\n{out.strip()[:200]}\n[score={self.score}]\n')
        if WIN_PAT.search(out):
            self.won = True
        elif not allow_win and DEATH_PAT.search(out):
            raise Desync(f'died/game-over at "{cmd}": ...{out.strip()[-160:]!r}')
        return out


# The verified route, split into milestones: (name, [commands],
# expected_true_score_after or None, must_see_regex or None). Commands are the
# exact seed-1 recording; every command (including the timed `wait`s) is kept,
# because turn count drives the scripted timers.
SEGMENTS = [
    ('open', ['x counter', 'read note', 'get pizza box'], 0, None),
    ('to-court', ['sw', 's', 'w', 's'], 0, r'crowded courthouse'),
    ('file', ['x district attorney', 'wait', 'open pizza box', 'search pizza'],
     2, r'confiscate a metal file'),
    ('guido-jailed', ['show file to district attorney'], 7,
     r'maximum security prison'),
    ('to-mayor', ['n', 'w', 'w', 'u', 'e', 'w', 'u', 'e'], 7, r"mayor's office"),
    ('cabinet-file', ['open window', 'unlock cabinet with key', 'open cabinet',
                      'get file'], 10, r'retrieve the file'),
    ('out-window', ['jump out window'], 15, r'three-story drop'),
    ('rescued', ['kick second window', 'wait', 'wait', 'jill, hold me', 'jump'],
     20, r'remarkably strong arms of Jill'),
    ('to-parlor', ['w', 'd', 'e', 'e', 'e', 'n'], 20, r'small pizza box'),
    ('bomb', ['get pizza box', 'open box', 'get bomb', 's', 'put bomb in sewer'],
     25, r'deposit the bomb in the sewer'),
    ('to-thug', ['e', 's', 'se'], 25, r'a thug here'),
    ('spray-thug', ['get spray', 'spray thug', 'kick thug', 'nw', 'n'], 30,
     r'right in the face'),
    ('hardware', ['s', 'sw', 'get hammer', 'get rope'], 32, r'rope and a hammer'),
    ('guard', ['ne', 'n', 'w', 'w', 'w', 'close box', 'show box to guard'], 35,
     r'grudgingly steps aside'),
    ('rope-swing', ['w', 'u', 'u', 'u', 'tie rope to rod', 'hold rope', 'jump'],
     40, r'zoom towards the window'),
    ('axe', ['break glass with hammer', 'get axe'], 43, r'smash the glass'),
    ('win', ['wait', 'wait', 'hit floor with axe'], 50, r'gigantic rift'),
]


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)
    for name, cmds, want, must in SEGMENTS:
        seen = []
        for c in cmds:
            seen.append(r.send(c, allow_win=(name == 'win')))
        blob = '\n'.join(seen)
        if must and not re.search(must, blob, re.I):
            raise Desync(f'{name}: expected /{must}/ missing')
        if want is not None and r.score != want:
            raise Desync(f'{name}: true score {r.score} != {want}')
        if verbose:
            print(f'*** {name}: score={r.score} cmds={len(r.commands)}')
    if not r.won:
        raise Desync('no winning banner seen')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-24')
    ap.add_argument('--out', help='write the recorded command list on a win')
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
        print(f'seed {seed}: WIN 50/50 in {len(r.commands)} commands')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Reverberations recorded adaptive solve, seed {seed}\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached 50/50')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
