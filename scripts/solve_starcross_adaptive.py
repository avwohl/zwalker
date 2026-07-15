#!/usr/bin/env python3
"""Starcross (r18/s830114) adaptive route harness.

Replays the verified 400/400 route milestone-by-milestone against GameWalker
under a pinned interpreter RNG seed, asserts score/text after each milestone,
adapts wherever the game is random, and RECORDS every command actually sent,
so a winning recording replays deterministically through
scripts/replay_solve.py (which uses this exact GameWalker+seed pathway).

Determinism model (ZIL citations in logs/starcross_notes.md):
  * Boot draws no randomness. The mass-detector contact is rolled by
    I-ALARM on the FIRST player turn (`<SETG MASSNUM <RANDOM 8>>`,
    actions.zil:38; queued in GO, main.zil:32) — i.e. AFTER the seed pin,
    so no `restart` prelude is needed. The recorder reads the detector
    screen at run time and computes the navigation program from the fixed
    MASS-LOCS table (dungeon.zil:186-198).
  * Live randomness the recorder adapts to: the maintenance mouse's walk
    (I-MOUSE every 2 turns, PROB 50 exit picks, 15%/tick Garage trips —
    actions.zil:955-1082), the trash-bin search (escalating PROB 25/50/75/
    100, actions.zil:1086-1119), the weasel chief (appears 3+RANDOM 3
    ticks, warren path 5+RANDOM 5 legs, actions.zil:2601/2842-2888), and
    the bad-air clock (75+RANDOM 50 turns after docking, defused by the
    oxygen repair well inside the earliest deadline).
  * Everything else is turn-based clockwork (burn at +3, five trip legs
    every 3 turns, four views every 2, tentacle grab, I-NEST 15).

Score plan (each 25 pts; SCORE-OBJ verbs.zil:196):
  Red Dock room 25; rods black 50, red 75, yellow 100, blue 125, pink 150,
  clear 175, gold 200, green 225, silver 250, brown 275, violet 300,
  white 325; Control Bubble room 350; execute (CONTROL-SCORE) 375;
  WIN-GAME +25 = 400 (actions.zil:4119-4173).

Usage:
  python3 scripts/solve_starcross_adaptive.py --seed 1 --verbose
  python3 scripts/solve_starcross_adaptive.py --seed 1 --out walkthroughs/starcross_verified_400.txt
  python3 scripts/solve_starcross_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys
from collections import deque

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'starcross.z3')

DEATH_PAT = re.compile(r'\*\*\*\*\s+You have died\s+\*\*\*\*', re.I)
WIN_PAT = re.compile(r'moves serenely toward Earth|'
                     r'Congratulations, you who have passed our test', re.I)

# Fixed contact table, MASS-LOCS dungeon.zil:186-198 (R, theta, phi).
MASS_LOCS = {
    'UM08': (150, 210, 17),  'UM12': (100, 345, 107),
    'UM24': (100, 285, 87),  'UM28': (250, 45, 178),
    'UM31': (150, 105, 67),  'UM52': (175, 165, 35),
    'UM70': (100, 135, 101), 'UM91': (50, 15, 121),
}

# Walkable interior graph (unconditional exits only) for the mouse-hunt
# pathfinding. Symbolic keys; DESC = the room name the game prints.
GRAPH = {
    # key: (desc, {dir: key})
    'RED1':  ('Red Hall', {'south': 'RED2', 'east': 'GREEN1', 'west': 'BLUE1'}),
    'RED2':  ('Red Hall', {'north': 'RED1', 'south': 'RED3', 'east': 'GREEN2', 'west': 'RING2'}),
    'RED3':  ('Red Hall', {'north': 'RED2', 'south': 'RED4', 'east': 'VNW', 'west': 'BLUE3'}),
    'RED4':  ('Red Hall', {'north': 'RED3', 'south': 'RED5', 'east': 'VSW', 'west': 'RING4'}),
    'RED5':  ('Red Hall', {'north': 'RED4', 'east': 'GREEN5', 'west': 'BLUE5'}),
    'BLUE1': ('Blue Hall', {'south': 'BLUE12', 'east': 'RED1', 'west': 'YELLOW1'}),
    'BLUE12': ('Blue Hall', {'north': 'BLUE1', 'south': 'BLUE2', 'west': 'OBS'}),
    'BLUE2': ('Blue Hall', {'north': 'BLUE12', 'south': 'BLUE3', 'east': 'RING2', 'west': 'YELLOW2'}),
    'BLUE3': ('Blue Hall', {'north': 'BLUE2', 'south': 'BLUE34', 'east': 'RED3', 'west': 'YELLOW3'}),
    'BLUE34': ('Melted Spot', {'north': 'BLUE3', 'south': 'BLUE4', 'west': 'WEAPONS'}),
    'BLUE4': ('Blue Hall', {'north': 'BLUE34', 'south': 'BLUE5', 'east': 'RING4', 'west': 'YELLOW4'}),
    'BLUE5': ('Blue Hall', {'north': 'BLUE4', 'east': 'RED5', 'west': 'YELLOW5'}),
    'YELLOW1': ('Yellow Hall', {'south': 'YELLOW2', 'east': 'BLUE1', 'west': 'RING1'}),
    'YELLOW2': ('Yellow Hall', {'north': 'YELLOW1', 'south': 'YELLOW3', 'east': 'BLUE2', 'west': 'GREEN2'}),
    'YELLOW3': ('Yellow Hall', {'north': 'YELLOW2', 'south': 'YELLOW4', 'east': 'BLUE3', 'west': 'VNE'}),
    'YELLOW4': ('Yellow Hall', {'north': 'YELLOW3', 'south': 'YELLOW45', 'east': 'BLUE4', 'west': 'VSE'}),
    'YELLOW45': ('Yellow Hall', {'north': 'YELLOW4', 'south': 'YELLOW5', 'east': 'LAB'}),
    'YELLOW5': ('Yellow Hall', {'north': 'YELLOW45', 'east': 'BLUE5', 'west': 'GREEN5'}),
    'GREEN1': ('Green Hall', {'south': 'GREEN2', 'east': 'RING1', 'west': 'RED1'}),
    'GREEN2': ('Green Hall', {'north': 'GREEN1', 'south': 'VN', 'east': 'YELLOW2', 'west': 'RED2'}),
    'GREEN5': ('Green Hall', {'north': 'VS', 'east': 'YELLOW5', 'west': 'RED5'}),
    'RING1': ('Room on Ring One', {'east': 'YELLOW1', 'west': 'GREEN1', 'south': 'CPU'}),
    'RING2': ('Room on Ring Two', {'north': 'ZOO', 'west': 'BLUE2', 'east': 'RED2'}),
    'RING4': ('Room on Ring Four', {'east': 'RED4', 'west': 'BLUE4'}),
    'ZOO':   ('Zoo', {'south': 'RING2', 'west': 'GRUE', 'east': 'NEST'}),
    'GRUE':  ('Broken Cage', {'east': 'ZOO'}),
    'NEST':  ('Nesting Cage', {'west': 'ZOO'}),
    'OBS':   ('Observatory', {'east': 'BLUE12'}),
    'CPU':   ('Computer Room', {'north': 'RING1'}),
    'WEAPONS': ('Weapons Deck', {'east': 'BLUE34'}),
    'LAB':   ('Laboratory', {'west': 'YELLOW45'}),
    'VNW':   ('Outskirts of Village', {'west': 'RED3', 'east': 'VILLAGE'}),
    'VNE':   ('Outskirts of Village', {'east': 'YELLOW3'}),
    'VSW':   ('Outskirts of Village', {'west': 'RED4', 'east': 'VSUB'}),
    'VSE':   ('Outskirts of Village', {'west': 'VSUB', 'east': 'YELLOW4'}),
    'VN':    ('Outskirts of Village', {'north': 'GREEN2'}),
    'VS':    ('Outskirts of Village', {'north': 'VSUB', 'south': 'GREEN5'}),
    'VSUB':  ('Village Suburbs', {'south': 'VS', 'east': 'VSE', 'west': 'VSW'}),
    'VILLAGE': ('Village Center', {'west': 'VNW'}),
    'GARAGE': ('Garage', {'north': 'RING4'}),
}

MOUSE_HERE = re.compile(
    r'maintenance mouse|small metal contraption|mechanical mouse', re.I)


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
        self.loc = None               # symbolic room key once inside

    def score(self):
        return self.w.vm.get_score()

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN_PAT.search(out):
            self.won = True
        if DEATH_PAT.search(out):
            raise Desync(f'died at {cmd!r}: ...{out[-200:]!r}')
        return out

    def until(self, pattern, cmd='wait', cap=15):
        rx = re.compile(pattern, re.I)
        if rx.search(self.last):
            return self.last
        for _ in range(cap):
            out = self.send(cmd)
            if rx.search(out):
                return out
        raise Desync(f'never saw /{pattern}/ within {cap} x {cmd!r}')

    def expect(self, cmd, pattern):
        out = self.send(cmd)
        if not re.search(pattern, out, re.I):
            raise Desync(f'{cmd!r}: expected /{pattern}/, got {out[-200:]!r}')
        return out

    def check_score(self, want, label):
        if self.score() != want:
            raise Desync(f'{label}: score {self.score()} != {want}')
        if self.verbose:
            print(f'*** {label}: score={want} cmds={len(self.commands)}')

    # -- symbolic movement over GRAPH ------------------------------------
    def move(self, direction, dest):
        out = self.send(direction)
        desc = GRAPH[dest][0]
        if desc not in out:
            raise Desync(f'move {direction} -> {dest}: expected {desc!r} in '
                         f'{out[-200:]!r}')
        self.loc = dest
        return out

    def path_to(self, dest):
        """BFS over GRAPH from self.loc; walk it (no adaptive checks)."""
        if self.loc == dest:
            return
        prev = {self.loc: None}
        q = deque([self.loc])
        while q:
            cur = q.popleft()
            for d, nxt in GRAPH[cur][1].items():
                if nxt not in prev:
                    prev[nxt] = (cur, d)
                    q.append(nxt)
        if dest not in prev:
            raise Desync(f'no path {self.loc} -> {dest}')
        steps = []
        cur = dest
        while prev[cur]:
            cur, d = prev[cur]
            steps.append(d)
        for d in reversed(steps):
            here = self.loc
            nxt = GRAPH[here][1][d]
            self.move(d, nxt)


# ---------------------------------------------------------------------------
# Phases
# ---------------------------------------------------------------------------

def phase_launch(r):
    """Read the (seed-rolled) contact off the detector, program the course,
    ride out burn/trip/views, survive the tentacle grab belted in."""
    r.send('stand up')
    r.expect('take tape library', 'Taken')
    r.send('east')
    r.send('push red button')            # alarm off
    out = r.expect('read screen', r'mass UM\d\d')
    mass = re.search(r'mass (UM\d\d)', out).group(1)
    rr, th, ph = MASS_LOCS[mass]
    r.send('sit on couch')
    r.expect('fasten seat belt', 'Click')
    r.send(f'computer, r is {rr}')
    r.send(f'computer, theta is {th}')
    r.expect(f'computer, phi is {ph}',
             'Sequence for intercept of mass concentration')
    r.expect('computer, confirm', 'will initiate in fifteen seconds')
    r.until(r'wraps itself around the hull', cap=35)
    if 'securely belted' not in r.last and 'slammed against your seat' not in r.last:
        raise Desync('tentacle grab without belt?')
    r.check_score(0, 'launch/dock')


def phase_red_dock(r):
    r.send('unfasten seat belt')
    r.send('stand up')
    r.send('east')                       # Storage
    r.expect('take suit', 'Taken')
    r.expect('wear suit', r'now wearing')
    r.expect('take line', 'Taken')
    r.send('west')                       # Bridge
    r.send('open inner door')
    r.send('south')                      # ship Airlock
    r.send('close inner door')
    r.expect('open outer door', 'outer door opens')
    r.expect('out', 'Red Dock')          # +25 room
    r.check_score(25, 'red dock')
    r.expect('push fourth bump', 'tiny column')
    r.expect('push tiny bump', 'rod of black crystal is extruded')
    r.expect('take black rod', 'airlock door opens')
    r.check_score(50, 'black rod')
    r.expect('up', 'Red Airlock')
    r.send('close outer door')
    r.send('open inner door')
    r.move('up', 'RED3')
    r.send('close inner door')


def phase_red_rod(r):
    r.move('north', 'RED2')
    r.move('west', 'RING2')
    r.move('north', 'ZOO')
    r.move('east', 'NEST')
    r.expect('throw tape library at nest', 'nest smashes into fragments')
    r.expect('take red rod', 'Taken')
    r.check_score(75, 'red rod')
    r.expect('take tape library', 'Taken')
    r.move('west', 'ZOO')
    r.move('south', 'RING2')
    r.move('west', 'BLUE2')
    r.move('south', 'BLUE3')


def phase_yellow_rod(r):
    r.send('open inner door')
    r.expect('down', 'Blue Airlock')
    r.send('close inner door')
    r.expect('open outer door', 'outer door opens')
    r.expect('down', 'Blue Dock')
    r.expect('south', 'Bubbles')
    r.expect('south', 'Spherical Ship')
    r.expect('give tape library to spider', 'tosses a yellow crystal rod')
    r.expect('take yellow rod', 'Taken')
    r.check_score(100, 'yellow rod')
    r.expect('north', 'Bubbles')
    r.expect('north', 'Blue Dock')
    r.expect('up', 'Blue Airlock')
    r.send('close outer door')
    r.send('open inner door')
    r.move('up', 'BLUE3')


def phase_repairs(r):
    r.expect('up', 'Grassland')
    r.expect('south', 'Thin Forest')
    r.send('open hatch')
    r.expect('down', 'Repair Room')
    r.expect('take square', 'Taken')
    r.expect('put yellow rod in yellow slot', 'disappears into the slot')
    r.expect('put red rod in second red slot', 'subdued hum of machinery')
    r.expect('up', 'Thin Forest')
    r.expect('north', 'Grassland')
    r.move('down', 'BLUE3')
    r.check_score(100, 'repairs')


def phase_blue_rod(r):
    r.move('south', 'BLUE34')
    r.move('south', 'BLUE4')
    r.move('west', 'YELLOW4')
    r.move('south', 'YELLOW45')
    r.move('east', 'LAB')
    r.expect('take red disk', 'Taken')
    r.expect('take blue disk', 'Taken')
    r.expect('drop red disk', 'inaudible click')
    r.expect('put blue disk under globe', 'slides under the globe')
    r.expect('put square on globe', 'now on the globe')
    r.expect('set dial to 4', 'blue rod must have been in range')
    r.check_score(125, 'blue rod')
    r.send('set dial to 1')
    r.expect('take blue rod', 'Taken')
    r.expect('take square', 'Taken')
    r.expect('take blue disk', 'Taken')
    r.expect('take red disk', 'Taken')


def phase_pink_rod(r):
    r.move('west', 'YELLOW45')
    r.move('north', 'YELLOW4')
    r.move('north', 'YELLOW3')
    r.send('open inner door')
    r.expect('down', 'Yellow Airlock')
    r.send('close inner door')
    # The metal basket (ROD-RACK) is the fumble-guard: more than 7 directly
    # held items risks ITAKE's fumble (verbs.zil:531-560, PROB count*8), so
    # rods ride in the basket and count as one item.
    r.expect('take basket', 'Taken')
    r.expect('put black rod in basket', 'inserted')
    r.expect('put blue rod in basket', 'inserted')
    r.expect('open outer door', 'pushed again')      # jammed once
    r.expect('open outer door', 'air rushes out')
    r.expect('down', 'Yellow Dock')
    r.expect('tie line to suit', 'Attached')
    r.expect('tie line to hook', 'Attached')
    r.expect('west', 'Among Debris')
    r.expect('take pink rod', 'Taken')
    r.check_score(150, 'pink rod')
    r.expect('put pink rod in basket', 'inserted')
    r.expect('east', 'Yellow Dock')
    r.expect('untie line from hook', 'Detached')
    r.expect('untie line from suit', 'Detached')
    r.send('drop line')                              # never needed again
    r.expect('up', 'Yellow Airlock')
    r.send('close outer door')
    r.send('open inner door')
    r.move('up', 'YELLOW3')


def phase_clear_rod(r):
    r.move('north', 'YELLOW2')
    r.move('east', 'BLUE2')
    r.move('north', 'BLUE12')
    r.move('west', 'OBS')
    r.expect('look at projector through black rod',
             'Inside the projector is a clear crystal rod')
    r.expect('take clear rod', 'Taken')
    r.check_score(175, 'clear rod')
    r.expect('put clear rod in basket', 'inserted')


def phase_gold_rod(r):
    r.move('east', 'BLUE12')
    r.move('north', 'BLUE1')
    r.move('west', 'YELLOW1')
    r.move('west', 'RING1')
    r.move('south', 'CPU')
    r.expect('open panel', 'rack upon rack of metallic cards')
    r.expect('put square in slot', 'slides snugly into the slot')
    r.expect('turn on switch', 'gold rod falls from the output hopper')
    r.expect('take gold rod', 'Taken')
    r.check_score(200, 'gold rod')
    r.expect('put gold rod in basket', 'inserted')
    r.move('north', 'RING1')


# -- green rod: the mouse ----------------------------------------------------

PATROL = ['RING1', 'YELLOW1', 'YELLOW2', 'YELLOW3', 'YELLOW4', 'YELLOW45',
          'LAB', 'YELLOW45', 'YELLOW4', 'BLUE4', 'RING4', 'RED4', 'RED3',
          'RED2', 'RING2', 'ZOO', 'RING2', 'BLUE2', 'BLUE12', 'OBS',
          'BLUE12', 'BLUE1', 'YELLOW1', 'RING1']


def mouse_present(r):
    """True when the mouse is in the CURRENT room (not just mentioned)."""
    if 'glides happily away' in r.last or 'disappears into' in r.last:
        return False
    return bool(MOUSE_HERE.search(r.last))


def find_mouse(r, cap_laps=30):
    """Walk the patrol circuit (with wait beats to break step-parity with
    the mouse's every-2-turns walk) until the mouse is in our room."""
    if mouse_present(r):
        return
    for lap in range(cap_laps):
        if r.loc not in PATROL:
            r.path_to('RING1')
            if mouse_present(r):
                return
        cur = PATROL.index(r.loc)
        for dest in PATROL[cur + 1:]:
            d = next(k for k, v in GRAPH[r.loc][1].items() if v == dest)
            r.move(d, dest)
            if mouse_present(r):
                return
        # a couple of wait beats each lap shift phase vs. the 2-turn tick
        for _ in range(2 + lap % 3):
            r.send('wait')
            if mouse_present(r):
                return
    raise Desync('mouse never found on patrol')


def ensure_take(r, obj, cap=6):
    """Take obj, pulling it back out of the mouse if it was just robbed."""
    for _ in range(cap):
        out = r.send(f'take {obj}')
        if 'Taken' in out or 'buzzes briefly' in out:
            return out
        if "can't see" in out.lower():
            # not here and not in a visible container: hope the mouse holds it
            out2 = r.send('empty mouse')
            if 'booty' in out2:
                continue
            raise Desync(f'lost the {obj}: {out[-150:]!r}')
    raise Desync(f'could not take {obj}')


def stand_teleport(r, disk, other_desc_choices, cap=40):
    """drop <disk>; stand on <disk> until the transporter fires (the other
    disk must be lying on a room floor). Protect the dropped disk from the
    mouse between attempts."""
    for _ in range(cap):
        if MOUSE_HERE.search(r.last) and 'glides happily away' not in r.last:
            r.send('wait')                  # don't feed the mouse our disk
            continue
        r.send(f'drop {disk}')
        out = r.send(f'stand on {disk}')
        if 'moment of disorientation' in out:
            for key, desc in other_desc_choices.items():
                if desc in out:
                    r.loc = key
                    return out
            raise Desync(f'teleported somewhere odd: {out[-200:]!r}')
        if 'Nothing happens' in out:
            ensure_take(r, disk)
            r.send('wait')
            continue
        if 'skitters out of the way' in out:
            r.send('empty mouse')           # it grabbed the disk we dropped
            continue
        raise Desync(f'stand on {disk}: {out[-200:]!r}')
    raise Desync('transporter never fired (other disk never on a floor)')


def phase_green_rod(r):
    find_mouse(r)
    r.send('drop red disk')
    r.until(r'picks up some refuse', cap=6)
    r.path_to('RING4')
    stand_teleport(r, 'blue disk', {'GARAGE': 'Garage'})
    ensure_take(r, 'red disk')
    for _ in range(8):
        out = r.send('search trash bin')
        if 'Ahah' in out:
            break
    else:
        raise Desync('green rod never surfaced in the trash')
    r.expect('take green rod', 'Taken')
    r.check_score(225, 'green rod')
    r.expect('put green rod in basket', 'inserted')
    r.move('north', 'RING4')
    ensure_take(r, 'blue disk')


def phase_silver_rod(r):
    r.path_to('WEAPONS')
    r.expect('drop red disk', 'inaudible click')     # escape anchor
    r.expect('take gun', 'Taken')
    r.expect('look inside gun', 'In the barrel is a silver rod')
    r.check_score(250, 'silver rod')
    r.expect('take silver rod', 'Taken')
    r.expect('put silver rod in basket', 'inserted')


def phase_brown_rod(r):
    r.path_to('RED3')
    r.move('east', 'VNW')
    r.move('east', 'VILLAGE')
    r.send('remove suit')
    r.until(r'appears a large, almost\s+all-grey alien', cap=12)
    r.expect('give suit to chief', 'removes his suit and dons yours')
    r.expect('point at brown rod', 'hands it to you')
    r.check_score(275, 'brown rod')
    # follow him through the warren (5+RANDOM 5 legs)
    leave_rx = (r'slips through an opening|enters a hovel|'
                r'slips through a crowd|leaves the room')
    for _leg in range(16):
        r.until(leave_rx, cap=8)
        out = r.send('follow chief')
        if 'Center of the Warren' in out:
            r.loc = None                      # off-graph now
            return
        if 'In the Warren' not in out:
            raise Desync(f'follow chief: {out[-200:]!r}')
    raise Desync('never reached the Center of the Warren')


def phase_violet_rod(r):
    r.until(r'points portentiously at the ladder', cap=6)
    r.send('open inner door')                 # harmless if already open
    r.expect('down', 'Green Airlock')
    r.send('close inner door')
    r.expect('open outer door', 'outer door opens')
    r.expect('down', 'Green Dock')
    r.expect('west', 'Umbilical')
    r.expect('west', 'Cargo Hold')
    r.expect('north', 'Control Room')
    r.expect('move skeleton', 'arm falls off')
    r.expect('take violet rod', 'Taken')
    r.check_score(300, 'violet rod')
    stand_teleport(r, 'blue disk',
                   {'WEAPONS': 'Weapons Deck', 'GARAGE': 'Garage'})


def phase_endgame(r):
    r.path_to('BLUE3')
    r.expect('up', 'Grassland')
    r.expect('east', 'Grassland')
    r.expect('south', 'Thin Forest')
    r.expect('south', 'Base of Tree')
    r.expect('up', 'Up a Tree')
    r.expect('up', 'Top of Tree')
    r.expect('jump', 'Drive Bubble Entrance')
    r.expect('put silver rod in silver slot', 'hatch opens')
    r.expect('in', 'Drive Bubble')
    r.expect('take white rod', 'Taken')
    r.check_score(325, 'white rod')
    r.expect('put white rod in white slot', 'walls come alive')
    r.expect('out', 'Drive Bubble Entrance')
    r.expect('up', 'On Drive Bubble')
    r.expect('jump', 'Floating in Air')
    r.expect('fire gun at drive bubble', 'Floating in Air')
    r.expect('fire gun at drive bubble', 'Floating in Air')
    r.expect('fire gun at drive bubble', 'On Control Bubble')
    r.expect('down', 'Control Bubble Entrance')
    r.expect('put gold rod in gold slot', 'hatch opens')
    r.expect('in', 'Control Bubble')
    r.check_score(350, 'control bubble')
    r.expect('put clear rod in clear slot', 'five other slots appear')
    r.expect('put pink rod in pink slot', 'ghostly image')
    r.expect('put brown rod in brown slot', 'ghostly image')
    r.expect('put violet rod in violet slot', 'ghostly image')
    r.expect('put green rod in green slot', 'ghostly image')
    r.expect('put blue rod in blue slot', 'ghostly image')
    r.expect('touch large square', 'inner solar system')
    r.send('touch brown spot')                # Sun
    r.send('touch brown spot')                # Mercury
    r.send('touch brown spot')                # Venus
    r.expect('touch brown spot', r'Earth brightly\s+highlighted')
    r.send('touch violet spot')               # center
    r.send('touch violet spot')               # parabola
    r.send('touch violet spot')               # ellipse
    r.expect('touch violet spot', r'circle around')
    r.expect('touch green spot', 'flash slowly')
    r.expect('touch blue spot', 'moves serenely toward Earth')
    r.check_score(400, 'WIN')


PHASES = [
    ('launch', phase_launch),
    ('red-dock', phase_red_dock),
    ('red-rod', phase_red_rod),
    ('yellow-rod', phase_yellow_rod),
    ('repairs', phase_repairs),
    ('blue-rod', phase_blue_rod),
    ('pink-rod', phase_pink_rod),
    ('clear-rod', phase_clear_rod),
    ('gold-rod', phase_gold_rod),
    ('green-rod', phase_green_rod),
    ('silver-rod', phase_silver_rod),
    ('brown-rod', phase_brown_rod),
    ('violet-rod', phase_violet_rod),
    ('endgame', phase_endgame),
]


def run_route(seed, verbose=False, upto=None):
    r = Runner(seed, verbose)
    for name, fn in PHASES:
        fn(r)
        if verbose or upto:
            print(f'=== {name}: score={r.score()} cmds={len(r.commands)}')
        if upto == name:
            raise SystemExit(0)
    if not r.won:
        raise Desync('no winning text seen')
    return r


HEADER = '''\
# Starcross (Infocom Release 18, serial 830114, Z-machine V3)
# VERIFIED COMPLETE SOLVE: 400/400, won=True, died=False
#
# Reproduce with the RNG-pinned replay harness (free, no API):
#   cd ~/src/zwalker
#   python3 scripts/replay_solve.py games/zcode/starcross.z3 walkthroughs/starcross_verified_400.txt --seeds 24 --out solutions/starcross_verified.json
#   => starcross_verified_400.txt: VERIFIED 400/400 at seed {seed} | {ncmds} cmds | died=False | won=True
#
# Ending: with all twelve crystal rods found and the ship computer repaired,
# the rods power up the Control Bubble console; the course is set to a
# circle around Earth at slow speed and the blue (execute) spot is pressed:
# "The artifact, under your assured control, moves serenely toward Earth...
# 'Congratulations, you who have passed our test.'" -> 400/400.
#
# Why a pinned seed (no restart prelude needed -- boot draws no randomness;
# two boots are byte-identical and the seed is pinned right after start()):
# the mass-detector contact is rolled by I-ALARM on the FIRST player turn
# (<SETG MASSNUM <RANDOM 8>>, actions.zil:38), i.e. on the pinned stream --
# under seed {seed} the contact is {mass} and the course keyed in is
# r {rr} / theta {th} / phi {ph} from the fixed MASS-LOCS table
# (dungeon.zil:186-198). The other live randomness this recording bakes in:
# the maintenance mouse's wander (I-MOUSE every 2 turns; it must carry a
# transporter disk to the Garage, 15%/tick), the trash-bin search count
# (escalating PROB 25/50/75/100), the weasel chief's appearance (3+RANDOM 3
# ticks) and warren path (5+RANDOM 5 follow legs), and the bad-air clock
# (75+RANDOM 50 turns, defused by the oxygen repair long before it can
# matter). Deaths cost -10 and the route never dies.
#
# Route: program the nav computer with the detector contact's coordinates
# and ride to the artifact belted in; Red Dock (+25) and the solar-system
# relief puzzle (press the FOURTH bump = Earth, then the tiny bump) for the
# black rod; tape library smashes the rat-ant nest (red rod), then buys the
# spider's yellow rod; Repair Room: yellow rod -> lights, red rod in SECOND
# red slot -> oxygen; Laboratory force-field/transporter-disk trick frees
# the blue rod; safety line to the hook for the pink rod in the debris;
# black rod filters the observatory projector (clear rod); card + switch
# revive the alien computer (gold rod + mandatory endgame precondition);
# a transporter disk fed to the maintenance mouse teleports us into the
# Garage (green rod in the trash bin); the ray gun holds the silver rod;
# the space suit buys the chief's brown rod and an escort to the warren
# ladder; the throne-room skeleton yields the violet rod (teleport escape);
# tree -> jump -> silver rod opens the Drive Bubble (white rod -> drive on);
# jump + three recoil shots cross the axis; gold rod opens the Control
# Bubble (+25); clear + 5 rods light the console; large square, brown x4
# (Earth), violet x4 (circle), green (slow), blue = execute (+25) and the
# winning ending (+25). 12 rods x 25 + 2 rooms x 25 + execute + win = 400.
#
# Recorded by scripts/solve_starcross_adaptive.py --seed {seed}.
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-8')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--upto', help='stop after this phase')
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
        print(f'seed {seed}: WIN 400/400 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            # recover the mass/coords actually used from the recording
            rr = th = ph = '?'
            for c in r.commands:
                m = re.match(r'computer, r is (\d+)', c)
                if m:
                    rr = int(m.group(1))
                m = re.match(r'computer, theta is (\d+)', c)
                if m:
                    th = int(m.group(1))
                m = re.match(r'computer, phi is (\d+)', c)
                if m:
                    ph = int(m.group(1))
            mass = next((k for k, v in MASS_LOCS.items()
                         if v == (rr, th, ph)), '?')
            with open(a.out, 'w') as f:
                f.write(HEADER.format(seed=seed, ncmds=len(r.commands),
                                      mass=mass, rr=rr, th=th, ph=ph))
                f.write('\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            break
    print(f'{wins}/{total} seeds won')


if __name__ == '__main__':
    main()
