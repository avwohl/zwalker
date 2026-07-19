#!/usr/bin/env python3
"""Generic adaptive route re-derivation for zorkie source builds.

When a zorkie build of a game is behaviorally correct but its RNG stream differs
from the official binary's, the official verified walkthrough stalls (a fight
takes one more blow, a random drift needs another wait). This harness replays a
route in which the RNG-sensitive spots are written as @-steps, retries each one
until its success condition holds, searches seeds, and RECORDS the exact command
stream that won -- which then replays deterministically through replay_solve.

Generalized from scripts/solve_zork1_zorkie_adaptive.py (which produced the
zork1 350/350 recording) and the zork2 equivalent.

@-step syntax in a route file (one per line; '#' lines are comments):

    @repeat <until-substring> | <command>            send until output matches
    @repeat-max<N> <until> | <command>               ... with an explicit cap
    @until <substring> | <probe-cmd> | <filler-cmd>  probe; filler until match
    @try <substring> | <cmd> | <filler>              alias of @until

Examples:
    @repeat breathes his last | kill troll with sword
    @until perfect health | diagnose | wait
    @repeat taken | take buoy

Usage:
    python3 scripts/rederive_route.py GAME.z3 route.txt --seeds 1-24 \
            --max-score 400 --win-text "rank of Master" --out recording.txt
    python3 scripts/rederive_route.py GAME.z3 route.txt --seed 3 --verbose
"""
import argparse
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from zwalker.walker import GameWalker  # noqa: E402

# Player-death texts (the enemy-death phrases are deliberately excluded).
DEATH = (
    'you have died', 'you are dead', "you're dead", 'removes your head',
    'you have been killed', 'lurking grue', 'smothering you', 'booooooom',
    'fills your lungs', 'deserve another chance', 'long way to fall',
    'your disrespect', 'is suicide painless', 'too much for you',
    'collapse from extreme', 'have passed away', '*** you have',
)
# Enemy-death / villain-defeat texts: NOT a player death.
NOT_DEATH = ('breathes his last', 'black fog', 'he dies', 'slumps to the floor')


class Died(Exception):
    pass


class Runner:
    def __init__(self, game, seed, verbose=False):
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
            print(f"[{len(self.sent):4}] {cmd!r} -> {out.strip()[:70]!r}")
        if any(d in low for d in DEATH) and not any(e in low for e in NOT_DEATH):
            raise Died(f"died at cmd {len(self.sent)} {cmd!r}: {out.strip()[:90]}")
        return out

    def step(self, line):
        m = re.match(r'@repeat(?:-max(\d+))?\s+(.*?)\s*\|\s*(.*)$', line)
        if m:
            cap = int(m.group(1) or 25)
            want, cmd = m.group(2).lower(), m.group(3)
            for _ in range(cap):
                if want in self.send(cmd).lower():
                    return
            raise Died(f'@repeat never matched {want!r} in {cap} tries')
        m = re.match(r'@(?:until|try)\s+(.*?)\s*\|\s*(.*?)\s*\|\s*(.*)$', line)
        if m:
            want, probe, filler = m.group(1).lower(), m.group(2), m.group(3)
            for _ in range(40):
                if want in self.send(probe).lower():
                    return
                self.send(filler)
            raise Died(f'@until never matched {want!r} in 40 probes')
        if line.startswith('@'):
            raise ValueError(f'unknown @-step: {line}')
        self.send(line)


def load_route(path):
    out = []
    for line in open(path):
        line = line.strip()
        if line and not line.startswith('#'):
            out.append(line)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('game')
    ap.add_argument('route')
    ap.add_argument('--seed', type=int)
    ap.add_argument('--seeds', default='1-24')
    ap.add_argument('--max-score', type=int)
    ap.add_argument('--win-text')
    ap.add_argument('--out')
    ap.add_argument('--verbose', action='store_true')
    a = ap.parse_args()

    lo, hi = (a.seed, a.seed) if a.seed else (
        int(a.seeds.split('-')[0]), int(a.seeds.split('-')[-1]))
    route = load_route(a.route)
    win_rx = re.compile(a.win_text, re.I | re.S) if a.win_text else None

    best = None
    for seed in range(lo, hi + 1):
        r = Runner(a.game, seed, a.verbose)
        try:
            for line in route:
                r.step(line)
            status = 'completed'
        except Died as e:
            status = f'DIED: {e}'
        except Exception as e:  # noqa: BLE001
            status = f'FAULT: {type(e).__name__}: {e}'
        sc = r.score()
        won = ((a.max_score is None or sc == a.max_score)
               and status == 'completed'
               and (win_rx is None or win_rx.search(r.last)))
        print(f"seed {seed}: {status} | score {sc}"
              + (f"/{a.max_score}" if a.max_score else "")
              + f" | {len(r.sent)} cmds"
              + (" | WIN" if won else ""))
        if best is None or sc > best[1]:
            best = (seed, sc, r)
        if won:
            if a.out:
                with open(a.out, 'w') as f:
                    if a.max_score:
                        f.write(f"#% MAX_SCORE: {a.max_score}\n")
                    if a.win_text:
                        f.write(f"#% WIN_TEXT: {a.win_text}\n")
                    f.write(f"# Recorded by scripts/rederive_route.py from {a.route}\n"
                            f"# at interpreter RNG seed {seed}; {len(r.sent)} commands.\n"
                            f"# Replays deterministically (every adaptive retry baked in).\n")
                    f.write('\n'.join(r.sent) + '\n')
                print(f"WROTE {a.out} ({len(r.sent)} cmds, seed {seed})")
            return 0
    if best:
        print(f"no win; best seed {best[0]} score {best[1]}, last output: "
              f"{best[2].last.strip()[:120]!r}")
    return 1


if __name__ == '__main__':
    sys.exit(main())
