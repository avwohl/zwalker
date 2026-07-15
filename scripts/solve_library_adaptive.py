#!/usr/bin/env python3
"""All Quiet on the Library Front (Release 2 / serial 951204) adaptive route
harness.

The game is a small, fully deterministic Inform-5 vignette: reach the library's
Rare Books Room, take the Graham Nelson biography, and smuggle it past the
circulation attendant and security gates before the 5:00 pm closing time. There
is NO combat and NO randomness in the state that matters (the clock is a plain
turn counter, one tick per command), so the same command list wins under every
interpreter seed. The "adaptive" work here is therefore just tripwire
verification: replay the fixed route milestone-by-milestone against GameWalker,
assert the game's own SCORE/FULL total and a distinctive text line after each
milestone, and RECORD every command actually sent so the recording replays
deterministically through scripts/replay_solve.py.

Score model (this is a clock/status-line game: the status line prints the TIME,
not the score, so zwalker's ZMachine.get_score() reads the wrong global and
returns garbage -- 0/1 -- for this game; I must NOT patch zwalker, so the route
verifies via the game's own SCORE/FULL text and, at replay time, via a WIN_TEXT
directive rather than a MAX_SCORE directive). In-game point ladder (max 30,
confirmed by the FULL command):
    key 5; red herring 1; herring->grue 2; Nelson bio 5; novel 5; tech leaves 2
    (this is also what disables the security gates); printout 5; printout->
    librarian 2; xyzzy 1; novel->attendant 2  ==>  30/30.

Boot quirk: the title screen ("ALL QUIET ON THE LIBRARY FRONT / [Please press
SPACE to begin.]") is a read_char prompt, so the FIRST recorded command must be
a keypress; we send the literal word 'enter' (the harness maps it to RETURN) to
get past it into the Lobby. Boot draws no randomness (two boots are byte-
identical), so no restart prelude is needed; the seed is pinned after start().

Usage:
  python3 scripts/solve_library_adaptive.py --seed 1 --out walkthroughs/library_verified_win.txt
  python3 scripts/solve_library_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'library.z5')

WIN_PAT = re.compile(
    r'investor who loves IF, and you write a wildly successful game',
    re.I | re.S)
LOSE_PAT = re.compile(r'You have lost|\*\*\*\s*You have lost', re.I)


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)        # pin AFTER start(); boot has no RNG
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.last = ''
        self.won = False

    def game_score(self):
        """Read the TRUE score from the game's own SCORE text (not the broken
        get_score()); does not record the probe command."""
        st = self.w.vm.save_state()
        r = self.w.try_command('score')
        out = (r.output if r else '') or ''
        self.w.vm.restore_state(st)
        m = re.search(r'scored\s+(\d+)\s+out of a possible\s+(\d+)', out)
        return (int(m.group(1)), int(m.group(2))) if m else (None, None)

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()[:300]}\n')
        if WIN_PAT.search(out):
            self.won = True
        if LOSE_PAT.search(out):
            raise Desync(f'LOST at "{cmd}": ...{out[-160:]!r}')
        return out


# The verified route, split into milestones: (name, [commands], want_score or
# None, must_see_regex or None). Commands are exactly the recorded winning list.
SEGMENTS = [
    ('boot', ['enter'], 0, r'circulation desk attendant'),
    ('ask-around', ['ask attendant about nelson',
                    'ask attendant about librarian', 'w',
                    'ask librarian about nelson', 'ask librarian about rare',
                    'ask librarian about key', 'e', 'ask attendant about key'],
     0, r'give me your ID card'),
    ('get-key', ['give card to attendant'], 5, r'gives you the key'),
    ('red-herring', ['w', 'n', 'look under stairs'], 6, r'red herring'),
    ('feed-grue', ['u', 'give herring to grue'], 8, r'indescribable blackness'),
    ('take-bio', ['s', 'unlock door with key', 'open door', 's', 'take nelson'],
     13, r'Taken'),
    ('lock-up-novel', ['n', 'close door', 'lock door with key',
                       'search shelves'], 18, r'Nietzsche'),
    ('tech-and-printout', ['e', 'ask technician about gates', 'x printout'],
     25, r'Encyclopedia Frobozzica'),
    ('printout-xyzzy', ['w', 'n', 'd', 's', 'give printout to librarian',
                        'xyzzy'], 28, r'No talking in the library'),
    ('endgame', ['e', 'give novel to attendant', 'give key to attendant', 'e'],
     30, r'You have won'),
]


def run_route(seed, verbose=False, upto=None):
    r = Runner(seed, verbose)
    for name, cmds, want, must in SEGMENTS:
        seen = []
        for c in cmds:
            seen.append(r.send(c))
        blob = '\n'.join(seen)
        if must and not re.search(must, blob, re.I | re.S):
            raise Desync(f'{name}: expected /{must}/ missing')
        if want is not None and name != 'endgame':
            got, mx = r.game_score()
            if got != want:
                raise Desync(f'{name}: score {got}/{mx} != {want}')
        if verbose or upto:
            print(f'*** {name}: cmds={len(r.commands)}')
        if upto == name:
            raise SystemExit(0)
    if not r.won:
        raise Desync('no winning text seen')
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
        print(f'seed {seed}: WIN 30/30 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write('# All Quiet on the Library Front - recorded adaptive '
                        f'solve, seed {seed}\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached the winning ending')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
