#!/usr/bin/env python3
"""Adaptive route harness for the ZORKIE build of zork1 (renovated Release 0).

Plays walkthroughs/zork1_zorkie_route.txt against GameWalker under a pinned
interpreter RNG seed, adapting the RNG-sensitive spots (troll/thief melee,
heal-to-full waits, Frigid-River buoy drift) and RECORDING every command
actually sent, so a winning recording replays deterministically through
scripts/replay_solve.py. Modeled on scripts/solve_minizork_adaptive.py, which
produced the minizork 350/350 recordings for both the official binary and the
zorkie build.

The base route is the official Release-119 solve (zork1_verified_350.txt);
this build is a DIFFERENT release with its own RNG stream, so every combat
length, heal count, and river-drift timing is re-derived per seed.

Usage:
  python3 scripts/solve_zork1_zorkie_adaptive.py --seeds 1-24 \
          --out walkthroughs/zork1_zorkie_350.txt
  python3 scripts/solve_zork1_zorkie_adaptive.py --seed 3 --verbose
"""
import argparse
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.expanduser('~/src/zorkie/builds/zork1_zorkie.z3')
ROUTE_FILE = os.path.join(REPO, 'walkthroughs', 'zork1_zorkie_route.txt')
MAX_SCORE = 350

# Enemy (troll/thief) death -- the VILLAIN-RESULT text; NOT a player death.
DEAD_ENEMY = ('breathes his last', 'black fog')
# Player death -- JIGS-UP texts.
DEATH = ('you have died', 'removes your head', 'you have been killed',
         'lurking grue', 'smothering you', 'fills your lungs',
         'deserve another chance', 'long way to fall', 'is suicide painless',
         'too much for you', 'you are dead')


class Died(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False, game=GAME):
        self.walker = GameWalker(open(game, 'rb').read())
        self.walker.vm.rng.seed(seed)
        self.walker.start()
        self.seed = seed
        self.verbose = verbose
        self.sent = []
        self.last = ''

    def score(self):
        m = self.walker.vm.memory
        gtab = (m[0x0C] << 8) | m[0x0D]
        v = (m[gtab + 2] << 8) | m[gtab + 3]
        return v - 0x10000 if v & 0x8000 else v

    def send(self, cmd):
        out = self.walker.try_command(cmd, skip_if_tried=False).output
        self.sent.append(cmd)
        self.last = out
        low = out.lower()
        if self.verbose:
            print(f"[{len(self.sent):3}] {cmd!r} -> {out.strip()[:70]!r}")
        if any(d in low for d in DEATH) and not any(e in low for e in DEAD_ENEMY):
            raise Died(f"player died at cmd {len(self.sent)} {cmd!r}: {out.strip()[:80]}")
        return out

    def step(self, cmd):
        if cmd == '@killtroll':
            for _ in range(16):
                low = self.send('kill troll with sword').lower()
                if any(m in low for m in DEAD_ENEMY) or "can't see any troll" in low:
                    return
            raise Died('troll would not die in 16 blows')
        if cmd == '@killthief':
            for _ in range(25):
                low = self.send('kill thief with knife').lower()
                if any(m in low for m in DEAD_ENEMY) or "can't see any thief" in low:
                    return
            raise Died('thief would not die in 25 blows')
        if cmd == '@heal':
            for _ in range(40):
                if 'perfect health' in self.send('diagnose').lower():
                    return
                self.send('wait')
            raise Died('never reached perfect health')
        if cmd == '@buoy':
            for _ in range(20):
                low = self.send('take buoy').lower()
                if 'taken' in low or 'feel' in low:
                    return
                self.send('wait')
            raise Died('never grabbed the buoy on the river')
        self.send(cmd)


def load_route():
    cmds = []
    for line in open(ROUTE_FILE):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        cmds.append(line)
    return cmds


def run_route(seed, verbose=False, game=GAME):
    r = Runner(seed, verbose, game)
    for cmd in load_route():
        r.step(cmd)
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--seed', type=int)
    ap.add_argument('--seeds', default='1-24', help='range like 1-24')
    ap.add_argument('--game', default=GAME)
    ap.add_argument('--out')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    seeds = [a.seed] if a.seed else list(
        range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[-1]) + 1))

    for seed in seeds:
        try:
            r = run_route(seed, a.verbose, a.game)
        except Died as e:
            print(f"seed {seed}: DIED -- {e}")
            continue
        except Exception as e:  # noqa: BLE001
            print(f"seed {seed}: FAULT -- {type(e).__name__}: {e}")
            continue
        sc = r.score()
        print(f"seed {seed}: finished route, score {sc}/{MAX_SCORE}, "
              f"{len(r.sent)} cmds, final output: {r.last.strip()[:90]!r}")
        if sc == MAX_SCORE:
            if a.out:
                with open(a.out, 'w') as f:
                    f.write(f"#% MAX_SCORE: {MAX_SCORE}\n")
                    f.write("#% WIN_TEXT: rank of Master Adventurer\n")
                    f.write(f"# ZORK 1 compiled FROM SOURCE by zorkie (renovated Release 0)\n"
                            f"# -- complete solve recorded by solve_zork1_zorkie_adaptive.py\n"
                            f"# at interpreter RNG seed {seed}; {len(r.sent)} commands.\n"
                            f"# Replays deterministically: every combat repeat, heal-wait,\n"
                            f"# and buoy retry is baked into this stream.\n")
                    for c in r.sent:
                        f.write(c + "\n")
                print(f"WROTE {a.out} ({len(r.sent)} cmds, seed {seed})")
            return 0
    print("no seed completed the route at full score")
    return 1


if __name__ == '__main__':
    sys.exit(main())
