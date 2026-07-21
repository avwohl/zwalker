#!/usr/bin/env python3
"""Fetch the IF Archive's playable Z-machine corpus into games/ifarchive/.

The IF Archive (ifarchive.org) hosts ~1,000 freely downloadable .z3/.z5/.z8
story files (IFComp entries, Spring Thing, the games/zcode tree, ...). IFDB's
15k listings mostly point HERE for the z-code ones -- this is the bulk corpus
the interpreter track can scale on (boot + differential testing needs no
walkthrough; the archive's solutions/ tree feeds the solve track).

The download cache is NOT committed (see .gitignore); this script makes it
reproducible. A manifest (games/ifarchive/manifest.json) records what was
fetched, with sizes and source paths.

Usage:
  python3 scripts/fetch_ifarchive_corpus.py               # fetch all .z3/.z5/.z8
  python3 scripts/fetch_ifarchive_corpus.py --limit 50    # first 50 (smoke run)
  python3 scripts/fetch_ifarchive_corpus.py --ext z3 z5   # subset by extension

Politeness: 4 workers, no re-download of existing files, honest User-Agent.
.zblorb/.z6 are skipped (zwalker has no blorb unwrapper / V6 support yet).
"""
import argparse
import concurrent.futures as cf
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEST = REPO / "games" / "ifarchive"
BASE = "https://ifarchive.org/"
LSLR = BASE + "if-archive/ls-lR"
UA = {"User-Agent": "zwalker-corpus-fetch/1.0 (Z-machine interpreter testing)"}

# names that are clearly not story files despite the extension
_SKIP_RX = re.compile(r"(^|/)(tools|infocom-replacements)/", re.I)


def parse_lslr(text):
    """Yield (archive_path, size) for every .z3/.z5/.z8 under a zcode dir."""
    cur = None
    for line in text.splitlines():
        if line.endswith(":") and not line.startswith("-"):
            cur = line[:-1]
        elif line.startswith("-") and cur and "zcode" in cur:
            parts = line.split(None, 8)
            if len(parts) >= 9:
                name = parts[8]
                if re.search(r"\.(z3|z5|z8)$", name.lower()) \
                        and not _SKIP_RX.search(f"{cur}/{name}"):
                    yield f"{cur}/{name}", int(parts[4])


def fetch_one(rel, size, dest_root):
    # flatten: competition2002/zcode/bofh/bofh.z5 -> competition2002__bofh.z5
    short = rel.replace("if-archive/games/", "").replace("/zcode/", "__")
    short = short.replace("/", "__")
    out = dest_root / short
    if out.exists() and out.stat().st_size == size:
        return short, size, "cached"
    url = BASE + urllib.request.quote(rel)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = r.read()
        out.write_bytes(data)
        return short, len(data), "fetched"
    except Exception as e:  # noqa: BLE001 - record and continue
        return short, 0, f"ERROR {e}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--ext", nargs="*", default=["z3", "z5", "z8"])
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()

    DEST.mkdir(parents=True, exist_ok=True)
    print("fetching ls-lR ...", flush=True)
    req = urllib.request.Request(LSLR, headers=UA)
    with urllib.request.urlopen(req, timeout=120) as r:
        text = r.read().decode("utf-8", "replace")

    wanted = [(rel, size) for rel, size in parse_lslr(text)
              if rel.lower().rsplit(".", 1)[-1] in a.ext]
    if a.limit:
        wanted = wanted[: a.limit]
    print(f"{len(wanted)} files to mirror -> {DEST}", flush=True)

    t0 = time.time()
    results = []
    with cf.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(fetch_one, rel, size, DEST): rel for rel, size in wanted}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            short, size, status = fut.result()
            results.append({"file": short, "size": size, "status": status,
                            "source": futs[fut]})
            if i % 50 == 0 or "ERROR" in status:
                print(f"  [{i}/{len(wanted)}] {short}: {status}", flush=True)

    ok = [r for r in results if "ERROR" not in r["status"]]
    err = [r for r in results if "ERROR" in r["status"]]
    manifest = {"generated_by": "scripts/fetch_ifarchive_corpus.py",
                "base": BASE, "count": len(ok), "errors": len(err),
                "files": sorted(results, key=lambda r: r["file"])}
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"done: {len(ok)} ok, {len(err)} errors, "
          f"{sum(r['size'] for r in ok)//(1<<20)} MiB, "
          f"{time.time()-t0:.0f}s", flush=True)
    return 0 if not err else 1


if __name__ == "__main__":
    sys.exit(main())
