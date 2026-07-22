#!/usr/bin/env python3
"""Replay a route file against a story file and print the full transcript.

The iteration tool for route derivation (human or agent): edit the route,
re-run, read the per-command transcript, repeat. Same replay semantics as
the verifiers (seed pinned AFTER start; '#' lines are comments; `#%`
directives ignored here).

  python3 scripts/try_route.py <game.z?> <route.txt> [--seed N] [--tail M]

Prints [i] > command / output for every step, flags the first Inform-style
"*** ... ***" ending, and exits 0 on a win-looking ending, 1 otherwise.
"""
import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from zwalker.walker import GameWalker  # noqa: E402

WIN_RX = re.compile(r"\*\*\*[^*\n]*(you have won|you won|victor|congratulat"
                    r"|you did it|finis|fin de l|occupant|rightful"
                    r"|freedom|good time|survived|you have escaped"
                    r"|managed to escape|have a good time)[^*\n]*\*\*\*", re.I)
# An Inform victory sets deadflag=2 and prints a "*** ... ***" banner; a LOSS
# (death, capture, failure, time-out) is deadflag=1 and shares the banner
# shape, so classify losers explicitly. A non-loss ending banner (or an
# explicit WIN word / declared WIN_PHRASE) is a win.
LOSS_RX = re.compile(r"\*\*\*[^*\n]*(die[ds]?|dead|you have failed|failed"
                     r"|you lose|lost|game over|perish|killed|fatal"
                     r"|captured|caught|arrested|imprisoned|trapped forever"
                     r"|out of time|too late|time.s up|defeat|doomed"
                     r"|the end of your|paranoi)[^*\n]*\*\*\*", re.I)
END_RX = re.compile(r"\*\*\*[^*\n]+\*\*\*")


def is_win(out: str, win_phrase=None) -> bool:
    if win_phrase and win_phrase in out:
        return True
    if LOSS_RX.search(out):
        return False
    if WIN_RX.search(out):
        return True
    # a non-loss "*** ... ***" ending banner (custom victory phrasing) is a win
    return bool(END_RX.search(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("route")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--win-phrase", default=None,
                    help="also accept this exact substring as a win")
    ap.add_argument("--tail", type=int, default=None,
                    help="only print the last M steps")
    a = ap.parse_args()

    # a leading "# WIN_PHRASE: ..." in the route is auto-picked-up
    wp = a.win_phrase
    for _l in Path(a.route).read_text().splitlines():
        _m = re.match(r"#\s*WIN_PHRASE:\s*(.+)", _l)
        if _m:
            wp = _m.group(1).strip()

    cmds = [l.strip() for l in Path(a.route).read_text().splitlines()
            if l.strip() and not l.strip().startswith("#")]
    w = GameWalker(Path(a.game).read_bytes())
    print("== START ==")
    print((w.start() or "").strip()[:1500])
    w.vm.rng.seed(a.seed)

    won = False
    logs = []
    for i, c in enumerate(cmds):
        try:
            r = w.try_command(c)
        except Exception as e:  # noqa: BLE001
            logs.append((i, c, f"[INTERPRETER ERROR {type(e).__name__}: {e}]"))
            break
        out = ((r.output if r is not None else "") or "").strip()
        logs.append((i, c, out))
        if (wp and wp in out) or END_RX.search(out):
            won = is_win(out, wp)
            if won or LOSS_RX.search(out):
                break   # stop on a decisive win or an explicit losing ending

    show = logs if a.tail is None else logs[-a.tail:]
    for i, c, out in show:
        print(f"\n[{i}] > {c}\n{out[:900]}")
    print(f"\n== {'WIN' if won else 'NO WIN'} after {len(logs)} steps "
          f"(seed {a.seed}) ==")
    sys.exit(0 if won else 1)


if __name__ == "__main__":
    main()
