#!/usr/bin/env python3
"""Plan A: deterministic walkthrough replay + verify + seed search.

Given a game and a command walkthrough, this finds an interpreter RNG seed under
which the walkthrough does NOT die, replays it deterministically, verifies the
score timeline, and writes a verified solution JSON.

Why seed search: the troll/thief combat in Zork-class games is random, so a
naive replay is non-deterministic (the same walkthrough can score 20 or 200
depending on whether the troll kills you). Pinning the interpreter's RNG seed
(`vm.rng.seed(s)`) makes the whole playthrough reproducible, so a correct
walkthrough either reliably wins at some seed or fails at a fixable step.

Usage:
    python3 scripts/replay_solve.py games/zcode/zork1.z3 scripts/zork1_final_solution.txt
    python3 scripts/replay_solve.py <game.z?> <walkthrough.txt|knowledge json> [--seeds N] [--out PATH]
"""
import sys
import os
import re
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from zwalker.walker import GameWalker  # noqa: E402

# Common walkthrough-word -> Infocom-parser-word fixes (walkthroughs from the
# web often use words the original parser doesn't know).
VOCAB = {
    "upstairs": "up", "downstairs": "down", "go upstairs": "up",
    "go downstairs": "down", "pick up": "take", "look at": "examine",
    "turn on the lamp": "turn on lamp", "n.": "north", "s.": "south",
    "e.": "east", "w.": "west",
}
DEATH_MARKERS = (
    # "eaten by a grue" alone would false-positive on the darkness WARNING
    # ("You are likely to be eaten by a grue."); match the actual kill text.
    # "fills your lungs" alone would false-positive on Enchanter's west gate
    # ("a blast of cold air fills your lungs"); require the drowning phrasing.
    # Bare "you are dead" false-positived on Plundered Hearts' mandatory
    # pre-duel taunt ("You will have no need of her when you are dead.");
    # require the Zork-family kill phrasing ("I'm afraid you are dead.").
    "you have died", "removes your head", "afraid you are dead",
    "slavering fangs of a lurking grue", "water fills your lungs",
    "you have been killed", "*** you have died ***",
)


def load_commands(path):
    """Load a command list from a .txt (one command per line, # comments) or a
    knowledge-style solution.json (list of {command: ...} steps)."""
    if path.endswith(".json"):
        d = json.load(open(path))
        steps = d.get("main_steps") or d.get("commands") or []
        return [s["command"] if isinstance(s, dict) else s
                for s in steps if (s.get("command") if isinstance(s, dict) else s)]
    return [ln.strip() for ln in open(path)
            if ln.strip() and not ln.strip().startswith("#")]


def load_directives(path):
    """Machine directives from walkthrough header comments (still plain
    comments to load_commands, so old walkthroughs are unaffected):

        #% WIN_TEXT: <regex>   -- the game is won when this matches any output
                                  (needed for scoreless games, where there is
                                  no max score to reach)
        #% MAX_SCORE: <N>      -- max score for games the interpreter's
                                  banner/serial map doesn't know
    """
    d = {}
    if not path.endswith(".json"):
        for ln in open(path):
            s = ln.strip()
            if s.startswith("#%"):
                key, _, val = s[2:].partition(":")
                d[key.strip().upper().replace(" ", "_")] = val.strip()
    return d


def normalize(cmd):
    c = cmd.strip().lower()
    if c in VOCAB:
        return VOCAB[c]
    for a, b in VOCAB.items():
        if " " not in a and (c == a or c.startswith(a + " ")):
            c = b + c[len(a):]
    return c


def run_once(data, cmds, seed, win_rx=None, max_override=None):
    """Replay the walkthrough under a fixed seed; return (score, max, died,
    score_timeline, turns, win_seen)."""
    w = GameWalker(data)
    w.start()
    w.vm.rng.seed(seed)            # pin RNG -> deterministic combat
    timeline = []
    prev = w.vm.get_score()
    died = False
    win_seen = False
    for i, raw in enumerate(cmds):
        try:
            r = w.try_command(normalize(raw))
        except Exception:
            # An interpreter fault under THIS seed (e.g. a storew that lands in
            # static memory after a particular RNG-driven Wizard spell). Treat the
            # seed as a dead end and stop replaying it, but do NOT abort the whole
            # seed search -- other seeds may run cleanly to a full win.
            died = True
            break
        out = (r.output if r is not None and hasattr(r, "output") else "") or ""
        s = w.vm.get_score()
        if s != prev:
            timeline.append({"step": i, "command": raw, "score": s})
            prev = s
        if win_rx is not None and win_rx.search(out):
            win_seen = True
        if any(m in out.lower() for m in DEATH_MARKERS):
            died = True
    maxs = max_override if max_override is not None else w.max_score
    return w.vm.get_score(), maxs, died, timeline, w.vm.get_turns(), win_seen


def is_won(score, maxs, died, win_seen, win_rx):
    """The win criterion: reach max score when one is known; when the
    walkthrough declares a WIN_TEXT, that text must also have appeared
    (and it alone decides for scoreless games)."""
    if died:
        return False
    if win_rx is not None:
        return win_seen and (maxs is None or score == maxs)
    return maxs is not None and score == maxs


def solve(game_path, wt_path, seeds=24):
    data = open(game_path, "rb").read()
    cmds = load_commands(wt_path)
    directives = load_directives(wt_path)
    win_rx = (re.compile(directives["WIN_TEXT"], re.I | re.S)
              if "WIN_TEXT" in directives else None)
    max_override = (int(directives["MAX_SCORE"])
                    if "MAX_SCORE" in directives else None)
    best = None
    for seed in range(1, seeds + 1):
        score, maxs, died, tl, turns, win_seen = run_once(
            data, cmds, seed, win_rx, max_override)
        cand = {"seed": seed, "score": score, "max_score": maxs, "died": died,
                "timeline": tl, "turns": turns, "win_seen": win_seen}
        better = (best is None
                  or (not died and best["died"])
                  or (died == best["died"] and score > best["score"]))
        if better:
            best = cand
        if is_won(score, maxs, died, win_seen, win_rx):
            best = cand
            break  # perfect verified win — stop searching
    best["commands"] = cmds
    best["won"] = is_won(best["score"], best["max_score"], best["died"],
                         best["win_seen"], win_rx)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("walkthrough")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    best = solve(a.game, a.walkthrough, a.seeds)
    won = best["won"]
    print(f"{os.path.basename(a.walkthrough)}: VERIFIED {best['score']}/{best['max_score']} "
          f"at seed {best['seed']} | {len(best['commands'])} cmds | "
          f"died={best['died']} | won={won}")

    stem = os.path.splitext(os.path.basename(a.game))[0]
    out = a.out or os.path.join(os.path.dirname(a.game) if a.out else "solutions",
                                f"{stem}_verified.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump({
        "game": a.game, "walkthrough": a.walkthrough, "solver": "replay+seed",
        "rng_seed": best["seed"], "score": best["score"],
        "max_score": best["max_score"], "won": won, "died": best["died"],
        "win_text_seen": best["win_seen"],
        "turns": best["turns"], "num_commands": len(best["commands"]),
        "score_timeline": best["timeline"], "commands": best["commands"],
    }, open(out, "w"), indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
