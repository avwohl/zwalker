#!/usr/bin/env python3
"""
Run AI solver on games that have no solution yet
Focus on simple games that are likely to be solvable
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant, create_context_from_walker


# Games without any solution - prioritized by likely difficulty
GAPS_PRIORITIZED = [
    # Very short/simple games (likely to complete)
    ("booth.z5", "Pick Up the Phone Booth and Die", 50),
    ("etude.z5", "Etude", 100),
    ("detective.z5", "Detective", 150),
    ("failsafe.z5", "FailSafe", 150),
    ("animals.z5", "Animals", 100),
    ("bunny.z5", "Bunny", 100),
    ("candy.z5", "Candy", 100),
    ("zombies.z5", "Zombies", 150),
    ("theatre.z5", "Theatre", 150),
    ("shade.z5", "Shade", 200),

    # Medium complexity
    ("allroads.z5", "All Roads", 200),
    ("adverbum.z5", "Ad Verbum", 250),
    ("edifice.z5", "The Edifice", 250),
    ("cheeseshop.z5", "Cheeseshop", 150),
    ("winter.z5", "Winter Wonderland", 150),
    ("acorncourt.z5", "Acorn Court", 200),

    # Classic adventures (harder)
    ("advent.z3", "Adventure", 300),
    ("catseye.z3", "Cat's Eye", 200),

    # Larger games (may not complete)
    ("tangle.z5", "Spider and Web", 400),
    ("devours.z5", "All Things Devours", 300),
    ("dracula.z8", "Dracula", 400),
    ("coldiron.z8", "Cold Iron", 400),
    ("enemies.z8", "Enemies", 400),
    ("amfv.z4", "A Mind Forever Voyaging", 400),

    # Test/Czech files (skip for now)
    # ("czech.z8", "Czech Test", 50),
    # ("gntests.z5", "GN Tests", 50),

    # Large adventure ports
    ("adv440.z8", "Adventure 440", 400),
    ("adv550.z8", "Adventure 550", 400),
]


def solve_game(game_file, game_name, max_iterations=100):
    """Solve a single game and return results."""
    print(f"\n{'='*60}")
    print(f"GAME: {game_name}")
    print(f"FILE: {game_file}")
    print(f"MAX ITERATIONS: {max_iterations}")
    print(f"{'='*60}\n")

    game_path = Path("games/zcode") / game_file
    if not game_path.exists():
        print(f"⚠ SKIP: File not found: {game_path}")
        return None

    # Check if already has solution
    output_name = game_file.replace('.z3', '').replace('.z4', '').replace('.z5', '').replace('.z8', '')
    output_file = Path("solutions") / f"{output_name}_solution.json"

    if output_file.exists():
        print(f"✓ SKIP: Already has solution (found {output_file})")
        return None

    try:
        # Load game
        with open(game_path, 'rb') as f:
            game_data = f.read()

        print(f"Loaded {len(game_data)} bytes")

        # Create walker
        walker = GameWalker(game_data)

        # Start game
        output = walker.start()
        print(f"Starting: {output[:100].replace(chr(10), ' ')}...")

        # Create AI assistant
        ai = AIAssistant(backend="anthropic", use_real_ai=True)

        # Solve iteratively
        print(f"\nRunning AI solver (max {max_iterations} iterations)...")
        stuck_count = 0
        last_room_count = 0

        for iteration in range(max_iterations):
            # Get context
            context = create_context_from_walker(walker)

            # Get AI decision
            command = ai.suggest_next_command(context)

            if not command:
                print(f"  AI gave up at iteration {iteration}")
                break

            # Try command
            result = walker.try_command(command)

            # Progress reporting
            if iteration % 20 == 0:
                print(f"  [{iteration}/{max_iterations}] Rooms: {len(walker.rooms_visited)}, Commands: {len(walker.command_history)}")

            # Check if making progress
            if len(walker.rooms_visited) == last_room_count:
                stuck_count += 1
                if stuck_count >= 30:
                    print(f"  Stuck - no new rooms for 30 iterations")
                    break
            else:
                stuck_count = 0
                last_room_count = len(walker.rooms_visited)

            # Check if won
            if any(phrase in result.lower() for phrase in [
                'you have won', 'congratulations', 'victory', '*** you have won ***'
            ]):
                print(f"\n  ✓ GAME WON at iteration {iteration}!")
                break

        # Save results
        result = {
            'game': str(game_path),
            'total_rooms': len(walker.rooms_visited),
            'total_commands': len(walker.command_history),
            'rooms_visited': list(walker.rooms_visited),
            'commands': [cmd['command'] for cmd in walker.command_history],
            'completed': any('won' in str(walker.command_history[-1:]).lower()),
            'source': 'AI'
        }

        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        status = "✓ WON" if result['completed'] else "⚠ INCOMPLETE"
        print(f"\n{status}: Saved to {output_file}")
        print(f"  Rooms: {result['total_rooms']}")
        print(f"  Commands: {result['total_commands']}")

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    print("="*60)
    print("ZWalker - AI Solver for Remaining Games")
    print("="*60)
    print(f"Total games to attempt: {len(GAPS_PRIORITIZED)}")
    print(f"Using AI: Anthropic Claude")
    print("="*60)

    results = []
    completed = 0
    skipped = 0
    failed = 0

    for i, (game_file, game_name, max_iter) in enumerate(GAPS_PRIORITIZED, 1):
        print(f"\n{'#'*60}")
        print(f"[{i}/{len(GAPS_PRIORITIZED)}] {game_name}")
        print(f"{'#'*60}")

        result = solve_game(game_file, game_name, max_iterations=max_iter)

        if result is None:
            skipped += 1
        elif result.get('completed'):
            completed += 1
            results.append({
                'game': game_name,
                'file': game_file,
                'completed': True,
                'rooms': result['total_rooms'],
                'commands': result['total_commands'],
            })
        else:
            results.append({
                'game': game_name,
                'file': game_file,
                'completed': False,
                'rooms': result['total_rooms'],
                'commands': result['total_commands'],
            })

    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total games attempted: {len(GAPS_PRIORITIZED)}")
    print(f"✓ Completed (won): {completed}")
    print(f"⚠ Incomplete: {len(results) - completed}")
    print(f"- Skipped: {skipped}")
    print(f"✗ Failed: {failed}")
    print("="*60)

    # Show completed games
    if completed > 0:
        print(f"\n✓ GAMES WON:")
        for r in results:
            if r.get('completed'):
                print(f"  - {r['game']}: {r['rooms']} rooms, {r['commands']} commands")

    # Save summary
    summary_file = Path("solutions/ai_solver_gaps_summary.json")
    with open(summary_file, 'w') as f:
        json.dump({
            'total': len(GAPS_PRIORITIZED),
            'completed': completed,
            'incomplete': len(results) - completed,
            'skipped': skipped,
            'failed': failed,
            'results': results,
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
