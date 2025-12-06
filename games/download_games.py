#!/usr/bin/env python3
"""
Download Z-machine games from IF Archive and IFDB for testing.
"""

import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# Priority games for testing (good variety of z3, z5, z8)
GAMES = [
    # Infocom classics (z3)
    ("zork1.z3", "https://eblong.com/infocom/gamefiles/zork1-r119-s880429.z3"),
    ("zork2.z3", "https://eblong.com/infocom/gamefiles/zork2-r63-s860811.z3"),
    ("enchanter.z3", "https://eblong.com/infocom/gamefiles/enchanter-r29-s860820.z3"),
    ("planetfall.z3", "https://eblong.com/infocom/gamefiles/planetfa-r29-s860313.z3"),
    ("lurking.z3", "https://eblong.com/infocom/gamefiles/lurking-r203-s870506.z3"),
    ("wishbringer.z3", "https://eblong.com/infocom/gamefiles/wishbrin-r68-s850501.z3"),

    # Infocom v4+ (z4)
    ("trinity.z4", "https://eblong.com/infocom/gamefiles/trinity-r15-s870628.z4"),
    ("amfv.z4", "https://eblong.com/infocom/gamefiles/amfv-r79-s851122.z4"),

    # IF Archive z3
    ("advent.z3", "https://ifarchive.org/if-archive/games/zcode/advent.z3"),
    ("catseye.z3", "https://ifarchive.org/if-archive/games/zcode/catseye.z3"),

    # IF Archive z5 (Inform games)
    ("photopia.z5", "https://ifarchive.org/if-archive/games/zcode/photopia.z5"),
    ("905.z5", "https://ifarchive.org/if-archive/games/zcode/905.z5"),
    ("curses.z5", "https://ifarchive.org/if-archive/games/zcode/curses.z5"),
    ("tangle.z5", "https://ifarchive.org/if-archive/games/zcode/Tangle.z5"),  # Spider and Web
    ("devours.z5", "https://ifarchive.org/if-archive/games/zcode/devours.z5"),
    ("shade.z5", "https://ifarchive.org/if-archive/games/zcode/shade.z5"),
    ("aisle.z5", "https://ifarchive.org/if-archive/games/zcode/Aisle.z5"),
    ("adverbum.z5", "https://ifarchive.org/if-archive/games/zcode/adverbum.z5"),
    ("booth.z5", "https://ifarchive.org/if-archive/games/zcode/booth.z5"),
    ("galatea.z5", "https://ifarchive.org/if-archive/games/zcode/galatea.z5"),
    ("edifice.z5", "https://ifarchive.org/if-archive/games/zcode/edifice.z5"),
    ("bedlam.z5", "https://ifarchive.org/if-archive/games/zcode/bedlam.z5"),
    ("babel.z5", "https://ifarchive.org/if-archive/games/zcode/babel.z5"),
    ("allroads.z5", "https://ifarchive.org/if-archive/games/zcode/AllRoads.z5"),
    ("acorncourt.z5", "https://ifarchive.org/if-archive/games/zcode/acorncourt.z5"),
    ("bluechairs.z5", "https://ifarchive.org/if-archive/games/zcode/bluechairs.z5"),
    ("cheeseshop.z5", "https://ifarchive.org/if-archive/games/zcode/cheeseshop.z5"),
    ("detective.z5", "https://ifarchive.org/if-archive/games/zcode/detective.z5"),
    ("failsafe.z5", "https://ifarchive.org/if-archive/games/zcode/FailSafe.z5"),
    ("heroes.z5", "https://ifarchive.org/if-archive/games/zcode/heroes.z5"),
    ("lists.z5", "https://ifarchive.org/if-archive/games/zcode/lists.z5"),
    ("spur.z5", "https://ifarchive.org/if-archive/games/zcode/spur.z5"),
    ("toonesia.z5", "https://ifarchive.org/if-archive/games/zcode/toonesia.z5"),
    ("winter.z5", "https://ifarchive.org/if-archive/games/zcode/winter.z5"),

    # IF Archive z8 (larger games)
    ("anchor.z8", "https://ifarchive.org/if-archive/games/zcode/anchor.z8"),
    ("lostpig.z8", "https://ifarchive.org/if-archive/games/zcode/LostPig.z8"),
    ("dreamhold.z8", "https://ifarchive.org/if-archive/games/zcode/dreamhold.z8"),
    ("coldiron.z8", "https://ifarchive.org/if-archive/games/zcode/coldiron.z8"),
    ("acheton.z8", "https://ifarchive.org/if-archive/games/zcode/Acheton.z8"),
    ("adv440.z8", "https://ifarchive.org/if-archive/games/zcode/adv440.z8"),
    ("adv550.z8", "https://ifarchive.org/if-archive/games/zcode/adv550.z8"),
    ("varicella.z8", "https://ifarchive.org/if-archive/games/zcode/varicella.z8"),
    ("savoir.z8", "https://ifarchive.org/if-archive/games/zcode/savoir-faire.z8"),
    ("makeitgood.z8", "https://ifarchive.org/if-archive/games/zcode/makeitgood.z8"),
    ("dracula.z8", "https://ifarchive.org/if-archive/games/zcode/dracula.z8"),
    ("enemies.z8", "https://ifarchive.org/if-archive/games/zcode/Enemies.z8"),
    ("jigsaw.z8", "https://ifarchive.org/if-archive/games/zcode/jigsaw.z8"),
    ("sofar.z8", "https://ifarchive.org/if-archive/games/zcode/sofar.z8"),

    # More z5 for variety
    ("metamorphoses.z5", "https://ifarchive.org/if-archive/games/zcode/metamorphoses.z5"),
    ("theatre.z5", "https://ifarchive.org/if-archive/games/zcode/theatre.z5"),
    ("zombies.z5", "https://ifarchive.org/if-archive/games/zcode/zombies.z5"),
    ("animals.z5", "https://ifarchive.org/if-archive/games/zcode/animals.z5"),
    ("bunny.z5", "https://ifarchive.org/if-archive/games/zcode/bunny.z5"),
    ("candy.z5", "https://ifarchive.org/if-archive/games/zcode/candy.z5"),
]


