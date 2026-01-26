#!/usr/bin/env python3
"""
Download and solve more games from the game_list.txt
"""

import urllib.request
import urllib.error
from pathlib import Path
import subprocess
import sys

# Games from game_list.txt that we want to try
PRIORITY_GAMES = [
    # Infocom classics we don't have yet
    ("zork3.z3", "https://eblong.com/infocom/gamefiles/zork3-r25-s860811.z3"),
    ("sorcerer.z3", "https://eblong.com/infocom/gamefiles/sorcerer-r18-s851021.z3"),
    ("spellbreaker.z3", "https://eblong.com/infocom/gamefiles/spellbre-r87-s860904.z3"),
    ("planetfall.z3", "https://eblong.com/infocom/gamefiles/planetfa-r29-s860313.z3"),
    ("stationfall.z3", "https://eblong.com/infocom/gamefiles/stationfal-r107-s870430.z3"),
    ("lurking.z3", "https://eblong.com/infocom/gamefiles/lurking-r203-s870506.z3"),
    ("infidel.z3", "https://eblong.com/infocom/gamefiles/infidel-r22-s830916.z3"),
    ("suspended.z3", "https://eblong.com/infocom/gamefiles/suspend-r8-s840521.z3"),
    ("deadline.z3", "https://eblong.com/infocom/gamefiles/deadline-r27-s831006.z3"),
    ("witness.z3", "https://eblong.com/infocom/gamefiles/witness-r22-s840924.z3"),
    ("suspect.z3", "https://eblong.com/infocom/gamefiles/suspect-r14-s841005.z3"),
    ("cutthroats.z3", "https://eblong.com/infocom/gamefiles/cutthro-r23-s840809.z3"),
    ("seastalker.z3", "https://eblong.com/infocom/gamefiles/seastal-r15-s840501.z3"),
    ("wishbringer.z3", "https://eblong.com/infocom/gamefiles/wishbrin-r68-s850501.z3"),
    ("ballyhoo.z3", "https://eblong.com/infocom/gamefiles/ballyhoo-r97-s851218.z3"),
    ("hhgg.z3", "https://eblong.com/infocom/gamefiles/hhgg-r31-s871119.z3"),
    ("lgop.z3", "https://eblong.com/infocom/gamefiles/lgop-r118-s860730.z3"),
    ("moonmist.z3", "https://eblong.com/infocom/gamefiles/moonmist-r9-s861022.z3"),
    ("plundered.z3", "https://eblong.com/infocom/gamefiles/plundere-r26-s870730.z3"),

    # Infocom z4
    ("nord.z4", "https://eblong.com/infocom/gamefiles/nord-r19-s870722.z4"),
    ("bureaucracy.z4", "https://eblong.com/infocom/gamefiles/bureaucr-r86-s870212.z4"),

    # Infocom z5
    ("beyondzork.z5", "https://eblong.com/infocom/gamefiles/beyondzo-r57-s871221.z5"),
    ("borderzone.z5", "https://eblong.com/infocom/gamefiles/borderzo-r9-s881008.z5"),
    ("sherlock.z5", "https://eblong.com/infocom/gamefiles/sherlock-r21-s871214.z5"),
]

def download_game(filename, url, dest_dir):
    """Download a single game file."""
    dest_path = dest_dir / filename

    if dest_path.exists():
        print(f"  [SKIP] {filename} already exists")
        return True

    try:
        print(f"  [GET]  {filename}")
        req = urllib.request.Request(url, headers={'User-Agent': 'zwalker/0.1'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            dest_path.write_bytes(data)
        print(f"  [OK]   {filename} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"  [FAIL] {filename}: {e}")
        return False

def solve_game(game_path, max_cmds=300):
    """Solve a game using solve_smart.py"""
    try:
        result = subprocess.run(
            ["python", "scripts/solve_smart.py", str(game_path), "--max-cmds", str(max_cmds)],
            capture_output=True,
            text=True,
            timeout=120
        )
        if "✓ DONE" in result.stdout:
            return True
        return False
    except Exception as e:
        print(f"  Error solving: {e}")
        return False

def main():
    games_dir = Path("games/zcode")
    games_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("Downloading and solving more games")
    print("="*60)
    print()

    downloaded = 0
    solved = 0
    failed = 0

    for filename, url in PRIORITY_GAMES:
        game_path = games_dir / filename
        game_name = filename.split('.')[0]
        solution_path = Path(f"solutions/{game_name}_solution.json")

        # Check if already solved
        if solution_path.exists():
            print(f"⊙ {game_name:20} - already solved")
            continue

        # Download if needed
        if not game_path.exists():
            print(f"↓ {game_name:20} - downloading...")
            if download_game(filename, url, games_dir):
                downloaded += 1
            else:
                failed += 1
                continue

        # Solve
        print(f"⟳ {game_name:20} - solving...")
        if solve_game(game_path):
            print(f"✓ {game_name:20} - solved!")
            solved += 1
        else:
            print(f"✗ {game_name:20} - failed to solve")
            failed += 1

        print()

    print()
    print("="*60)
    print("Summary")
    print("="*60)
    print(f"  Downloaded: {downloaded}")
    print(f"  Solved:     {solved}")
    print(f"  Failed:     {failed}")
    print()

if __name__ == "__main__":
    main()
