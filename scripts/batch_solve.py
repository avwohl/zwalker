#!/usr/bin/env python3
"""Batch-solve the wild corpus: match IF Archive solutions to story files,
extract command routes, replay them in zwalker, and record verified wins.

Pipeline:
  1. MATCH   solution texts (games/ifarchive_solutions/, *.sol/*.txt) to
             story files (games/ifarchive/ + games/zcode/) by normalized
             name-stem containment.
  2. EXTRACT a command list from each solution text. Archive solutions come
             as bare command lists, "> command" transcripts, prose with
             embedded commands, or hint files; the extractor keeps plausible
             command lines and drops prose/headers.
  3. REPLAY  each route in a sandboxed subprocess (seed sweep, step cap) and
             classify: WIN (an Inform "*** ... ***" ending containing
             win-words, or a custom win phrase), NEAR (route ran deep and
             raised the score but no win), FAIL, ERROR.
  4. RECORD  wins as walkthroughs/ifarchive/<game>.txt (replayable, with
             #% WIN_TEXT) and a summary JSON for triage of the NEARs.

Usage:
  python3 scripts/batch_solve.py                 # full run
  python3 scripts/batch_solve.py --limit 20      # first 20 matches
"""
import argparse
import concurrent.futures as cf
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SOLDIR = REPO / "games" / "ifarchive_solutions"
GAMEDIRS = [REPO / "games" / "ifarchive", REPO / "games" / "zcode"]
OUTDIR = REPO / "walkthroughs" / "ifarchive"
REPORT = REPO / "logs" / "batch_solve.json"

WIN_RX = re.compile(
    r"\*\*\*[^*\n]*(won|win|victor|congratulat|success|you did it|the end"
    r"|finis|complete)[^*\n]*\*\*\*", re.I)
