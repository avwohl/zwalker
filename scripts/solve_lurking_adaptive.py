#!/usr/bin/env python3
"""The Lurking Horror (r221) adaptive route harness.

Replays the verified route milestone-by-milestone against GameWalker under a
pinned interpreter RNG seed, asserts the expected score/text after each
milestone, adapts where the game's one piece of state-relevant randomness can
bite (the wandering urchin, frob.zil:346-436 — every 10 turns he walks a
random open exit and ROBs any player-less room he enters), and RECORDS every
command actually sent, so a winning recording replays deterministically
through scripts/replay_solve.py.

Determinism model (see logs/lurking_notes.md for ZIL citations):
  * Boot draws no randomness (verified: two boots byte-identical), so the
    seed is pinned right after start() and no `restart` prelude is needed.
  * All clocks are turn-based (waxer 5-turn ping-pong, rats' approach,
    professor's TIED-UP? count, freeze/exhaustion timers, frob END-CNT),
    so with identical command lists every seed lines these up identically.
  * Only the urchin's walk differs between seeds. The base route meets him
    on the Infinite Corridor (seed 1); if he isn't met on schedule, the
    recovery hunts him around the corridor/basement circuit, scares him
    with the animated hand, and rejoins the route. Seeds where he robbed a
    stashed tool before we retrieve it are declared DESYNC and skipped
    (replay_solve only needs one clean seed; seed 1 is the verified one).

Score plan (5 pts each, ZIL: logs/lurking_notes.md):
  stone 5; master key 10; Ancient Storage 15; manhole 20; waxer-man in wax
  25; Top of Dome 30; suicide note 35; hand 40; flier 45; professor 50;
  animated hand 55; bolt cutter 60; Steam Tunnel 65; scalded rats 70;
  Concrete Box 75; brick wall ripped 80; urchin wire 85; curtain 90;
  frob appears 95; frob destroyed => SETG SCORE 100 (frob.zil:1598).

Usage:
  python3 scripts/solve_lurking_adaptive.py --seed 1 --out walkthroughs/cmds.txt
  python3 scripts/solve_lurking_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'lurking.z3')

DEATH_PAT = re.compile(r'\*\*\*\*\s+You have died\s+\*\*\*\*|'
                       r'\(Type RESTART, RESTORE, or QUIT\)')
WIN_PAT = re.compile(r'Your score is 100 of a possible 100')


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.last = ''
        self.won = False

    def score(self):
        return self.w.vm.get_score()

    def send(self, cmd, allow_death=False):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN_PAT.search(out):
            self.won = True
        elif DEATH_PAT.search(out) and not allow_death:
            raise Desync(f'died at "{cmd}": ...{out[-200:]!r}')
        return out

    def until(self, pattern, cmd='z', cap=12):
        """Wait (recording the waits) until pattern shows; includes the case
        where it already showed in the previous output."""
        rx = re.compile(pattern, re.I)
        if rx.search(self.last):
            return self.last
        for _ in range(cap):
            out = self.send(cmd)
            if rx.search(out):
                return out
        raise Desync(f'never saw /{pattern}/ within {cap} waits')


# ---------------------------------------------------------------------------
# The verified route, split into milestones: (name, [commands],
# expected_score_after or None). Commands are exactly the seed-1 recording —
# including a few harmless probe/no-op turns — because every turn advances
# the interleaved RNG stream and the shared turn-based clocks.
# ---------------------------------------------------------------------------
SEGMENTS = [
    ('pc-login', ['sit on chair', 'turn on pc', 'login 872325412',
                  'password uhlersoth', 'click menu', 'click paper',
                  'read paper', 'z', 'z', 'z', 'z'], None),
    ('yuggoth-stone', ['d', 'd', 'take stone', 'z', 'z', 'z'], 5),
    ('hacker-fixes', ['z', 'z', 'z', 'ask hacker about keys'], 5),
    ('microwave', ['s', 'w', 'open fridge', 'take coke and carton',
                   'open microwave', 'put carton in microwave',
                   'close microwave', 'press 5', 'press 0', 'press 0',
                   'press hi', 'press start', 'z', 'z', 'z', 'z',
                   'open microwave', 'take carton'], 5),
    ('master-key', ['e', 'n', 'give carton to hacker',
                    'hacker, give me master key', 'drop assignment'], 10),
    ('elevator-down', ['s', 'press down', 'z', 'z', 's', 'open panel',
                       'take flashlight', 'press 1', 'z', 'z', 'z',
                       'n', 'look', 'n'], 10),
    ('gloves-crowbar', ['d', 'e', 'take gloves and crowbar',
                        'wear gloves'], 10),
    ('forklift', ['w', 'w', 'enter forklift', 'turn on forklift', 'e', 'e',
                  'e', 'turn on flashlight', 'move junk with forklift',
                  'again', 'again', 'again', 'turn off forklift',
                  'get out of forklift', 'e'], 15),
    ('manhole-knife', ['open manhole with crowbar', 'd', 'n', 'd',
                       'take knife', 'u', 's', 'u', 'w', 'w',
                       'turn off flashlight', 'w', 'w', 'w', 'u', 's',
                       'take container'], 20),
    ('waxer-man', ['e', 'e', 'z', 'z', 'z', 'e', 'z', 'z', 'z', 'e',
                   'smash cabinet with crowbar', 'take axe',
                   'cut cord with axe', 'open container',
                   'pour wax on floor', 'drop container'], 25),
    ('great-dome', ['w', 'u', 'climb rope'], 30),
    ('suicide-note', ['open door', 'n', 'u', 'take plug', 'drop plug',
                      'take paper'], 35),
    ('ladder-down', ['d', 's', 'close door', 'lower ladder', 'd', 'd'], 35),
    ('brown-boots', ['e', 'e', 'n', 'd', 'se', 'take boots',
                     'wear boots'], 35),
    ('weather-dome-hand', ['u', 'u', 'unlock door with key', 'open door',
                           'w', 'u', 'dig in dirt', 'take hand'], 40),
    ('flier', ['d', 'throw stone at creature', 'e'], 45),
    ('courtyard-stone', ['d', 'd', 'u', 'out', 'take stone', 'in'], 45),
    ('professor', ['d', 'nw', 'u', 's', 's', 'knock on door', 'z', 'z',
                   'show note to professor', 's', 'z', 'z',
                   'cut line with knife', 'exit pentagram', 'move bench',
                   'open trapdoor', 'd'], 50),
    ('animate-hand', ['turn on flashlight', 'open trapdoor', 'u',
                      'put hand in vat', 'z', 'z', 'take hand',
                      'drink coke'], 55),
    ('urchin', ['n', 'open door', 'n', 'turn off flashlight', 'n', 'w', 'w',
                'w', 'w', 'show hand to urchin', 'take bolt cutter'], 60),
    ('flask-stash', ['n', 'd', 'e', 'e', 'e', 'u', 'take flask', 'd', 'w',
                     'e', 'u', 'turn on flashlight', 'take flask', 'd',
                     'turn off flashlight', 'w', 'drop flask', 'drop axe',
                     'drop bolt cutter', 'drop knife', 'drop coke'], 60),
    ('tomb-hatch', ['w', 'w', 'd', 'nw', 'unlock padlock with key',
                    'take padlock', 'open hatch', 'turn on flashlight',
                    'd'], 65),
    ('rats-valve', ['e', 'open valve with crowbar', 'z', 'z', 'z',
                    'open valve with crowbar', 'close valve'], 70),
    ('brick-pry', ['e', 'e', 'move brick with crowbar',
                   'move new brick with crowbar', 'look through hole',
                   'w', 'w', 'w', 'w', 'u', 'se', 'u',
                   'turn off flashlight', 'e', 'e', 'w', 'u', 'se', 'u',
                   'e', 'e', 'look'], 70),
    ('concrete-box', ['open doors with crowbar', 'put crowbar in doors',
                      's', 'take chain', 'put chain around rod',
                      'lock chain with padlock', 'u', 'put chain on hook',
                      'take crowbar'], 75),
    ('rip-the-rod', ['u', 'press up', 'z', 'z', 'press up', 's', 'press 2',
                     'z', 'z', 'z', 'n', 'd', 'd'], 80),
    ('final-gear', ['take axe', 'take bolt cutter', 'take flask',
                    'open doors with crowbar', 'put crowbar in doors',
                    'turn on flashlight', 's', 'n'], 80),
    ('urchin-wire', ['w', 'w', 'w', 'w', 'w', 'w', 'd',
                     'cut wire with cutter'], 85),
    ('maze-curtain', ['d', 'n', 'd', 's', 's', 'd', 'open flask',
                      'pour liquid on curtain', 'drop flask'], 90),
    ('inner-lair', ['unlock door with key', 'open door', 's'], 90),
    ('frob-appears', ['open cover', 'unplug coaxial cable', 'search pool',
                      'take line', 'cut line with axe', 'again', 'again',
                      'take line', 'put line in socket'], 95),
    ('the-kill', ['z', 'throw stone at creature', 'take stone'], 100),
]

# Segment-level text asserts: milestone -> regex that must appear somewhere
# in that segment's output (cheap desync tripwires).
MUST_SEE = {
    'yuggoth-stone': r'terminal in front of you',
    'master-key': r'He hands you the key',
    'manhole-knife': r'Taken',
    'waxer-man': r'slip and slide|begins to slip',
    'great-dome': r'heave yourself up onto the catwalk',
    'suicide-note': r'piece of paper',
    'weather-dome-hand': r'hand',
    'flier': r'creature follows it, screaming',
    'professor': r'thunderous noise, a maniacal scream',
    'animate-hand': r'newly animated',
    'urchin': r'scream of fear',
    'rats-valve': r'scalded rats charge past you',
    'concrete-box': r'looks quite secure',
    'rip-the-rod': r'tearing, rending sound',
    'urchin-wire': r'jaws cut the wire',
    'maze-curtain': r'revealing an ancient wooden door',
    'frob-appears': r'squats a being',
    'the-kill': r'Can I have my key back',
}

URCHIN_HERE = re.compile(r'\burchin\b(?! wire)', re.I)


def scare_urchin(r):
    out = r.send('show hand to urchin')
    if 'scream of fear' not in out:
        raise Desync('urchin scare failed: ' + out[-150:])
    r.send('take bolt cutter')
    return out


def hunt_urchin(r):
    """Recovery: walk a strict INF-1 -> basements -> INF-1 loop until the
    urchin is in the room, scare him with the animated hand (he drops
    EVERYTHING he has stolen, frob.zil:265-280), take the cutter, then
    finish the loop so we re-anchor at the Infinite Corridor west end."""
    circuit = ['n', 'd', 'e', 'e', 'e', 'w', 'w', 'w', 'u', 's']
    for _lap in range(6):
        for j, step in enumerate(circuit):
            if URCHIN_HERE.search(r.last) and 'saunters' not in r.last:
                out = scare_urchin(r)
                for rest in circuit[j:]:   # complete the loop to INF-1
                    r.send(rest)
                return out
            r.send(step)
    raise Desync('urchin never found on the hunt circuit')


def recover_concrete_box(r):
    """Recovery: RANDOM-ELEVATOR-MOTION (cs.zil:3460-3464, rolled with
    PROB 25 on entering the pit or Steam Tunnel East) parked the car
    somewhere other than floor 1, so the underside hook wasn't where the
    chain needs it. Call the car back to floor 1 from the Computer Center
    lobby and redo the chain work."""
    for _try in range(3):
        out = r.send('look')
        if 'Computer Center' not in out:
            r.send('u')                    # Basement -> Computer Center
        r.send('press up')
        r.until(r'elevator doors slide open', cap=10)
        r.send('d')                        # back to the Basement doors
        blob = []
        for c in ['open doors with crowbar', 'put crowbar in doors', 's',
                  'take chain', 'put chain around rod',
                  'lock chain with padlock', 'u', 'put chain on hook',
                  'take crowbar']:
            blob.append(r.send(c))
        if r.score() == 75 and re.search(r'looks quite secure',
                                         '\n'.join(blob)):
            return '\n'.join(blob)
    raise Desync('concrete-box recovery failed (elevator uncooperative)')


def run_route(seed, verbose=False, upto=None):
    r = Runner(seed, verbose)
    for name, cmds, want in SEGMENTS:
        seen = []
        if name == 'urchin':
            # Base route: walk the corridor; scare him the moment he shows,
            # then finish the walk so we re-anchor at INF-1 regardless.
            walk = cmds[:-2]
            done = 0
            for c in walk:
                r.send(c)
                seen.append(r.last)
                done += 1
                if URCHIN_HERE.search(r.last):
                    break
            if URCHIN_HERE.search(r.last):
                seen.append(scare_urchin(r))
                for c in walk[done:]:
                    r.send(c)
                    seen.append(r.last)
            if r.score() != want:
                seen.append(hunt_urchin(r))   # adaptive recovery
        else:
            for c in cmds:
                r.send(c, allow_death=(name == 'the-kill'))
                seen.append(r.last)
        blob = '\n'.join(seen)
        bad = ((name in MUST_SEE and not re.search(MUST_SEE[name], blob, re.I))
               or (want is not None and r.score() != want))
        if bad and name == 'concrete-box':
            blob = recover_concrete_box(r)       # adaptive recovery
            bad = False
        if bad:
            if name in MUST_SEE and not re.search(MUST_SEE[name], blob, re.I):
                raise Desync(f'{name}: expected /{MUST_SEE[name]}/ missing')
            raise Desync(f'{name}: score {r.score()} != {want}')
        if verbose or upto:
            print(f'*** {name}: score={r.score()} cmds={len(r.commands)}')
        if upto == name:
            raise SystemExit(0)
    if not r.won:
        raise Desync('no winning banner seen')
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
        print(f'seed {seed}: WIN 100/100 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Lurking Horror recorded adaptive solve, '
                        f'seed {seed}\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached 100/100')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
