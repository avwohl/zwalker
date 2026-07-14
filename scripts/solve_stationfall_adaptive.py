#!/usr/bin/env python3
"""Stationfall r107 route harness — machine-verifies the route segment by
segment and RECORDS every command it sends (including adaptive interventions),
so the recording replays deterministically through scripts/replay_solve.py.

Determinism model:
  The GO routine draws RANDOM 1220 for the starting GST *during boot*, i.e.
  BEFORE the seed is pinned, so the raw boot is non-reproducible. The first
  two recorded commands are therefore `restart` + `yes`: the Z-machine
  restart opcode re-runs GO with the already-seeded RNG, making the start
  time — and everything after it — a pure function of the seed. The correct
  spacetruck course is then computed from the (now deterministic) chronometer:
      RIGHT-COURSE = ((t//50 - 132)**2)//4 + 103        [verbs.zil:2140-2152]

Route (2 in-game days, ~370 commands):
  Day 1: robot form -> Floyd (bin 3); spacetruck; course; dock (+5);
         stamp (under Commander's bed); crumpled form (L7 trash) + drill;
         laundry presser -> ironed form; chapel pulpit switch (flame off) +
         validate; form in slot (+6, iris hatch); Floyd fetches medium bit
         (+3); drill safe (medium hole); sleep in Sick Bay bed (+3).
  Day 2: fromitz board (Astro Lab); village east: headlamp, ceiling panel
         nip (+3), Shady Dan ID -> rank 10, taffy; armory (+5) zapgun;
         spray can; strongbox coin (+5); ostrich escort to PX -> timer via
         dispenser (+6); jammer (dark Storage-5); foil (+4, barbershop
         mirror); balloon lure to chapel -> leash -> star (+7) -> M diode;
         detonator (Main Storage); stash at quarters; casino roulette (+4);
         flophouse suit; junkyard boots; airlock/vacuum (+3) frezone in
         thermos; bomb in drilled hole (+3); timer 40; boom; key (+7);
         Plato attack survived via "floyd, help" (+7, floating event);
         Dome bin (KO scene); air shaft (+2); jammer 710 freezes exercise
         machine, jammer-off makes it kill the forklift; Factory (+2);
         shoot Floyd; wrap foil on pyramid (+5) => 80/80.
Score global: standard V3 pair — score var 17 (globals[1]), turns var 18
(globals[2]) = the GST chronometer (a move costs 7, room moves 22, z 40).
"""
import os
import re
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'stationfall.z3')

DEATH_PAT = re.compile(
    r'\*\*\*\* {2}You have died {2}\*\*\*\*|RESTART, RESTORE, or QUIT')
STUN_PAT = re.compile(r'aiming a stun ray right at your chest')
WELDER_PAT = re.compile(
    r'welder approaching|welder moves closer|welder is now almost upon you')
HUNGER_LEVELS = [
    (re.compile(r'growl from your stomach'), 1),
    (re.compile(r'really ravenous'), 2),
    (re.compile(r'feel faint from lack'), 3),
    (re.compile(r"probably pass out"), 4),
    (re.compile(r'incredibly famished'), 3),
]
FED_PAT = re.compile(r'tasted just like|not hungry')

