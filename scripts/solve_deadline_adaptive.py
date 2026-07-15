#!/usr/bin/env python3
"""Deadline (r28) adaptive route recorder.

Drives GameWalker through the winning playthrough of Infocom's Deadline under a
pinned interpreter RNG seed and RECORDS every command actually sent -- including
each 'y' that answers a "Do you want to keep waiting? (Y/N)" interrupt and each
fixed filler 'look' -- so the recorded list replays deterministically through
scripts/replay_solve.py.

Deadline is a V3 "time" game: the status line is a 12-hour clock (global 17 =
hours, global 18 = minutes; clock.zil: "SCORE INDICATES HOURS / MOVES =
MINUTES"), there is no numeric score, and vm.get_max_score() is None. The
ending is decided by evidence flags, so the win is detected by WIN_TEXT.

Determinism model (ZIL citations in logs/deadline_notes.md):
  * Boot draws no randomness (two boots byte-identical), so the seed is pinned
    right after start() and no `restart` prelude is needed.
  * Every randomized delay is then fixed by the seed: Sgt Duffy's 15-30 min lab
    turnaround (DO-FINGERPRINT, actions.zil:2715), McNabb's 2-12 min "holes"
    outburst (I-G-I-G, goal.zil:509), George's GEORGE-SEARCH safe window
    (I-GEORGE-HACK-3, actions.zil:1885-1978) and the Dunbar flee/ticket timing
    (I-DUNBAR-SEQ*, actions.zil:3385-3469).

Win = the OBJECT-PAIR-F ARREST branch (actions.zil:3914-3929), reached by
arresting the Baxter+Dunbar pair after 11:40 AM with Dunbar alive and all four
evidence flags set: NOTE-READ (rub pad), LAB-REPORT held (analyze the buried
teacup fragment for LoBlo), BAXTER-PAPERS taken (George's hidden safe) and
STUB-D (show Dunbar her dropped concert ticket). Prints Klutz's letter: "a jury
convicted Mr. Baxter and Ms. Dunbar today of the murder of Mr. Robner."

Usage:
  python3 scripts/solve_deadline_adaptive.py --seed 1 --out walkthroughs/cmds.txt
  python3 scripts/solve_deadline_adaptive.py --seeds 1-4
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'deadline.z3')

KEEP_WAITING = re.compile(r'keep waiting\?\s*\(Y/N\)', re.I)
WIN = re.compile(r'convicted Mr\.\s+Baxter\s+and\s+Ms\.\s+Dunbar', re.I)
FATAL = re.compile(r'your time is up here|Ms\. Dunbar is dead|shot herself', re.I)


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)          # pin RNG AFTER start() (boot is fixed)
        self.seed = seed
        self.verbose = verbose
        self.cmds = []
        self.log = ''
        self.won = False

    def clock(self):
        return f"{self.w.vm.get_score()}:{self.w.vm.get_turns():02d}"

    def send(self, cmd):
        c0 = self.clock()
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.cmds.append(cmd)
        self.log += '\n' + out
        if WIN.search(out):
            self.won = True
        elif FATAL.search(out):
            raise Desync(f'fatal at "{cmd}" [{self.clock()}]: ...{out.strip()[-120:]!r}')
        if self.verbose:
            print(f'>>> {cmd}   [{c0} -> {self.clock()}]\n{out.strip()}\n')
        return out

    def _answer(self, out, cap=40):
        """Answer 'y' to each keep-waiting prompt raised by a wait command."""
        n = 0
        while KEEP_WAITING.search(out) and n < cap:
            out = self.send('y')
            n += 1
        return out

    def wait_until(self, t):
        return self._answer(self.send(f'wait until {t}'))

    def wait_for(self, who):
        return self._answer(self.send(f'wait for {who}'))


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)

    # 1. opening: to the library, gather NOTE-READ + calendar, out to Garden Path.
    for c in ['n', 'open door', 'n', 'n', 'e', 'u', 'u', 'w', 'w', 'w', 'w', 'n',
              'take pad', 'take pencil', 'rub pencil on pad', 'take calendar',
              'turn calendar',
              's', 'e', 'e', 'e', 'e', 'd', 'd', 'w', 's', 'open door', 's',
              'w', 'w', 'ne']:
        r.send(c)

    # 2. McNabb -> buried porcelain teacup fragment -> analyze for LoBlo.
    r.wait_until('11:00')
    r.wait_for('mcnabb')                     # McNabb arrives at the Garden Path
    for _ in range(16):                      # his "holes" outburst fires 2-12 min later
        if re.search(r'Crushed my roses', r.log):
            break
        r.send('mcnabb, hello')
    r.send('mcnabb, what is wrong')
    r.send('mcnabb, show me the holes')
    r.send('follow mcnabb')                  # -> Among the Roses
    r.send('examine holes')
    r.send('examine ground')                 # first probe usually unearths the shard
    for _ in range(12):                      # ~30%/turn to unearth it otherwise
        if re.search(r'piece of porcelain|shiny substance', r.log[-400:]):
            break
        r.send('dig around holes')
    r.send('analyze fragment for loblo')     # Sgt Duffy carries it to the lab

    # 3. to the Living Room for the will reading (noon); Duffy delivers the
    #    LAB-REPORT to you en route / during the wait.
    for c in ['n', 'w', 'se', 'e', 'open door', 'n', 'n', 'w']:
        r.send(c)
    r.wait_until('12:00')

    # 4. George/safe -> BAXTER-PAPERS. Showing the July-8 calendar makes George
    #    bolt for his room; leaving it starts his hidden-safe run. Watch from the
    #    library balcony, give him 10-15 turns at the safe (twelve fixed 'look'
    #    fillers), then press the library button to catch him with the safe OPEN.
    r.send('show calendar to george')
    for _ in range(10):
        out = r.send('follow george')
        if 'in the same place' in out.lower() or 'would you mind leaving' in out.lower():
            break
    for c in ['n', 'w', 'n', 'open balcony door', 'n']:
        r.send(c)
    for _ in range(25):
        out = r.send('look')
        if 'keep waiting' in out.lower():
            r.send('y')
        if re.search(r'rotates away from the wall', out):
            break
    else:
        raise Desync('George never moved the bookshelf')
    for _ in range(9):
        r.send('look')
    r.send('s')
    r.send('examine bookshelf')
    out = r.send('press button')
    if 'crumples to the floor' not in out.lower() and 'lying open' not in out.lower():
        raise Desync(f'wrong safe branch: {out.strip()[:100]!r}')
    r.send('examine safe')                   # reveals the stack of papers
    r.send('get papers')
    for c in ['w', 's', 'e', 'e', 'e', 'e', 'd', 'd', 'w', 'w']:   # -> Living Room
        r.send(c)

    # 5. show the LoBlo lab report to Dunbar (sets LOBLO-FLAG so the accusation
    #    bites), accuse her, intercept her flight on the front path and take the
    #    concert ticket she drops; showing it to her sets STUB-D.
    r.send('show lab report to dunbar')
    r.send('accuse dunbar')
    for c in ['e', 's', 'open door', 's']:
        r.send(c)
    r.wait_for('dunbar')
    for _ in range(15):
        if re.search(r'ticket stub falls out|floats to the ground', r.log[-500:]):
            break
        out = r.send('follow dunbar')
        if 'keep waiting' in out.lower():
            r.send('y')
    r.send('get ticket')
    r.send('read ticket')
    r.send('show ticket to dunbar')

    # 6. to the shed; wait until Baxter AND Dunbar are both present, then arrest
    #    the pair -> conviction epilogue.
    for c in ['e', 'e', 'se']:
        r.send(c)
    for _ in range(20):
        seg = r.log[-260:].lower()
        if 'baxter' in seg and 'dunbar' in seg and 'off to' not in seg:
            break
        r.wait_for('baxter')
    r.send('show ticket to baxter')
    r.send('arrest baxter and dunbar')

    if not r.won:
        raise Desync('no conviction epilogue seen after arrest')
    return r


MUST_SEE = [
    (r'impressions left by writing', 'NOTE-READ (pad rubbing)'),
    (r'The fragment did contain LoBlo', 'LAB-REPORT delivered'),
    (r'stack of papers bound together', 'BAXTER-PAPERS at open safe'),
    (r'seeing each other socially', 'STUB-D (Dunbar concert confession)'),
    (r'convicted Mr\.\s+Baxter', 'conviction epilogue'),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-1', help='range, e.g. 1-4')
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
        missing = [name for pat, name in MUST_SEE if not re.search(pat, r.log)]
        if missing:
            print(f'seed {seed}: milestones missing: {missing}')
            continue
        print(f'seed {seed}: WIN in {len(r.cmds)} commands, arrest at {r.clock()}')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Deadline recorded adaptive solve, seed {seed}\n')
                for c in r.cmds:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds won')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