DEATH_RX = re.compile(r"\*\*\*[^*\n]*(died|dead|you have failed|game is over"
                      r"|you lose)[^*\n]*\*\*\*", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def game_stems(p: Path):
    """Candidate name stems for a story file (flattened archive names)."""
    stem = p.stem
    parts = re.split(r"__", stem)
    outs = {stem, parts[-1]}
    if len(parts) > 1:
        outs.add(parts[-2])
    return {norm(x) for x in outs if x}


def solution_stem(p: Path) -> str:
    s = p.stem
    s = re.sub(r"(_solution|_walkthrough|_walk|_soln|-hints|_hints|-solution"
               r"|-walk|walkthru|_wt)$", "", s, flags=re.I)
    return norm(s)


# ---------------------------------------------------------------- extraction
_CMD_OK = re.compile(r"^[A-Za-z][A-Za-z0-9 ,.'/-]{0,50}$")
_PROSE_HINTS = re.compile(
    r"\b(the|you|your|this|that|there|which|will|should|would|could|because"
    r"|walkthrough|solution|version|copyright|author|http|www)\b", re.I)


def extract_commands(text: str):
    """Pull a plausible command list out of a solution text."""
    cmds = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or len(line) > 60:
            continue
        # "> command" transcript style always wins
        m = re.match(r"^[>.]\s*([A-Za-z].*)$", line)
        if m:
            cmds.append(m.group(1).strip())
            continue
        # numbered/comma-separated command runs: "n. e. get lamp. s"
        if re.match(r"^\d+[.)]\s+(.*)$", line):
            line = re.sub(r"^\d+[.)]\s+", "", line)
        # comma/period-separated single-line command sequences
        if re.search(r"[,.]", line) and not _PROSE_HINTS.search(line):
            parts = [p.strip() for p in re.split(r"[,.;]", line)]
            good = [p for p in parts if p and _CMD_OK.match(p)
                    and len(p.split()) <= 5]
            if good and len(good) >= max(1, len(parts) - 2):
                cmds.extend(good)
                continue
        # bare short line that looks like a command, not prose
        if _CMD_OK.match(line) and len(line.split()) <= 5 \
                and not _PROSE_HINTS.search(line):
            cmds.append(line)
    # de-noise: drop obvious section headers that slipped through
    return [c for c in cmds if norm(c) not in
            ("walkthrough", "solution", "commands", "hints", "notes", "map")]


def game_dictionary(vm) -> set:
    """The story file's own vocabulary (each word truncated per version).

    Used to separate real commands from walkthrough prose: a candidate line
    whose first token is not in the game's dictionary can only ever produce
    "That's not a verb I recognise."
    """
    dict_addr = vm.header.dictionary
    n_seps = vm.read_byte(dict_addr)
    p = dict_addr + 1 + n_seps
    entry_len = vm.read_byte(p)
    num = vm.read_word(p + 1)
    p += 3
    words = set()
    for i in range(num):
        addr = p + i * entry_len
        try:
            w, _ = vm.decode_zstring(addr)
        except Exception:  # noqa: BLE001
            continue
        if w:
            words.add(w)
    return words


# ------------------------------------------------------------------- replay
def _replay(game: str, cmds_json: str) -> dict:
    """Subprocess worker: dictionary-filter the commands, replay, classify."""
    sys.path.insert(0, str(REPO))
    from zwalker.walker import GameWalker  # noqa: PLC0415
    cmds = json.loads(cmds_json)
    data = Path(game).read_bytes()
    # Dictionary filter: drop lines whose first word the game cannot parse.
    probe = GameWalker(data)
    vocab = game_dictionary(probe.vm)
    trunc = 6 if probe.vm.header.version <= 3 else 9
    def _known(word):
        return word.lower()[:trunc] in vocab
    filtered = []
    for c in cmds:
        toks = c.lower().split()
        if toks and _known(toks[0]) and (
                len(toks) == 1
                or sum(_known(t) for t in toks) >= (len(toks) + 1) // 2):
            filtered.append(c)
    cmds = filtered
    if len(cmds) < 4:
        return {"outcome": "NO-CMDS", "win_step": None, "seed": None,
                "steps_run": 0, "final": f"{len(cmds)} dict-valid commands"}

    best = {"outcome": "FAIL", "win_step": None, "seed": None,
            "steps_run": 0, "final": ""}
    for seed in (1, 2, 3):
        try:
            w = GameWalker(data)
            w.start()
            w.vm.rng.seed(seed)
            win_at = None
            last = ""
            for i, c in enumerate(cmds):
                r = w.try_command(c)
                out = (r.output if r is not None else "") or ""
                last = out or last
                if WIN_RX.search(out):
                    win_at = i
                    break
                if DEATH_RX.search(out):
                    break
            if win_at is not None:
                return {"outcome": "WIN", "win_step": win_at, "seed": seed,
                        "steps_run": win_at + 1, "final": last[-200:],
                        "cmds": cmds}
            if i + 1 > best["steps_run"]:
                best = {"outcome": "FAIL", "win_step": None, "seed": seed,
                        "steps_run": i + 1, "final": last[-200:]}
        except Exception as e:  # noqa: BLE001
            best = {"outcome": "ERROR", "win_step": None, "seed": seed,
                    "steps_run": 0, "final": f"{type(e).__name__}: {e}"[:200]}
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()

    games = {}
    for d in GAMEDIRS:
        for p in sorted(d.glob("*.z[1-8]")):
            for st in game_stems(p):
                games.setdefault(st, p)

    matches = []
    for sol in sorted(SOLDIR.iterdir()):
        if sol.suffix.lower() not in (".sol", ".txt", ".wt"):
            continue
        st = solution_stem(sol)
        if not st:
            continue
        hit = games.get(st)
        if hit is None:
            # containment fallback -- STRONG only: the shorter stem must be
            # >=6 chars and >=60% of the longer, else "heist" matches "A
            # Matter of Heist Urgency" and the route replays the wrong game.
            for gs, gp in games.items():
                shorter, longer = sorted((st, gs), key=len)
                if len(shorter) >= 6 and shorter in longer \
                        and len(shorter) / len(longer) >= 0.6:
                    hit = gp
                    break
        if hit is not None:
            matches.append((sol, hit))
    if a.limit:
        matches = matches[: a.limit]
    print(f"{len(matches)} solution->game matches "
          f"({len(games)} game stems, {len(list(SOLDIR.iterdir()))} solutions)",
          flush=True)

    t0 = time.time()
    results = []
    with cf.ProcessPoolExecutor(max_workers=a.workers) as ex:
        futs = {}
        for sol, game in matches:
            cmds = extract_commands(sol.read_text(errors="replace"))
            if len(cmds) < 4:
                results.append({"solution": sol.name, "game": game.name,
                                "outcome": "NO-CMDS", "n_cmds": len(cmds)})
                continue
            fut = ex.submit(_replay, str(game), json.dumps(cmds))
            futs[fut] = (sol, game, cmds)
        for i, fut in enumerate(cf.as_completed(futs), 1):
            sol, game, cmds = futs[fut]
            try:
                rec = fut.result(timeout=300)
            except Exception as e:  # noqa: BLE001
                rec = {"outcome": "WORKER-FAIL", "final": str(e)[:120]}
            rec.update({"solution": sol.name, "game": game.name,
                        "n_cmds": len(cmds)})
            results.append(rec)
            if rec["outcome"] == "WIN":
                OUTDIR.mkdir(parents=True, exist_ok=True)
                route = OUTDIR / (game.stem + ".txt")
                body = [f"# auto-extracted from IF Archive solution {sol.name}",
                        f"# verified WIN at seed {rec['seed']} "
                        f"(step {rec['win_step']})",
                        "#% WIN_TEXT_SUFFICIENT: 1"]
                body += rec.get("cmds", cmds)[: rec["win_step"] + 1]
                route.write_text("\n".join(body) + "\n")
                rec.pop("cmds", None)
            if i % 25 == 0:
                print(f"  [{i}/{len(futs)}] {time.time()-t0:.0f}s", flush=True)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"results": sorted(
        results, key=lambda r: r["solution"])}, indent=1) + "\n")

    from collections import Counter
    c = Counter(r["outcome"] for r in results)
    print(f"\nOUTCOMES: {dict(c.most_common())}")
    wins = [r for r in results if r["outcome"] == "WIN"]
    for r in wins[:15]:
        print(f"  WIN {r['game']} <- {r['solution']} "
              f"(step {r['win_step']}, seed {r['seed']})")
    print(f"routes -> {OUTDIR}; report -> {REPORT} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
