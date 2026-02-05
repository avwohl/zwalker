#!/usr/bin/env python3
"""
Audit solution files and update game_list.txt to mark games with solutions as "pass".
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Set

# Configuration
SOLUTIONS_DIR = Path("/home/wohl/src/zwalker/solutions")
GAME_LIST_PATH = Path("/home/wohl/src/zwalker/games/game_list.txt")
EXCLUDE_FILES = {"batch_summary.json", ".gitkeep"}


def normalize_name(name: str) -> str:
    """Normalize game name for comparison (lowercase, remove special chars)."""
    # Convert to lowercase
    name = name.lower()
    # Remove common prefixes/suffixes
    name = re.sub(r'^(the|a|an)\s+', '', name)
    # Replace punctuation and spaces with empty string for comparison
    name = re.sub(r'[^a-z0-9]+', '', name)
    return name


def extract_game_name(filename: str) -> str:
    """Extract game name from solution filename (e.g., 'zork1_solution.json' -> 'zork1')."""
    # Remove _solution.json suffix
    if filename.endswith('_solution.json'):
        return filename[:-14]  # Remove '_solution.json'
    return filename


def list_solution_files(solutions_dir: Path) -> List[str]:
    """List all solution files in the solutions directory."""
    if not solutions_dir.exists():
        print(f"Error: Solutions directory not found: {solutions_dir}")
        return []
    
    solution_files = []
    for file in solutions_dir.iterdir():
        if file.is_file() and file.name not in EXCLUDE_FILES:
            if file.name.endswith('_solution.json'):
                solution_files.append(file.name)
    
    return sorted(solution_files)


def parse_game_list(game_list_path: Path) -> List[Dict]:
    """Parse game_list.txt and return list of game entries with line numbers."""
    if not game_list_path.exists():
        print(f"Error: game_list.txt not found: {game_list_path}")
        return []
    
    games = []
    with open(game_list_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, 1):
        # Skip comments, empty lines, and separator lines
        stripped = line.strip()
        if not stripped or stripped.startswith('#') or stripped.startswith('='):
            continue
        
        # Parse game entry: name | ifdb_id | format | url | zwalker_status | ...
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 5:
            games.append({
                'line_num': line_num,
                'line_index': line_num - 1,  # 0-based index for list
                'original_line': line,
                'name': parts[0],
                'ifdb_id': parts[1],
                'format': parts[2],
                'url': parts[3],
                'zwalker_status': parts[4],
                'other_fields': parts[5:] if len(parts) > 5 else []
            })
    
    return games


def create_name_mapping(games: List[Dict]) -> Dict[str, Dict]:
    """Create a mapping from normalized names to game entries."""
    mapping = {}
    for game in games:
        normalized = normalize_name(game['name'])
        if normalized in mapping:
            print(f"Warning: Duplicate normalized name '{normalized}' for games:")
            print(f"  - {mapping[normalized]['name']}")
            print(f"  - {game['name']}")
        mapping[normalized] = game
    return mapping


def match_solution_to_game(solution_name: str, name_mapping: Dict[str, Dict]) -> Dict:
    """Match a solution file to a game entry using fuzzy matching."""
    normalized_solution = normalize_name(solution_name)
    
    # Direct match
    if normalized_solution in name_mapping:
        return name_mapping[normalized_solution]
    
    # Try partial matches
    for normalized_game, game in name_mapping.items():
        # Check if solution name is contained in game name or vice versa
        if normalized_solution in normalized_game or normalized_game in normalized_solution:
            return game
    
    return None


def backup_file(file_path: Path) -> Path:
    """Create a backup of the file with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
    
    with open(file_path, 'r', encoding='utf-8') as src:
        content = src.read()
    with open(backup_path, 'w', encoding='utf-8') as dst:
        dst.write(content)
    
    return backup_path


