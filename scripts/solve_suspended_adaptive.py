#!/usr/bin/env python3
"""Suspended (r8) adaptive route harness.

Replays the verified 70-cycle route milestone-by-milestone against GameWalker
under a pinned interpreter RNG seed, waits (recording the waits) for robot
arrival interrupts before issuing dependent orders, READS the randomized
Filtering-Computer reset code off Iris's TV transmission and presses the two
matching circles, and RECORDS every command actually sent, so a winning
recording replays deterministically through scripts/replay_solve.py.

Determinism model (ZIL citations in logs/suspended_notes.md):
  * Boot draws no randomness (two boots byte-identical; GENERATE-CODES is
    NOT called at boot), so the seed is pinned right after start() and no
    `restart` prelude is needed.
  * Every disaster clock is cycle-based and fixed: acid spill at cycle 15
    (I-TREMOR1, main.zil:45 / ACID-KILLS main.zil:10), second quake at 75
    (I-TREMOR2 / RTD-KILLS main.zil:8), intruders at 100 (I-PEOPLE1 /
    PEOPLE-APPEAR main.zil:12).  Weather drifts every 5 cycles (I-WEATHER,
    robots.zil:566) and the casualty meter runs every cycle (I-SCORE,
    robots.zil:699).  Acid-exposed robots die 5 cycles after entering the
    Cavernous Room (I-ROBOTKILLER, robots.zil:799; DYING3=7, globals.zil:390).
  * The ONLY state-relevant RNG draw is GENERATE-CODES (objects.zil:1660),
    fired the first time the TV camera is taken (TV-FCN, objects.zil:790-792).
    It PICK-ONEs two of the eight code circles (FOO MUM BLE BAR KLA CON BOZ
    TRA).  Under a pinned seed the pair is fixed; this recorder reads it from
    "It says XXXYYY." (verbs.zil:1864) and presses the right two circles, so
    the recorded command list replays verbatim under the same seed.

Win = END-GAME (robots.zil:620), reached by pressing both code circles once
REDSET==REDWIRE and ORANGESET==ORANGE-WIRE (CIRCLE-FCN, objects.zil:1610-1648;
I-WIRE-MESSAGE, robots.zil:766).  The route wins in 70 cycles with 8,000
casualties, ranking 1 of 7 (best bracket: TOTAL-SCORE <= 40, robots.zil:667).

Usage:
  python3 scripts/solve_suspended_adaptive.py --seed 1 --out walkthroughs/cmds.txt
  python3 scripts/solve_suspended_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'suspended.z3')

WIN_PAT = re.compile(
    r'successfully completed your task, bringing the Filtering Computers '
    r'back into balance', re.I)
CODE_PAT = re.compile(r'It says ([A-Z]{3})([A-Z]{3})\.')
FATAL_PAT = re.compile(
    r'All systems are shutting down|no point in continuing|'
    r'yanking all of our plugs', re.I)

# A quiet, state-neutral one-cycle filler (Iris is fixed and parked in the
# Main Supply Room by the time any wait is needed).
FILLER = 'iris, look'


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
        self.log = ''           # full accumulated game output
        self.won = False
        self.code = None

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.log += '\n' + out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN_PAT.search(out):
            self.won = True
        elif FATAL_PAT.search(out):
            raise Desync(f'game over at "{cmd}": ...{out[-200:]!r}')
        m = CODE_PAT.search(out)
        if m:
            self.code = (m.group(1), m.group(2))
        return out

    def wait_for(self, pattern, cap=15):
        """If pattern hasn't already appeared anywhere in the transcript
        (every awaited interrupt is a unique one-time quip), burn recorded
        filler cycles until it does."""
        rx = re.compile(pattern, re.I)
        if rx.search(self.log):
            return
        for _ in range(cap):
            self.send(FILLER)
            if rx.search(self.log):
                return
        raise Desync(f'never saw /{pattern}/ within {cap} filler cycles')


# ---------------------------------------------------------------------------
# The route.  Steps are either ('cmd', <command>) or ('wait', <regex>).
# Commands are issued in this exact order; 'wait' burns recorded filler
# cycles only if the awaited interrupt has not already been printed.  The
# whole schedule is cycle-deterministic (see module docstring), so under any
# seed the same list of commands is emitted; only the two circle presses
# differ (chosen from the transmitted code).
# ---------------------------------------------------------------------------
PLAN = [
    # --- dispatch (cycles 1-9): weather fix, wedge, Whiz pre-positions past
    #     the (not yet acid-flooded) Cavernous Room into the Secondary
    #     Channel, Auda heads for Gamma Repair.
    ('cmd', 'poet, go to weather control'),
    ('cmd', 'sensa, go to sub supply room'),
    ('cmd', 'whiz, go to secondary channel'),
    ('wait', r'I am at the Sub Supply Room'),
    ('cmd', 'sensa, take ramp'),
    ('cmd', 'sensa, go west'),
    ('cmd', 'sensa, take container and grasper'),
    ('cmd', 'sensa, go to hallway junction'),
    ('cmd', 'waldo, go to hallway junction'),
    ('cmd', 'auda, go to gamma repair'),
    ('wait', r"here at the Weather Control Area"),
    # --- weather: dial 2 to 100 counters the pressure-2 DECAY drain
    #     (I-WEATHER/I-DECAY, robots.zil:566-589) so WINDS stay low.
    ('cmd', 'poet, turn second dial to 100'),
    ('cmd', 'poet, go to hallway end'),
    ('cmd', 'iris, go to main supply room'),
    ('wait', r'I am at the Hallway Junction'),
    ('cmd', 'sensa, put ramp at dropoff'),   # WEDGE-PLACED=2 opens the
                                             # Junction<->Sloping-Corridor step
    ('cmd', 'auda, listen'),
    ('wait', r'arrival at the Hallway Junction'),
    ('cmd', 'waldo, take container and grasper'),
    ('cmd', 'waldo, go to main supply'),
    ('cmd', 'waldo, install grasper'),
    ('cmd', 'waldo, take red ic and yellow ic'),
    ('cmd', 'sensa, go north'),
    ('cmd', 'sensa, take ramp'),
    ('cmd', 'sensa, go to small supply'),
    # --- fix Iris (needs Waldo + microsurgery grasper + blue RX1 "rough
    #     object" swapped for the fried CX1 "rough device"; PANEL-FCN,
    #     objects.zil:65-108).
    ('wait', r'arrival at the Main Supply Room'),
    ('cmd', 'waldo, open panel'),
    ('cmd', 'waldo, replace rough device with rough object'),
    ('cmd', 'waldo, close panel'),
    # --- Poet fetches the TV camera (BIO-LAB); first TAKE of the TV rolls
    #     GENERATE-CODES on the pinned RNG stream.
    ('wait', r"here at the Hallway End"),
    ('cmd', 'poet, get in car'),
    ('cmd', 'poet, get out of car'),
    ('cmd', 'poet, go to biology lab'),
    ('cmd', 'waldo, take burned chip and fried chip'),
    ('wait', r"here at the Biological Laboratory"),
    ('cmd', 'poet, take camera'),
    # --- Sensa: wire cutter off the Small Supply top shelf (needs the wedge).
    ('wait', r'I am at the Small Supply Room'),
    ('cmd', 'sensa, put ramp at holder'),
    ('cmd', 'sensa, get on ramp'),
    ('cmd', 'sensa, take cutter'),
    ('cmd', 'sensa, get off ramp'),
    ('cmd', 'sensa, take ramp'),
    ('cmd', 'sensa, go to sloping corridor'),
    ('cmd', 'poet, go to vehicle debarkation'),
    # --- machine chips: red RX0 IC -> red socket, yellow RX2 IC -> yellow
    #     socket (ORANGE-BUTTON-FCN, objects.zil:1429).
    ('cmd', 'waldo, put red ic in red socket'),
    ('cmd', 'waldo, put yellow ic in yellow socket'),
    ('wait', r"here at the Vehicle Debarkation Area"),
    ('cmd', 'poet, get in car'),
    ('cmd', 'poet, get out of car'),
    # --- Poet's kamikaze run: through the acid-flooded Cavernous Room to the
    #     Primary Channel (5 cycles of life after exposure).
    ('cmd', 'poet, go to primary channel'),
    ('wait', r'I am at the Sloping Corridor'),
    ('cmd', 'sensa, put ramp at dropoff'),
    ('cmd', 'sensa, go to gamma repair'),
    # --- open the machine, pull the FUSE FIRST (touching the fourteen-inch
    #     orange wire with the fuse in is fatal: ORANGE-WIRE-FCN,
    #     objects.zil:1465-1473), then Waldo's kamikaze cable run.
    ('cmd', 'waldo, push button'),
    ('cmd', 'iris, take fuse'),
    ('cmd', 'waldo, take cable'),
    ('cmd', 'waldo, go to secondary channel'),
    ('cmd', 'iris, go to middle supply'),
    ('cmd', 'iris, take cable'),
    ('cmd', 'iris, go to main supply'),
    # --- Sensa at Gamma Repair: flowswitch opens FRED's cabinet, two robots
    #     shift FRED (TWOBOTS-FCN, robots.zil:458), cut out the twelve-inch
    #     red wire.
    ('wait', r'I am at the Gamma Repair'),
    ('cmd', 'sensa, examine cabinet'),
    ('cmd', 'sensa, turn flowswitch'),
    ('cmd', 'both sensa and auda, move fred'),
    ('cmd', 'sensa, cut cable with cutter'),
    # --- Poet arrived dying; plug the TV and shoot the reset-code sign on
    #     his last two cycles.  Iris (fixed) receives "It says XXXYYY."
    ('wait', r"here at the Primary Channel"),
    ('cmd', 'poet, plug tv1 in'),
    ('cmd', 'poet, aim tv1 at sign'),
    # --- Sensa hauls the twelve-inch wire to the Primary Channel (her own
    #     kamikaze run); Iris restores the machine (spare sixteen-inch cable
    #     in, fuse back in -- circles are dead without the fuse,
    #     CIRCLE-FCN objects.zil:1612).
    ('cmd', 'sensa, take cable'),
    ('cmd', 'sensa, go to primary channel'),
    ('cmd', 'iris, put cable in machine'),
    ('cmd', 'iris, put fuse in machine'),
    # --- Whiz was pre-positioned in the Secondary Channel; Waldo's corpse
    #     (and the fourteen-inch cable) landed there on cycle 60.
    ('wait', r'WALDO INTERRUPT: SYSTEM FAILURE'),
    ('cmd', 'whiz, take fourteen-inch cable'),
    ('cmd', 'whiz, replace nine-inch cable with fourteen-inch cable'),
    ('cmd', 'auda, go to sleep chamber'),
    # --- wait out Sensa's walk, swap the Primary Channel cable, then key in
    #     the transmitted code.
    ('wait', r'I am at the Primary Channel'),
    ('cmd', 'sensa, replace four-inch cable with twelve-inch cable'),
    ('wait', r'Reset codes may be entered now'),
    ('code', None),                       # press the two code circles
]

MUST_SEE = [
    (r'The second dial has been set to 100', 'weather dial'),
    (r'You never looked so good', 'iris fixed'),
    (r'front panel has popped open|panel popped open', 'machine opened'),
    (r'It says [A-Z]{6}\.', 'code transmitted'),
    (r'Reset codes may be entered now', 'FCs balanced'),
    (r'First access code accepted', 'code digit 1'),
]


def run_route(seed, verbose=False, upto=None):
    r = Runner(seed, verbose)
    for kind, arg in PLAN:
        if kind == 'cmd':
            r.send(arg)
        elif kind == 'wait':
            r.wait_for(arg)
        elif kind == 'code':
            if not r.code:
                raise Desync('reset code was never transmitted')
            r.send(f'iris, press {r.code[0].lower()} circle')
            if not r.won:
                r.send(f'iris, press {r.code[1].lower()} circle')
        if upto and upto in (arg or ''):
            break
    for pat, name in MUST_SEE:
        if not re.search(pat, r.log):
            raise Desync(f'milestone missing: {name} (/{pat}/)')
    if not r.won:
        raise Desync('no END-GAME banner seen')
    m = re.search(r'Current surface casualties: ([\d,]+).*?'
                  r'ranking was (\d).*?in (\d+) cycles', r.log, re.S)
    r.stats = m.groups() if m else ('?', '?', '?')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-8')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--upto', help='stop after the step containing this text')
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
        cas, rank, cyc = r.stats
        print(f'seed {seed}: WIN in {len(r.commands)} commands, {cyc} cycles, '
              f'{cas} casualties, ranking {rank}/7, '
              f'code {"".join(r.code)}')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Suspended recorded adaptive solve, seed {seed}\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds won')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
