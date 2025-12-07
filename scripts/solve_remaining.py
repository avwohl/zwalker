#!/usr/bin/env python3
"""
Generate walkthroughs for all games we have that haven't been solved yet.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.zmachine import ZMachine
from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant, create_context_from_walker


def solve_game(game_path, max_iterations=100):
    """Solve a single game and return results."""
    game_name = game_path.stem
    
    print(f"\n{'='*60}")
    print(f"GAME: {game_name}")
    print(f"FILE: {game_path}")
    print(f"{'='*60}\n")

    # Check if already solved
    output_file = Path("solutions") / f"{game_name}_solution.json"

    if output_file.exists():
        print(f"✓ SKIP: Already solved")
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
        print(f"Starting: {output[:100]}...")

        # Create AI assistant
        ai = AIAssistant(backend="anthropic")

        # Solve iteratively
        print(f"Running AI solver (max {max_iterations} iterations)...")
        for iteration in range(max_iterations):
            # Get context
            context = create_context_from_walker(walker)

            # Get AI decision
            command = ai.suggest_next_command(context)

            if not command:
                print(f"AI gave up at iteration {iteration}")
                break

            # Try command
            result = walker.try_command(command)

            if iteration % 10 == 0:
                print(f"  [{iteration}/{max_iterations}] {len(walker.rooms_visited)} rooms, {len(walker.command_history)} commands")

            # Check if stuck (repeating same room)
            if len(walker.command_history) > 20:
                recent_rooms = [cmd.get('room') for cmd in walker.command_history[-20:]]
                if len(set(recent_rooms)) <= 2:
                    print(f"Stuck in same rooms, stopping at iteration {iteration}")
                    break

        # Save results
        result = {
            'game': str(game_path),
            'total_rooms': len(walker.rooms_visited),
            'total_commands': len(walker.command_history),
            'rooms_visited': list(walker.rooms_visited),
            'commands': [cmd['command'] for cmd in walker.command_history],
        }

        output_file.parent.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

        print(f"\n✓ SUCCESS: Saved to {output_file}")
        print(f"  Rooms: {result['total_rooms']}")
        print(f"  Commands: {result['total_commands']}")

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    # Find all game files
    games_dir = Path("games/zcode")
    game_files = sorted(games_dir.glob("*.z[3458]"))
    
    print("="*60)
    print("ZWalker - Batch Walkthrough Generator")
    print("="*60)
    print(f"Found {len(game_files)} game files")
    print(f"Using AI: Anthropic Claude")
    print(f"Max iterations per game: 100")
    print("="*60)

    results = []
    completed = 0
    skipped = 0
    failed = 0

    for i, game_path in enumerate(game_files, 1):
        print(f"\n[{i}/{len(game_files)}] Processing: {game_path.name}")

        result = solve_game(game_path, max_iterations=100)

        if result is None:
            skipped += 1
        elif result:
            completed += 1
            results.append({
                'game': game_path.name,
                'rooms': result['total_rooms'],
                'commands': result['total_commands'],
            })
        else:
            failed += 1

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Total games: {len(game_files)}")
    print(f"Completed: {completed}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {failed}")
    print("="*60)

    # Save summary
    summary_file = Path("solutions/batch_summary.json")
    summary_file.parent.mkdir(exist_ok=True)
    with open(summary_file, 'w') as f:
        json.dump({
            'total': len(game_files),
            'completed': completed,
            'skipped': skipped,
            'failed': failed,
            'results': results,
        }, f, indent=2)

    print(f"\nSummary saved to: {summary_file}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