def update_game_list(game_list_path: Path, games_to_update: List[Dict]) -> int:
    """Update game_list.txt to mark games as 'pass' if they have solutions."""
    if not games_to_update:
        return 0
    
    # Read all lines
    with open(game_list_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update lines
    updated_count = 0
    for game in games_to_update:
        line_index = game['line_index']
        original_line = lines[line_index]
        
        # Parse and update the line
        parts = [p.strip() for p in original_line.split('|')]
        if len(parts) >= 5:
            old_status = parts[4]
            if old_status != 'pass':
                parts[4] = 'pass'
                new_line = ' | '.join(parts) + '\n' if original_line.endswith('\n') else ' | '.join(parts)
                lines[line_index] = new_line
                updated_count += 1
                print(f"  Updated '{game['name']}': {old_status} -> pass")
            else:
                print(f"  Already marked as pass: '{game['name']}'")
    
    # Write back if there were updates
    if updated_count > 0:
        with open(game_list_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    return updated_count


def count_pass_status(game_list_path: Path) -> int:
    """Count how many games are marked as 'pass' in game_list.txt."""
    games = parse_game_list(game_list_path)
    return sum(1 for game in games if game['zwalker_status'] == 'pass')


def main():
    """Main execution function."""
    print("=" * 80)
    print("SOLUTION FILES AUDIT")
    print("=" * 80)
    print()
    
    # Step 1: List all solution files
    print("Step 1: Scanning solution files...")
    solution_files = list_solution_files(SOLUTIONS_DIR)
    print(f"Found {len(solution_files)} solution files in {SOLUTIONS_DIR}")
    print()
    
    # Step 2: Extract game names from solution files
    print("Step 2: Extracting game names from solution files...")
    solution_games = {}  # game_name -> filename
    for filename in solution_files:
        game_name = extract_game_name(filename)
        solution_games[game_name] = filename
    print(f"Extracted {len(solution_games)} game names")
    print()
    
    # Step 3: Parse game_list.txt
    print("Step 3: Parsing game_list.txt...")
    games = parse_game_list(GAME_LIST_PATH)
    print(f"Found {len(games)} game entries in game_list.txt")
    print()
    
    # Step 4: Create name mapping
    print("Step 4: Creating name mapping...")
    name_mapping = create_name_mapping(games)
    print(f"Created mapping for {len(name_mapping)} games")
    print()
    
    # Step 5: Match solutions to games
    print("Step 5: Matching solution files to game entries...")
    matched_games = []
    unmatched_solutions = []
    
    for solution_name, filename in solution_games.items():
        matched_game = match_solution_to_game(solution_name, name_mapping)
        if matched_game:
            matched_games.append({
                'solution_name': solution_name,
                'filename': filename,
                'game': matched_game
            })
            print(f"  ✓ Matched '{solution_name}' -> '{matched_game['name']}'")
        else:
            unmatched_solutions.append((solution_name, filename))
            print(f"  ✗ No match for '{solution_name}'")
    
    print()
    print(f"Matched: {len(matched_games)} / {len(solution_games)}")
    print()
    
    # Step 6: Create backup
    print("Step 6: Creating backup of game_list.txt...")
    backup_path = backup_file(GAME_LIST_PATH)
    print(f"Backup created: {backup_path}")
    print()
    
    # Step 7: Update game_list.txt
    print("Step 7: Updating game_list.txt...")
    games_to_update = [match['game'] for match in matched_games]
    updated_count = update_game_list(GAME_LIST_PATH, games_to_update)
    print()
    
    # Step 8: Final summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total solution files found: {len(solution_files)}")
    print(f"Game entries matched: {len(matched_games)}")
    print(f"Game entries updated: {updated_count}")
    print(f"Solutions without match: {len(unmatched_solutions)}")
    print()
    
    if unmatched_solutions:
        print("Unmatched solutions:")
        for solution_name, filename in unmatched_solutions:
            print(f"  - {filename} (extracted name: '{solution_name}')")
        print()
    
    # Count current pass status
    pass_count = count_pass_status(GAME_LIST_PATH)
    print(f"Current games marked as 'pass': {pass_count}")
    print()
    
    print(f"Backup saved to: {backup_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
