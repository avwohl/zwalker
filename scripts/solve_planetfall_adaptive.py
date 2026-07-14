#!/usr/bin/env python3
"""Planetfall r37 route harness — machine-verifies the route segment by segment.

Route plan (2 in-game days):
  Day 1: opening/pod; east sweep (tool room, key, buttons, robot/Floyd, bedistor);
         west sweep (goo, padlock, storage west, ladder/rift, office cards);
         stash laser/pliers/bedistor at Elevator Lobby; comm cycle 1;
         kitchen dinner (canteen used once, abandoned); bed in Dorm B.
  Day 2: comm cycles 2..3 (until fixed); pick up stash; lower elevator; shuttle;
         Lawanda: course control, Floyd fromitz board, planetary defense,
         computer room, battery swap, bio-lock foray (Floyd dies), mini booth,
         speck, microbe, gas mask, fungicide flood, mutant chase, cryo ending.
Invariants: CCOUNT <= 7 at every take (no fumble rolls); weight under LOAD.
"""
import os
import re, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker

GAME = '/home/wohl/src/zwalker/games/zcode/planetfall.z3'

HUNGER_PAT = re.compile(r'growl from your stomach|really ravenous|feel faint from lack|'
                        r'pass out|incredibly famished')

class Desync(Exception):
    pass

class Runner:
    def __init__(self, seed, verbose=False, log=None):
        # GameWalker pathway with post-start seeding: identical to what
        # scripts/replay_solve.py replays, so the recorded command list
        # verifies deterministically.
        self.w = GameWalker(open(GAME, 'rb').read())
        self.boot = self.w.start()
        self.w.vm.rng.seed(seed)
        self.commands = []
        self.verbose = verbose
        self.moves = 0
        self.hungry = False
        self.hunger_level = 0
        self.canteen_full = False
        self.goos = ['red goo', 'green goo', 'brown goo']
        self.log = open(log, 'w') if log else None
        self.last = self.boot
        self._emit('[BOOT]\n' + self.boot)

    def _emit(self, s):
        if self.verbose:
            print(s)
        if self.log:
            self.log.write(s + '\n')
            self.log.flush()

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None and hasattr(r, 'output') else '') or ''
        self.commands.append(cmd)
        self.moves += 1
        self.last = out
        self._emit(f'> {cmd}\n{out}')
        if 'growl from your stomach' in out:
            self.hungry, self.hunger_level = True, 1
        elif 'really ravenous' in out:
            self.hungry, self.hunger_level = True, 2
        elif 'feel faint from lack' in out:
            self.hungry, self.hunger_level = True, 3
        elif 'millichrons' in out or 'incredibly famished' in out:
            self.hungry, self.hunger_level = True, 4
        if 'You have died' in out:
            raise Desync(f'DIED after {cmd!r}: {out[-400:]}')
        return out

    def feed(self):
        """Drink from the canteen (preferred) or eat goo when hungry."""
        if not self.hungry:
            return None
        if self.canteen_full:
            self.send('open canteen')
            out = self.send('drink liquid')
            if 'quenched your thirst' in out:
                self.canteen_full = False
                self.hungry = False
                self.hunger_level = 0
                self.send('drop canteen')
                return out
            if 'not hungry' in out:
                self.hungry = False
                self.hunger_level = 0
                return out
            if "can't see any" in out or 'not holding' in out:
                self.canteen_full = False   # canteen not on us; fall through
            else:
                raise Desync(f'canteen drink failed: {out[-200:]}')
        if not self.goos:
            raise Desync('out of goo')
        g = self.goos[0]
        out = self.send(f'eat {g}')
        if 'tasted just like' in out:
            self.goos.pop(0)
            self.hungry = False
            self.hunger_level = 0
        elif 'not hungry' in out:
            self.hungry = False
            self.hunger_level = 0
        elif "can't see any" in out:
            # kit not with us right now; tolerable at low hunger
            if self.hunger_level >= 3:
                raise Desync(f'starving with no kit: {out[-200:]}')
        else:
            raise Desync(f'feed failed: {out[-300:]}')
        return out

    def until(self, patterns, cmds, cap=120, autofeed=True):
        if isinstance(patterns, str):
            patterns = [patterns]
        if isinstance(cmds, str):
            cmds = [cmds]
        for pat in patterns:
            if re.search(pat, self.last):
                return self.last
        for i in range(cap):
            if autofeed and self.hungry:
                out = self.feed()
                for pat in patterns:
                    if re.search(pat, out or ''):
                        return out
            for c in cmds:
                out = self.send(c)
                for pat in patterns:
                    if re.search(pat, out):
                        return out
        raise Desync(f'@until cap hit: {patterns}')

    def expect(self, cmd, pattern):
        out = self.send(cmd)
        if not re.search(pattern, out):
            raise Desync(f'expect failed: {cmd!r} -> wanted {pattern!r}, '
                         f'got: {out[-400:]}')
        return out

    def time(self):
        out = self.send('time')
        m = re.search(r'current time is (\d+)', out)
        return int(m.group(1)) if m else None

    def score(self):
        out = self.send('score')
        m = re.search(r'Your score (?:is|would be) (\d+)', out)
        d = re.search(r'Day (\d+)', out)
        return (int(m.group(1)) if m else None, int(d.group(1)) if d else None)


