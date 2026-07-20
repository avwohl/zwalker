#!/usr/bin/env python3
"""Phase 0: build corpus_manifest.json -- the single source of truth for the
two-track corpus (published .z binaries vs zorkie-compiled ZIL/ZILF source).

One row per game, merging three inputs:
  - SRC: the Infocom ZIL sources under ../zorkie/tests/test-games/infocom-zil/
    (+ the zorkie toys and ZILF samples registered in test_zorkie_game.py),
    tagged with the Z-version from the <VERSION> directive / COMPILED .z.
  - PUB: released .z binaries in games/zcode/ (version = header byte 0).
  - walkthroughs/ matched to each, split into PUB routes (*_verified_*) and
    SRC routes (*_zorkie_* / *_zilf_* / *_src_*).

The manifest is data; verify_corpus.py runs the tracks against it and
GAME_SOURCE_MATRIX.md is regenerated from it.
"""
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ZORKIE = Path.home() / "src" / "zorkie"
ZIL_SRC = ZORKIE / "tests" / "test-games" / "infocom-zil"
ZCODE = REPO / "games" / "zcode"
WT = REPO / "walkthroughs"

_VMAP = {"ZIP": 3, "EZIP": 4, "XZIP": 5, "YZIP": 6}

# Games that COMPILE + BOOT from source but have no verified win yet (no
# locally-distributable published binary to derive a route from). Phase-1
# outcome; these are route-derivation candidates for the binary/solve track.
# value = (correct entry relative to the source dir, extra compile flags, version)
SRC_BOOTS = {
    "seastalker": ("seastalker.zil", ["--allow-undefined-routines"], 3),
    "bureaucracy": ("b.zil", ["--allow-undefined-routines"], 4),
    "minizork2": ("MULTI:macros,syntax,dungeon,clock,main,parser,demons,crufty,"
                  "verbs,actions,fights,melee", ["--allow-undefined-routines"], 3),
    "sampler": ("sampler.zil", ["--allow-undefined-routines"], 3),
    "nordandbert": ("nordandbert.zil", [], 4),  # the-infocom-files mirror
    "borderzone": ("spy.zil", [], 5),  # first V5 game: compiles/boots/parses
}
# Confirmed source-incomplete (not zorkie bugs) -- documented, not attempted.
SRC_SOURCE_BLOCKED = {
    # (planetfall + nordandbert historicalsource truncation resolved by
    # repointing those submodules to the more-complete the-infocom-files mirror.)
}


def src_version(game_dir: Path):
    """Z-version of a ZIL source tree: <VERSION ...> directive, else a COMPILED .z."""
    for zil in game_dir.glob("*.zil"):
        m = re.search(r"<VERSION\s+(ZIP|EZIP|XZIP|YZIP|[1-8])\b",
                      zil.read_text(errors="ignore"), re.I)
        if m:
            tok = m.group(1).upper()
            return _VMAP.get(tok, int(tok) if tok.isdigit() else None)
    # fall back to any compiled .z<N> in the tree
    for z in list(game_dir.rglob("*.z[1-8]")):
        return int(z.suffix[-1])
    return None


def pub_version(zfile: Path):
    try:
        return zfile.read_bytes()[0]
    except Exception:
        return None


def load_l2_registry():
    """Parse test_zorkie_game.py GAMES: {name: (src_entry, version, frontier)}."""
    src = (REPO / "scripts" / "test_zorkie_game.py").read_text()
    out = {}
    for m in re.finditer(r'"(\w+)":\s*\{(.*?)\n    \}', src, re.S):
        name, body = m.group(1), m.group(2)
        ver = re.search(r'"version":\s*(\d)', body)
        zil = re.search(r'"zil":\s*[^,]*?/\s*"([^"]+\.zil)"', body)
        out[name] = {
            "version": int(ver.group(1)) if ver else None,
            "frontier": "frontier" in body and "True" in body,
            "src_entry": zil.group(1) if zil else None,
        }
    return out


def match_walkthroughs(name):
    """Return (pub_routes, src_routes) for a game by name heuristics."""
    stem = name.replace("hitchhikersguide", "hhgg").replace("leathergoddesses", "lgop")
    keys = {name, stem, name.replace("-", ""), name[:6]}
    pub, src = [], []
    for w in sorted(WT.glob("*.txt")):
        n = w.name.lower()
        if not any(k and k in n for k in keys):
            continue
        if any(t in n for t in ("_zorkie", "_zilf", "_src", "_source")):
            src.append(w.name)
        elif "_verified" in n or "verified" in n:
            pub.append(w.name)
        else:
            (src if "zorkie" in n else pub).append(w.name)
    return pub, src


