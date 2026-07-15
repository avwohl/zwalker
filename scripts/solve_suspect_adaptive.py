#!/usr/bin/env python3
"""Suspect (r14) adaptive route recorder.

Drives Infocom's Suspect to the true winning ending -- Michael Wellman and
Alicia Barron arrested for the murder of Veronica -- over the GameWalker
pathway under a pinned interpreter RNG seed, and RECORDS every command it
actually sends (including the RESTART/YES boot-RNG prelude and every "yes"
needed to answer a "Do you want to keep waiting?" prompt), so the recording
replays deterministically through scripts/replay_solve.py.

Determinism model (ZIL citations in logs/suspect_notes.md):
  * Suspect draws RNG at boot, so the recording opens with `restart`/`yes`:
    the RESTART opcode re-runs GO with the RNG already seeded, pinning the
    whole party schedule.  (Boot the walker twice -> byte-different; after
    restart under a fixed seed -> identical.)
  * The mansion runs on a party clock (SCORE = hours, MOVES = minutes,
    events.zil:4).  NPC movement and the murder-discovery chain fire on
    RNG-varied timers, so each rendezvous uses `wait for <person>`
    (V-WAIT-FOR, verbs.zil:2289) -- one command that burns many minutes
    until the awaited NPC arrives.  When an in-game event prints during a
    wait, V-WAIT asks "keep waiting?"; the recorder answers with `yes`
    (recording each) until the wait completes.
  * Michael hides the Trust folder in the BMW trunk on his own timer
    (I-MICHAEL-HIDES-FOLDER, people.zil:638), so no garage stake-out is
    needed -- just crowbar the trunk once he has left.

Win = CASE-OVER's correct branch (events.zil:307), reached by giving the
detective all twelve clues (DETECTIVE-SEEN == DETECTIVE-CONVINCED = 12,
people.zil:3669) then `detective, arrest michael and alicia`.  The detective
auto-counts the corpse and the planted lariat when he searches the office
(people.zil:4287, DETECTIVE-SEEN = 2); the recorder supplies the other ten.
Intercept him ROAMING -- at the ballroom fireplace he flips to arresting
YOU (I-START-ARREST, people.zil:4290), which he cannot do while
DETECTIVE-SEEN > 4 (people.zil:4374).

Usage:
  python3 scripts/solve_suspect_adaptive.py --seed 1 --out walkthroughs/cmds.txt
  python3 scripts/solve_suspect_adaptive.py --seeds 1-4
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'suspect.z3')

WIN_PAT = re.compile(
    r'secures\s+the\s+conviction\s+of\s+Michael\s+for\s+the\s+first\s+degree'
    r'\s+murder\s+of\s+his\s+wife', re.I | re.S)
PROMPT_PAT = re.compile(r'Answer YES or NO|keep waiting', re.I)
# Ways to lose: the detective cuffs YOU, or a fatal deadline passes.
LOSE_PAT = re.compile(
    r"under arrest for the murder|missed the morning edition|"
    r"convicted of (?:second|first) degree murder", re.I)


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)           # pin RNG AFTER start()
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.log = ''
        self.won = False
        # Boot-RNG prelude: restart re-rolls the party clock on the seeded
        # stream so the whole run is reproducible.
        self.send('restart')
        self.send('yes')

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.log += '\n' + out
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN_PAT.search(out):
            self.won = True
        if LOSE_PAT.search(out):
            raise Desync(f'lost at "{cmd}": ...{out.strip()[-140:]!r}')
        return out

    def wait_for(self, who):
        """`wait for <who>` burns minutes until WHO arrives; answer every
        interrupting "keep waiting?" prompt with a recorded `yes`."""
        out = self.send(f'wait for {who}')
        guard = 0
        while PROMPT_PAT.search(out) and guard < 60:
            out = self.send('yes')
            guard += 1
        return out


# The route.  ('cmd', <command>) issues a command; ('wait', <who>) issues
# `wait for <who>` plus however many `yes` answers the seed needs.  Every
# command actually sent is recorded, so the emitted list replays verbatim.
PLAN = [
    # --- Opening: note the drizzle (rain has slacked off -> clue-12 gate)
    #     and answer the door for Alicia.
    ('cmd', 'west'), ('cmd', 'examine veronica'),
    ('cmd', 'west'), ('cmd', 'west'),
    ('cmd', 'south'), ('cmd', 'south'), ('cmd', 'south'), ('cmd', 'south'),
    ('cmd', 'west'), ('cmd', 'west'), ('cmd', 'south'), ('cmd', 'west'),
    ('cmd', 'open curtains'), ('cmd', 'look through window'),
    ('cmd', 'east'),
    ('cmd', 'look'), ('cmd', 'look'), ('cmd', 'look'),
    ('cmd', 'open front door'),
    # --- Loot the office (BEFORE the body is found): folder, mask+hair,
    #     card, the silver bullet back into your gunbelt.  LEAVE THE LARIAT.
    ('cmd', 'north'), ('cmd', 'west'), ('cmd', 'west'),
    ('cmd', 'south'), ('cmd', 'west'), ('cmd', 'north'),
    ('cmd', 'take folder'), ('cmd', 'take fairy mask'),
    ('cmd', 'look in wastebasket'), ('cmd', 'take card'),
    ('cmd', 'search corpse'), ('cmd', 'take bullet'),
    ('cmd', 'put bullet in gunbelt'),
    ('cmd', 'look in fairy mask'), ('cmd', 'examine dark hair'),
    # --- Kitchen: take the WHOLE trash basket (touching the glass spoils
    #     Alicia's prints).
    ('cmd', 'south'), ('cmd', 'east'), ('cmd', 'north'),
    ('cmd', 'east'), ('cmd', 'east'), ('cmd', 'east'), ('cmd', 'east'),
    ('cmd', 'north'), ('cmd', 'north'), ('cmd', 'north'),
    ('cmd', 'north'), ('cmd', 'north'), ('cmd', 'east'),
    ('cmd', 'take basket'),
    # --- East Coat Closet: Alicia's soaked overcoat.
    ('cmd', 'west'), ('cmd', 'south'), ('cmd', 'south'),
    ('cmd', 'south'), ('cmd', 'south'), ('cmd', 'west'),
    ('cmd', 'take wet overcoat'),
    # --- Library: hide behind the armchair and watch the Michael/Marston
    #     meeting; then race the pair to the fireplace.
    ('cmd', 'east'), ('cmd', 'south'), ('cmd', 'south'), ('cmd', 'south'),
    ('cmd', 'hide behind chair'),
    ('wait', 'marston'),
    ('wait', 'michael'),
    ('cmd', 'unlock north door'), ('cmd', 'open north door'),
    ('cmd', 'north'), ('cmd', 'north'), ('cmd', 'north'),
    ('cmd', 'east'), ('cmd', 'east'),
    ('cmd', 'take paper'),          # snatch the burning investor list
    # --- Garage: crowbar the BMW trunk for the Trust folder (Michael has
    #     already hidden it and gone).  Drop excess baggage for the weight.
    ('cmd', 'west'), ('cmd', 'west'), ('cmd', 'south'),
    ('cmd', 'west'), ('cmd', 'west'), ('cmd', 'west'), ('cmd', 'west'),
    ('cmd', 'north'), ('cmd', 'north'),
    ('cmd', 'unlock door'), ('cmd', 'open door'),
    ('cmd', 'north'), ('cmd', 'west'),
    ('cmd', 'open tool chest'),
    ('cmd', 'drop receipt'), ('cmd', 'drop notebook'), ('cmd', 'drop pen'),
    ('cmd', 'take crowbar'),
    ('cmd', 'open bmw trunk with crowbar'),
    ('cmd', 'drop crowbar'), ('cmd', 'take trust folder'),
    # --- Intercept the roaming detective and hand over the ten clues.
    ('cmd', 'east'), ('cmd', 'south'), ('cmd', 'south'),
    ('wait', 'detective'),
    ('cmd', 'show card to detective'),
    ('cmd', 'show manila folder to detective'),
    ('cmd', 'show trust folder to detective'),
    ('cmd', 'show paper to detective'),
    ('cmd', 'look in fairy mask'),
    ('cmd', 'show hair to detective'),
    ('cmd', 'detective, analyze glass for fingerprints'),   # +3
    ('cmd', 'show wet overcoat to detective'),
    ('cmd', 'tell detective about rain'),                   # +2
    # --- The arrest (DETECTIVE-SEEN == 12).
    ('cmd', 'detective, arrest michael and alicia'),
]

MUST_SEE = [
    (r'rain has slacked off', 'saw the drizzle'),
    (r'thanking you for answering the doorbell', 'let Alicia in'),
    (r'grab the piece of paper just in time', 'snatched the investor list'),
    (r'revealing a trust folder', 'opened the BMW trunk'),
    (r"motive I've been looking for", 'detective got the motive'),
    (r'she was here earlier', 'coat+rain clue landed'),
]


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)
    for kind, arg in PLAN:
        if kind == 'cmd':
            r.send(arg)
        else:
            r.wait_for(arg)
    for pat, name in MUST_SEE:
        if not re.search(pat, r.log, re.I):
            raise Desync(f'milestone missing: {name} (/{pat}/)')
    if not r.won:
        raise Desync('no winning-conviction banner seen')
    return r


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
        h, m = r.w.vm._read_global(17), r.w.vm._read_global(18)
        print(f'seed {seed}: WIN in {len(r.commands)} commands, '
              f'arrested at {h}:{m:02d}')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Suspect recorded adaptive solve, seed {seed}\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds won')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
