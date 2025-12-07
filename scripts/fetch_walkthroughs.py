#!/usr/bin/env python3
"""
Fetch human-generated walkthroughs from IF Archive and other sources
"""

import sys
import json
import requests
from pathlib import Path
from urllib.parse import urljoin

# IF Archive solutions index
IF_ARCHIVE_BASE = "https://www.ifarchive.org/if-archive/solutions/"

# Known solution files for our games
# Format: game_name: (solution_file, base_url)
# If base_url is None, uses IF_ARCHIVE_BASE
KNOWN_SOLUTIONS = {
    # Infocom classics (in hints.many)
    # Note: Most Infocom games are in the compiled hints.many file
    # Individual solutions available via Infocom hints directory
    "zork1": ("hints.many", None),  # Contains Zork I-III
    "zork2": ("hints.many", None),
    "zork3": ("hints.many", None),
    "enchanter": ("hints.many", None),
    "planetfa": ("hints.many", None),

    # Classic adventures
    "advent": ("Adventure.sol", None),
    "acheton": ("acheton.sol", None),

    # Modern IF classics
    "curses": ("Curses.sol", None),
    "trinity": ("trinity.txt", "https://www.ifarchive.org/if-archive/infocom/hints/solutions/"),
    "photopia": ("photopia.sol", None),
    "shade": ("shade-walkthrough.txt", None),
    "aisle": ("putpbaa.sol", None),  # Covers Phone Booth and Aisle
    "lostpig": ("LostPig.sol", None),
    "anchor": ("anchor.sol", None),
    "dreamhold": ("Dreamhold.zip", None),  # ZIP file with walkthrough
    "jigsaw": ("Jigsaw.sol", None),
    "galatea": ("galatea-walkthrough.txt", None),
}


def fetch_solution(game_name: str, output_dir: Path) -> bool:
    """
    Fetch walkthrough for a game from IF Archive

    Returns True if successful
    """
    if game_name not in KNOWN_SOLUTIONS:
        print(f"  No known solution file for {game_name}")
        return False

    solution_info = KNOWN_SOLUTIONS[game_name]
    if isinstance(solution_info, tuple):
        solution_file, base_url = solution_info
        base_url = base_url or IF_ARCHIVE_BASE
    else:
        solution_file = solution_info
        base_url = IF_ARCHIVE_BASE

    url = urljoin(base_url, solution_file)
    output_path = output_dir / f"{game_name}_human_walkthrough.txt"

    if output_path.exists():
        print(f"  ✓ Already have {game_name}")
        return True

    try:
        print(f"  Downloading {solution_file}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        output_path.write_text(response.text)
        print(f"  ✓ Saved {game_name} ({len(response.text)} bytes)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to fetch {game_name}: {e}")
        return False


def parse_solution_txt(text: str) -> list:
    """
    Parse a text walkthrough into command list

    Simple heuristic: lines that look like commands
    """
    commands = []
    for line in text.split('\n'):
        line = line.strip()

        # Skip empty lines, headers, comments
        if not line or line.startswith('#') or line.startswith(';'):
            continue
        if line.startswith('>'):
            line = line[1:].strip()

        # Lines that are likely commands
        if len(line) < 100 and not line.endswith(':'):
            commands.append(line.lower())

    return commands


def main():
    output_dir = Path("walkthroughs")
    output_dir.mkdir(exist_ok=True)

    print(f"Fetching walkthroughs from IF Archive")
    print(f"Output directory: {output_dir}\n")

    success = 0
    failed = 0
    skipped = 0

    for game_name in KNOWN_SOLUTIONS:
        result = fetch_solution(game_name, output_dir)
        if result:
            success += 1
        elif game_name not in KNOWN_SOLUTIONS:
            skipped += 1
        else:
            failed += 1

    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"  ✓ Downloaded: {success}")
    print(f"  ✗ Failed: {failed}")
    print(f"  - Skipped: {skipped}")
    print(f"{'='*60}")

    # Parse downloaded walkthroughs
    print(f"\nParsing walkthroughs...")
    for txt_file in output_dir.glob("*_human_walkthrough.txt"):
        game_name = txt_file.stem.replace("_human_walkthrough", "")
        text = txt_file.read_text()
        commands = parse_solution_txt(text)

        json_path = output_dir / f"{game_name}_commands.json"
        json_path.write_text(json.dumps({
            "game": game_name,
            "source": "IF Archive",
            "commands": commands,
            "total_commands": len(commands)
        }, indent=2))

        print(f"  ✓ {game_name}: {len(commands)} commands")


if __name__ == "__main__":
    main()
