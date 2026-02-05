#!/usr/bin/env python3
"""
Download all untested games from game_list.txt
"""

import urllib.request
import urllib.error
from pathlib import Path
import sys
import time

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
GAME_LIST_FILE = PROJECT_ROOT / "games" / "game_list.txt"
GAMES_DIR = PROJECT_ROOT / "games" / "zcode"

def parse_game_list():
    """Parse game_list.txt and return list of untested games."""
    games_to_download = []

    if not GAME_LIST_FILE.exists():
        print(f"Error: {GAME_LIST_FILE} not found")
        return []

    with open(GAME_LIST_FILE, 'r') as f:
        for line in f:
            # Skip comments, empty lines, and section headers
            if line.strip().startswith('#') or line.strip().startswith('=') or not line.strip():
                continue

            # Parse game line: name|ifdb_id|format|url|zwalker_status|zorkie_status|z2js_status
            if '|' in line:
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    game_name = parts[0].strip()
                    file_format = parts[2].strip()
                    download_url = parts[3].strip()
                    zwalker_status = parts[4].strip()

                    # Only download untested games
                    if zwalker_status == 'untested':
                        # Create filename from game name and format
                        # Remove special characters and spaces
                        safe_name = game_name.lower()
                        safe_name = safe_name.replace("'", "")
                        safe_name = safe_name.replace(":", "")
                        safe_name = safe_name.replace(" - ", "_")
                        safe_name = safe_name.replace(" ", "_")
                        safe_name = safe_name.replace("(", "")
                        safe_name = safe_name.replace(")", "")
                        safe_name = safe_name.replace(",", "")
                        safe_name = safe_name.replace("!", "")
                        safe_name = safe_name.replace("?", "")

                        filename = f"{safe_name}.{file_format}"

                        games_to_download.append({
                            'name': game_name,
                            'filename': filename,
                            'url': download_url,
                            'format': file_format
                        })

    return games_to_download

def download_game(game_info, dest_dir):
    """Download a single game file."""
    dest_path = dest_dir / game_info['filename']

    # Check if file already exists
    if dest_path.exists():
        print(f"  [SKIP] {game_info['name']:40} - already exists")
        return 'skipped'

    try:
        print(f"  [GET]  {game_info['name']:40} ", end='', flush=True)
        req = urllib.request.Request(game_info['url'], headers={'User-Agent': 'zwalker/0.1'})
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
            dest_path.write_bytes(data)
        print(f"✓ ({len(data):,} bytes)")
        return 'success'
    except urllib.error.HTTPError as e:
        print(f"✗ HTTP {e.code}")
        return 'failed'
    except urllib.error.URLError as e:
        print(f"✗ {e.reason}")
        return 'failed'
    except Exception as e:
        print(f"✗ {e}")
        return 'failed'

def main():
    # Create destination directory
    GAMES_DIR.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("Downloading Untested Games from game_list.txt")
    print("="*80)
    print()

    # Parse game list
    games_to_download = parse_game_list()

    if not games_to_download:
        print("No untested games found in game_list.txt")
        return 0

    print(f"Found {len(games_to_download)} untested games to download")
    print(f"Destination: {GAMES_DIR}")
    print()

    # Track statistics
    success_count = 0
    failed_count = 0
    skipped_count = 0

    # Download each game
    for i, game_info in enumerate(games_to_download, 1):
        print(f"[{i}/{len(games_to_download)}] ", end='')
        result = download_game(game_info, GAMES_DIR)

        if result == 'success':
            success_count += 1
        elif result == 'failed':
            failed_count += 1
        elif result == 'skipped':
            skipped_count += 1

        # Small delay to be respectful to servers
        if result == 'success':
            time.sleep(0.5)

    print()
    print("="*80)
    print("Download Summary")
    print("="*80)
    print(f"  Downloaded: {success_count:3} games")
    print(f"  Skipped:    {skipped_count:3} games (already exist)")
    print(f"  Failed:     {failed_count:3} games")
    print(f"  Total:      {len(games_to_download):3} games")
    print()
    print(f"Games stored in: {GAMES_DIR}")
    print()

    return 0 if failed_count == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