# room name -> (escape_dir, return_dir): a 2-move bounce that despawns a
# welder (any successful room change resets it — interrupts.zil:22-25).
BOUNCE = {
    'Printing Plant': ('nw', 'se'),
    'Level Three': ('sw', 'e'),
    'Level Four': ('d', 'u'),
    'Level Five': ('u', 'd'),
    'Level Six': ('u', 'd'),
    'Mess Hall': ('n', 'sw'),
    'South Connection': ('w', 'e'),
    'North Connection': ('e', 'w'),
    'North Junction': ('e', 'w'),
    'South Junction': ('sw', 'ne'),
    'East Junction': ('nw', 'se'),
    'East Connection': ('nw', 'se'),
    "Shady Dan's": ('nw', 'se'),
    'Grocery': ('n', 's'),
    'Pet Store': ('ne', 'sw'),
    'The PX': ('sw', 'ne'),
    'Storage': ('e', 'w'),
    'Barbershop': ('nw', 'se'),
    'Trading Post': ('n', 's'),
    'Warehouse': ('u', 'd'),
    'Alley': ('s', 'n'),
    'Main Street': ('n', 's'),
    'Broadway': ('e', 'w'),
    'Saloon': ('w', 'e'),
    'Greasy Straw': ('sw', 'ne'),
    'Grimy Passage': ('s', 'n'),
    'Makeshift Connector': ('e', 'w'),
    "Commander's Office": ('nw', 'se'),
    'Station Control': ('w', 'e'),
    'Engineering Lab': ('n', 's'),
    'Astro Lab': ('n', 's'),
    'Tube': ('s', 'n'),
    'End of Corridor': ('w', 'se'),
    'Workshop': ('s', 'n'),
    'Docking Bay #2': ('e', 'w'),
    'Junk Yard': ('u', 'd'),
    'Flophouse': ('d', 'u'),
    'Bank': ('n', 's'),
    'Casino': ('w', 'e'),
    'Field Office': ('w', 'e'),
}


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False, log=None):
        # GameWalker pathway (matches scripts/replay_solve.py): seed AFTER
        # start(). The recorded `restart`/`yes` prelude then re-rolls the
        # boot RANDOM draws from the seeded stream, so the whole game is a
        # deterministic function of the seed.
        self.w = GameWalker(open(GAME, 'rb').read())
        self.boot = self.w.start()
        self.w.vm.rng.seed(seed)
        self.seed = seed
        self.commands = []
        self.verbose = verbose
        self.log = open(log, 'w') if log else None
        self.last = self.boot
        self.buf = ''             # rolling output since last until()/reset
        self.hunger = 0
        self.suited = False
        self.attack_done = False
        self.in_attack = False
        self.critical = []        # items to re-take after a Plato-attack ROB
        self.foods = []           # (name, verb) available meals, in order
        self.done = False
        self._emit('[BOOT]\n' + self.boot)
        self.send('restart', guard=False)
        self.expect('yes', r'five years since your planetfall|Deck Twelve',
                    guard=False)

    # ---------- infrastructure ----------
    def _emit(self, s):
        if self.verbose:
            print(s)
        if self.log:
            self.log.write(s + '\n')
            self.log.flush()

    def score(self):
        return self.w.vm.get_score()

    def gst(self):
        return self.w.vm.get_turns()

    def room(self):
        try:
            return self.w.vm.get_current_room_name()
        except Exception:
            return ''

    def send(self, cmd, guard=True, allow_death=False):
        res = self.w.try_command(cmd)
        out = res.output or ''
        self.commands.append(cmd)
        self.last = out
        self.buf += '\n' + out
        self._emit(f'[t={self.gst()} s={self.score()}] > {cmd}\n{out}')
        for pat, lvl in HUNGER_LEVELS:
            if pat.search(out):
                self.hunger = max(self.hunger, lvl)
        if FED_PAT.search(out):
            self.hunger = 0
        if not allow_death and DEATH_PAT.search(out):
            raise Desync(f'DEAD after {cmd!r}: ...{out[-350:]}')
        if not self.in_attack and STUN_PAT.search(out):
            self._attack()
        if guard:
            if WELDER_PAT.search(out):
                self._welder()
            if self.hunger >= 2 and not self.suited and not self.in_attack:
                self.feed()
        return out

    def expect(self, cmd, pattern, guard=True, allow_death=False):
        out = self.send(cmd, guard=guard, allow_death=allow_death)
        if not re.search(pattern, out):
            raise Desync(f'expect failed: {cmd!r} -> wanted {pattern!r}, '
                         f'got: ...{out[-400:]}')
        return out

    def until(self, patterns, cmds='z', cap=60, use_buf=False,
              allow_death=False):
        if isinstance(patterns, str):
            patterns = [patterns]
        if isinstance(cmds, str):
            cmds = [cmds]
        hay = self.buf if use_buf else self.last
        for pat in patterns:
            if re.search(pat, hay):
                self.buf = ''
                return hay
        for _ in range(cap):
            for c in cmds:
                out = self.send(c, allow_death=allow_death)
                for pat in patterns:
                    if re.search(pat, self.buf):
                        self.buf = ''
                        return out
        raise Desync(f'until cap hit waiting for {patterns} '
                     f'(room {self.room()!r}, t={self.gst()})')

    # ---------- adaptive guards ----------
    def _welder(self):
        rm = self.room()
        if rm not in BOUNCE:
            self._emit(f'*** welder in unmapped room {rm!r}; continuing')
            return
        a, b = BOUNCE[rm]
        self._emit(f'*** welder in {rm!r}: bounce {a}/{b}')
        self.send(a, guard=False)
        out = self.send(b, guard=False)
        if WELDER_PAT.search(out):
            self._welder()

    def _attack(self):
        """Plato stun-ray scene: keep telling Floyd to help (sets FLOYD-TOLD,
        station.zil:3583 -> +7), then recover the inventory ROB dropped."""
        self.in_attack = True
        for _ in range(8):
            out = self.send('floyd, help', guard=False)
            if 'blown apart' in out:
                break
        else:
            raise Desync('Plato attack never resolved')
        self.attack_done = True
        self.in_attack = False
        out = self.send('take all')
        # drop anything the ROB scene made us re-grab that we don't need,
        # so the 7-object hand limit can't block later takes
        taken = re.findall(r'^ *(.+?): Taken\.', out, re.M)
        crit_words = [set(c.split()) for c in self.critical]
        for name in taken:
            words = set(name.lower().split())
            if not any(cw <= words for cw in crit_words):
                self.send(f'drop {name}')
        for item in self.critical:
            out = self.send(f'take {item}')
            if re.search(r"can't see any", out):
                self._emit(f'*** note: {item!r} not present after attack')
        self._emit('*** Plato attack survived (+7)')

    def feed(self):
        if self.hunger == 0:
            return
        for name, verb in list(self.foods):
            out = self.send(f'{verb} {name}', guard=False)
            if 'tasted just like' in out:
                self.foods.remove((name, verb))
                self.hunger = 0
                return
            if 'not hungry' in out:
                self.hunger = 0
                return
        if self.hunger >= 3:
            raise Desync(f'starving with no reachable food (t={self.gst()})')

    def floyd_cmd(self, cmd, want):
        for _ in range(6):
            out = self.send(cmd)
            if re.search(want, out):
                return out
            if re.search(r"can't see (any )?Floyd|Floyd isn't", out):
                self.until(r'Floyd (follows|bounds|rushes|meanders|here now)',
                           'z', cap=30)
                continue
            raise Desync(f'floyd_cmd {cmd!r}: {out[-300:]}')
        raise Desync(f'floyd_cmd retries exhausted: {cmd!r}')


