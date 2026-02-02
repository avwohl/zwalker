#!/usr/bin/env python3
"""
Update game_list.txt with zwalker_status based on existing solutions.
"""

import os
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
SOLUTIONS_DIR = PROJECT_ROOT / "solutions"
GAME_LIST_FILE = PROJECT_ROOT / "games" / "game_list.txt"

def get_solved_games():
    """Get list of solved game names from solutions directory."""
    solved = set()
    if SOLUTIONS_DIR.exists():
        for solution_file in SOLUTIONS_DIR.glob("*_solution.json"):
            game_name = solution_file.stem.replace("_solution", "")
            solved.add(game_name.lower())
    return solved

def normalize_game_name(name):
    """Normalize game name for comparison."""
    # Remove common punctuation and spaces
    return name.lower().replace(" ", "").replace("'", "").replace("-", "")

def update_game_list():
    """Update game_list.txt with current zwalker status."""
    solved_games = get_solved_games()

    # Create mapping of normalized names to actual solution names
    solved_normalized = {}
    for game in solved_games:
        norm = normalize_game_name(game)
        solved_normalized[norm] = game

    if not GAME_LIST_FILE.exists():
        print(f"Error: {GAME_LIST_FILE} not found")
        return 1

    lines = []
    updated_count = 0

    with open(GAME_LIST_FILE, 'r') as f:
        for line in f:
            original_line = line

            # Skip comments and empty lines
            if line.strip().startswith('#') or line.strip().startswith('=') or not line.strip():
                lines.append(original_line)
                continue

            # Parse game line: name|ifdb_id|format|url|zwalker_status|zorkie_status|z2js_status
            if '|' in line:
                parts = line.strip().split('|')
                if len(parts) >= 5:
                    game_name = parts[0]
                    norm_name = normalize_game_name(game_name)

                    # Check if this game is solved
                    is_solved = False
                    solution_name = None

                    # Direct match
                    if norm_name in solved_normalized:
                        is_solved = True
                        solution_name = solved_normalized[norm_name]
                    # Check for partial matches (e.g., "Zork I" -> "zork1")
                    else:
                        for solved_norm, solved_orig in solved_normalized.items():
                            if solved_norm in norm_name or norm_name in solved_norm:
                                is_solved = True
                                solution_name = solved_orig
                                break

                    # Update status
                    if is_solved:
                        parts[4] = 'pass'
                        updated_count += 1
                        print(f"✓ {game_name} -> {solution_name}")
                    elif parts[4] == 'untested':
                        # Keep as untested if not solved
                        pass

                    # Reconstruct line
                    line = '|'.join(parts) + '\n'

            lines.append(line)

    # Write updated file
    with open(GAME_LIST_FILE, 'w') as f:
        f.writelines(lines)

    print(f"\n✓ Updated {updated_count} games to 'pass' status")
    print(f"✓ Total solved games: {len(solved_games)}")
    return 0

if __name__ == '__main__':
    sys.exit(update_game_list())