def main():
    reg = load_l2_registry()

    # canonical game name -> row
    rows = {}

    # 1. SRC: every Infocom ZIL source dir + version
    for d in sorted(p for p in ZIL_SRC.iterdir() if p.is_dir() and p.name != "zilf"):
        name = {"minizork-1987": "minizork", "minizork-1982": "minizork2",
                "hollywoodhijinx": "hollywoodhijinx", "infocom-sampler": "sampler"
                }.get(d.name, d.name)
        # registry version is authoritative for registered games (its <VERSION>
        # may live in a subfile the directory scan can't see, e.g. stationfall).
        ver = reg.get(name, {}).get("version") or src_version(d)
        rows[name] = {
            "game": name, "src_kind": "zil", "src_dir": d.name,
            "src_version": ver,
            "src_entry": reg.get(name, {}).get("src_entry"),
            "src_win": name in reg and not reg[name]["frontier"],
            "src_frontier": reg.get(name, {}).get("frontier", False),
        }

    # 2. zorkie toys + ZILF samples registered but not in infocom-zil
    for name, info in reg.items():
        if name in rows:
            continue
        rows[name] = {
            "game": name, "src_kind": "zilf/toy", "src_dir": None,
            "src_version": info["version"], "src_entry": info["src_entry"],
            "src_win": not info["frontier"], "src_frontier": info["frontier"],
        }

    # 3. PUB binaries: attach to a matching row or add a pub-only row
    pub_index = {}
    for z in sorted(ZCODE.glob("*.z[1-8]")):
        pub_index[z.stem.lower()] = z
    aliases = {"minizork": "minizork", "hhgg": "hitchhikersguide", "lgop": "leathergoddesses",
               "hollywood": "hollywoodhijinx", "amfv": "amfv", "plundered": "plunderedhearts",
               "lurking": "lurkinghorror"}
    for stem, z in pub_index.items():
        key = aliases.get(stem, stem)
        row = rows.get(key)
        if row is None:
            # try loose contains-match against known rows
            row = next((r for k, r in rows.items() if k in stem or stem in k), None)
        if row is not None and "pub_path" not in row:
            row["pub_path"] = f"games/zcode/{z.name}"
            row["pub_version"] = pub_version(z)
        elif row is None:
            rows[stem] = {"game": stem, "src_kind": None, "src_dir": None,
                          "src_version": None, "src_win": False,
                          "pub_path": f"games/zcode/{z.name}", "pub_version": pub_version(z)}

    # 3b. Phase-1 compile+boot status and source-blocked notes
    for name, (entry, flags, ver) in SRC_BOOTS.items():
        r = rows.get(name)
        if r is not None:
            r["src_boots"] = True
            r["src_entry"] = entry
            r["src_compile_flags"] = flags
            r.setdefault("src_version", ver)
    for name, why in SRC_SOURCE_BLOCKED.items():
        r = rows.get(name)
        if r is not None:
            r["src_blocked"] = why

    # 4. walkthroughs
    for name, row in rows.items():
        pub, src = match_walkthroughs(row.get("src_dir") or name)
        row["pub_walkthroughs"] = pub
        row["src_walkthroughs"] = src

    manifest = {"generated_by": "scripts/build_manifest.py",
                "games": [rows[k] for k in sorted(rows)]}
    out = REPO / "corpus_manifest.json"
    out.write_text(json.dumps(manifest, indent=2) + "\n")

    # summary
    g = manifest["games"]
    print(f"wrote {out} : {len(g)} games")
    from collections import Counter
    src_by_v = Counter(r["src_version"] for r in g if r.get("src_dir") or r.get("src_kind"))
    win_by_v = Counter(r["src_version"] for r in g if r.get("src_win"))
    pub_by_v = Counter(r.get("pub_version") for r in g if r.get("pub_path"))
    print("SRC sources by version:", dict(sorted((k, v) for k, v in src_by_v.items() if k)))
    print("SRC wins by version:   ", dict(sorted((k, v) for k, v in win_by_v.items() if k)))
    print("PUB binaries by version:", dict(sorted((k, v) for k, v in pub_by_v.items() if k)))


if __name__ == "__main__":
    main()
