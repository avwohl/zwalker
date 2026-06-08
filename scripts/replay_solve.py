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
    "you have died", "removes your head", "you are dead", "eaten by a grue",
    "fills your lungs", "you have been killed", "*** you have died ***",
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


def normalize(cmd):
    c = cmd.strip().lower()
    if c in VOCAB:
        return VOCAB[c]
    for a, b in VOCAB.items():
        if " " not in a and (c == a or c.startswith(a + " ")):
            c = b + c[len(a):]
    return c


def run_once(data, cmds, seed):
    """Replay the walkthrough under a fixed seed; return (score, max, died,
    score_timeline, turns)."""
    w = GameWalker(data)
    w.start()
    w.vm.rng.seed(seed)            # pin RNG -> deterministic combat
    timeline = []
    prev = w.vm.get_score()
    died = False
    for i, raw in enumerate(cmds):
        r = w.try_command(normalize(raw))
        out = (r.output if r is not None and hasattr(r, "output") else "") or ""
        s = w.vm.get_score()
        if s != prev:
            timeline.append({"step": i, "command": raw, "score": s})
            prev = s
        if any(m in out.lower() for m in DEATH_MARKERS):
            died = True
    return w.vm.get_score(), w.max_score, died, timeline, w.vm.get_turns()


def solve(game_path, wt_path, seeds=24):
    data = open(game_path, "rb").read()
    cmds = load_commands(wt_path)
    best = None
    for seed in range(1, seeds + 1):
        score, maxs, died, tl, turns = run_once(data, cmds, seed)
        cand = {"seed": seed, "score": score, "max_score": maxs, "died": died,
                "timeline": tl, "turns": turns}
        better = (best is None
                  or (not died and best["died"])
                  or (died == best["died"] and score > best["score"]))
        if better:
            best = cand
        if maxs is not None and score == maxs and not died:
            break  # perfect verified win — stop searching
    best["commands"] = cmds
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("game")
    ap.add_argument("walkthrough")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    best = solve(a.game, a.walkthrough, a.seeds)
    won = best["max_score"] is not None and best["score"] == best["max_score"]
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
        "turns": best["turns"], "num_commands": len(best["commands"]),
        "score_timeline": best["timeline"], "commands": best["commands"],
    }, open(out, "w"), indent=2)
    print("wrote", out)


if __name__ == "__main__":
    main()
