#!/usr/bin/env python3
"""
Batch download and solve games from IF Archive
"""

import urllib.request
import urllib.error
from pathlib import Path
import subprocess
import sys

# More games to try
MORE_GAMES = [
    # IF Archive smaller games
    ("fantasydimension.z3", "https://ifarchive.org/if-archive/games/zcode/fantasydimension.z3"),
    ("adventureland.z5", "https://ifarchive.org/if-archive/games/zcode/Adventureland.z5"),
    ("amish.z5", "https://ifarchive.org/if-archive/games/zcode/amish.z5"),
    ("asylum.z5", "https://ifarchive.org/if-archive/games/zcode/Asylum.z5"),
    ("bear.z5", "https://ifarchive.org/if-archive/games/zcode/bear.z5"),
    ("djinni.z5", "https://ifarchive.org/if-archive/games/zcode/djinni.z5"),
    ("farm.z5", "https://ifarchive.org/if-archive/games/zcode/farm.z5"),
    ("heroes.z5", "https://ifarchive.org/if-archive/games/zcode/heroes.z5"),
    ("humbug.z5", "https://ifarchive.org/if-archive/games/zcode/humbug.z5"),
    ("kissing.z5", "https://ifarchive.org/if-archive/games/zcode/kissing.z5"),
    ("mloose.z5", "https://ifarchive.org/if-archive/games/zcode/mloose.z5"),
    ("oprobing.z5", "https://ifarchive.org/if-archive/games/zcode/oprobing.z5"),
    ("parking.z5", "https://ifarchive.org/if-archive/games/zcode/parking.z5"),
    ("rematch.z5", "https://ifarchive.org/if-archive/games/zcode/rematch.z5"),
    ("spur.z5", "https://ifarchive.org/if-archive/games/zcode/spur.z5"),
    ("tattoo.z5", "https://ifarchive.org/if-archive/games/zcode/tattoo.z5"),
    ("misdirect.z5", "https://ifarchive.org/if-archive/games/zcode/misdirect.z5"),
    ("plant.z5", "https://ifarchive.org/if-archive/games/zcode/plant.z5"),
    ("weapon.z5", "https://ifarchive.org/if-archive/games/zcode/weapon.z5"),
    ("toonesia.z5", "https://ifarchive.org/if-archive/games/zcode/toonesia.z5"),
    ("uncle.z5", "https://ifarchive.org/if-archive/games/zcode/uncle.z5"),

    # z8 games
    ("fairyland.z8", "https://ifarchive.org/if-archive/games/zcode/Fairyland.z8"),
    ("varicella.z8", "https://ifarchive.org/if-archive/games/zcode/varicella.z8"),
]

def download_game(filename, url, dest_dir):
    """Download a single game file."""
    dest_path = dest_dir / filename

    if dest_path.exists():
        return None

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'zwalker/0.1'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            dest_path.write_bytes(data)
        return True
    except Exception as e:
        return False

def solve_game(game_path, max_cmds=400):
    """Solve a game using solve_smart.py"""
    try:
        result = subprocess.run(
            ["python", "scripts/solve_smart.py", str(game_path), "--max-cmds", str(max_cmds)],
            capture_output=True,
            text=True,
            timeout=180
        )
        if "✓ DONE" in result.stdout:
            return True
        return False
    except:
        return False

def main():
    games_dir = Path("games/zcode")
    games_dir.mkdir(parents=True, exist_ok=True)

    print("Batch downloading and solving...")
    print()

    downloaded = 0
    solved = 0
    skipped = 0

    for filename, url in MORE_GAMES:
        game_path = games_dir / filename
        game_name = filename.split('.')[0]
        solution_path = Path(f"solutions/{game_name}_solution.json")

        # Check if already solved
        if solution_path.exists():
            skipped += 1
            continue

        # Download if needed
        if not game_path.exists():
            result = download_game(filename, url, games_dir)
            if result is True:
                downloaded += 1
            elif result is False:
                continue

        # Solve
        if solve_game(game_path):
            print(f"✓ {game_name}")
            solved += 1
        else:
            print(f"✗ {game_name}")

    print()
    print(f"Downloaded: {downloaded}, Solved: {solved}, Skipped: {skipped}")

if __name__ == "__main__":
    main()