def download_game(filename, url, dest_dir):
    """Download a single game file."""
    dest_path = dest_dir / filename

    if dest_path.exists():
        print(f"  [SKIP] {filename} already exists")
        return True

    try:
        print(f"  [GET]  {filename} <- {url}")
        req = urllib.request.Request(url, headers={'User-Agent': 'zwalker/0.1'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            dest_path.write_bytes(data)
        print(f"  [OK]   {filename} ({len(data)} bytes)")
        return True
    except urllib.error.HTTPError as e:
        print(f"  [FAIL] {filename}: HTTP {e.code}")
        return False
    except urllib.error.URLError as e:
        print(f"  [FAIL] {filename}: {e.reason}")
        return False
    except Exception as e:
        print(f"  [FAIL] {filename}: {e}")
        return False


def main():
    dest_dir = Path(__file__).parent / "zcode"
    dest_dir.mkdir(exist_ok=True)

    print(f"Downloading {len(GAMES)} Z-machine games to {dest_dir}")
    print()

    success = 0
    failed = 0
    skipped = 0

    for filename, url in GAMES:
        dest_path = dest_dir / filename
        if dest_path.exists():
            skipped += 1
            print(f"  [SKIP] {filename}")
        elif download_game(filename, url, dest_dir):
            success += 1
        else:
            failed += 1

    print()
    print(f"Done: {success} downloaded, {skipped} skipped, {failed} failed")
    print()
    print(f"Games directory: {dest_dir}")
    print(f"Run tests with: python -m zwalker explore {dest_dir}/<game>.z5")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
