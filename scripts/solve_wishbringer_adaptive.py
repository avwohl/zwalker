#!/usr/bin/env python3
"""Wishbringer r68 route harness — machine-verifies the route segment by segment.

Route plan (no wishes used; all 7 Wishes untouched => clean 100/100):
  Festeron (15:00, deadline 17:00): post office/envelope; cemetery bone
      (gravedigger shooed via copse->glen walk); poodle+bone; Voss violet
      note; fountain coin; wharf seahorse rescue; bridge; trail maze up
      (u w n u e s u); Magick Shoppe scene (clock frozen inside).
  Witchville (18:00, moonset 06:00 = 720 turns, plenty): fog maze down
      (d n w d s e d); branch; troll vs snake-can; stone; platypus/whistle;
      Misty Island hat; cemetery dash (2 turns!) into grave; tunnels;
      jail sneak from below (blanket); grue nest (blanket on baby, worm);
      stump; pelican word (PARSED); worm->piranha->token; Voss ticket;
      theater glasses; arcade teleport to Hilltop; SAY <word>; tower
      capture; violet note to Crisp; coat/key/chains/lever; lab via 3D
      glasses (broom, security switch); crank; ALEXIS HEEL; steel key;
      library; break case with broom; stone into sculpture; finale.
Score global: GSCORE = global index 136 (variable 152). SCORE/MOVES
globals (indices 1/2) are the CLOCK (hour/minute) — 1 turn = 1 minute.
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'wishbringer.z3')

GSCORE_GLOBAL = 136          # 0-based index into the globals table (var 152)
HOUR_GLOBAL = 1              # 'SCORE' in the ZIL = hour of day
MINUTE_GLOBAL = 2            # 'MOVES' in the ZIL = minute of hour

DEATH_PAT = re.compile(
    r'\*\*\*\* You have died \*\*\*\*|RESTART, RESTORE|'
    r"You're FIRED|The story has ended|torture at the skilled hands")
CAPTURE_PAT = re.compile(r"It's the Boot Patrol")


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False, log=None):
        # GameWalker pathway (matches scripts/replay_solve.py): seed the RNG
        # AFTER start() so the recorded command list replays identically.
        self.w = GameWalker(open(GAME, 'rb').read())
        self.boot = self.w.start()
        self.w.vm.rng.seed(seed)
        self.commands = []
        self.verbose = verbose
        self.moves = 0
        self.log = open(log, 'w') if log else None
        self.last = self.boot
        self.power_word = None
        self.done = False
        self._emit('[BOOT]\n' + self.boot)
        if 'Release 68' not in self.boot:
            raise Desync('wrong game binary (want Release 68)')

    def _emit(self, s):
        if self.verbose:
            print(s)
        if self.log:
            self.log.write(s + '\n')
            self.log.flush()

    def gscore(self):
        base = self.w.vm.header.globals
        return self.w.vm.read_word(base + 2 * GSCORE_GLOBAL)

    def clock(self):
        base = self.w.vm.header.globals
        return (self.w.vm.read_word(base + 2 * HOUR_GLOBAL),
                self.w.vm.read_word(base + 2 * MINUTE_GLOBAL))

    def send(self, cmd, allow_death=False):
        res = self.w.try_command(cmd)
        out = res.output
        self.commands.append(cmd)
        self.moves += 1
        self.last = out
        self._emit(f'> {cmd}\n{out}')
        if not allow_death and DEATH_PAT.search(out):
            raise Desync(f'DEAD/LOCKOUT after {cmd!r}: ...{out[-400:]}')
        if not allow_death and CAPTURE_PAT.search(out):
            raise Desync(f'CAPTURED by Boot Patrol after {cmd!r}: '
                         f'...{out[-400:]}')
        return out

    def expect(self, cmd, pattern, allow_death=False):
        out = self.send(cmd, allow_death=allow_death)
        if not re.search(pattern, out):
            raise Desync(f'expect failed: {cmd!r} -> wanted {pattern!r}, '
                         f'got: ...{out[-500:]}')
        return out

    def until(self, patterns, cmds, cap=40, allow_death=False):
        if isinstance(patterns, str):
            patterns = [patterns]
        if isinstance(cmds, str):
            cmds = [cmds]
        for pat in patterns:
            if re.search(pat, self.last):
                return self.last
        for _ in range(cap):
            for c in cmds:
                out = self.send(c, allow_death=allow_death)
                for pat in patterns:
                    if re.search(pat, out):
                        return out
        raise Desync(f'@until cap hit waiting for {patterns}')


def run_route(seed, verbose=False, log=None, upto=None):
    r = Runner(seed, verbose, log)
    checkpoints = {}

    def ckpt(name, want=None):
        s = r.gscore()
        h, m = r.clock()
        checkpoints[name] = (s, h, m, r.moves)
        r._emit(f'*** CKPT {name}: score={s} clock={h}:{m:02d} '
                f'moves={r.moves}')
        if want is not None and s != want:
            raise Desync(f'checkpoint {name}: score {s} != {want}')
        if upto == name:
            print(f'stopped at {name}: score={s} clock={h}:{m:02d}')
            raise SystemExit(0)

    # ================= FESTERON (15:00; Shoppe closes 17:00) ==============
    # ---- post office: +1 entry, +5 envelope ----
    r.expect('s', r'Post Office')                 # +1 (I-HOORAY; sets POWER)
    r.until(r'tossing it onto the service counter', 'z', cap=4)
    r.expect('take envelope', r'score just went up by 5')
    r.send('n')                                   # Hilltop
    ckpt('envelope', 6)

    # ---- cemetery: shoo the gravedigger, rob the grave ----
    r.send('w')                                   # Outside Cemetery
    r.expect('w', r'sure you want to go in there\?')
    r.expect('yes', r'You have been warned')      # Creepy Corner
    r.expect('n', r'nods a greeting')             # Spooky Copse (digger)
    r.expect('w', r'locks it|locking the')        # Glen; digger leaves
    r.send('e')                                   # Spooky Copse (empty)
    r.expect('d', r'manage to squeeze yourself into the grave|Grave')
    r.expect('take bone', r'score just went up by 1')
    r.expect('u', r'manage to climb out')         # Spooky Copse
    r.send('s')                                   # Creepy Corner
    r.send('e')                                   # Outside Cemetery
    r.send('e')                                   # Hilltop
    ckpt('bone', 7)

    # ---- poodle, Voss note, coin ----
    r.expect('e', r'poodle')                      # Outside Cottage
    r.expect('give bone to poodle', r'score just went up by 3')
    r.send('n')                                   # Rotary South (Voss)
    r.until(r'holding it out to you|note in her purse|take this note',
            'z', cap=6)
    r.expect('take note', r'score just went up by 3')
    r.send('n')                                   # Park
    r.send('look in fountain')
    r.expect('take coin', r'score just went up by 1')
    ckpt('coin', 14)

    # ---- seahorse rescue (insurance vs 3rd capture; no points) ----
    r.send('e')                                   # Rotary East
    r.send('e')                                   # Pleasure Wharf
    r.expect('e', r'seahorse')                    # Wharf's End
    r.expect('take seahorse', r'Taken')
    r.expect('throw seahorse in bay', r'springs suddenly to life')
    r.send('w')                                   # Pleasure Wharf
    ckpt('seahorse', 14)

    # ---- north over the covered bridge, up the trail maze ----
    r.send('n')                                   # Tidal Pool
    r.send('n')                                   # Festeron Point
    r.send('w')                                   # Rocky Path
    r.send('w')                                   # South of Bridge
    r.send('n')                                   # On Bridge
    r.send('n')                                   # North of Bridge
    r.send('e')                                   # Cliff Bottom
    r.expect('u', r'good idea to draw a map|Steep Trail')   # TLOC 1
    r.send('w')                                   # TLOC 2
    r.send('n')                                   # TLOC 3
    r.send('u')                                   # TLOC 4
    r.send('e')                                   # TLOC 5
    r.send('s')                                   # TLOC 6
    r.expect('u', r'score just went up by 1')     # Cliff Edge (+1)
    ckpt('cliff-edge', 15)

    # ---- Magick Shoppe (clock frozen inside) ----
    r.expect('knock on door', r'Come in')
    r.expect('open door', r'bell tinkles')
    r.expect('w', r'Magick Shoppe')               # inside
    r.until(r'takes? the envelope|An old woman|old woman', 'z', cap=8)
    r.expect('give envelope to woman', r'score just went up by 5')
    r.expect('open envelope', r'letter')
    r.expect('read letter to woman', r'score just went up by 1')
    r.until(r'holds out a small metal can|Take this', 'z', cap=6)
    r.expect('take can', r'score just went up by 3')
    r.until(r'Cliff Edge', 'z', cap=8)            # transformation
    ckpt('witchville', 24)

    # ============== WITCHVILLE (18:00; moonset 06:00) =====================
    # ---- fog maze down; branch; troll; the Stone ----
    r.expect('d', r'engulfed|thick layer', allow_death=False)  # Fog TLOC 6
    r.send('n')                                   # TLOC 5
    r.send('w')                                   # TLOC 4
    r.send('d')                                   # TLOC 3
    r.send('s')                                   # TLOC 2
    r.send('e')                                   # TLOC 1
    r.expect('d', r'Cliff Bottom|dissolves the fog')
    r.expect('take branch', r'snaps off')
    r.expect('take branch', r'Taken')
    r.expect('w', r'troll|Toll')                  # North of Bridge
    r.expect('open can', r'score just went up by 3')   # snake; troll flees
    r.expect('take can', r'Taken')
    r.expect('squeeze can', r'small stone drops out|Pop!')
    r.expect('take stone', r'score just went up by 5')
    r.expect('open gate', r'open|Okay')
    r.send('s')                                   # On Bridge
    r.send('s')                                   # South of Bridge
    r.send('w')                                   # River Outlet
    r.expect('s', r'Lake Edge|pit')               # Edge of Lake
    ckpt('stone', 32)

    # ---- platypus, whistle, Misty Island, wizard's hat ----
    r.send('look in pit')
    r.expect('put branch in pit', r'grabs the end|holding on|branch')
    r.expect('take branch', r'score just went up by 5')
    r.send('drop branch')
    r.expect('dig in sand', r'discovered a silver whistle')
    r.expect('take whistle', r'score just went up by 3')
    r.expect('blow whistle', r'Misty Island|drawing closer')
    r.expect('w', r'Throne Room|platypuses|Anatinus')
    r.until(r'holding it out to you|Take this', 'z', cap=6)
    r.expect('take hat', r'score just went up by 1')
    r.until(r'blow into the whistle one more time|look at you expectantly',
            'z', cap=6)
    r.expect('blow whistle', r'Lake Edge|streak across the lake')
    ckpt('island', 41)

    # ---- cemetery dash into the grave (2 turns before vapors grab) ----
    r.expect('s', r'sure you want to go in there\?')
    r.expect('yes', r'You have been warned')      # Twilight Glen
    r.send('e')                                   # Spooky Copse
    r.expect('d', r'grave|Grave')                 # escape the vapors
    r.expect('n', r'underground chamber')         # Tunnel Fork
    r.expect('e', r'hole|concrete|Underground')   # Under Cell
    ckpt('under-cell', 41)

    # ---- jail sneak: blanket from above ----
    r.expect('push bunk', r'moved the bunk|Faint light')
    r.send('drop all')                            # hole limit is 18 units
    r.expect('u', r'Jail Cell|jail cell')
    r.expect('take blanket', r'score just went up by 3')
    r.expect('d', r'Underground')
    r.send('take all')
    ckpt('blanket', 44)

    # ---- grue nest: cover the baby, raid the fridge ----
    r.send('n')                                   # Tunnel Corner
    r.expect('e', r'nesting place of a family of grues')
    r.expect('put blanket on beast', r'score just went up by 3')
    r.expect('open fridge', r'light inside|Opened|opening')
    r.expect('take worm', r'score just went up by 3')
    r.send('w')                                   # Tunnel Corner
    r.send('w')                                   # Under Hill
    r.expect('open stump', r'reveals a round hole|hinged top')
    r.expect('u', r'Lookout Hill')
    ckpt('grue', 50)

    # ---- pelican: the Word of Power (VARIABLE - parse it!) ----
    r.send('n')                                   # River Outlet
    r.send('e')                                   # South of Bridge
    r.send('e')                                   # Rocky Path
    r.expect('e', r'pelican|Festeron Point')
    out = r.expect('give hat to pelican', r'score just went up by 5')
    m = re.search(r'traces a word on a passing cloud: ([A-Z]+)', out)
    if not m:
        raise Desync('no power word in pelican text: ' + out[-400:])
    r.power_word = m.group(1)
    r._emit(f'*** POWER WORD: {r.power_word}')
    ckpt('pelican', 55)

    # ---- token from the piranha fountain ----
    r.send('w')                                   # Rocky Path
    r.send('w')                                   # South of Bridge
    r.send('s')                                   # Rotary North
    r.expect('s', r'Park')
    r.expect('put worm in fountain', r'snatches away the worm')
    r.expect('take token', r'score just went up by 3')
    ckpt('token', 58)

    # ---- movie theater: ticket, 3D glasses ----
    r.expect('e', r'Rotary East')
    r.expect('give coin to voss', r'score just went up by 3')
    r.expect('in', r'lobby|Lobby')
    r.expect('give ticket to gravedigger', r'takes the ticket')
    r.expect('n', r'Inside Theater|movie theater unlike any')
    r.expect('look under seat', r'discovered a used pair of 3D glasses')
    r.expect('take glasses', r'score just went up by 3')
    r.expect('s', r'lobby|Lobby')
    r.expect('out', r'leave the movie theater\?')
    r.expect('yes', r'Come again|Rotary East')
    ckpt('glasses', 64)

    # ---- video arcade: teleport to Hilltop ----
    r.send('e')                                   # Pleasure Wharf
    r.expect('s', r'Video Arcade|arcade')
    r.expect('put token in slot', r'score just went up by 1')
    r.expect('push joystick west', r'one square to the left')
    r.expect('push joystick west', r'one square to the left')
    r.expect('push joystick south', r'one square downward')
    r.expect('push joystick south', r'one square downward')
    r.expect('press red button', r'sure you want to push')
    r.expect('yes', r"You don't really want to press")
    r.expect('yes', r'score just went up by 5')   # Hilltop
    ckpt('hilltop', 70)

    # ---- the Word, the Tower, Mr. Crisp ----
    r.expect(f'say {r.power_word}',
             r'score just went up by 3')          # drawbridge lowers
    r.expect('s', r'Turn back|chained to the floor|Vestibule')
    r.expect('z', r'Nice of you to drop by', allow_death=True)
    r.expect('give note to crisp', r'Violet scolds me')
    r.expect('take coat', r'You got it|Taken')
    r.expect('take key', r'score just went up by 3')
    r.expect('unlock chains with key', r'score just went up by 1')
    r.expect('pull lever', r'lifts? gently|released|free')
    r.expect('take note', r'Taken')
    r.expect('read note', r'score just went up by 3')
    ckpt('crisp', 80)

    # ---- laboratory via 3D glasses; security off; broom; crank ----
    r.expect('open hatch', r'opens reluctantly')
    r.expect('u', r'Round Chamber')
    r.expect('look behind paintings', r'reveals a metal crank')
    r.send('u')                                   # Fuzziness
    r.expect('wear glasses', r'Laboratory')
    r.expect('take broom', r'Taken')
    r.expect('open second switch', r'score just went up by 3')
    r.send('d')                                   # Fuzziness
    r.expect('take off glasses', r'Round Chamber')
    r.expect('turn crank', r'score just went up by 1')
    r.send('n')                                   # Vestibule
    r.expect('n', r'Hilltop')
    ckpt('lab', 84)

    # ---- ALEXIS HEEL; the steel key; the library ----
    r.expect('e', r'hellhound')                   # Outside Cottage
    r.expect('alexis, heel', r'score just went up by 5')
    r.expect('open door', r'Okay|open')
    r.expect('in', r'Inside Cottage|cottage')
    r.expect('take steel key', r'score just went up by 3')
    r.send('out')
    r.send('n')                                   # Rotary South
    r.expect('unlock library door with steel key',
             r'score just went up by 3')
    r.expect('in', r'Circulation Desk|large desk')
    r.until(r'somebody locks', 'z', cap=4)        # the door slams shut
    r.expect('s', r'museum|Museum|fossil')
    ckpt('library', 95)

    # ---- the vault: break the case, give up the Stone ----
    r.expect('break case with broom', r'broke the display case open')
    r.expect('put stone in sculpture', r'Wait!|familiar voice')
    r.expect('yes', r"Don't!")
    r.expect('yes', r'folds around you|Cliff Edge')  # +5 (quiet)
    ckpt('sculpture', 100)

    # ---- finale ----
    r.until(r'rubbing against your leg', 'z', cap=4)
    r.send('knock on door', allow_death=True)
    out = r.until(r'finished the story', 'z', cap=6, allow_death=True)
    final = r.gscore()
    m = re.search(r'[Yy]our score is (\d+) points? out of 100', out)
    text_score = int(m.group(1)) if m else None
    r._emit(f'*** FINAL: gscore={final} text={text_score} '
            f'moves={r.moves}')
    if 'finished the story' not in out:
        raise Desync('finale text missing: ' + out[-400:])
    return final, checkpoints, out, r.commands


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-10', help='range like 1-10')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--log')
    ap.add_argument('--upto')
    a = ap.parse_args()
    seeds = [a.seed] if a.seed is not None else \
        range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[1]) + 1)
    wins = 0
    for seed in seeds:
        try:
            final, ck, out, cmds = run_route(seed, a.verbose, a.log, a.upto)
        except Desync as e:
            print(f'seed {seed}: DESYNC: {e}')
            continue
        print(f'seed {seed}: FINAL={final} commands={len(cmds)}')
        if final == 100:
            wins += 1
            if a.out:
                with open(a.out, 'w') as f:
                    f.write(f'# Wishbringer recorded solve, seed {seed}\n')
                    for c in cmds:
                        f.write(c + '\n')
                print('wrote', a.out)
                a.out = None
    print(f'{wins}/{len(list(seeds))} seeds at 100/100')
    sys.exit(0 if wins else 1)