def run_route(seed, verbose=False, log=None, upto=None):
    r = Runner(seed, verbose, log)
    checkpoints = {}

    def ckpt(name, want=None):
        r.feed()
        s, d = r.score()
        t = r.time()
        checkpoints[name] = (s, d, t, r.moves)
        r._emit(f'*** CKPT {name}: score={s} day={d} time={t} moves={r.moves}')
        if want is not None and s != want:
            raise Desync(f'checkpoint {name}: score {s} != {want}')
        if upto == name:
            print(f'stopped at {name}: score={s} day={d} time={t}')
            raise SystemExit(0)

    # ---------- Feinstein & pod ----------
    r.until(r'massive explosion rocks the ship', 'z', cap=60)
    r.send('w')                     # Escape Pod (+3)
    r.send('get in web')
    r.until(r'pod lands with a thud', 'z', cap=30)
    r.send('stand')
    r.expect('take kit', r'Taken|kit')
    r.expect('open door', r'ocean water rushes in')
    r.send('out')                   # Underwater
    r.send('u')                     # Crag (+3)
    ckpt('landed', 6)

    # ---------- climb to complex ----------
    r.send('u'); r.send('u'); r.send('u')   # Balcony, Winding Stair, Courtyard
    r.send('drop brush')
    r.send('drop brochure')         # only present if the ambassador visited
    r.send('open kit')              # so goo is reachable all game
    r.send('n')                     # Plain Hall
    r.send('ne')                    # Rec Corridor
    r.send('e'); r.send('e')        # Mess, Dorm Corridor
    r.send('e')                     # long hall -> Corridor Junction

    # ---------- east sweep: tool room ----------
    r.send('s'); r.send('s'); r.send('s')   # Mech Corridor S
    r.send('sw')                    # Tool Room
    r.expect('take magnet', r'Taken')
    r.expect('take flask', r'Taken')
    r.expect('take laser', r'Taken')
    r.expect('take pliers', r'Taken')
    r.send('e')                     # Machine Shop

    # ---------- key via magnet ----------
    r.send('n'); r.send('n'); r.send('n'); r.send('n')   # Corridor Junction
    r.send('n')                     # Admin Corridor South
    r.expect('put magnet on crevice', r'leaps from the')
    r.send('drop magnet')
    ckpt('key', 6)

    # ---------- lobby: stash + call both elevators ----------
    r.send('s')                     # Junction
    r.send('e')                     # Elevator Lobby
    r.send('drop laser')
    r.send('drop pliers')
    r.expect('press blue button', r'whirring noise')
    r.expect('press red button', r'begins vibrating')

    # ---------- robot shop: lower card + Floyd; bedistor ----------
    r.send('w')                     # Junction
    r.send('s'); r.send('s'); r.send('s'); r.send('se')  # Robot Shop
    r.expect('search robot', r'find and take a magnetic-striped card')  # +1
    r.send('put lower card in kit')
    r.expect('turn on robot', r'Nothing happens')                        # +2
    r.send('nw'); r.send('n'); r.send('n')  # Mech Corridor N
    r.send('e')                     # Storage East
    r.expect('take good bedistor', r'Taken')
    r.send('w')                     # Mech Corridor N
    r.send('n')                     # Junction
    r.send('e')                     # Lobby
    r.send('drop bedistor')         # joins the stash
    ckpt('floyd-on', 9)

    # ---------- west sweep: goo, padlock, ladder, rift, cards ----------
    r.send('w')                     # Junction
    r.send('w')                     # long hall -> Dorm Corridor
    r.send('w')                     # Mess Corridor
    r.feed()
    r.expect('unlock padlock with key', r'padlock springs open')
    r.send('take padlock')
    r.send('drop padlock')
    r.send('drop key')
    r.expect('open door', r'Opened')
    r.send('drop kit')              # ladder + kit exceeds load limit
    r.send('n')                     # Storage West (+4)
    r.expect('take ladder', r'Taken')
    r.send('s')
    r.send('e')                     # Dorm Corridor
    r.send('e')                     # long hall -> Junction
    r.send('n'); r.send('n')        # Admin Corridor
    r.send('drop ladder')
    r.expect('extend ladder', r'extends to a length')
    r.expect('put ladder across rift', r'spanning the precipice')
    r.send('n')                     # Admin Corridor N (+4)
    r.send('w')                     # Small Office
    r.send('open desk')
    r.expect('take kitchen card', r'Taken')
    r.expect('take upper card', r'Taken')
    r.send('w')                     # Large Office
    r.send('open desk')
    r.expect('take shuttle card', r'Taken')
    r.send('e'); r.send('e')        # Admin Corridor N
    r.send('s')                     # across the rift
    r.send('s'); r.send('s')        # Junction
    ckpt('cards', 20)

    # ---------- comm cycle 1 (day 1) ----------
    r.send('e')                     # Lobby (blue door should be open by now)
    def up_to_tower():
        out = r.send('n')           # try Upper Elevator
        if 'door is closed' in out or 'Elevator Lobby' in out:
            r.until(r'slides open', 'look', cap=40)
            r.send('n')
        if 'Upper Elevator' not in r.last:
            raise Desync('not in upper elevator: ' + r.last[-200:])
        r.expect('slide upper card through slot', r'Elevator enabled')
        r.send('press up button')
        r.until(r'elevator door slides open', 'look', cap=20)
        r.send('s')                 # Tower Core (+4 first time)
    def down_from_tower():
        r.send('n')                 # Upper Elevator (top)
        if 'Upper Elevator' not in r.last:
            raise Desync('not in upper elevator at tower: ' + r.last[-200:])
        r.expect('slide upper card through slot', r'Elevator enabled')
        r.send('press down button')
        r.until(r'elevator door slides open', 'look', cap=20)
        r.send('s')                 # Elevator Lobby

    up_to_tower()
    r.send('ne')                    # Comm Room
    m = re.search(r'A (red|blue|green|yellow|gray|brown|black) colored light is '
                  r'flashing', r.last)
    if not m:
        raise Desync('no enunciator color: ' + r.last[-400:])
    color = [m.group(1)]
    comm_fixed = [False]

    def comm_cycle():
        """From Comm Room: go fill flask with current color, return, pour."""
        r.send('sw')                # Tower Core
        down_from_tower()
        r.send('w')                 # Junction
        r.send('s'); r.send('s'); r.send('s'); r.send('s')   # Machine Shop
        r.expect('put flask under spout', r'now sitting under the spout')
        r.expect(f'press {color[0]} button', r'flask fills with some')
        r.expect('take flask', r'Taken')
        r.send('n'); r.send('n'); r.send('n'); r.send('n')   # Junction
        r.send('e')                 # Lobby
        up_to_tower()
        r.send('ne')                # Comm Room
        out = r.expect('pour fluid into hole', r'enunciator')
        r.expect('put flask under spout', r'spout') if False else None
        if 'go dark' in out:
            comm_fixed[0] = True
        else:
            m = re.search(r'except one, a (red|blue|green|yellow|gray|brown|black)'
                          r' light', out)
            if not m:
                raise Desync('no next color: ' + out[-300:])
            color[0] = m.group(1)

    comm_cycle()                    # cycle 1 (day 1)
    ckpt('comm1', None)

    # ---------- day 1 evening: kitchen dinner, bed ----------
    r.send('sw')                    # Tower Core
    down_from_tower()
    r.send('w')                     # Junction
    r.send('w')                     # long -> Dorm Corridor
    r.send('w')                     # Mess Corridor
    r.expect('take kit', r'Taken')
    r.send('s')                     # Mess Hall
    r.expect('take canteen', r'Taken')
    r.send('open canteen')
    r.expect('slide kitchen card through slot', r'kitchen door quietly slides open')
    r.send('s')                     # Kitchen (+4)
    r.expect('put canteen in niche', r'fits snugly')
    r.expect('press button', r'fills almost to the brim')
    r.expect('take canteen', r'Taken')
    out = r.send('drink liquid')
    if 'quenched your thirst' in out:
        r.hungry = False
        r.hunger_level = 0
    elif 'not hungry' not in out:
        raise Desync('drink failed: ' + out[-200:])
    # refill for tomorrow's breakfast and carry the closed canteen to bed
    r.expect('put canteen in niche', r'fits snugly')
    r.expect('press button', r'fills almost to the brim')
    r.expect('take canteen', r'Taken')
    r.send('close canteen')
    r.canteen_full = True
    r.send('drop kitchen card')
    r.send('n')                     # Mess Hall
    r.send('n')                     # Mess Corridor
    ckpt('dinner', None)

    r.send('w')                     # Rec Corridor
    r.send('n')                     # Dorm B
    r.send('get in bed')
    r.until(r'SEPTEM', 'z', cap=140)
    ckpt('day2-wake', None)

    # ---------- day 2 morning: gather, finish comm ----------
    # Everything non-worn was dropped at the bedside overnight.
    r.send('stand')
    r.expect('take kit', r'Taken')
    r.expect('take upper card', r'Taken')
    r.expect('take shuttle card', r'Taken')
    r.send('put shuttle card in kit')
    r.expect('take flask', r'Taken')
    r.expect('take canteen', r'Taken')
    r.send('s')                     # Rec Corridor
    r.send('e')                     # Mess Corridor
    r.send('e')                     # Dorm Corridor
    r.send('e')                     # long -> Junction
    r.send('e')                     # Lobby
    if not comm_fixed[0]:
        up_to_tower()
        r.send('ne')                # Comm Room (comm_cycle loops from here)
        guard = 0
        while not comm_fixed[0]:
            guard += 1
            if guard > 3:
                raise Desync('comm loop runaway')
            comm_cycle()
    # we are in Comm Room; drop flask here (done with it)
    r.send('drop flask')
    r.send('sw')                    # Tower Core
    down_from_tower()
    r.send('drop upper card')       # in lobby
    ckpt('comm-fixed', None)

    # ---------- pick up stash; lower elevator ----------
    r.feed()
    r.expect('take lower card', r'Taken')      # from kit
    r.expect('take laser', r'Taken')
    r.expect('take pliers', r'Taken')
    r.expect('take bedistor', r'Taken')
    out = r.send('s')               # Lower Elevator (door open since day 1)
    if 'Lower Elevator' not in out:
        r.send('press red button')
        r.until(r'south end of the room slides open', 'look', cap=40)
        r.expect('s', r'Lower Elevator')
    r.expect('slide lower card through slot', r'Elevator enabled')
    r.send('press down button')
    r.until(r'elevator door slides open', 'look', cap=25)
    r.send('drop lower card')
    r.send('n')                     # Waiting Area
    r.send('e')                     # Kalamontee Platform (+4)
    ckpt('platform', None)

    # ---------- shuttle ----------
    r.send('s')                     # Shuttle Car Alfie
    r.send('e')                     # Alfie Control East
    r.expect('take shuttle card', r'Taken')    # from kit
    r.expect('slide shuttle card through slot', r'Shuttle controls activated')
    r.send('drop shuttle card')
    r.expect('push lever up', r'lever is now in the upper position')
    for _ in range(11):
        r.send('z')
    r.expect('pull lever', r'lever is now in the central position')
    r.expect('pull lever', r'lever is now in the lower position')
    r.until(r'glides into the station', 'z', cap=15)
    r.send('w')                     # Shuttle Car Alfie
    r.send('n')                     # Lawanda Platform (+4)
    ckpt('lawanda', None)

    # ---------- course control ----------
    r.feed()
    r.send('e')                     # Escalator
    r.send('u')                     # Fork
    r.send('ne')                    # Systems Corridor West
    r.send('e'); r.send('e')        # Systems Corridor East
    r.send('n')                     # Course Control
    r.send('open lid')
    r.expect('take fused bedistor with pliers', r'manage to remove')
    r.send('drop fused bedistor')
    r.expect('put good bedistor in cube', r'warning lights go out')   # +6
    r.send('drop pliers')
    ckpt('course-fixed', None)

    # ---------- Floyd fetches the fromitz board ----------
    r.send('s')                     # Systems Corridor East
    r.send('w'); r.send('w')        # Systems Corridor West
    r.send('n')                     # Repair Room
    r.until(r'Floyd follows you|Floyd bounds into|Floyd here now|'
            r"That's Achilles|Floyd rushes into", 'z', cap=40)

    def floyd_cmd(cmd, want):
        """Issue an order to Floyd, waiting for him to wander back if needed."""
        for _ in range(6):
            out = r.send(cmd)
            if re.search(want, out):
                return out
            if "can't see any Floyd" in out:
                r.until(r'Floyd follows you|Floyd bounds into|Floyd here now|'
                        r'Floyd rushes into', 'z', cap=40)
                continue
            raise Desync(f'floyd_cmd {cmd!r}: {out[-300:]}')
        raise Desync(f'floyd_cmd retries exhausted: {cmd!r}')

    floyd_cmd('floyd, go north', r'squeezes through the opening')
    floyd_cmd('floyd, take shiny board', r'manage to catch it')
    r.send('s')                     # Systems Corridor West
    r.send('e')                     # Systems Corridor
    r.send('n')                     # Planetary Defense
    r.expect('open panel', r'panel swings open')
    r.expect('take second board', r'slides out of the panel')
    r.send('drop fried board')
    r.expect('put shiny board in socket', r'warning lights stop flashing')  # +6
    ckpt('defense-fixed', None)

    # ---------- computer room ----------
    r.feed()
    r.send('s')                     # Systems Corridor
    r.send('e')                     # Systems Corridor East
    r.send('s')                     # Library Lobby
    r.send('s')                     # Project Corridor East
    out = r.send('s')               # Computer Room
    have_flag = 'Computer is' in out
    r.expect('take output', r'Taken')
    if not have_flag:
        r.until(r'Floyd follows you|Floyd bounds into|Floyd here now|'
                r'Floyd rushes into|Computer is', 'z', cap=40)
        if 'Computer is' not in r.last:
            r.expect('show output to floyd', r'Computer is')
    r.send('drop output')
    ckpt('computer-flagged', None)

    # ---------- battery swap ----------
    r.send('ne')                    # Main Lab
    r.send('s')                     # Lab Storage
    r.expect('take old battery', r'Taken')
    r.send('drop old battery')
    r.expect('take new battery', r'Taken')
    r.expect('put new battery in laser', r'resting in the depression')
    r.send('n')                     # Main Lab
    ckpt('battery', None)

    # ---------- bio-lock: Floyd's sacrifice ----------
    r.send('open bio-lock door')
    r.send('se')                    # Bio Lock West
    if 'Bio Lock West' not in r.last:
        raise Desync('bio lock west entry failed: ' + r.last[-300:])
    r.send('e')                     # Bio Lock East
    r.until(r'Floyd will get card', 'z', cap=50)
    r.expect('open door', r'plunges into')
    r.expect('close door', r'door closes')
    r.send('z')
    r.expect('open door', r'Floyd stumbles out')
    r.expect('close door', r'not a moment too soon')          # +2
    r.expect('take mini card', r'Taken')                      # +1
    ckpt('floyd-died', None)

    # ---------- miniaturization ----------
    r.feed()
    r.send('w')                     # Bio Lock West
    r.send('open door')
    r.send('w')                     # Main Lab
    r.send('sw')                    # Computer Room
    r.send('s')                     # Mini Booth
    r.expect('slide mini card through slot', r'type in damaged sector')
    r.expect('type 384', r'walls of the booth sliding away')
    ckpt('mini', None)

    # ---------- speck & microbe ----------
    r.send('e')                     # Strip Near Station (+4)
    r.send('n')                     # Middle of Strip
    r.send('n')                     # Strip Near Relay
    r.expect('set dial to 1', r'dial is now set to 1')
    warmth = 0
    for shot in range(30):
        out = r.send('shoot speck with laser')
        warmth += 1
        if 'vaporizes' in out:
            break
        if 'Click' in out:
            raise Desync('battery empty during speck')
    else:
        raise Desync('speck never died')
    out = r.send('s')               # Middle of Strip - microbe appears
    warmth -= 1
    if 'elephant-sized monster' not in out:
        raise Desync('no microbe: ' + out[-300:])
    r.expect('set dial to 6', r'dial is now set to 6')
    warmth -= 1
    while warmth < 9:
        out = r.send('shoot microbe with laser')
        warmth += 1
        if 'Click' in out:
            raise Desync('battery empty during microbe')
    r.expect('throw laser off strip', r'plummet into the void|plunge into the void')
    r.send('s')                     # Strip Near Station
    out = r.send('w')               # Station 384 -> Auxiliary Booth (+4)
    if 'Auxiliary Booth' not in out:
        raise Desync('aux booth teleport failed: ' + out[-300:])
    ckpt('aux-booth', None)

    # ---------- gas mask, flood, chase, cryo ----------
    r.send('n')                     # Lab Office
    r.send('search desk')           # memo (auto-taken)
    r.send('open desk')
    r.expect('take gas mask', r'Taken')
    r.expect('wear gas mask', r'wearing')
    r.expect('press red button', r'hissing from beyond the door')
    r.send('open office door')
    r.send('w')                     # Bio Lab (flooded; mask on)
    r.send('open lab door')
    r.send('w')                     # Bio Lock East (east door auto-closes)
    r.send('w')                     # Bio Lock West (grace turn room)
    r.send('open door')             # west door (east has auto-closed)
    r.send('w')                     # Main Lab
    r.send('w')                     # Project Corridor East
    r.send('w')                     # Project Corridor
    r.send('s')                     # ProjCon Office
    r.send('s')                     # Cryo Elevator
    r.expect('press button', r'monsters reach it')            # +5
    r.until(r'elevator door opens onto a room', 'z', cap=10)
    out = r.send('n')               # Cryo Anteroom, ending fires
    m = re.search(r'Your score (?:is|would be) (\d+)', out)
    final = int(m.group(1)) if m else None
    r._emit(f'*** FINAL SCORE: {final} moves={r.moves}')
    if 'Veldina' not in out:
        raise Desync('ending scene missing: ' + out[-400:])
    return final, checkpoints, out, r.commands


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-10', help='range like 1-10')
    ap.add_argument('--out', help='write the recorded command list here on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--log')
    ap.add_argument('--upto')
    a = ap.parse_args()
    seeds = [a.seed] if a.seed is not None else \
        range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[1]) + 1)
    for seed in seeds:
        try:
            final, ck, out, cmds = run_route(seed, a.verbose, a.log, a.upto)
        except Desync as e:
            print(f'seed {seed}: DESYNC: {e}')
            continue
        print(f'seed {seed}: FINAL={final} commands={len(cmds)}')
        print(out[-400:])
        if final == 80 and a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Planetfall recorded adaptive solve, seed {seed}\n')
                for c in cmds:
                    f.write(c + '\n')
            print('wrote', a.out)
        if final == 80:
            break
    else:
        sys.exit(1)
