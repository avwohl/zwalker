#!/usr/bin/env python3
"""
AI-powered game solver that COMPLETES games
Uses Anthropic Claude to solve games to completion
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from zwalker.walker import GameWalker
from zwalker.ai_assist import AIAssistant, create_context_from_walker


def is_game_won(output: str) -> bool:
    """Check if the game has been won"""
    win_patterns = [
        "you have won",
        "you win",
        "congratulations",
        "you've won",
        "victory",
        "you are victorious",
        "the end",
        "*** you have won ***",
        "you have completed",
        "well done",
        "you have succeeded",
    ]
    output_lower = output.lower()
    return any(pattern in output_lower for pattern in win_patterns)


def solve_game_to_completion(game_path, max_iterations=500):
    """Solve one game to completion using AI."""
    game_name = game_path.stem
    output_path = Path("solutions") / f"{game_name}_solution.json"

    if output_path.exists():
        # Check if it's actually complete
        existing = json.loads(output_path.read_text())
        if existing.get('completed', False):
            print(f"✓ SKIP {game_name} (already completed)")
            return None
        else:
            print(f"⟳ RETRY {game_name} (incomplete solution)")

    print(f"\n{'='*70}")
    print(f"SOLVING TO COMPLETION: {game_name}")
    print(f"{'='*70}")

    try:
        game_data = game_path.read_bytes()
        walker = GameWalker(game_data)
        initial_output = walker.start()

        # Check if we already won (some games auto-complete)
        if is_game_won(initial_output):
            print(f"✓ AUTO-WIN {game_name}")
            save_solution(output_path, game_name, walker, True)
            return True

        ai = AIAssistant(backend='anthropic')

        last_output = initial_output
        stuck_counter = 0
        last_room_count = 0

        for iteration in range(max_iterations):
            # Create rich context for AI
            context = create_context_from_walker(walker)

            # Get AI suggestions - the AI should be goal-oriented
            response = ai.analyze(context)

            if iteration % 10 == 0:
                print(f"  [{iteration}/{max_iterations}] Rooms: {len(walker.rooms)}, Commands: {len(walker.full_transcript)}")

            # Try multiple commands if first ones don't work
            command_tried = False
            for cmd in response.suggested_commands[:5]:  # Try top 5 suggestions
                result = walker.try_command(cmd)
                command_tried = True
                last_output = result.output

                # Check if we won!
                if is_game_won(last_output):
                    print(f"\n{'='*70}")
                    print(f"🎉 WON {game_name} in {len(walker.full_transcript)} commands!")
                    print(f"{'='*70}")
                    save_solution(output_path, game_name, walker, True)
                    return True

                # If this command made progress (new room or interesting), stop trying alternates
                if result.new_room or result.interesting:
                    stuck_counter = 0
                    break

            if not command_tried:
                print(f"  AI gave up at iteration {iteration}")
                break

            # Detect if stuck
            current_room_count = len(walker.rooms)
            if current_room_count == last_room_count:
                stuck_counter += 1
            else:
                stuck_counter = 0
                last_room_count = current_room_count

            # If stuck for too long, give more explicit instructions
            if stuck_counter > 20:
                print(f"  WARNING: Stuck in same area for 20 iterations")
                # Continue anyway - AI might find a way out

        # Didn't complete
        print(f"✗ INCOMPLETE {game_name}: {len(walker.rooms)} rooms, {len(walker.full_transcript)} commands")
        save_solution(output_path, game_name, walker, False)
        return False

    except Exception as e:
        print(f"✗ ERROR {game_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


def save_solution(output_path, game_name, walker, completed):
    """Save the solution (complete or partial)"""
    result = {
        'game': game_name,
        'completed': completed,
        'total_rooms': len(walker.rooms),
        'total_commands': len(walker.full_transcript),
        'rooms_visited': list(walker.known_room_names),
        'commands': [cmd for cmd, _ in walker.full_transcript],
    }

    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2))

    status = "COMPLETE" if completed else "INCOMPLETE"
    print(f"  Saved {status} solution: {result['total_commands']} commands")


def main():
    games = sorted(Path("games/zcode").glob("*.z[3458]"))
    print(f"Solving {len(games)} games TO COMPLETION")
    print(f"Max iterations per game: 500")
    print(f"Backend: Anthropic Claude\n")

    completed = 0
    incomplete = 0
    skipped = 0
    failed = 0

    for i, game in enumerate(games, 1):
        print(f"\n[{i}/{len(games)}] {game.name}")
        result = solve_game_to_completion(game)

        if result is None:
            skipped += 1
        elif result is True:
            completed += 1
        elif result is False:
            incomplete += 1
        else:
            failed += 1

    print(f"\n{'='*70}")
    print(f"FINAL SUMMARY:")
    print(f"  COMPLETED: {completed} games")
    print(f"  INCOMPLETE: {incomplete} games")
    print(f"  SKIPPED: {skipped} games")
    print(f"  FAILED: {failed} games")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
