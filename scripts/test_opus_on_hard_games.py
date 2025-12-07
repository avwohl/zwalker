#!/usr/bin/env python3
"""
Test the advanced Opus solver on the hardest IF games.

This tests if the solver can actually handle complex puzzles, not just simple games.
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime


# Hard games that should test the solver's capabilities
HARD_GAMES = [
    # Moderately hard - good starting tests
    ("detective.z5", "Detective", 300, "Simple mystery with a few puzzles"),
    ("shade.z5", "Shade", 200, "One-room puzzle with psychological elements"),

    # Classic IF - medium difficulty
    ("zork1.z3", "Zork I", 500, "Classic adventure, ~20 treasures, maze, troll, thief"),
    ("enchanter.z3", "Enchanter", 500, "Infocom magic system, spell puzzles"),

    # Complex narrative
    ("photopia.z5", "Photopia", 300, "Narrative game with multiple perspectives"),
    ("trinity.z4", "Trinity", 600, "Time-travel puzzles, multiple locations/eras"),

    # Puzzle-focused
    ("curses.z5", "Curses", 800, "Notoriously difficult, 550 points, time travel"),
    ("anchor.z8", "Anchorhead", 600, "Lovecraftian horror, multiple chapters"),

    # Very hard
    ("zork2.z3", "Zork II", 600, "Harder than Zork I, wizard, unicorn"),
]


def test_game(game_file: str, game_name: str, max_turns: int, description: str) -> dict:
    """Test solver on a single game"""
    print("\n" + "="*80)
    print(f"TESTING: {game_name}")
    print("="*80)
    print(f"File: {game_file}")
    print(f"Description: {description}")
    print(f"Max turns: {max_turns}")
    print("="*80)

    game_path = Path("games/zcode") / game_file

    if not game_path.exists():
        print(f"⚠️  SKIP: File not found: {game_path}")
        return {"status": "skipped", "reason": "file_not_found"}

    # Check if already has a complete solution
    solution_file = Path("solutions") / f"{game_path.stem}_solution.json"
    if solution_file.exists():
        existing = json.loads(solution_file.read_text())
        if existing.get("completed") and existing.get("source") == "advanced_ai_opus":
            print(f"✓ SKIP: Already solved with Opus")
            return {"status": "already_solved", "data": existing}

    # Run solver
    start_time = datetime.now()

    try:
        result = subprocess.run(
            ["python3", "scripts/solve_with_opus.py", str(game_path),
             "--max-turns", str(max_turns)],
            capture_output=False,  # Show output in real-time
            timeout=max_turns * 3  # ~3 seconds per turn max
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Load result
        if solution_file.exists():
            solution = json.loads(solution_file.read_text())

            return {
                "status": "completed" if solution.get("completed") else "attempted",
                "won": solution.get("completed", False),
                "turns": solution.get("turns_taken", 0),
                "commands": solution.get("total_commands", 0),
                "rooms": solution.get("total_rooms", 0),
                "duration_seconds": duration,
                "data": solution
            }

    except subprocess.TimeoutExpired:
        print(f"\n⏱️  TIMEOUT after {max_turns * 3}s")
        return {"status": "timeout", "max_turns": max_turns}

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return {"status": "error", "error": str(e)}

    return {"status": "unknown"}


def main():
    print("="*80)
    print("ADVANCED SOLVER - HARD GAMES TEST")
    print("="*80)
    print(f"Testing on {len(HARD_GAMES)} challenging IF games")
    print(f"Using: Claude Opus 4.5")
    print("="*80)

    results = []
    wins = 0
    attempts = 0

    for game_file, game_name, max_turns, description in HARD_GAMES:
        result = test_game(game_file, game_name, max_turns, description)
        result['game'] = game_name
        result['file'] = game_file
        result['description'] = description

        results.append(result)

        if result['status'] == 'completed' or result['status'] == 'attempted':
            attempts += 1
            if result.get('won'):
                wins += 1

    # Summary report
    print("\n\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)

    print(f"\nGames tested: {len(HARD_GAMES)}")
    print(f"Games attempted: {attempts}")
    print(f"Games won: {wins}")
    if attempts > 0:
        print(f"Success rate: {wins/attempts*100:.1f}%")

    print("\n" + "-"*80)
    print("DETAILED RESULTS:")
    print("-"*80)

    for r in results:
        status_icon = {
            'completed': '✓' if r.get('won') else '⚠',
            'attempted': '⚠',
            'skipped': '⊘',
            'timeout': '⏱',
            'error': '❌',
            'already_solved': '✓✓'
        }.get(r['status'], '?')

        game = r['game']
        status = r['status']

        if r.get('won'):
            print(f"{status_icon} {game:30s} WON in {r.get('turns', 0)} turns ({r.get('commands', 0)} commands)")
        elif status == 'attempted':
            print(f"{status_icon} {game:30s} Not completed - {r.get('rooms', 0)} rooms, {r.get('commands', 0)} commands")
        elif status == 'already_solved':
            print(f"{status_icon} {game:30s} Already solved")
        else:
            print(f"{status_icon} {game:30s} {status}")

    # Save detailed report
    report_file = Path("solutions/opus_hard_games_report.json")
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'model': 'claude-opus-4-20250514',
            'total_games': len(HARD_GAMES),
            'wins': wins,
            'attempts': attempts,
            'success_rate': wins/attempts if attempts > 0 else 0,
            'results': results
        }, f, indent=2)

    print(f"\n✓ Detailed report saved to: {report_file}")

    # Recommendations
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    if wins >= 5:
        print("🎉 Excellent! Solver successfully handles complex games.")
        print("   This demonstrates strong IF understanding and puzzle-solving ability.")
    elif wins >= 3:
        print("✓ Good progress. Solver can handle some complex games.")
        print("  May need refinement for hardest puzzles.")
    elif wins >= 1:
        print("⚠ Limited success. Solver needs improvement for hard games.")
    else:
        print("❌ Solver struggling with complex games.")
        print("   May need architectural changes or better prompting.")

    return 0 if wins > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
