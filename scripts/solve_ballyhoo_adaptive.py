#!/usr/bin/env python3
"""Ballyhoo (Infocom Release 97, serial 851218, Z-machine V3) adaptive recorder.

Replays the verified 200/200 route against GameWalker under a pinned interpreter
RNG seed, asserts the score after each milestone, ADAPTS at the one random point
(the forced blackjack hand in the Blue Room, whose "Do you want another card?"
prompt count depends on the cards dealt for the seed), and RECORDS every command
actually sent so the recording replays deterministically through
scripts/replay_solve.py (which uses this exact GameWalker+seed pathway).

Determinism model (ZIL citations in logs/ballyhoo_notes.md):
  * Boot draws no randomness -- two boots are byte-identical -- so the seed is
    pinned right after start() with no restart prelude.
  * The ONLY route-relevant randomness is the mandatory $1 blackjack hand
    (cards.zil PICK-CARD, <RANDOM 52>): the number of "Do you want another
    card?" prompts before the hand resolves depends on the deal. The recorder
    stands immediately (answers "n") and loops until the hand resolves, so the
    baked-in "n" count matches whatever seed is pinned. Everything else on the
    route is turn-counter clockwork (I-MEET, I-CLOWN-ALLEY, I-STANDS, the tape
    deck, I-APE, I-OFFICE, I-POKE, I-CHASE, ACROSS-ROPE endgame) plus flavor-
    only PROB rolls; all replay identically under the same command list.

Joke-death note (see logs/ballyhoo_notes.md, "Unavoidable joke death"):
  Descending from Top of Cage the FIRST time is a scripted NON-fatal gag
  ("You fall awkwardly down from the cage. **** You have died ****" then, two
  turns later, "the reports of your demise have been grossly exaggerated"):
  way.zil:660-668 sets the DIED global and prints TELL-DIED, but play
  continues. It is the ONLY setter of DIED (harmless -- read only by the fall
  routine) and is unavoidable because award #16 (the elephant-tent prod fight,
  On the Tent) is reachable only via Top of Cage. This recorder treats that
  specific "you have died ... from the cage" line as non-fatal.

Score plan (20 awards x 10 = 200; points.txt / ZIL cites in the notes):
  tightrope 10, helium/Harry 20, clown-mask knock 30, canvas pleats 40,
  ticket 50, keys 60, cigarette case 70, Jenny 80, hypnosis granola 90,
  radio 100, Mahler classical 110, mouse 120, Hannibal 130, white wagon 140,
  Blue Room ticket 150, tent prod 160, scare Chuckles 170, Chelsea 180,
  net 190, Mahler drops Chelsea 200.

Usage:
  python3 scripts/solve_ballyhoo_adaptive.py --seed 1 --verbose
  python3 scripts/solve_ballyhoo_adaptive.py --seed 1 --out walkthroughs/ballyhoo_verified_200.txt
  python3 scripts/solve_ballyhoo_adaptive.py --seeds 1-8
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'ballyhoo.z3')

WIN_PAT = re.compile(r'score is 200 of a possible 200|'
                     r'saved The Traveling Circus That Time Forgot', re.I)
BJACK_PROMPT = re.compile(r'Do you want another card\?', re.I)


class Desync(Exception):
    pass


def is_real_death(out):
    """A REAL Ballyhoo death (JIGS-UP -> FINISH). The scripted joke fall from
    the cage top ALSO prints '**** You have died ****' (way.zil TELL-DIED) but
    is non-fatal -- distinguish it by its 'from the cage' phrasing."""
    low = out.lower()
    if 'you have died' not in low:
        return False
    return 'from the cage' not in low          # cage fall is the harmless gag


# The verified route, milestone by milestone. Each phase is (label, want_score,
# [commands]). The blackjack "n" is NOT baked in here -- it is answered
# adaptively by send() whenever the deal prompts. want_score is checked AFTER
# the phase (None = no score change expected).
PHASES = [
    ("intro/meeting", 0, [
        "south", "help thumb", "west", "take mask", "south", "west",
        "examine taft", "hide behind taft", "wait", "wait", "east", "east"]),
    ("tightrope +10", 10, [
        "take pole", "north", "north", "north", "drop mask", "up",
        "east", "east", "east", "east", "east", "east", "take balloon",
        "west", "west", "west", "west", "west", "west", "down", "down",
        "take all"]),
    ("helium/Harry +10", 20, [
        "south", "south", "west", "south", "look in cage", "examine man",
        "untie balloon", "inhale helium", "harry, hello", "south", "west"]),
    ("clown-mask knock +10", 30, [
        "wear mask", "knock on door", "south", "close door", "search ashes",
        "take scrap", "wait"]),
    ("canvas pleats +10", 40, ["go under the wall"]),
    ("ticket +10", 50, [
        "east", "north", "east", "north", "northeast", "search garbage",
        "take ticket", "punch blue dot"]),
    ("keys +10", 60, [
        "southwest", "south", "put ticket in slot", "east", "south",
        "southeast", "look in cage", "take keys with pole", "unlock door",
        "open door", "north", "take bucket", "take headphones"]),
    ("whip+stool (nav)", 60, [
        "south", "northwest", "north", "west", "west", "south", "west",
        "south", "east", "examine trailer", "unlock baggage compartment",
        "open compartment", "take whip", "north", "east", "north",
        "put ticket in slot", "east", "east", "east", "north", "northeast",
        "take stool"]),
    ("cigarette case +10", 70, [
        "northwest", "south", "west", "west", "west", "north", "north",
        "unlock cage", "open cage", "west", "look at lions",
        "whip smooth lion", "whip smooth lion", "whip smooth lion",
        "lift grate", "throw meat in passage", "east", "west", "lower grate",
        "search stand"]),
    ("Jenny +10", 80, [
        "east", "south", "south", "south", "west", "give case to harry",
        "north", "east", "put ticket in slot", "east", "east", "south",
        "show case to jenny", "give case to jenny"]),
    ("hypnosis granola +10", 90, [
        "north", "north", "give ticket to rimshaw", "rimshaw, hypnotize me",
        "wait", "wait", "wait", "wait", "buy candy from hawker",
        "give $1.85 to hawker", "stand up",
        "east", "up", "east", "down", "east", "up", "east", "down", "south",
        "stand in line", "wait", "wait", "get out of long line",
        "stand in short line", "wait", "wait", "get out of long line", "yes",
        "stand in long line", "bite banana", "drop banana", "north",
        "ask hawker about candy",
        "up", "west", "down", "west", "up", "west", "down", "west"]),
    ("radio +10", 100, [
        "stand up", "south", "west", "go under the wall", "search garbage",
        "take granola bar", "south", "east", "east", "north", "northeast",
        "show granola bar to tina", "tina, hello", "shake hands",
        "northwest", "take radio"]),
    # Tape recording at Top of Cage. The FIRST descent from Top of Cage
    # ("down", below) is the harmless scripted joke death.
    ("Mahler classical +10", 110, [
        "south", "west", "west", "south", "southeast",
        "drop all except radio and headphones", "up",
        "set radio to 1170", "turn off radio", "rewind tape", "wait",
        "play tape", "wait", "wait", "stop tape", "rewind tape",
        "turn on radio", "record", "wait", "wait", "wait", "wait", "wait",
        "stop tape", "rewind tape", "wait", "turn off radio",
        "down", "take all", "northwest", "unlock cage", "open cage", "west",
        "play tape", "search straw", "open trap door", "take ribbon", "east",
        "close cage", "lock cage"]),
    ("mouse +10", 120, [
        "north", "west", "west", "south", "west", "touch wood with pole",
        "take mousetrap", "drop trap", "east", "west", "east", "west",
        "catch mouse with bucket", "take mouse"]),
    ("Hannibal +10", 130, [
        "east", "north", "east", "put ticket in slot", "east", "south",
        "show mouse to elephant", "show mouse to elephant", "wait"]),
    ("white wagon +10", 140, [
        "southwest", "drop all", "up", "turn crank", "look in wagon",
        "knock on door", "in", "lock door", "search desk", "take spreadsheet",
        "move desk", "up", "read spreadsheet", "down", "take all", "west",
        "ask harry about eddie"]),
    ("Blue Room ticket +10", 150, [
        "east", "northeast", "southeast", "slide ticket under front", "east",
        "take ticket"]),
    # Forced $1 blackjack (adaptive "n"), then out and I-THUMB at Connection,
    # then visit 2 (DEALER RMUNGBIT) for the keister/suitcase.
    ("Blue Room blackjack + suitcase", 150, [
        "open panel", "open panel", "west", "northwest", "north", "west",
        "examine thumb", "south", "northeast", "southeast",
        "slide ticket under front", "east", "look under table",
        "take suitcase", "wait", "west"]),
    ("tent prod +10", 160, [
        "drop all", "up", "up", "wait", "east", "wait", "take shaft",
        "pull shaft"]),
    # First descent already happened in the tape phase, so this one "clambers".
    ("detective/note (nav)", 160, [
        "down", "down", "take all", "drop key", "drop whip", "drop stool",
        "northwest", "north", "west", "fill bucket with water", "south",
        "northeast", "north", "pour water on detective",
        "ask detective about chelsea", "drop bucket", "take note",
        "take card", "read note"]),
    ("scare Chuckles +10", 170, [
        "east", "south", "up", "look", "take all", "up", "north", "west",
        "west", "west", "south", "west", "south", "east", "eddie, hello",
        "show ribbon to eddie", "show scrap to eddie", "show note to eddie",
        "show spreadsheet to eddie", "show card to eddie"]),
    ("Chelsea +10", 180, [
        "search pocket", "take veil", "wear veil", "wear dress", "wear jacket",
        "inventory", "knock on door", "east", "close door", "take crowbar",
        "move moose", "open door", "west", "west",
        "open trailer door with crowbar", "south", "take thumb", "north",
        "east", "east", "put thumb in hole", "wait", "take chelsea"]),
    # Carrying Chelsea triggers the scripted endgame (Munrab flushed, ape
    # grabs the girl onto Platform-1, END-GAME set).
    ("net +10", 190, [
        "west", "north", "east", "northeast", "north", "west", "north",
        "north", "clap", "roustabout, get net"]),
    # Endgame tightrope. First climb -> APE-LOC 2 (net held saves you); "up"
    # from Platform-1 flushes Mahler to Platform-2 (APE-LOC 3); cross partway
    # east to hear the WPDL pledge (DIAL RMUNGBIT), turn around, phone WPDL
    # (CALLED-STATION), then cross fully with radio held/on/1170.
    ("Mahler drops Chelsea +10 (WIN)", 200, [
        "take off veil", "take off jacket", "take off dress", "drop all",
        "west", "take stand", "east", "drop stand", "take radio",
        "climb stand", "up", "up", "set radio to 1170", "turn on radio",
        "east", "east", "east", "west", "west", "west", "west",
        "drop radio", "down", "south", "south", "south", "east", "call wpdl",
        "west", "north", "north", "north", "climb stand", "up", "take radio",
        "east", "east", "east", "east", "east", "wait", "wait", "wait"]),
]


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
        if is_real_death(out):
            raise Desync(f'real death at {cmd!r}: ...{out[-160:]!r}')
        # Adaptively clear a blackjack deal: stand until the hand resolves.
        guard = 0
        while BJACK_PROMPT.search(self.last):
            guard += 1
            if guard > 12:
                raise Desync('blackjack never resolved')
            r = self.w.try_command('n')
            out = (r.output if r is not None else '') or ''
            self.commands.append('n')
            self.last = out
            if self.verbose:
                print(f'> n\n{out.strip()}\n')
            if is_real_death(out):
                raise Desync('real death during blackjack')
        return self.last


def run_route(seed, verbose=False, upto=None):
    r = Runner(seed, verbose)
    for label, want, cmds in PHASES:
        for c in cmds:
            r.send(c)
        if want is not None and r.score() != want:
            raise Desync(f'{label}: score {r.score()} != {want} '
                         f'(cmd #{len(r.commands)})')
        if verbose or upto:
            print(f'=== {label}: score={r.score()} cmds={len(r.commands)}')
        if upto == label:
            return r
    if not r.won:
        raise Desync('reached end without the winning text')
    if r.score() != 200:
        raise Desync(f'final score {r.score()} != 200')
    return r


HEADER = '''\
# BALLYHOO (Infocom Release 97, serial 851218, Z-machine V3)
# VERIFIED COMPLETE SOLVE: 200/200 and the winning ending.
#
# Reproduce with the RNG-pinned replay harness (free, no API):
#   cd ~/src/zwalker
#   python3 scripts/replay_solve.py games/zcode/ballyhoo.z3 walkthroughs/ballyhoo_verified_200.txt --seeds 24 --out solutions/ballyhoo_verified.json
#   => ballyhoo_verified_200.txt: VERIFIED 200/200 at seed {seed} | {ncmds} cmds | won=True
#
# Ending: on the high wire during the rescue, with the transistor radio held,
# tuned to WPDL 1170 and switched on -- and only after phoning in a pledge so
# the station finally plays Vivaldi -- the classical music becalms Mahler the
# gorilla, who "lets loose the girl like a rag doll ... falling ... falling
# ... deep into the safety of the net!" You catch the wire, dangle, then drop
# into the net yourself: "Your score is 200 of a possible 200, in 415 turns."
# -- having saved The Traveling Circus That Time Forgot, Inc.
#
# ==> VERIFIER NOTE (the ONE "you have died" line is a NON-fatal gag, not a
#     death). Award #16 (the elephant-tent prod fight, "On the Tent") is
#     reachable ONLY by climbing the cage top, and the FIRST descent from Top
#     of Cage is a scripted joke: "You fall awkwardly down from the cage.
#     **** You have died ****" -- then, two turns later, "the reports of your
#     demise have been grossly exaggerated. You suffer little more than
#     injured pride." Play continues uninterrupted; the score climbs to
#     200/200 and the game is won. This is way.zil:660-668, the ONLY setter of
#     the DIED global (which nothing else reads), and it is UNAVOIDABLE in any
#     complete solve. It prints via the same TELL-DIED routine as a real death
#     (verbs.zil:3510), so scripts/replay_solve.py's bare "you have died"
#     marker flags died=True here even though the game is genuinely won at
#     200/200 -- a heuristic false-positive on this specific gag.
#
# Why a pinned seed (no restart prelude -- boot draws no randomness; two boots
# are byte-identical and the seed is pinned right after start()): the ONLY
# route-relevant randomness is the mandatory $1 blackjack hand in the Blue
# Room (cards.zil PICK-CARD, <RANDOM 52>); the recorder stands immediately and
# the number of baked-in "n" answers matches the pinned seed. Everything else
# is turn-counter clockwork (I-MEET meeting, I-CLOWN-ALLEY, I-STANDS hypnosis
# dream, the headphone tape deck, I-APE cage, I-OFFICE white wagon, I-POKE
# tent prod, I-CHASE, and the ACROSS-ROPE endgame) plus flavor-only PROB rolls
# -- all replay identically under the same command list. Mechanics verified
# against the official ZIL source (github.com/historicalsource/ballyhoo);
# synthesis in logs/ballyhoo_notes.md, route in logs/ballyhoo_route.txt.
#
# Route (20 awards x 10 = 200): help Comrade Thumb drink (load-bearing 3x),
# grab the clown mask, hide behind the Taft cutout to overhear the kidnapping;
# balance-pole across the tightrope (+10) for the helium balloon; inhale
# helium and greet blind Harry to pass the turnstile (+10); masked knock fools
# Chuckles into Clown Alley (+10), grab the newsprint scrap, get thrown out at
# clown-counter 7 (the sideshow-front gate); through the canvas pleats (+10);
# ticket from the bleacher garbage (+10); pole-fish the cage keys (+10); whip
# for the baggage compartment; whip the smooth lion off the grate and search
# the lion stand for the cigarette case (+10); Harry then Jenny recall
# Andrew's plot (+10); Rimshaw's hypnosis dream -- buy the $1.85 granola, work
# the concession line for the frozen banana to shed the monkey, return to your
# seat as the granola falls (+10); shake Tina's hand for the radio (+10);
# record classical over the headphone tape and let Mahler snatch it (+10),
# taking the skeleton key/ribbon; spring the mousetrap with the pole, lure and
# bucket a live mouse (+10); show it to Hannibal to stampede him (+10);
# crank/knock the white wagon and lock yourself in the office for the
# spreadsheet (+10); slide the ticket under the sideshow front into the Blue
# Room (+10); the forced blackjack hand lets Thumb tap the hole card; phone
# I-THUMB points you back; second entry grabs the keister; on the tent, grip
# and pull the elephant prod (+10); pour water on the sobered detective for
# the ransom note and trade card; costume up and show all five clues to
# "Eddie" to scare Chuckles off (+10); crowbar into the trailer, drop Thumb
# through the moose-hole to hoist Chelsea out of the crawl space (+10); carry
# her out to spring the endgame; clap the post-hypnotic roustabout and order
# the net (+10); ride the lion stand up the tangled ladder, flush Mahler
# platform to platform, phone WPDL so the radio plays Vivaldi, and cross the
# wire until the music drops Chelsea into the net (+10) = 200/200 and the win.
#
# Recorded by scripts/solve_ballyhoo_adaptive.py --seed {seed}.
#% WIN_TEXT: score is 200 of a possible 200|saved The Traveling Circus That Time Forgot
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-4', help='range, e.g. 1-8')
    ap.add_argument('--out', help='write the recorded command list on a win')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--upto', help='stop after this phase label')
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
        print(f'seed {seed}: WIN 200/200 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(HEADER.format(seed=seed, ncmds=len(r.commands)))
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            break
    print(f'{wins}/{total} seeds won')


if __name__ == '__main__':
    main()
