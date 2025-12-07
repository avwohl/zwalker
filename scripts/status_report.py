#!/usr/bin/env python3
"""
Generate comprehensive status report for top 100 games coverage
Shows: available .z files, AI solutions, human walkthroughs, and gaps
"""

import json
from pathlib import Path
from collections import defaultdict

def main():
    # Get all available .z files
    games_dir = Path("games/zcode")
    available_games = {}
    for f in games_dir.glob("*.z[3458]"):
        game_name = f.stem.lower()
        available_games[game_name] = {
            'file': f.name,
            'version': f.suffix,
            'path': str(f)
        }

    # Check AI solutions
    solutions_dir = Path("solutions")
    ai_solutions = {}
    for f in solutions_dir.glob("*_solution.json"):
        game = f.stem.replace("_solution", "").lower()
        try:
            data = json.loads(f.read_text())
            ai_solutions[game] = {
                'completed': data.get('completed', False),
                'rooms': data.get('total_rooms', 0),
                'commands': data.get('total_commands', 0),
                'path': str(f)
            }
        except:
            pass

    # Check human walkthroughs
    walkthroughs_dir = Path("walkthroughs")
    walkthroughs_dir.mkdir(exist_ok=True)
    human_walkthroughs = {}
    for f in walkthroughs_dir.glob("*_human_walkthrough.txt"):
        game = f.stem.replace("_human_walkthrough", "").lower()
        human_walkthroughs[game] = {
            'size': f.stat().st_size,
            'path': str(f)
        }

    # Check command JSONs
    command_jsons = {}
    for f in walkthroughs_dir.glob("*_commands.json"):
        game = f.stem.replace("_commands", "").lower()
        try:
            data = json.loads(f.read_text())
            command_jsons[game] = {
                'commands': data.get('total_commands', 0),
                'path': str(f)
            }
        except:
            pass

    # Generate report
    print("="*80)
    print("ZWALKER TOP 100 STATUS REPORT")
    print("="*80)
    print()

    print(f"AVAILABLE Z-FILES: {len(available_games)}")
    z_versions = defaultdict(list)
    for game, info in available_games.items():
        z_versions[info['version']].append(game)

    for version in sorted(z_versions.keys()):
        print(f"  {version}: {len(z_versions[version])} games")
    print()

    print(f"AI SOLUTIONS: {len(ai_solutions)}")
    completed = [g for g, info in ai_solutions.items() if info['completed']]
    incomplete = [g for g, info in ai_solutions.items() if not info['completed']]
    print(f"  ✓ Completed (won): {len(completed)}")
    print(f"  ⚠ Incomplete (exploration): {len(incomplete)}")
    print()

    print(f"HUMAN WALKTHROUGHS: {len(human_walkthroughs)}")
    print(f"  Converted to JSON: {len(command_jsons)}")
    print()

    # Coverage analysis
    all_games = set(available_games.keys())
    has_ai = set(ai_solutions.keys())
    has_human = set(human_walkthroughs.keys())
    has_ai_complete = set(g for g, info in ai_solutions.items() if info['completed'])

    print("COVERAGE BREAKDOWN:")
    print(f"  ✓ Complete AI solution: {len(has_ai_complete)} games")
    print(f"  ⚠ Incomplete AI solution: {len(has_ai - has_ai_complete)} games")
    print(f"  📖 Human walkthrough: {len(has_human)} games")
    print(f"  ✗ No solution at all: {len(all_games - has_ai - has_human)} games")
    print()

    # Detailed breakdown
    print("COMPLETE SOLUTIONS (AI):")
    for game in sorted(has_ai_complete):
        info = ai_solutions[game]
        print(f"  ✓ {game:20s} - {info['rooms']:3d} rooms, {info['commands']:4d} commands")
    print()

    print("INCOMPLETE AI SOLUTIONS:")
    for game in sorted(has_ai - has_ai_complete):
        info = ai_solutions[game]
        print(f"  ⚠ {game:20s} - {info['rooms']:3d} rooms, {info['commands']:4d} commands")
    print()

    print("HUMAN WALKTHROUGHS AVAILABLE:")
    for game in sorted(has_human):
        print(f"  📖 {game:20s} - {human_walkthroughs[game]['size']:6d} bytes")
    print()

    print("GAPS (no solution):")
    gaps = sorted(all_games - has_ai - has_human)
    for game in gaps[:30]:
        print(f"  ✗ {game:20s} ({available_games[game]['version']})")
    if len(gaps) > 30:
        print(f"  ... and {len(gaps) - 30} more")
    print()

    # Recommendations
    print("="*80)
    print("RECOMMENDATIONS:")
    print("="*80)
    print()
    print("1. FETCH HUMAN WALKTHROUGHS:")
    print(f"   Run: python3 scripts/fetch_walkthroughs.py")
    print(f"   This will download {len([g for g in gaps if g in ['zork1', 'zork2', 'enchanter', 'curses', 'trinity']])}+ walkthroughs from IF Archive")
    print()
    print("2. CONVERT INCOMPLETE AI TO HUMAN:")
    print(f"   {len(incomplete)} games have incomplete AI solutions")
    print(f"   Check if human walkthroughs exist for these games")
    print()
    print("3. RETRY AI SOLVER ON SIMPLE GAMES:")
    print(f"   {len(gaps)} games have no solution attempt yet")
    print(f"   Many may be simple enough for AI to complete")
    print()

    # Summary for z2js
    print("="*80)
    print("FOR Z2JS TESTING:")
    print("="*80)
    total_usable = len(has_ai_complete) + len(has_human)
    print(f"Total usable solutions: {total_usable}/{len(all_games)}")
    print(f"  - {len(has_ai_complete)} complete AI solutions")
    print(f"  - {len(has_human)} human walkthroughs (need conversion)")
    print(f"  - {len(has_ai - has_ai_complete)} incomplete (can be used for partial testing)")
    print()
    print(f"Target: Get to 50+ complete solutions for comprehensive testing")
    print()

    # Save JSON report
    report = {
        'total_games': len(all_games),
        'ai_complete': len(has_ai_complete),
        'ai_incomplete': len(has_ai - has_ai_complete),
        'human_walkthroughs': len(has_human),
        'no_solution': len(gaps),
        'games': {
            game: {
                'has_zfile': True,
                'zversion': available_games[game]['version'],
                'ai_complete': game in has_ai_complete,
                'ai_incomplete': game in (has_ai - has_ai_complete),
                'human_walkthrough': game in has_human,
            }
            for game in all_games
        }
    }

    report_file = Path("docs/TOP100_STATUS.json")
    report_file.write_text(json.dumps(report, indent=2))
    print(f"Detailed report saved to: {report_file}")

if __name__ == "__main__":
    main()
