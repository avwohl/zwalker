#!/usr/bin/env python3
"""Draft an adaptive @-route from a verified walkthrough.

A verified walkthrough targets the OFFICIAL binary and bakes in that binary's
RNG outcomes: a fight that took 5 blows there appears as 5 identical commands,
a drift that needed 3 waits appears as 3 waits. A zorkie source build has its
own RNG stream, so those baked runs are exactly where replays stall.

This tool finds runs of repeated commands (and repeated wait/again patterns)
and rewrites them as adaptive @-steps for scripts/rederive_route.py, guessing a
success condition from the command verb. The output is a DRAFT: check the
@-step conditions against the game's actual success messages before recording.

Usage:
    python3 scripts/draft_adaptive_route.py walkthroughs/foo_verified_400.txt \
        [--min-run 2] [--out routes/foo_zorkie_route.txt]
"""
import argparse
import re
import sys

# verb -> (success substring, kind). 'repeat' = send until match;
# 'until' = probe/filler pair (probe, filler, match).
ATTACK_WORDS = ('kill', 'attack', 'fight', 'stab', 'strike', 'hit ', 'slay')
SUCCESS_HINTS = {
    'take': 'taken',
    'get': 'taken',
    'pick': 'taken',
    'open': 'open',
    'dig': 'sand',
    'search': 'find',
    'knock': 'answer',
    'push': 'moves',
    'pull': 'moves',
}
ENEMY_DEAD = 'breathes his last'


def draft(cmds, min_run=2):
    out = []
    i = 0
    while i < len(cmds):
        cmd = cmds[i]
        n = 1
        while i + n < len(cmds) and cmds[i + n] == cmd:
            n += 1
        low = cmd.lower()
        if n >= min_run:
            if any(w in low for w in ATTACK_WORDS):
                out.append(f'@repeat-max{max(16, n * 3)} {ENEMY_DEAD} | {cmd}')
            elif low in ('wait', 'z') and n >= 3:
                # A long wait run is usually "wait for a state change"; the
                # probe is game-specific, so keep the waits but flag them.
                out.append(f'# ADAPTIVE? {n} waits here -- consider '
                           f'"@until <state text> | <probe cmd> | wait"')
                out.extend([cmd] * n)
            else:
                hint = next((v for k, v in SUCCESS_HINTS.items() if low.startswith(k)), None)
                if hint:
                    out.append(f'@repeat-max{max(8, n * 3)} {hint} | {cmd}')
                else:
                    out.extend([cmd] * n)
            i += n
            continue
        out.append(cmd)
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('walkthrough')
    ap.add_argument('--min-run', type=int, default=2)
    ap.add_argument('--out')
    a = ap.parse_args()

    header, cmds = [], []
    for line in open(a.walkthrough):
        s = line.rstrip()
        if s.startswith('#') or not s.strip():
            header.append(s)
        else:
            cmds.append(s.strip())

    routed = draft(cmds, a.min_run)
    n_adaptive = sum(1 for r in routed if r.startswith('@'))
    text = '\n'.join(
        [f'# DRAFT adaptive route from {a.walkthrough}',
         f'# {n_adaptive} adaptive steps; verify each condition before recording.']
        + [h for h in header if h.startswith('#%')]
        + routed) + '\n'
    if a.out:
        open(a.out, 'w').write(text)
        print(f'{a.out}: {len(cmds)} cmds -> {len(routed)} lines, {n_adaptive} adaptive')
    else:
        sys.stdout.write(text)
    return 0


if __name__ == '__main__':
    sys.exit(main())
