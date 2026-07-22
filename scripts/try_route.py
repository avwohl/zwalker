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

WIN_RX = re.compile(r"\*\*\*[^*\n]*(won|win|victor|congratulat|success"
                    r"|you did it|the end|finis|complete|fin de"
                    r"|occupant|rightful|escape[ds]?|freedom|good time"
                    r"|survived|home)[^*\n]*\*\*\*", re.I)
# An Inform victory sets deadflag=2 and prints a "*** ... ***" banner; a death
# is deadflag=1. The banners share the "*** ... ***" shape, so a positive
# WIN_RX or a NON-death ending both count. DEATH_RX classifies the losers.
DEATH_RX = re.compile(r"\*\*\*[^*\n]*(died|dead|you have failed|you lose"
                      r"|game over|perish|killed|fatal)[^*\n]*\*\*\*", re.I)
END_RX = re.compile(r"\*\*\*[^*\n]+\*\*\*")


def is_win(out: str, win_phrase=None) -> bool:
    if win_phrase and win_phrase in out:
        return True
    if not END_RX.search(out):
        return False
    if DEATH_RX.search(out):
        return False
    # An ending banner that is not a death: treat as a win (covers custom
    # victory banners -- "FIN DE L'HISTOIRE", escape/freedom endings -- that
    # the positive word list would miss). Positive WIN_RX also always wins.
    return True


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
            break

    show = logs if a.tail is None else logs[-a.tail:]
    for i, c, out in show:
        print(f"\n[{i}] > {c}\n{out[:900]}")
    print(f"\n== {'WIN' if won else 'NO WIN'} after {len(logs)} steps "
          f"(seed {a.seed}) ==")
    sys.exit(0 if won else 1)


if __name__ == "__main__":
    main()
