#!/usr/bin/env python3
"""Spellbreaker adaptive solver/recorder.

Plays Spellbreaker (r87) under a pinned interpreter RNG seed by executing the
directive script logs/spellbreaker_route.txt (mechanics verified against the
original ZIL source, github.com/historicalsource/spellbreaker). The route was
machine-validated at 600/600 across 20 seeds during research; this recorder
replays it through the same GameWalker pathway replay_solve.py uses, so the
recorded command list verifies deterministically.

Adaptive machinery (all values parsed from game text at runtime):
  - spell-fizzle retry loops (every cast can fail until the magic cube is held),
  - the sliding-rock chase (expectimax over the exact I-OTHER-ROCK automaton),
  - Belboz's identity question (parsed, answered from the guild-lore table),
  - the vault weighing: 12 shuffled cubes, jindak glow comparisons, a
    3-weighing decision tree with unknown bright/dim bias; the identified
    time-cube label is captured and reused for later blorples,
  - the roc catch, the malyon/espnis idol, and the tiredness sleep gates.

Usage:
    python3 scripts/solve_spellbreaker_adaptive.py --seeds 1-20
    python3 scripts/solve_spellbreaker_adaptive.py --seed 3 --verbose
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from solve_zork3_adaptive import Player, SeedFailed  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(REPO, "games", "zcode", "spellbreaker.z3")
ROUTE = os.path.join(REPO, "logs", "spellbreaker_route.txt")

# ---------------------------------------------------------------------------
# Sliding-rock chase: exact model of the brown rock's I-OTHER-ROCK automaton
# (ZIL c3.zil), searched with expectimax to pick our green rock's moves.
# Grid is 4x4 (row, col); the northeast/southwest line links (1,0)<->(0,1).
# ---------------------------------------------------------------------------
DIRW = {'north': (-1, 0), 'south': (1, 0), 'east': (0, 1), 'west': (0, -1),
        'northeast': (-1, 1), 'southwest': (1, -1)}


def g_legal(pos, d):
    r, c = pos
    if pos == (1, 0) and d == 'northeast':
        return True
    if pos == (0, 1) and d == 'southwest':
        return True
    if d == 'north':
        return r > 1 or (r > 0 and c > 0)
    if d == 'south':
        return r < 3
    if d == 'east':
        return c < 3
    if d == 'west':
        return c > 1 or (c > 0 and r > 0)
    return False


def apply_d(pos, d):
    if pos == (0, 1) and d == 'southwest':
        return (1, 0)
    if pos == (1, 0) and d == 'northeast':
        return (0, 1)
    dr, dc = DIRW[d]
    return (pos[0] + dr, pos[1] + dc)


def brown_moves(R, O):
    """Possible next positions of the brown rock (2 entries for its PROB-50s)."""
    rrow, rcol = R
    orow, ocol = O
    rl = 4 * rrow + rcol
    ol = 4 * orow + ocol
    drow = abs(rrow - orow)
    dcol = abs(rcol - ocol)

    def mv(d):
        return apply_d(O, d)

    if ol == 1:
        if rl not in (4, 5, 8) and (drow + dcol) % 2 == 0:
            return [mv('southwest')]
        if rl != 5:
            return [mv('south')]
        if rl != 2:
            return [mv('east')]
        return [O]
    if ol == 4:
        if rl not in (1, 2, 5) and (drow + dcol) % 2 == 0:
            return [mv('northeast')]
        if rl != 5:
            return [mv('east')]
        if rl != 8:
            return [mv('south')]
        return [O]
    if ol == 5 and rl in (1, 4):
        return [mv('east') if rl == 4 else mv('south')]
    if rrow == orow:
        if orow == 0 or (orow == 1 and ocol == 0):
            return [mv('south')]
        if orow == 3:
            return [mv('north')]
        return [mv('north'), mv('south')]
    if rcol == ocol:
        if ocol == 0 or (ocol == 1 and orow == 0):
            return [mv('east')]
        if ocol == 3:
            return [mv('west')]
        return [mv('west'), mv('east')]
    if ocol == 0 and orow == 3:
        return [mv('east'), mv('north')]
    if ocol == 3 and orow == 3:
        return [mv('west'), mv('north')]
    if ocol == 3 and orow == 0:
        return [mv('west'), mv('south')]
    if rrow > orow and orow > 0 and (orow > 1 or ocol > 0):
        return [mv('north')]
    if rcol > ocol and ocol > 0 and (ocol > 1 or orow > 0):
        return [mv('west')]
    if rrow < orow and orow < 3:
        return [mv('south')]
    if rcol < ocol and ocol < 3:
        return [mv('east')]
    return [mv('southwest')]


_MEMO = {}


def capture_prob(g, b, depth):
    if depth == 0:
        return 0.0, None
    key = (g, b, depth)
    if key in _MEMO:
        return _MEMO[key]
    best = (-1.0, None)
    for d in ('north', 'south', 'east', 'west', 'northeast', 'southwest'):
        if not g_legal(g, d):
            continue
        ng = apply_d(g, d)
        if ng == b:
            p = 1.0
        else:
            outs = brown_moves(ng, b)
            p = sum(1.0 if nb == ng else capture_prob(ng, nb, depth - 1)[0]
                    for nb in outs) / len(outs)
        if p > best[0]:
            best = (p, d)
    _MEMO[key] = best
    return best


# ---------------------------------------------------------------------------
# Directive handlers
# ---------------------------------------------------------------------------
QA = [("hardest trick", "barsap"), ("golmac", "barbel"), ("coconut", "gustar"),
      ("fireworks", "dimithio"), ("fanucci", "forburn"),
      ("necromancers", "berknip")]


class SB:
    def __init__(self, player):
        self.p = player
        self.time_label = None

    def send(self, cmd):
        return self.p.send(cmd)

    def do_learn(self, line):
        fails = 0
        for _ in range(40):
            out = self.send(line)
            if ('learn the' in out and "can't concentrate" not in out) \
                    or 'complex syllables' in out or 'know that spell by heart' in out:
                return
            if "can't concentrate" in out:
                fails += 1
                if fails >= 3:
                    self.send('sleep')
                    fails = 0
        raise SeedFailed(f"could not learn: {line}")

    def ensure_learn(self, spell):
        for _ in range(20):
            out = self.send('learn ' + spell)
            if 'learn the' in out:
                return
        raise SeedFailed(f"ensure_learn failed for {spell}")

    def cast_until(self, cmd, spell, success):
        out = ""
        for _ in range(20):
            out = self.send(cmd)
            if success in out:
                return out
            if "don't have" in out or 'memorized' in out or 'casting feels wrong' in out:
                self.ensure_learn(spell)
        return out

    def do_until(self, line):
        m = re.match(r'@until (.*?) :: (.*)', line)
        pats, cmds = m.group(1), m.group(2).split(' ;; ')
        fails = 0
        for _ in range(250):
            for cmd in cmds:
                out = self.send(cmd)
                if any(t.lower() in out.lower() for t in pats.split('|')):
                    return
                if "can't concentrate" in out:
                    fails += 1
                    if fails >= 3 and 'sleep' not in cmds[0]:
                        self.send('sleep')
                        fails = 0
        raise SeedFailed(f"@until never satisfied: {pats}")

    def do_fall(self):
        # The roc always catches the first fall within a few turns; a deathless
        # run is required (death would abort via the Player's death check).
        out = self.send('d')
        for _ in range(30):
            if 'releases you' in out:
                return
            out = self.send('z')
        raise SeedFailed("roc never caught us")

    def do_rocks(self):
        g, b = (1, 1), (1, 3)
        for _ in range(80):
            best_p, best_d = -1.0, None
            for k in range(1, 15):
                _MEMO.clear()
                p, d = capture_prob(g, b, k)
                if p > best_p + 1e-9:
                    best_p, best_d = p, d
                if best_p >= 1.0:
                    break
            out = self.send('rock, ' + best_d)
            g = apply_d(g, best_d)
            if 'mesmerized' in out or 'does not move' in out:
                return
            m = re.search(r'brown eyed rock slides gracefully (\w+)', out)
            if m:
                b = apply_d(b, m.group(1))
            elif g == b:
                return
        raise SeedFailed("rock chase: no catch in 80 moves")

    def do_idol(self):
        for _ in range(10):
            out = self.cast_until('malyon idol', 'malyon', 'comes to life')
            if 'comes to life' not in out:
                raise SeedFailed(f"idol malyon failed: {out.strip()[:80]}")
            self.send('z')
            out = self.send('espnis idol')
            if 'begins to yawn' in out:
                for _ in range(4):
                    out = self.send('z')
                    if 'cheek-stretching yawn' in out:
                        return
                continue
            for _ in range(8):
                if 'turns back into basalt' in out:
                    break
                out = self.send('z')
            self.ensure_learn('espnis')
        raise SeedFailed("idol routine never completed")

    def do_belboz(self):
        out = self.send('ask belboz about me')
        for key, ans in QA:
            if key in out.lower():
                out2 = self.send('answer ' + ans)
                if 'Good! I knew it was you' in out2:
                    return
                raise SeedFailed(f"belboz rejected answer {ans}")
        raise SeedFailed(f"belboz question not recognized: {out.strip()[:100]}")

    # -- the vault: 3-weighing counterfeit search with unknown glow bias ----
    def jindak(self):
        out = self.send('jindak')
        if 'identical brightness' in out:
            return 0
        if 'first pile is glowing more brightly' in out:
            return 1
        if 'second pile is glowing more brightly' in out:
            return 2
        raise SeedFailed(f"jindak parse failure: {out.strip()[:100]}")

    def do_vault(self):
        def park(c):
            self.send('take ' + c)
            self.send('put ' + c + ' in zipper')

        def to_pile(c, pile):
            self.send('take ' + c)
            self.send('put ' + c + ' on ' + pile + ' pile')

        for c in ('x1', 'x2', 'x7', 'x8'):
            park(c)
        r1 = self.jindak()
        if r1 == 0:
            park('x3')
            park('x4')
            to_pile('x1', 'first')
            to_pile('x2', 'first')
            r2 = self.jindak()
            to_pile('x7', 'first')
            park('x1')
            r3 = self.jindak()
            if r2 == 0:
                lbl = 'x8' if r3 == 0 else 'x7'
            else:
                lbl = 'x1' if r3 == 0 else 'x2'
        else:
            dir1 = r1
            to_pile('x9', 'first')
            to_pile('x6', 'second')
            to_pile('x1', 'second')
            to_pile('x2', 'second')
            to_pile('x7', 'second')
            park('x10')
            park('x11')
            park('x12')
            r2 = self.jindak()
            if r2 == 0:
                bright = (dir1 == 2)
                to_pile('x10', 'first')
                to_pile('x11', 'second')
                r3 = self.jindak()
                if r3 == 0:
                    lbl = 'x12'
                else:
                    lbl = 'x10' if (r3 == 1) == bright else 'x11'
            elif r2 == dir1:
                bright = (dir1 == 1)
                park('x3')
                to_pile('x4', 'second')
                park('x6')
                to_pile('x10', 'first')
                to_pile('x8', 'first')
                r3 = self.jindak()
                if r3 == 0:
                    lbl = 'x3'
                else:
                    lbl = 'x5' if (r3 == 1) == bright else 'x4'
            else:
                park('x9')
                to_pile('x8', 'first')
                r3 = self.jindak()
                lbl = 'x9' if r3 == 0 else 'x6'
        self.time_label = lbl
        self.send('take ' + lbl)
        out = self.send('blorple ' + lbl)
        if 'Sand Room' not in out:
            raise SeedFailed(f"vault: blorple {lbl} did not reach the Sand Room")

    def run_route(self, lines):
        for line in lines:
            if self.time_label:
                line = line.replace('$TIME', self.time_label)
            if line.startswith('learn '):
                self.do_learn(line)
            elif line == '@fall':
                self.do_fall()
            elif line == '@rocks':
                self.do_rocks()
            elif line == '@idol':
                self.do_idol()
            elif line == '@belboz':
                self.do_belboz()
            elif line == '@vault':
                self.do_vault()
            elif line.startswith('@until '):
                self.do_until(line)
            else:
                self.send(line)


def attempt(data, lines, seed, verbose=False):
    p = Player(data, seed, verbose=verbose)
    sb = SB(p)
    sb.run_route(lines)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()

    data = open(GAME, "rb").read()
    lines = [ln.rstrip("\n") for ln in open(ROUTE)
             if ln.strip() and not ln.strip().startswith("#")]
    seeds = [a.seed] if a.seed is not None else \
        range(int(a.seeds.split("-")[0]), int(a.seeds.split("-")[1]) + 1)

    for seed in seeds:
        try:
            p = attempt(data, lines, seed, verbose=a.verbose)
        except SeedFailed as e:
            print(f"seed {seed}: FAILED - {e}")
            continue
        except Exception as e:  # interpreter fault under this seed
            print(f"seed {seed}: ERROR - {e}")
            continue
        won = p.score == 600
        final = p.log[-1][1] if p.log else ""
        print(f"seed {seed}: score {p.score}/600 turns {p.turns} "
              f"commands {len(p.commands)} won={won}")
        print("ending:", final.strip().replace("\n", " | ")[:300])
        if won and a.out:
            with open(a.out, "w") as f:
                f.write(f"# Spellbreaker recorded adaptive solve, seed {seed}\n")
                for c in p.commands:
                    f.write(c + "\n")
            print("wrote", a.out)
        if won:
            break


if __name__ == "__main__":
    main()
