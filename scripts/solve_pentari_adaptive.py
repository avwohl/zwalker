#!/usr/bin/env python3
"""Pentari (Howard A. Sherman, 1998; Release 6 / Serial 030206, Z-machine V5)
adaptive route recorder for the maximum 70/70 "you killed him yourself" ending.

Replays the verified route against GameWalker under a pinned interpreter RNG
seed, adapts around the game's single source of state-relevant randomness -- the
Dark Elf's wander (frob-style random walk around the castle) -- and RECORDS every
command actually sent, so a winning recording replays deterministically through
scripts/replay_solve.py (same GameWalker + seed-after-start() pathway).

Determinism model (see logs/pentari_notes.md for details):
  * Boot draws no randomness (two boots are byte-identical), so the seed is
    pinned right after start() and no `restart` prelude is needed.
  * All spell/puzzle scoring is turn-order deterministic; with an identical
    command list every seed lines up identically.
  * Only the Dark Elf (Vamvevmew) wanders randomly. He does not attack while
    you are `covert`, but two moments depend on where he is:
      1. FWOOSH in the Treasury blasts the oaken chest open ONLY IF the elf is
         NOT in the room; if he is present the fireball hits HIM, he flies into
         a rage and kills you. So we wait for him to wander out first.
      2. Once you carry the freed "daughter" emerald your aura of power betrays
         you: the moment the elf shares your room he steals the emerald and you
         are yanked into the Upper Level, where Morden (who came the instant the
         anti-magic zone shattered) is dueling him. There you `kill elf` -- you
         run him through from behind while he is distracted -- reclaim the
         emerald and crown the platinum box to summon Duke Galin. So we patrol
         the castle until that encounter fires.

Score plan (max 70; the SCORE verb reports "out of a possible 70"):
  city 5; smash seal 15; get scroll 25; get dagger 30; fwoosh-open-chest 40;
  free daughter emerald 45; kill the distracted elf 55; crown the box / summon
  Galin => *** You have won *** 70.

Usage:
  python3 scripts/solve_pentari_adaptive.py --seeds 1-24 --out walkthroughs/pentari_verified_70.txt
  python3 scripts/solve_pentari_adaptive.py --seed 7 --verbose
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

GAME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    'games', 'zcode', 'pentari.z5')

WIN_PAT = re.compile(r'\*\*\*\s*You have won\s*\*\*\*', re.I)
DEATH_PAT = re.compile(r'\*\*\*\s*You have died\s*\*\*\*|does you in|decapitates you',
                       re.I)
# The elf is in the current room (present) vs. gone.
ELF_IN = re.compile(r'Dark Elf walks in|see The Dark Elf here|'
                    r'Dark Elf walks around', re.I)
ELF_OUT = re.compile(r'Dark Elf leaves the room', re.I)
# The "aura of power" encounter that yanks us into the Morden duel.
ENCOUNTER = re.compile(r'senses your aura of power|locked in sorceral combat', re.I)


class Desync(Exception):
    pass


class Runner:
    def __init__(self, seed, verbose=False):
        data = open(GAME, 'rb').read()
        self.w = GameWalker(data)
        self.w.start()
        self.w.vm.rng.seed(seed)      # pin RNG AFTER start() -> deterministic
        self.seed = seed
        self.verbose = verbose
        self.commands = []
        self.last = ''
        self.won = False
        self.elf_here = False

    def score(self):
        return self.w.vm.get_score()

    def send(self, cmd):
        r = self.w.try_command(cmd)
        out = (r.output if r is not None else '') or ''
        self.commands.append(cmd)
        self.last = out
        # Recompute elf presence in the *current* room fresh every turn: the elf
        # prints its daemon line ("walks around ...") on every turn it shares our
        # room, so no elf text at all means it is elsewhere.  (Recomputing rather
        # than latching avoids carrying a stale "here" across a room change.)
        if ELF_OUT.search(out):
            self.elf_here = False
        elif ELF_IN.search(out):
            self.elf_here = True
        else:
            self.elf_here = False
        if self.verbose:
            print(f'> {cmd}\n{out.strip()}\n')
        if WIN_PAT.search(out):
            self.won = True
        elif DEATH_PAT.search(out):
            raise Desync(f'died at "{cmd}": ...{out.strip()[-160:]!r}')
        return out


# Phase A: fixed prologue -- transport to the guild, `covert` to the castle,
# break the anti-magic ward, collect scroll (Fwoosh spell), towel and dagger,
# then step into the Treasury.  Ends at score 30, standing in the Treasury.
PROLOGUE = [
    'N', 'N', 'IN', 'CITY', 'E', 'COVERT', 'S', 'SMASH SEAL',
    'N', 'N', 'N', 'IN', 'GET SCROLL', 'OUT', 'S', 'E', 'N', 'GET TOWEL',
    'S', 'W', 'W', 'GET DAGGER', 'N',
]

# Phase C: from the Treasury walk to the Main Hall -- the castle's most-connected
# hub (four exits) -- and wait there.  The elf's random walk passes through the
# hub often, and the moment he shares our room the "aura of power" encounter
# fires.  If waiting stalls, PATROL tours every room as a fallback flush.
TO_HUB = ['S', 'E']            # Treasury -> Armory -> Main Hall
PATROL = ['N', 'S', 'E', 'U', 'D', 'N', 'N', 'S', 'S', 'D', 'U', 'W',
          'S', 'E', 'W', 'W', 'E', 'S', 'N', 'W', 'N', 'E']  # loop back to hub


def run_route(seed, verbose=False):
    r = Runner(seed, verbose)

    # --- Phase A: prologue (arrival output of the last 'N' tells us if the elf
    #     is waiting in the Treasury). ---
    for c in PROLOGUE:
        r.send(c)
    if r.score() != 30:
        raise Desync(f'prologue score {r.score()} != 30')

    # --- Phase B: open the towel, wait for the elf to leave the Treasury, then
    #     FWOOSH the chest open and free the daughter emerald. ---
    r.send('OPEN TOWEL')
    waits = 0
    while r.elf_here:
        if waits >= 14:
            raise Desync('elf will not leave the Treasury for FWOOSH')
        r.send('Z')
        waits += 1
    r.send('FWOOSH')
    if r.score() != 40:
        raise Desync(f'FWOOSH did not open the chest (score {r.score()})')
    r.send('LOOK')
    r.send('GET SMALL EMERALD')
    if r.score() != 45:
        raise Desync(f'did not free the emerald (score {r.score()})')

    # --- Phase C: go to the hub and wait for the elf to steal the emerald and
    #     drag us into the Morden duel; patrol as a fallback flush. ---
    def encountered():
        return ENCOUNTER.search(r.last) is not None

    for d in TO_HUB:
        r.send(d)
        if encountered():
            break
    hub_waits = 0
    while not encountered() and hub_waits < 30:
        r.send('Z')
        hub_waits += 1
    laps = 0
    while not encountered() and laps < 3:      # fallback: tour every room
        for d in PATROL:
            r.send(d)
            if encountered():
                break
        laps += 1
    if not encountered():
        raise Desync('elf never crossed our path while carrying the emerald')

    # --- Phase D: finish him, reclaim the emerald, crown the box, summon Galin. ---
    r.send('KILL ELF')
    if r.score() != 55:
        raise Desync(f'kill did not land (score {r.score()})')
    r.send('GET SMALL EMERALD')
    r.send('PUT SMALL EMERALD ON BOX')
    r.send('LOOK')
    if not (r.won and r.score() == 70):
        raise Desync(f'no 70/70 win (score {r.score()}, won={r.won})')
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--seeds', default='1-24', help='range, e.g. 1-24')
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
        print(f'seed {seed}: WIN 70/70 in {len(r.commands)} commands '
              f'({r.w.vm.get_turns()} moves)')
        wins += 1
        if a.out:
            with open(a.out, 'w') as f:
                f.write(f'# Pentari verified adaptive solve, seed {seed}, '
                        f'70/70\n')
                for c in r.commands:
                    f.write(c + '\n')
            print('wrote', a.out)
            a.out = None
    print(f'{wins}/{total} seeds reached 70/70')
    sys.exit(0 if wins else 1)


if __name__ == '__main__':
    main()
