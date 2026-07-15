#!/usr/bin/env python3
"""The Hitchhiker's Guide to the Galaxy (r60/861002) adaptive route harness.

Replays the verified route milestone-by-milestone against GameWalker under a
pinned interpreter RNG seed, adapts at every point where the game's scripted
randomness branches, and RECORDS every command actually sent, so a winning
recording replays deterministically through scripts/replay_solve.py.

Seed-dependent branches this harness adapts to (ZIL: logs/hhgg_notes.md):
  * The glass-case password: LINE-NUMBER <- RANDOM 6 and WORD-NUMBER <-
    RANDOM 3 are rolled when the Vogon Hold is first entered (vogon.zil:56-57).
    The case switch names the word position; the first line of the poem's
    second verse (I-CAPTAIN counter 7, vogon.zil:687-693) supplies the words.
    The harness reads both from the transcript and types the right word.
  * Improbability-trip destinations: each `push switch` rolls the DARK-F
    M-ENTER PROB chain (globals.zil:801-841; VOGON 10 / TRAAL 60->10 /
    TRILLIAN 15->25->10 / FORD 15->25->10 / ZAPHOD 0->25->10 / FLEET 0->60->10),
    so the five dream scenarios arrive in a seed-dependent order, with revisit
    "bounces" (instant dream deaths) in between.  The harness identifies each
    destination from the dark-room litany (the missing sense) plus the
    disambiguating sense-verb reply, and dispatches the right handler.
  * The synapse maze: each move is blocked with PROB 40 (unearth.zil:676) and
    the common-sense particle only surfaces at MAZE-COUNTER 3/17/36 - the
    harness walks until the particle appears, then takes it that same turn.
  * The whale trip: with the dangly bit in real tea the dark is CONTROLLED
    (heart.zil:1722-1723): every filler turn rotates DARK-EXIT-TABLE
    (globals.zil:1036-1040).  The harness probes `feel darkness` each turn and
    only tastes the liquid when the reply says "warm" (INSIDE-WHALE), never
    "cold" (LIVING-ROOM).
  * The tool Marvin wants: eating the fruit re-rolls PICK-ONE ,TOOL-LIST up
    to 50 times while the pick is aboard (heart.zil:475-480); with every tool
    aboard the 51st pick stands.  The harness parses the vision and hands
    Marvin exactly that tool.

Hard scripted deaths avoided by construction: eat sandwich (-30), drinking
the tea substitute, entering the Pantry below 300 points (heart.zil:62-63),
wrong glass-case word (case explodes), fewer/more than 3 beers before the
matter transference beam (globals.zil:1556), Vogon-Hold revisits are dream
deaths, a WAR-CHAMBER re-selection after the particle is taken would be a
real death (I-BRAIN-DEATH) - seeds where that happens are declared DESYNC.

Score plan (sums to 400, ZIL citations in logs/hhgg_notes.md):
  analgesic 10; 3 beers 15; Hold entry 8; babel fish 12; enjoy poetry 15;
  glass case 25; spare drive 25; interface 25; party fluff 25; rifles 25;
  particle 25; Ford's beer 15; sauna bloom 25; drink tea 100; Pantry 25;
  Marvin's tool 25.

Usage:
  python3 scripts/solve_hhgg_adaptive.py --seed 1 --out walkthroughs/cmds.txt
  python3 scripts/solve_hhgg_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'hhgg.z3')

REAL_DEATH = re.compile(r'\*\*\*\*\s+You have died\s+\*\*\*\*')
WIN_PAT = re.compile(r'one single foot on the ancient dust')

# First line of the second verse -> the three candidate passwords
# (LINE-A/B/C, vogon.zil:717-722; V-TYPE word checks, verbs.zil:2040-2075).
VERSE_WORDS = {
    'fripping': ['fripping', 'lyshus', 'wimbgunts'],
    'gashee': ['gashee', 'morphousite', 'thou'],
    'bleem': ['bleem', 'miserable', 'venchit'],
}

TOOLS = ['screwdriver', 'wrench', 'chisel', 'awl', 'pliers', 'tweezers',
         'pincer', 'rasp', 'chipper', 'toothbrush']


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)   # pin RNG AFTER start(); boot is RNG-free
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
        elif REAL_DEATH.search(out) and not allow_death:
            raise Desync(f'died at {cmd!r}: ...{out[-250:]!r}')
        return out

    def until(self, pattern, cmd='z', cap=20):
        rx = re.compile(pattern, re.I)
        if rx.search(self.last):
            return self.last
        for _ in range(cap):
            out = self.send(cmd)
            if rx.search(out):
                return out
        raise Desync(f'never saw /{pattern}/ within {cap} x {cmd!r}')

    def run(self, cmds):
        for c in cmds:
            self.send(c)

    def expect_score(self, want, where):
        if self.score() != want:
            raise Desync(f'{where}: score {self.score()} != {want}')


# ---------------------------------------------------------------------------
# Act 1: Earth (fixed; ends teleported into the Dark).  Exactly 3 beers
# (DRUNK-LEVEL must be 3 when the green button is pressed, globals.zil:1556);
# the sandwich goes to the dog (DOG-FED gates the war-chamber peace,
# earth.zil:1574-1592); eating it is -30.
# ---------------------------------------------------------------------------
EARTH = [
    'turn on light', 'get up', 'take gown', 'wear gown', 'look in pocket',
    'take analgesic',                      # +10
    'take screwdriver', 'take toothbrush',  # tools for the endgame fruit draw
    's', 'take mail',                      # junk mail = 4th babel-fish blocker
    's', 'lie in front of bulldozer',
    'z', 'z', 'z',                         # bulldozer halts; Ford arrives
    'z', 'z', 'z',                         # home exchange; Prosser lies down
    'take towel',                          # only AFTER Prosser swap (else Ford leaves)
    's', 'w',                              # to the Pub (Ford follows)
    'z',                                   # Ford buys the beer
    'drink beer', 'drink beer', 'drink beer',  # +5 each
    'buy sandwich',
    'e', 'give sandwich to dog',
    'z', 'z', 'z', 'z', 'z', 'z', 'z', 'z',    # Vogon fleet; Ford drops the Thumb
    'take device', 'press green button',
]


def act_earth(r):
    r.run(EARTH)
    if 'Dark' not in r.last:
        raise Desync('green button did not teleport: ' + r.last[-200:])
    r.expect_score(25, 'earth')


# ---------------------------------------------------------------------------
# Act 2: Vogon ship.
# ---------------------------------------------------------------------------
def act_vogon(r):
    # Dark #1 is always the Hold (VOGON-PROB starts 100).  Sense verbs only
    # work once DARK-COUNTER > 3 (MISSING?, globals.zil:1124-1129).
    if dark_missing_sense(r) != 'smell':
        raise Desync('first dark is not smell-flavoured')
    r.send('smell')
    if 'shadow' not in r.last:
        raise Desync('no shadow after smell: ' + r.last[-150:])
    r.send('examine shadow')
    if 'Vogon Hold' not in r.last:
        raise Desync('not in the Hold: ' + r.last[-200:])
    r.expect_score(33, 'hold entry')       # +8, vogon.zil:58
    # Groggy timer kills at I-GROGGY counter 4 (vogon.zil:118-130).
    r.send('eat peanuts')
    # Babel fish blockers: gown on hook, towel on drain, satchel before the
    # robot panel, junk mail on the satchel (vogon.zil:176-251).
    r.run(['remove gown', 'hang gown on hook', 'put towel on drain'])
    r.until(r'you pick up The Hitchhiker', 'z', cap=8)   # Ford naps, drops satchel
    r.run(['take satchel', 'put satchel in front of panel',
           'put mail on satchel', 'press dispenser button'])
    if 'landing with a loud "squish" in your ear' not in r.last:
        raise Desync('babel fish failed: ' + r.last[-250:])
    r.expect_score(45, 'babel fish')       # +12, vogon.zil:238
    r.run(['take gown', 'wear gown'])
    # The case switch announces which word opens it (vogon.zil:495-508).
    out = r.send('press switch')
    m = re.search(r'type in the (first|second|third) word', out)
    if not m:
        raise Desync('case switch gave no word position: ' + out[-200:])
    word_idx = {'first': 0, 'second': 1, 'third': 2}[m.group(1)]
    # Guards arrive (I-GUARDS); then the poetry.
    r.until(r"Captain's Quarters", 'z', cap=40)
    r.until(r'read you a verse of my poetry', 'z', cap=6)
    r.send('z')                            # first line of verse one
    r.send('enjoy poetry')                 # +15 (vogon.zil:773-779)
    if 'grit your teeth and enjoy the stuff' not in r.last:
        raise Desync('enjoy poetry failed: ' + r.last[-200:])
    r.expect_score(60, 'enjoy poetry')
    # Second verse: its FIRST line (I-CAPTAIN counter 7) carries the password.
    out = r.until(r'read\s+the NEXT verse', 'z', cap=8)
    first_line = None
    for _ in range(6):
        out = r.send('z')
        m2 = re.search(r'"(Fripping|Gashee|Bleem)', out, re.I)
        if m2:
            first_line = m2.group(1).lower()
            break
    if first_line is None:
        raise Desync('never saw the second verse first line')
    word = VERSE_WORDS[first_line][word_idx]
    # Wait to be dragged back to the Hold, then type the word (quoted).
    r.until(r'Vogon Hold', 'z', cap=10)
    out = r.send(f'type "{word}"')
    if 'The glass case opens' not in out:
        raise Desync(f'case did not open for "{word}": ' + out[-200:])
    r.expect_score(85, 'glass case')       # +25, vogon.zil:479
    r.run(['take plotter', 'take towel'])
    # Guard throws us in the airlock; 4 turns later we are spaced, and the
    # Heart of Gold picks us up (AIRLOCK-F, vogon.zil:858-886).
    r.until(r'scooped up by a passing ship', 'z', cap=12)


# ---------------------------------------------------------------------------
# Act 3: boarding the Heart of Gold and rigging the spare drive.
# ---------------------------------------------------------------------------
def leave_dark_to_entry_bay(r):
    """From a fresh Dark with HEART-PROB 100: litany, listen, walk aft."""
    if dark_missing_sense(r) != 'hear':
        raise Desync('post-scenario dark is not hear-flavoured')
    r.send('listen')
    if 'star drive' not in r.last:
        raise Desync('no star drive hum: ' + r.last[-150:])
    if 'far above' not in r.last:
        raise Desync('star drive not above (not the Entry Bay?): '
                     + r.last[-150:])
    r.send('s')                            # "(We were lying about the exit to port.)"
    if 'Entry Bay' not in r.last:
        raise Desync('did not emerge in Entry Bay: ' + r.last[-200:])


def act_board_hog(r):
    leave_dark_to_entry_bay(r)
    r.send('look')                         # Ford leads the way to the Bridge
    if 'Bridge' not in r.last:
        raise Desync('Ford did not lead to Bridge: ' + r.last[-200:])
    r.until(r'head off to port', 'z', cap=6)   # crew leaves for the sauna
    # Lighten the load (spare drive is SIZE 50), stash everything we will
    # need later on the Bridge - our staging area.
    r.run(['drop plotter', 'drop device', 'drop screwdriver',
           'drop toothbrush', 'drop guide'])
    # Eddie's five-stage refusal gauntlet guards the Engine Room
    # (sols verified; none of the refusals match walker BLOCKED_PATTERNS).
    r.run(['d', 's', 's', 's', 's', 's', 's'])
    if 'Engine Room' not in r.last:
        raise Desync('did not enter Engine Room: ' + r.last[-200:])
    # Third M-LOOK materialises the spare drive (+25, heart.zil:1483-1491).
    r.send('look')
    out = r.send('look')
    if 'spare' not in out:
        raise Desync('spare drive never appeared: ' + out[-200:])
    r.expect_score(110, 'spare drive')
    r.run(['take drive', 'n', 'n', 'w',    # to the Galley
           'touch pad', 'take cup',        # Advanced Tea Substitute (do NOT drink)
           'e', 'u',                       # back to the Bridge
           'drop drive', 'drop cup',
           'put small plug in plotter',    # DRIVE-TO-PLOTTER, heart.zil:1626-1633
           'put dangly bit in cup'])       # BROWNIAN-SOURCE = substitute


# ---------------------------------------------------------------------------
# Act 4: the five improbability dream scenarios, in seed order.
# ---------------------------------------------------------------------------
def dark_missing_sense(r):
    """Wait out the dark until the litany drops one sense; return it.
    (MISSING? unlocks once DARK-COUNTER > 3, globals.zil:1124-1129; extra
    waits are harmless and stay in the recording.)"""
    for _ in range(10):
        out = r.send('z')
        if 'nothing' not in out and 'anything' not in out:
            continue
        missing = [s for s in ('hear', 'smell', 'see', 'feel')
                   if s not in out]
        if len(missing) == 1:
            return missing[0]
    raise Desync('no missing sense in litany: ' + r.last[-250:])


def scenario_lair(r, state):
    """Bugblatter Beast: name, stone, towel, carve, interface, beasthunters."""
    r.send('say arthur dent')
    if 'roars your name with relish' not in r.last:
        raise Desync('beast did not hear the name: ' + r.last[-200:])
    r.run(['e', 'take stone', 'put towel on head',
           'carve my name on memorial'])
    if 'settles down for a snooze' not in r.last:
        raise Desync('carve did not fool the beast: ' + r.last[-250:])
    r.run(['remove towel', 'w', 'sw', 'take interface'])
    r.expect_score(state['score'] + 25, 'interface')
    state['score'] += 25
    # Fronurbdian Beasthunters end the dream (I-BEAST 9 turns after the
    # carve) and hand us the paint chipper (unearth.zil:315-334).
    r.until(r'Everything becomes', 'z', cap=12)
    state['lair'] = True


def scenario_party(r, state):
    """Trillian at the Islington party: jacket fluff into the handbag."""
    # Hands are full (wine + hors d'oeuvres).  Retrieve the plate afterwards
    # or I-HOSTESS pesters forever and I-ZAPHOD never completes.  The huge
    # ball of fluff on Arthur's jacket only shows up once he is examined.
    r.run(['drop plate', 'examine arthur', 'take fluff', 'open handbag',
           'put fluff in handbag', 'take plate'])
    r.send('hello phil')                   # enables I-ZAPHOD (heart.zil:1162-1163)
    out = r.until(r'Everything becomes', 'z', cap=12)
    state['score'] += 25                   # I-ZAPHOD completion, heart.zil:1211
    if r.score() != state['score']:
        raise Desync(f'party: score {r.score()} != {state["score"]}')
    state['party'] = True
    return out


def scenario_speedboat(r, state):
    """Zaphod at Damogran: fluff+key+toolbox, spire trick, rifles."""
    r.run(['look under seat',              # cushion fluff + small key
           'take toolbox',
           'steer boat toward spire'])     # autopilot saves us at CRASH-COUNTER 4
    r.until(r'south of the ceremonial dais', 'z', cap=8)
    r.run(['stand', 'n'])
    if 'Dais' not in r.last:
        raise Desync('did not reach the Dais: ' + r.last[-200:])
    r.until(r'leaps out of the crowd', 'z', cap=8)   # Trillian + guards
    r.send('guards, drop the rifles')
    r.send('trillian, shoot the rifles')
    if 'disintegrates' not in r.last and 'rifles explode' not in r.last:
        raise Desync('rifles not destroyed: ' + r.last[-250:])
    out = r.send('e')                      # +25 (unearth.zil:1333) then dream end
    state['score'] += 25
    if r.score() != state['score']:
        raise Desync(f'speedboat: score {r.score()} != {state["score"]}')
    if 'Everything becomes' not in out:
        r.until(r'Everything becomes', 'z', cap=4)
    state['speedboat'] = True


def scenario_ford(r, state):
    """Ford on Earth: towel to Arthur, Prosser, peanuts, beer, fluff."""
    r.run(['open satchel', 'take fluff', 'take towel',
           'n', 'give towel to arthur'])
    if 'what about my home' not in r.last:
        raise Desync('towel offer misfired: ' + r.last[-250:])
    r.send('idiot')                        # "...what's the word?"
    r.send('go to prosser')
    r.send('prosser, lie down')
    if 'Prosser lies in the mud' not in r.last:
        raise Desync('Prosser refused: ' + r.last[-250:])
    r.run(['s', 'w',                       # to the Pub (Arthur follows)
           'buy peanuts',
           'buy beer',                     # three pints (muscle relaxant)
           'drink beer'])                  # +15 FORD-POINT (earth.zil:1895)
    state['score'] += 15
    if r.score() != state['score']:
        raise Desync(f'ford beer: score {r.score()} != {state["score"]}')
    r.send('drink beer')                   # house crash, Arthur tears out
    if 'muffled crash' not in r.last:
        raise Desync('no house crash on second beer: ' + r.last[-250:])
    r.run(['e', 'n', 'give fluff to arthur'])
    if 'sticks it in his pocket' not in r.last:
        raise Desync('Arthur refused the fluff: ' + r.last[-250:])
    # I-VOGONS: fleet arrives, Ford fumbles the Thumb, Arthur presses the
    # button, LEAVE-EARTH -> Dark.
    r.until(r'Dark|Everything becomes', 'z', cap=20)
    state['ford'] = True


def scenario_war_chamber(r, state):
    """Vl'Hurg/G'Gugvunt war chamber, then the synapse maze."""
    r.send('take awl')
    # I-DOG counts 13 turns (earth.zil:1566-1592); with DOG-FED the fleet
    # spares Earth and beams us (microscopic) into our own brain: GOTO MAZE.
    r.until(r'Transporter Chamber|surroundings change', 'z', cap=18)
    if 'Maze' not in r.last:
        r.until(r'Maze', 'z', cap=3)
    # Walk the maze until the particle surfaces (MAZE-COUNTER 3, 40% blocks),
    # then take it the same turn (it retreats on the next step).
    for _ in range(20):
        if 'particle' in r.last:
            break
        r.send('n')
    else:
        raise Desync('particle never surfaced in the maze')
    out = r.send('take particle')          # +25 then dream death
    state['score'] += 25
    if r.score() != state['score']:
        raise Desync(f'particle: score {r.score()} != {state["score"]}')
    if 'Everything becomes' not in out:
        r.until(r'Everything becomes', 'z', cap=4)
    state['war'] = True


def identify_and_run_scenario(r, state):
    """From a fresh Dark: identify the destination, dispatch its handler.
    Returns after the scenario/bounce, with the game back in the Dark."""
    sense = dark_missing_sense(r)
    if sense == 'hear':
        out = r.send('listen')
        if 'far above' in out:             # Entry Bay: bounce back aboard
            r.send('s')
            return 'ship'
        r.send('s')                        # war chamber ("far below")
        if 'War Chamber' not in r.last:
            raise Desync('not the War Chamber: ' + r.last[-200:])
        if state.get('war'):
            raise Desync('war chamber re-selected after particle: real death')
        scenario_war_chamber(r, state)
        return 'war'
    if sense == 'smell':
        r.send('smell')
        out = r.send('examine shadow')     # leaves the dark
        if 'Beast' in out.split('shaped')[0][-40:]:
            if state.get('lair'):          # revisit: claws, instant dream death
                r.until(r'Everything becomes', 'z', cap=3)
                return 'bounce'
            scenario_lair(r, state)
            return 'lair'
        # Ford/guard shaped: Vogon Hold revisit = instant dream death
        r.until(r'Everything becomes', 'z', cap=3)
        return 'bounce'
    if sense == 'see':
        r.send('examine darkness')
        out = r.send('examine light')      # leaves the dark
        if 'Sun of Earth' in out:
            if state.get('ford'):          # revisit: fumble, dream death
                r.until(r'Everything becomes', 'z', cap=3)
                return 'bounce'
            scenario_ford(r, state)
            return 'ford'
        # Damogran sun
        if state.get('speedboat'):         # revisit: Dais, guards, dream death
            r.until(r'Everything becomes', 'z', cap=3)
            return 'bounce'
        scenario_speedboat(r, state)
        return 'speedboat'
    # sense == 'feel'
    r.send('feel darkness')
    out = r.send('taste liquid')           # leaves the dark
    if 'wine' in out:
        if state.get('party'):             # revisit: hostess, dream death
            r.until(r'Everything becomes', 'z', cap=3)
            return 'bounce'
        scenario_party(r, state)
        return 'party'
    raise Desync('uncontrolled trip reached the whale?! ' + out[-200:])


def arm_careless_words(r, state):
    """Deliberate careless words: an unresolvable 4+-word input after the
    Earth's demolition arms I-CARELESS-WORDS (misc.zil:405-410), which sets
    FLEET-PROB 60 (unearth.zil:456) - without it the War Chamber (awl +
    common-sense particle) can never be rolled.  We fire it only once the
    other four scenarios are complete: a War Chamber re-roll AFTER the
    particle is taken would materialise us inside our own brain and
    I-BRAIN-DEATH is a real, unavoidable death (globals.zil:1098-1113,
    1206-1212), so the fleet must stay un-rollable until the war trip is
    the only one left, and no uncontrolled trip ever follows it."""
    if state.get('careless'):
        return
    r.send('put stone in satchel')         # "You can't see any stone here!"
    if "can't see any stone" not in r.last:
        raise Desync('careless-words phrase resolved unexpectedly: '
                     + r.last[-150:])
    r.until(r'careless talk costs lives', 'z', cap=5)
    state['careless'] = True


def act_scenarios(r):
    state = {'score': 110}
    trips = 0
    done4 = ('lair', 'party', 'speedboat', 'ford')

    def finished():
        return all(state.get(k) for k in done4 + ('war',))

    while not finished():
        trips += 1
        if trips > 16:
            raise Desync('too many improbability trips without finishing')
        outcome = identify_and_run_scenario(r, state)
        if outcome != 'ship':
            # scenario or bounce ended in a dream death -> Dark -> Entry Bay
            leave_dark_to_entry_bay(r)
        if finished():
            break                          # done, standing in the Entry Bay
        r.run(['s', 'u'])                  # Entry Bay -> Fore End -> Bridge
        if all(state.get(k) for k in done4) and not state.get('war'):
            arm_careless_words(r, state)   # unlock the fleet, last of all
        r.send('push switch')
    r.expect_score(225, 'after all five scenarios')
    return state


# ---------------------------------------------------------------------------
# Act 5: real tea, Magrathea missiles -> whale, flowerpot.
# ---------------------------------------------------------------------------
def act_tea_and_whale(r):
    # We are in the Entry Bay after the last scenario.  Fetch the cushion
    # fluff (Zaphod's pockets were dumped in the Hatchway, unearth.zil:1336).
    r.run(['s', 's', 'd', 'take fluff', 'take key', 'u', 'n', 'w'])
    if 'Galley' not in r.last:
        raise Desync('not in the Galley: ' + r.last[-150:])
    # Interface into the Nutrimat; TEA sits in the PAD, so touching the pad
    # starts I-TEA (heart.zil:642-653).
    r.run(['open panel', 'take board', 'put interface in nutrimat',
           'touch pad'])
    if 'need some help from Eddie' not in r.last:
        raise Desync('nutrimat did not engage: ' + r.last[-250:])
    r.run(['e', 'u', 'put large plug in large receptacle'])
    if 'Plugged' not in r.last:
        raise Desync('large plug failed: ' + r.last[-200:])
    # Missiles at TEA-COUNTER 7; the switch works while 6 < counter < 15.
    r.until(r'Nuclear missiles have just been launched', 'z', cap=12)
    r.send('push generator switch')        # we hold the circuit board (dipswitch)
    if 'The missiles have turned into a sperm whale' not in r.last:
        raise Desync('whale improbability failed: ' + r.last[-300:])
    # Real tea is now in the Galley slot.  Re-rig the drive to the tea:
    # BROWNIAN-SOURCE = TEA makes the next dark CONTROLLED (heart.zil:1722).
    r.run(['d', 'w', 'take tea', 'e', 'u',
           'drop tea', 'remove dangly bit', 'put dangly bit in tea'])
    if 'Done' not in r.last:
        raise Desync('dangly bit not in the real tea: ' + r.last[-200:])
    # Strip down for the whale: everything dropped on the Bridge except the
    # Thing (the flowerpot must ride home inside it, verbs.zil:2716) and the
    # worn gown; the babel fish is exempt.  Anything else carried would be
    # dumped into the BULLDOZER (verbs.zil:2718) and lost with the Earth.
    inv = r.send('i')
    for item in ('board', 'key', 'cushion fluff', 'awl', 'chipper', 'towel',
                 'satchel', 'plotter', 'guide', 'device', 'screwdriver',
                 'toothbrush', 'toolbox'):
        if item in inv:
            r.send(f'drop {item}')
    r.send('push generator switch')
    if 'Dark' not in r.last:
        raise Desync('controlled trip did not start: ' + r.last[-200:])
    # Controlled dark: each miss of `feel darkness` advances the exit table
    # by one; "cold" = LIVING-ROOM (do NOT taste), "warm" = INSIDE-WHALE.
    for _ in range(20):
        out = r.send('feel darkness')
        if 'warm' in out and 'squishy' in out:
            break
        if 'cold' in out:
            r.send('z')                    # rotate off LIVING-ROOM first
    else:
        raise Desync('never felt the warm whale lining')
    r.send('taste liquid')
    if 'whale' not in r.last:
        raise Desync('taste did not reach the whale: ' + r.last[-200:])
    r.run(['take flowerpot', 'put flowerpot in thing'])
    # I-WHALE ends the dream 11 turns after entry: SPLAT -> Dark.
    r.until(r'Everything becomes', 'z', cap=12)
    leave_dark_to_entry_bay(r)


# ---------------------------------------------------------------------------
# Act 6: plant the fluff, sauna, fruit, tea+no tea, Marvin, Magrathea.
# ---------------------------------------------------------------------------
def act_endgame(r):
    # The Thing (with the flowerpot inside) re-appears within a few turns of
    # the whale dream - I-THING re-queues every 4+RANDOM(4) turns and drops
    # it either at our feet, into the worn gown, or into our hands
    # (earth.zil:391-409).  Keep trying to take it wherever it lands.
    got = False
    for _ in range(20):
        out = r.send('take thing')
        if 'Taken' in out or 'already have' in out:
            got = True
            break
        r.send('z')
    if not got:
        raise Desync('the Thing never came back: ' + r.last[-200:])
    out = r.send('i')
    if 'flowerpot' not in out:
        raise Desync('flowerpot did not survive the whale: ' + out[-250:])
    r.run(['take flowerpot',               # out of the Thing
           's', 'u'])                      # Entry Bay -> Fore Corridor -> Bridge
    if 'Bridge' not in r.last:
        raise Desync('not back on the Bridge: ' + r.last[-150:])
    # Four fluffs: pocket + satchel (both in the gown - FLUFF-TO-GOWN),
    # jacket (in Trillian's handbag here), cushion (dropped here earlier).
    r.run(['take pocket fluff', 'take satchel fluff',
           'open handbag', 'take jacket fluff', 'take cushion fluff',
           'put pocket fluff in pot', 'put satchel fluff in pot',
           'put jacket fluff in pot', 'put cushion fluff in pot'])
    r.until(r'tiny sprout', 'z', cap=12)   # I-PLANT, 10 turns after 4th fluff
    r.send('w')                            # sauna: PLANT-BLOOMED +25
    if 'changed plant' not in r.last:
        raise Desync('plant did not bloom in the sauna: ' + r.last[-250:])
    r.expect_score(250, 'sauna bloom')
    out = r.send('eat fruit')              # Tree of Foreknowledge vision
    m = None
    for tool in TOOLS:
        if re.search(r'asks you for[^.]*\b' + tool.split()[-1], out):
            m = tool
            break
    if not m:
        raise Desync('could not parse the tool vision: ' + out[-300:])
    tool = m
    # Collect the named tool.
    fetch = {
        'screwdriver': ['take screwdriver'],
        'toothbrush': ['take toothbrush'],
        'pincer': ['take pincer'],
        'awl': ['take awl'],
        'chipper': ['take chipper'],
        'tweezers': ['take tweezers'],     # in the handbag on the Bridge
        'wrench': ['take key', 'take toolbox', 'unlock toolbox with key',
                   'open toolbox', 'take wrench'],
        'pliers': ['d', 's', 's', 's', 's', 's', 's', 'take pliers',
                   'n', 'n', 'u'],
        'rasp': ['d', 's', 's', 's', 's', 's', 's', 'take rasp',
                 'n', 'n', 'u'],
        'chisel': [],                      # lives in the Pantry itself
    }[tool]
    if tool in ('wrench',):                # toolbox etc. are on the Bridge
        pass
    r.run(fetch)
    if tool not in ('chisel',) and tool not in r.send('i'):
        raise Desync(f'failed to pick up the {tool}')
    # Tea + no tea (the particle is gone, so common sense no longer objects).
    r.run(['take tea', 'take no tea'])
    if 'no tea: Taken' not in r.last:
        raise Desync('could not take no tea: ' + r.last[-200:])
    # To the screening door; open it while holding tea AND no tea; drink the
    # tea only after it opens (Pantry entry below 300 is lethal; with the
    # +100 we are at 350).
    r.run(['d', 's', 'open door'])
    if 'heavy-duty philosopher' not in r.last:
        raise Desync('screening door unimpressed: ' + r.last[-250:])
    r.send('drink tea')                    # +100 (globals.zil:1393)
    r.expect_score(350, 'drink tea')
    r.send('w')                            # Pantry: +25 (survives at >=300)
    if 'help you to survive' not in r.last:
        raise Desync('pantry entry went wrong: ' + r.last[-250:])
    r.expect_score(375, 'pantry')
    if tool == 'chisel':
        r.send('take chisel')
    r.send('marvin, open the hatch')
    if 'twelve turns' not in r.last:
        raise Desync('Marvin did not take the job: ' + r.last[-250:])
    # Access space admits at most ONE carried item (ACCESS-SPACE-LOOP):
    # shed everything but the tool (gown worn+empty and babel fish exempt).
    r.run(['e', 'd',                       # Pantry -> Aft Corridor -> Hatchway
           'drop thing'])
    inv = r.send('i')
    for junk in ('plotter', 'satchel', 'towel', 'guide', 'flowerpot',
                 'board', 'key', 'toolbox', 'cup'):
        if junk in inv:
            r.send(f'drop {junk}')
    r.send('e')                            # Access Space
    if 'Access Space' not in r.last:
        raise Desync('could not squeeze into the Access Space: '
                     + r.last[-200:])
    r.until(r'Marvin shambles in', 'z', cap=14)
    r.until(r'Hand me', 'z', cap=3)
    tool_noun = tool.split()[-1]
    r.send(f'give {tool_noun} to marvin')
    if 'You hear the hatchway slide open' not in r.last:
        raise Desync('Marvin rejected the tool: ' + r.last[-250:])
    r.expect_score(400, 'Marvin tool')
    r.run(['w', 'd'])                      # Hatchway -> down the Hatch -> Ramp
    if not r.won:
        r.until(r'one single foot on the ancient dust', 'z', cap=4)
    r.send('z')                            # the peril-sensitive-score keypress
    return tool


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)
    act_earth(r)
    act_vogon(r)
    act_board_hog(r)
    r.send('push switch')                  # first improbability trip
    act_scenarios(r)
    act_tea_and_whale(r)
    tool = act_endgame(r)
    if not r.won:
        raise Desync('no winning text seen')
    if verbose:
        print(f'*** WON: 400/400, tool was the {tool}, '
              f'{len(r.commands)} commands')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-8')
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
        print(f'seed {seed}: WIN 400/400 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# HHGG recorded adaptive solve, seed {seed}\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached 400/400')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
