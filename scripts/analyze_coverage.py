#!/usr/bin/env python3
"""
Analyze game coverage and solution quality
"""

import json
from pathlib import Path
from collections import defaultdict

def analyze_solutions():
    """Analyze all solution files"""
    solutions_dir = Path("solutions")
    solutions = []

    for sol_file in solutions_dir.glob("*_solution.json"):
        if any(x in sol_file.name for x in ['progress', 'state', 'test', 'batch']):
            continue

        try:
            data = json.loads(sol_file.read_text())
            game_name = sol_file.stem.replace('_solution', '')

            # Get command count
            commands = data.get('commands', []) or data.get('solution_commands', [])
            cmd_count = len([c for c in commands if c])  # Non-empty commands

            # Get room count
            rooms = data.get('rooms_visited', []) or data.get('total_rooms', 0)
            room_count = len(rooms) if isinstance(rooms, list) else rooms

            # Determine format
            game_file = data.get('game', '')
            if '.z1' in game_file or 'z1' in sol_file.name:
                z_format = 'z1'
            elif '.z3' in game_file or any(g in game_name for g in ['zork', 'enchanter', 'trinity']):
                z_format = 'z3'
            elif '.z4' in game_file or 'amfv' in game_name or 'trinity' in game_name:
                z_format = 'z4'
            elif '.z5' in game_file:
                z_format = 'z5'
            elif '.z6' in game_file:
                z_format = 'z6'
            elif '.z8' in game_file:
                z_format = 'z8'
            else:
                z_format = 'z5'  # default guess

            solutions.append({
                'name': game_name,
                'commands': cmd_count,
                'rooms': room_count,
                'format': z_format,
                'file': sol_file.name
            })
        except Exception as e:
            print(f"Error reading {sol_file}: {e}")

    return solutions

def categorize_by_size(solutions):
    """Categorize games by command count"""
    tiny = [s for s in solutions if s['commands'] < 100]
    small = [s for s in solutions if 100 <= s['commands'] < 200]
    medium = [s for s in solutions if 200 <= s['commands'] < 400]
    large = [s for s in solutions if 400 <= s['commands'] < 800]
    huge = [s for s in solutions if s['commands'] >= 800]

    return {
        'tiny': tiny,
        'small': small,
        'medium': medium,
        'large': large,
        'huge': huge
    }

def categorize_by_format(solutions):
    """Categorize games by Z-machine version"""
    by_format = defaultdict(list)
    for sol in solutions:
        by_format[sol['format']].append(sol)
    return dict(by_format)

def main():
    print("="*60)
    print("ZWalker Coverage Analysis")
    print("="*60)
    print()

    solutions = analyze_solutions()

    print(f"Total solutions: {len(solutions)}")
    print()

    # By size
    print("By Size:")
    print("-" * 60)
    by_size = categorize_by_size(solutions)
    for size, games in by_size.items():
        print(f"  {size.capitalize():10} (<{size_ranges[size]:4} cmds): {len(games):3} games")
    print()

    # By format
    print("By Format:")
    print("-" * 60)
    by_format = categorize_by_format(solutions)
    for fmt in sorted(by_format.keys()):
        games = by_format[fmt]
        total_cmds = sum(g['commands'] for g in games)
        avg_cmds = total_cmds / len(games) if games else 0
        print(f"  {fmt:4}: {len(games):3} games, {total_cmds:6} total cmds, {avg_cmds:6.1f} avg")
    print()

    # Top games by command count
    print("Top 10 by Command Count:")
    print("-" * 60)
    top_games = sorted(solutions, key=lambda x: x['commands'], reverse=True)[:10]
    for i, game in enumerate(top_games, 1):
        print(f"  {i:2}. {game['name']:20} - {game['commands']:4} commands ({game['format']})")
    print()

    # Statistics
    total_commands = sum(s['commands'] for s in solutions)
    total_rooms = sum(s['rooms'] for s in solutions)
    avg_commands = total_commands / len(solutions)
    avg_rooms = total_rooms / len(solutions)

    print("Statistics:")
    print("-" * 60)
    print(f"  Total commands:  {total_commands:,}")
    print(f"  Total rooms:     {total_rooms:,}")
    print(f"  Avg commands:    {avg_commands:.1f}")
    print(f"  Avg rooms:       {avg_rooms:.1f}")
    print()

    # Test scripts
    test_scripts = list(Path("scripts").glob("test_*_solution.js"))
    z2js_files = list(Path("scripts").glob("*_z2js.js"))
    z2js_files = [f for f in z2js_files if not f.name.startswith('test_')]

    print("Test Infrastructure:")
    print("-" * 60)
    print(f"  Test scripts:    {len(test_scripts)}")
    print(f"  Z2JS files:      {len(z2js_files)}")
    print(f"  Testable:        {len(z2js_files)} games")
    print(f"  Pending:         {len(solutions) - len(z2js_files)} games")
    print()

size_ranges = {
    'tiny': 100,
    'small': 200,
    'medium': 400,
    'large': 800,
    'huge': 9999
}

if __name__ == "__main__":
    main()