def run_route(seed, verbose=False, log=None, upto=None):
    r = Runner(seed, verbose, log)
    checkpoints = {}

    def ckpt(name, want=None, attack_bonus=False):
        s = r.score()
        expected = want
        if want is not None and attack_bonus and r.attack_done:
            expected = want + 7
        checkpoints[name] = (s, r.gst(), len(r.commands))
        r._emit(f'*** CKPT {name}: score={s} t={r.gst()} '
                f'cmds={len(r.commands)} attack={r.attack_done}')
        if expected is not None and s != expected:
            raise Desync(f'checkpoint {name}: score {s} != {expected}')
        if upto == name:
            print(f'stopped at {name}: score={s} t={r.gst()}')
            raise SystemExit(0)

    # ================= DAY 1: ship, truck, dock ==========================
    r.send('e')                       # Cargo Bay Entrance
    r.send('n')                       # Robot Pool
    r.expect('insert robot form in slot', r'Authorization approved')
    r.expect('type 3', r'Yippee')     # Floyd picked
    r.send('s')
    r.send('e')                       # Cargo Bay
    r.expect('open hatch', r'hatch swings open')
    r.expect('in', r'Spacetruck')
    r.expect('close hatch', r'now closed')
    r.expect('sit in pilot seat', r'pilot seat')
    r.expect('insert spacecraft form in slot', r'Type in the course')
    t = r.gst()
    course = ((t // 50 - 132) ** 2) // 4 + 103   # verbs.zil copy protection
    r._emit(f'*** course from t={t}: {course}')
    r.expect(f'type {course}', r'Course set')
    r.until(r'a voice whispers, "Stationfall|glides into the docking bay',
            'z', cap=20)
    ckpt('dock', 5)

    # ---- kit & first meal (hunger warning lands around docking) ----
    r.send('stand')
    r.expect('take kit', r'Taken')
    r.send('open kit')
    r.foods = [('gray goo', 'eat'), ('orange goo', 'eat'),
               ('soup', 'drink'), ('taffy', 'eat')]
    r.hunger = max(r.hunger, 1)
    r.feed()                          # eats the gray goo
    r.expect('open hatch', r'swings open')
    r.send('out')                     # Docking Bay 2
    r.send('e')                       # Level Five
    r.critical = ['survival kit']

    # ---- validation stamp ----
    r.send('se')                      # South Junction
    r.send('se')                      # Commander's Office
    r.send('e')                       # Commander's Quarters (welder-safe)
    r.expect('look under bed', r'validation stamp')
    r.expect('take stamp', r'Taken')
    r.send('w')
    r.send('nw')                      # South Junction

    # ---- L7: crumpled village form + drill ----
    r.send('nw')                      # Level Five
    r.send('d')                       # Level Six
    r.send('d')                       # Printing Plant
    r.expect('open trash can', r'crumpled form')
    r.expect('take crumpled form', r'Taken')
    r.send('nw')                      # Paper Recycling (welder-safe)
    r.expect('take drill', r'Taken')
    r.send('se')
    r.send('u')
    r.send('u')                       # Level Five
    ckpt('form-drill', 5)

    # ---- L3: presser irons the form; chapel flame off; validate ----
    r.send('u')                       # Level Four
    r.send('u')                       # Level Three
    r.send('nw')                      # Laundry (welder-safe)
    r.send('open presser')
    r.expect('put crumpled form in presser', r'Done')
    r.expect('close presser', r'now closed')
    r.expect('turn on presser', r'trickle of steam')
    r.expect('open presser', r'neatly ironed')
    r.expect('take form', r'Taken')
    r.send('e')                       # Level Three
    r.send('sw')                      # Chapel (welder-safe)
    r.send('examine pulpit')
    r.expect('open pulpit', r'switch')
    r.expect('turn switch', r'flame goes out')
    r.expect('validate entry form', r'Done')
    r.send('e')                       # Level Three

    # ---- insert form (+6); Floyd fetches the medium bit (+3) ----
    r.send('d')
    r.send('d')                       # Level Five
    r.send('se')                      # South Junction
    r.send('s')                       # South Connection
    r.expect('put entry form in slot', r'irising open|half dilated')
    r.send('w')                       # Robot Shop (welder-safe)
    r.floyd_cmd('floyd, take medium bit', r'Yikes|drops it to the deck')
    r.expect('take medium bit', r'Taken')
    r.expect('take small bit', r'Taken')
    r.expect('put medium bit in drill', r'Done')
    r.send('drop small bit')
    r.send('e')
    r.send('n')                       # South Junction
    ckpt('village-form', 14)

    # ---- drill the safe; go to bed ----
    r.send('se')                      # Commander's Office
    r.send('e')                       # Quarters
    r.expect('drill safe', r'You drill a hole in the safe')
    r.send('drop drill')
    r.send('w')
    r.send('nw')                      # South Junction
    r.send('ne')                      # East Junction
    r.send('nw')                      # North Junction
    r.send('e')                       # Sick Bay (welder-safe)
    r.expect('get in bed', r'now in bed|You are now in|bed is soft and comfortable')
    r.until(r'NOVEM', 'z', cap=150)
    ckpt('day2', 17)

    # ================= DAY 2 ==============================================
    r.send('stand')
    r.expect('take kit', r'Taken')
    r.feed()                          # breakfast: orange goo (famished)

    # ---- LEG A: twenty-prong fromitz board ----
    r.send('w')                       # North Junction
    r.send('n')                       # North Connection
    r.send('n')                       # Tube
    r.send('n')                       # Engineering Lab
    r.send('u')                       # Astro Lab
    r.expect('take twenty-prong board', r'Taken')
    r.send('d')
    r.send('s')
    r.send('s')                       # North Connection
    r.critical = ['survival kit', 'twenty-prong fromitz board']

    # ---- LEG B: village east — headlamp, nip, ID rank, taffy ----
    r.send('s')                       # North Junction
    r.send('se')                      # East Junction
    r.send('e')                       # East Connection
    r.send('e')                       # Makeshift Connector
    r.send('e')                       # Broadway
    r.send('e')                       # Field Office (welder-safe)
    r.expect('take headlamp', r'Taken')
    r.expect('wear headlamp', r'wearing')
    r.send('w')                       # Broadway
    r.send('sw')                      # Pet Store
    r.expect('examine ceiling', r'panel')
    r.expect('open panel', r'nip')
    r.expect('take nip', r'Taken')    # +3
    r.send('se')                      # Trading Post
    r.send('se')                      # Shady Dan's
    r.expect('put id in machine', r'fits neatly')
    r.expect('turn on machine', r'Current rank is')
    r.expect('type 10', r'New rank is 10')
    r.expect('take id', r'Taken')
    r.send('nw')                      # Trading Post
    r.send('n')                       # Grocery
    r.expect('open bag', r'taffy')
    r.expect('take taffy', r'Taken')
    r.send('put taffy in pocket')
    r.send('n')                       # Broadway
    r.send('w')
    r.send('w')                       # East Connection
    ckpt('village-east', 20, attack_bonus=True)

    # ---- LEG C: armory (+5), zapgun ----
    r.send('w')                       # East Junction
    r.send('sw')                      # South Junction
    r.send('nw')                      # Level Five
    r.send('d')                       # Level Six
    r.send('se')                      # End of Corridor
    r.feed()                          # so a meal can't eat the door window
    for _ in range(4):
        out = r.send('put id in reader', guard=False)
        if WELDER_PAT.search(out):
            r._welder()
            continue
        if not re.search(r'security door slides open', out):
            raise Desync('ID reader refused: ' + out[-200:])
        out = r.send('n', guard=False)
        if 'Armory' in out:
            break
        if WELDER_PAT.search(out):
            r._welder()
    else:
        raise Desync('armory entry failed')
    r.expect('take zapgun', r'Taken')
    r.send('s')
    r.send('drop id')
    r.send('w')                       # Level Six
    r.send('u')                       # Level Five
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun']
    ckpt('armory', 25, attack_bonus=True)

    # ---- LEG D: spray can; coin (+5); ostrich escort; PX timer (+6) ----
    r.send('se')                      # South Junction
    r.send('s')                       # South Connection
    r.send('s')                       # Grimy Passage
    r.send('s')                       # Main Street
    r.send('se')                      # Alley
    r.send('sw')                      # Pawn Shop (welder-safe)
    r.expect('take spray can', r'Taken')
    r.send('ne')                      # Alley
    r.send('s')                       # Loan Shark (welder-safe)
    r.expect('shoot strongbox', r'vaporized, leaving a solitary coin')
    r.expect('take coin', r'Taken')   # +5
    r.send('n')                       # Alley
    r.send('se')                      # Doc Schuster's: ostrich sees the nip
    r.send('nw')                      # Alley
    r.send('nw')                      # Main Street
    r.send('n')                       # Grimy Passage
    r.send('n')                       # South Connection
    r.send('n')                       # South Junction
    r.send('nw')                      # Level Five
    r.send('ne')                      # North Junction
    r.send('ne')                      # The PX
    r.expect('put coin in slot', r'Clink')
    r.expect('type 6', r'klunk')
    r.expect('scare ostrich', r'sticks its head into the dispenser hole')
    r.expect('take timer', r'Taken')  # dispenser scene was +6
    r.expect('give nip to ostrich', r'keels over')
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'timer', 'spray can']
    ckpt('px-timer', 36, attack_bonus=True)

    # ---- LEG F: foil (+4, stored inside the kit so Floyd can never
    # pilfer it); balloon lure; star (+7) ----
    r.send('sw')                      # North Junction
    r.send('se')                      # East Junction
    r.send('e')                       # East Connection
    r.send('e')                       # Makeshift Connector
    r.send('e')                       # Broadway
    r.send('se')                      # Barbershop
    r.expect('break mirror', r'reflective foil')
    r.expect('take foil', r'Taken')   # +4
    r.expect('put foil in kit', r'Done')
    r.send('nw')                      # Broadway
    r.send('sw')                      # Pet Store
    r.expect('open cage', r'floats out')
    # Lure the balloon room by room to the chapel; a spray pulls it in from
    # the adjacent room, so after any welder bounce just spray again.
    for step in ['ne', 'w', 'w', 'w', 'sw', 'nw', 'u', 'u', 'sw']:
        r.send(step)
        for attempt in range(3):
            out = r.send('spray can')
            if re.search(r'gobbling up the spores|darting around the room',
                         out):
                break
        else:
            raise Desync(f'balloon lost at {r.room()!r}')
    # in the Chapel now (welder-safe); flame was switched off on day 1
    r.send('drop spray can')
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'timer', 'M-series hyperdiode']
    r.expect('take leash', r'hanging two meters off the floor')
    r.expect('take star', r'Taken')   # +7
    r.send('drop leash')
    r.expect('open star', r'M-series hyperdiode')
    r.expect('take m diode', r'Taken')
    r.send('drop star')
    r.expect('put m diode in kit', r'Done')
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'timer']
    ckpt('star', 47, attack_bonus=True)

    # ---- LEG G: detonator; M diode installed ----
    r.send('e')                       # Level Three
    r.send('u')                       # Mess Hall
    r.send('n')                       # Main Storage (welder-safe)
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'timer', 'detonator',
                  'M-series hyperdiode']
    r.expect('take detonator', r'Taken')
    r.expect('open detonator', r'blackened hyperdiode')
    r.expect('take blackened diode', r'Taken')
    r.send('drop blackened diode')
    r.send('take m diode')            # from the kit (no-op if already held)
    r.expect('put m diode in detonator', r'Done')
    r.send('take detonator')          # no-op if already held
    # the diode is now protected by the detonator itself: retaking it after
    # an attack would pull it back OUT, so it leaves the critical list
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'timer', 'detonator']

    # ---- LEG H: stash at quarters; roulette (+4); suit; boots; frezone ----
    r.send('sw')                      # Mess Hall
    r.send('d')                       # Level Three
    r.send('d')                       # Level Four
    r.send('d')                       # Level Five
    r.send('se')                      # South Junction
    r.send('se')                      # Commander's Office
    r.send('e')                       # Quarters (welder-safe stash)
    # Only the detonator (CONTBIT) and timer are stashed: I-FLOYD's pilfer
    # branch only ever looks at the FIRST object in the room and skips both
    # (interrupts.zil:188-198), so this stash is Floyd-proof.
    r.send('drop detonator')
    r.send('drop timer')
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun']
    r.send('w')
    r.send('nw')                      # South Junction
    r.send('s')                       # South Connection
    r.send('s')                       # Grimy Passage
    r.send('s')                       # Main Street
    r.send('ne')                      # Greasy Straw
    r.send('ne')                      # Trading Post
    r.send('e')                       # Saloon
    r.send('e')                       # Casino (welder-safe)
    r.expect('turn wheel', r'exits appear')    # +4
    r.send('u')                       # Flophouse (welder-safe)
    r.expect('open locker', r'space suit')
    r.expect('take suit', r'Taken')
    r.feed()                          # last chance to eat before the suit
    r.expect('wear suit', r'wearing')
    r.suited = True
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun']
    r.send('d')                       # Casino
    r.send('w')                       # Saloon
    r.send('w')                       # Trading Post
    r.send('se')                      # Shady Dan's
    r.send('d')                       # Junk Yard
    r.expect('take boots', r'Taken')
    r.expect('wear boots', r'wearing')
    r.send('u')                       # Shady Dan's
    r.send('nw')                      # Trading Post
    r.send('d')                       # Warehouse
    # ---- gate: the Plato attack (+7) must be behind us BEFORE we touch
    # the frezone. After the pickup every turn costs melt budget, and an
    # attack beside a ticking timer (or with the thermos junk-dropped en
    # route) is fatal. The attack is armed by now on every seed (evilness
    # is far past 11); it fires as soon as Plato isn't standing with us.
    if not r.attack_done:
        r._emit('*** waiting at the Warehouse for the Plato attack')
        for _ in range(80):
            r.send('z')
            if r.attack_done:
                break
        else:
            raise Desync('Plato attack never fired before the frezone trip')
    r.expect('take thermos', r'Taken')
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'space suit', 'pair of magnetic boots',
                  'Thermos bottle']
    r.expect('open thermos', r'soup|Opened')
    r.feed()                          # soup for lunch if hungry by now
    r.expect('open inner door', r'swings open')
    r.expect('d', r'Airlock')
    r.expect('close inner door', r'now closed')
    r.expect('turn on headlamp', r'now on')
    r.expect('open outer door', r'whooshes out')
    r.expect('d', r'In Space|vac yard')        # +3
    r.expect('take explosive', r'Taken')
    r.expect('u', r'Airlock')
    r.expect('close outer door', r'air hisses back')
    r.expect('put explosive in thermos', r'Done')
    r.expect('close thermos', r'now closed')
    r.expect('open inner door', r'swings open')
    r.expect('take off suit', r'no longer wearing')
    r.suited = False
    r.send('drop suit')
    r.expect('take off boots', r'no longer wearing')
    r.send('drop boots')
    r.expect('turn off headlamp', r'now off')
    r.send('u')                       # Warehouse
    r.send('u')                       # Trading Post
    r.critical = ['survival kit', 'twenty-prong fromitz board',
                  'fusor-beam zapgun', 'Thermos bottle']
    ckpt('frezone', 54, attack_bonus=True)

    # ---- shortest way back (melt clock ticks at 1/4 in the closed
    # thermos; the budget only allows ~4 welder bounces of slack) ----
    r.send('sw')                      # Greasy Straw
    r.send('sw')                      # Main Street
    r.send('n')                       # Grimy Passage
    r.send('n')                       # South Connection
    r.send('n')                       # South Junction
    r.send('se')                      # Commander's Office
    r.send('e')                       # Quarters

    # ---- LEG I: bomb, boom heard from the office next door, key (+7).
    # Every turn from the outer-door close until the boom costs melt
    # budget (sublimation at 210), so the assembly is as short as it can
    # be and the timer is set to 22: it hits zero on the escape move
    # itself, one room away. ----
    if not r.attack_done:
        raise Desync('Plato attack still pending at bomb assembly')
    r.expect('open thermos', r'explosive|Opened')
    r.expect('take explosive', r'Taken')
    r.expect('put explosive in hole', r'Done')  # +3
    r.expect('connect detonator to explosive', r'Done')
    r.expect('connect timer to detonator', r'Done')
    r.expect('set timer to 22', r'begins ticking')
    r.send('w')                       # Commander's Office (blast-safe)
    r.until(r'explosion', 'z', cap=10, use_buf=True)
    r.expect('turn on headlamp', r'now on')
    r.feed()
    r.send('e')                       # Quarters
    r.expect('take key', r'Taken')    # +7
    r.critical = ['key', 'survival kit', 'fusor-beam zapgun',
                  'twenty-prong fromitz board']
    r.send('w')                       # Commander's Office
    ckpt('key', 71)                   # attack is guaranteed done by now

    # ---- fetch the jammer (dark Storage-5; headlamp already on) ----
    r.send('nw')                      # South Junction
    r.send('nw')                      # Level Five
    r.send('ne')                      # North Junction
    r.send('n')                       # North Connection
    r.send('w')                       # Storage
    r.expect('take jammer', r'Taken')
    r.send('e')                       # North Connection
    r.expect('connect board to jammer', r'Done')
    r.expect('set jammer to 710', r'set the jammer to 710')
    r.critical = ['key', 'survival kit', 'fusor-beam zapgun', 'jammer']

    # ---- LEG J: Dome bin; air shaft (+2); factory (+2); finale (+5) ----
    r.send('s')                       # North Junction
    r.send('sw')                      # Level Five
    r.send('u')                       # Level Four
    r.send('u')                       # Level Three
    r.send('u')                       # Mess Hall
    r.send('u')                       # Dome (welder-safe)
    r.expect('unlock bin with key', r'unlock the bin')
    r.expect('open bin', r'cells explode', allow_death=True)
    r.expect('take zapgun', r'Taken')
    r.expect('take jammer', r'Taken')
    r.expect('take kit', r'Taken')
    r.expect('take foil', r'Taken')   # from inside the kit
    r.expect('move grating', r'bend the grating')
    r.expect('enter grating', r'Top of Air Shaft')   # +2, welders dequeued
    for _ in range(7):
        r.send('d')
    if 'Bottom of the air vent' not in r.last and \
            'the bottom of the air vent' not in r.last:
        if not re.search(r'[Bb]ottom of', r.last):
            raise Desync('air shaft descent failed: ' + r.last[-200:])
    r.expect('turn on jammer', r'now on')
    r.expect('open grating', r'spilling you into the room below',
             allow_death=True)
    if not re.search(r'freezes', r.last):
        raise Desync('exercise machine not jammed: ' + r.last[-300:])
    r.expect('turn off jammer', r'death grip and then explode')
    r.expect('u', r'Factory')         # +2
    r.expect('shoot floyd', r'bolt hits Floyd squarely')
    out = r.expect('put foil on pyramid', r'Play game with Oliver',
                   allow_death=True)
    ckpt('pyramid', 80)
    # flush the [Hit RETURN] pause to capture the score banner
    out = r.send('z', guard=False, allow_death=True)
    m = re.search(r'[Yy]our score is (\d+) \(of 80 points\)', out)
    text_score = int(m.group(1)) if m else None
    final = r.score()
    r._emit(f'*** FINAL: score={final} text={text_score} '
            f'cmds={len(r.commands)} t={r.gst()}')
    if text_score != 80:
        raise Desync('final score banner missing: ' + out[-300:])
    return final, checkpoints, out, r.commands


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-10', help='range like 1-20')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--log')
    ap.add_argument('--upto')
    a = ap.parse_args()
    seeds = [a.seed] if a.seed is not None else \
        range(int(a.seeds.split('-')[0]), int(a.seeds.split('-')[1]) + 1)
    wins = 0
    total = 0
    for seed in seeds:
        total += 1
        try:
            final, ck, out, cmds = run_route(seed, a.verbose, a.log, a.upto)
        except Desync as e:
            print(f'seed {seed}: DESYNC: {e}')
            continue
        print(f'seed {seed}: FINAL={final} commands={len(cmds)}')
        if final == 80:
            wins += 1
            if a.out:
                with open(a.out, 'w') as f:
                    f.write(f'# Stationfall recorded adaptive solve, '
                            f'seed {seed}\n')
                    for c in cmds:
                        f.write(c + '\n')
                print('wrote', a.out)
                a.out = None
    print(f'{wins}/{total} seeds at 80/80')
    sys.exit(0 if wins else 1)
